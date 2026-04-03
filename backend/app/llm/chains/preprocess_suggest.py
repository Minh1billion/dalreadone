from __future__ import annotations
import json

from app.llm.llm_engine import BaseLLMEngine
from app.llm.schemas import SuggestedLayer, CustomLayer
from app.llm.cost_tracker import CostTracker

_SYSTEM = """\
You are a senior data engineer and ML practitioner. You design preprocessing \
pipelines that are correct, minimal, and ready for model training. \
Respond ONLY with valid JSON - no markdown, no explanation outside the JSON object.\
"""

_HUMAN = """\
Design a complete, ordered preprocessing pipeline for the dataset described below.
Each layer must map to a concrete strategy class.

## EDA Context
{eda_json}

## Available strategies - exact class names and constructor params

### missing (handle nulls)
| Strategy         | When to use                                   | Key params                    |
|------------------|-----------------------------------------------|-------------------------------|
| MeanStrategy     | numeric, roughly symmetric distribution       | -                             |
| MedianStrategy   | numeric, skewed or has outliers               | -                             |
| ModeStrategy     | categorical or binary                         | -                             |
| ConstantStrategy | fill with a known sentinel value              | value: any                    |
| DropRowStrategy  | null_pct < 5% and row loss is acceptable      | -                             |
| DropColStrategy  | null_pct > 60% or column is irrelevant        | -                             |

### outlier (numeric non-label columns only)
| Strategy              | When to use                                       | Key params                        |
|-----------------------|---------------------------------------------------|-----------------------------------|
| IQRStrategy           | general-purpose, robust to heavy tails            | action: "clip" or "drop"          |
| ZScoreStrategy        | roughly normal distribution                       | threshold: float, action: str     |
| PercentileClipStrategy| clip to domain-safe percentile bounds             | lower: float, upper: float        |

### encoding (categorical + likely_cat_cols)
| Strategy       | When to use                                                 | Key params                    |
|----------------|-------------------------------------------------------------|-------------------------------|
| OneHotStrategy | nominal categorical, cardinality ≤ 15                       | -                             |
| OrdinalStrategy| ordinal categorical with a known order                      | order: list[str]              |
| LabelStrategy  | binary categorical OR numeric label column (0/1/2 classes)  | -                             |

### scaling (numeric non-label, after encoding)
| Strategy       | When to use                                        | Key params                     |
|----------------|----------------------------------------------------|--------------------------------|
| MinMaxStrategy | bounded domain, no severe outliers                 | feature_range: [min, max]      |
| StandardStrategy| roughly normal, for distance-based models         | -                              |
| RobustStrategy | skewed or outlier-prone numeric columns            | -                              |

### custom (use when NO existing strategy covers the transformation)
Write a Python function `transform(df: pd.DataFrame) -> pd.DataFrame`.
`pd` and `math` are pre-injected. No import statements allowed. One transformation per custom layer.

---

## When to use custom_layers - concrete examples

Use a custom layer whenever the transformation logic requires:

1. **Log / power transform** - column is severely right-skewed (skewness > 1) \
   and StandardStrategy alone is insufficient. \
   `pd` and `math` are pre-injected — do NOT write any import statements:
   ```
   def transform(df):
       df = df.copy()
       df["salary"] = df["salary"].clip(lower=0).apply(lambda x: math.log1p(x))
       return df
   ```

2. **Frequency encoding** - high-cardinality categorical (cardinality > 15) \
   where OneHot would explode dimensionality:
   ```
   def transform(df):
       df = df.copy()
       freq = df["primary_skill"].value_counts(normalize=True)
       df["primary_skill_freq"] = df["primary_skill"].map(freq)
       return df
   ```

3. **Derived / ratio features** - domain-meaningful combination of two columns:
   ```
   def transform(df):
       df = df.copy()
       df["salary_per_demand"] = df["salary"] / (df["skill_demand_score"] + 1)
       return df
   ```

4. **Domain-boundary clip** - column must be strictly positive (e.g. salary, price) \
   and has_negatives=true:
   ```
   def transform(df):
       df = df.copy()
       df["salary"] = df["salary"].clip(lower=0)
       return df
   ```

5. **Class rebalancing weights** - target label column has class imbalance \
   (zeros_pct > 10% or one class > 80%); produce a sample_weight column for downstream:
   ```
   def transform(df):
       df = df.copy()
       counts = df["job_survival_class"].value_counts()
       total = len(df)
       df["sample_weight"] = df["job_survival_class"].map(
           lambda c: total / (len(counts) * counts[c])
       )
       return df
   ```

6. **Year / datetime decomposition** - datetime column available; extract useful features:
   ```
   def transform(df):
       df = df.copy()
       df["year_num"] = pd.to_datetime(df["year"], errors="coerce").dt.year
       df["decade"]   = (df["year_num"] // 10) * 10
       return df
   ```

---

## Mandatory classification rules before building the pipeline

1. Read `col_roles.likely_categorical_numeric` first.
   - These columns MUST go through encoding, NOT outlier handling or scaling.
   - Use LabelStrategy for binary/multiclass targets (e.g. 0/1/2 labels).
   - Use OrdinalStrategy if there is a clear order.

2. Read `col_roles.id_like`. NEVER encode, scale, or impute these columns.

3. Read `col_roles.datetime`. Only include in custom layer for feature extraction \
   if there is an analytical reason. Never scale raw datetime.

4. Read `col_roles.boolean`. Use ModeStrategy for imputation, LabelStrategy or \
   skip encoding if already 0/1.

---

## Pipeline construction rules

- **Order: missing → outlier → encoding → scaling → custom**
- Only suggest layers for issues actually evidenced in the EDA numbers
- `cols` must contain ONLY column names present in `overview.column_names`
- For encoding layers: never also suggest scaling on the same cols
- For scaling layers: only numeric cols not encoded in a prior layer
- For outlier layers: exclude cols that appear in `col_roles.likely_categorical_numeric`
- `params` must match the strategy constructor signature exactly
- Prefer named cols over `null` (null = "all applicable" which is risky)
- custom_layers: only when no available strategy handles the transformation
- custom code signature: `def transform(df: pd.DataFrame) -> pd.DataFrame:`
- NO import statements allowed — `pd` and `math` are pre-injected and ready to use directly
- If skewness > 1 on a numeric column, prefer a log-transform custom layer \
  over StandardStrategy alone
- If a categorical column has cardinality > 15, prefer frequency-encoding custom layer \
  over OneHotStrategy
- If class imbalance is detected on a label column, add a sample_weight custom layer

## Response schema
{{
  "layers": [
    {{
      "operation":  "missing | outlier | scaling | encoding",
      "strategy":   "<StrategyName>",
      "cols":       ["col1", "col2"] or null,
      "params":     {{}},
      "rationale":  "one sentence linking to the specific EDA number"
    }}
  ],
  "custom_layers": [
    {{
      "operation":  "custom",
      "cols":       ["col1"] or null,
      "code":       "def transform(df):\\n    df = df.copy()\\n    ...\\n    return df",
      "rationale":  "one sentence - which EDA finding requires this, why no strategy covers it"
    }}
  ]
}}

Return ONLY the JSON object, nothing else.
"""

CHAIN_NAME = "preprocess_suggest"


class PreprocessSuggestChain:
    def __init__(self, engine: BaseLLMEngine, tracker: CostTracker) -> None:
        self._engine  = engine
        self._tracker = tracker

    async def arun(self, slim_eda: dict) -> tuple[list[SuggestedLayer], list[CustomLayer]]:
        response = await self._engine.ainvoke(
            system_prompt=_SYSTEM,
            user_message=_HUMAN.format(
                eda_json=json.dumps(slim_eda, indent=2, ensure_ascii=False)
            ),
        )

        self._tracker.record(
            chain_name        = CHAIN_NAME,
            prompt_tokens     = response.prompt_tokens,
            completion_tokens = response.completion_tokens,
            model             = response.model,
        )

        raw = response.content.strip()
        if raw.startswith("```"):
            parts = raw.split("```")
            raw = parts[1]
            if raw.startswith("json"):
                raw = raw[4:]
        raw = raw.strip()

        data   = json.loads(raw)
        layers = [SuggestedLayer.model_validate(l) for l in data.get("layers", [])]
        custom = [CustomLayer.model_validate(l)    for l in data.get("custom_layers", [])]
        return layers, custom