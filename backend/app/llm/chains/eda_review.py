from __future__ import annotations
import json

from app.llm.llm_engine import BaseLLMEngine
from app.llm.schemas import IssueItem, PrepStep
from app.llm.cost_tracker import CostTracker

_SYSTEM = """\
You are a senior data analyst with deep expertise in data quality assessment \
and machine learning preprocessing. Respond ONLY with valid JSON - no markdown, \
no explanation outside the JSON object.\
"""

_HUMAN = """\
Review the EDA summary below. Your job is to identify ALL meaningful data quality \
issues and recommend the correct preprocessing steps to address them.

## EDA Summary
{eda_json}

## Response schema
{{
  "issues": [
    {{
      "col": "column name or '__dataset__' for dataset-level issues",
      "severity": "high | medium | low",
      "detail": "specific observation with numbers from the EDA",
      "impact": "consequence if left unaddressed"
    }}
  ],
  "prep_steps": [
    {{
      "priority": "must | should | optional",
      "col": "column name or null for dataset-level",
      "action": "short_snake_case label",
      "rationale": "one sentence - why this step, what it fixes"
    }}
  ],
  "opportunities": [
    "brief analytical opportunity"
  ]
}}

## Step 1 - Understand the dataset domain
Before flagging anything, read `overview.col_names` and infer the domain \
(e.g. job market data, e-commerce transactions, IoT sensor readings). \
Tailor every observation and opportunity to that domain.

## Step 2 - Column type classification (do this before anything else)
Read `col_roles` carefully:

- `col_roles.lc_numeric`: These columns have numeric dtype (int/float) \
but very low cardinality. They are LABEL columns, not measurements. Rules:
  * DO NOT flag them for outliers or skewness - those stats are meaningless for labels
  * DO NOT recommend scaling on them
  * DO recommend encoding (LabelStrategy or OrdinalStrategy) if they are target/ordinal labels
  * DO flag class imbalance if z% is high (> 5%) or one value dominates > 80%
  * Example: job_survival_class with values 0/1/2 is a multiclass label, not salary data

- `col_roles.datetime`: Flag if there are gaps, irregular intervals, or future dates \
beyond the expected range. Opportunity: time-series decomposition, trend analysis.

- `col_roles.boolean`: Flag if severe imbalance (one value > 95%).

- `col_roles.id_like`: Never flag high cardinality on these. Never recommend encoding them.

## Step 3 - Issue detection rules
Flag an issue ONLY when evidenced by the actual numbers:

**Missing values**
- null_pct > 0 → flag (severity: high if > 20%, medium if 5-20%, low if < 5%)

**Outliers** (numeric non-label columns only)
- out% > 5% → high, 1-5% → medium, < 1% → low
- Also check: has_negatives=true in a column where negatives are invalid \
  (salary, price, count, age → must be positive)

**Skewness / distribution**
- |skewness| > 1 → high skew, flag it
- |skewness| between 0.5 and 1 → moderate skew, mention if relevant

**Duplicates**
- duplicate_pct > 1% → flag at dataset level

**Class imbalance** (for likely_cat columns and boolean columns)
- z% > 10% → flag - may indicate missing class representation
- One category dominates top_3 with pct > 80% → flag imbalance

**Cardinality**
- High cardinality on true categorical columns (not id_like) → flag if > 50 unique \
  because OneHot will explode dimensionality; suggest target or frequency encoding

**Correlation**
- |correlation| > 0.9 → flag as near-multicollinearity
- |correlation| > 0.7 → mention as strong correlation (opportunity for feature reduction)

**Domain violations**
- has_negatives=true in a numeric column where domain requires positive values → flag as high

## Step 4 - Preprocessing recommendations
Order: must → should → optional. Dataset-level steps come first.

Map issues 1:1 to prep_steps - every flagged issue must have at least one prep_step. \
Use these action labels:
- Missing: `impute_mean` | `impute_median` | `impute_mode` | `impute_constant` | \
  `drop_rows_missing` | `drop_col_missing`
- Outliers: `handle_outliers_iqr` | `handle_outliers_zscore` | `clip_percentile`
- Skew: `transform_log1p` | `transform_sqrt` | `transform_boxcox`
- Encoding: `encode_label` | `encode_ordinal` | `encode_onehot` | `encode_frequency` | \
  `encode_target`
- Scaling: `scale_standard` | `scale_minmax` | `scale_robust`
- Imbalance: `balance_classes_oversample` | `balance_classes_undersample` | \
  `balance_classes_weights`
- Dedup: `drop_duplicates`
- Domain fix: `clip_negative_to_zero` | `drop_invalid_rows`

## Step 5 - Opportunities
Provide 3-5 specific analytical opportunities tied to the actual columns and domain. \
Think: what questions could this dataset answer? what models would benefit from \
the preprocessing steps above?

## Hard rules
- Return ONLY the JSON object, nothing else
- Do NOT invent issues that are not supported by numbers in the EDA
- Do NOT flag ID/invoice/date columns for high cardinality
- Do NOT apply outlier or scaling rules to lc_numeric columns
- Do NOT omit encoding recommendations for lc_numeric columns \
  that are clearly label/target columns
"""

CHAIN_NAME = "eda_review"


class EDAReviewChain:
    def __init__(
        self,
        engine: BaseLLMEngine,
        tracker: CostTracker,
    ) -> None:
        self._engine  = engine
        self._tracker = tracker

    async def arun(self, slim_eda: dict) -> tuple[
        list[IssueItem], list[PrepStep], list[str]
    ]:
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
        issues = [IssueItem.model_validate(i) for i in data.get("issues", [])]
        prep   = [PrepStep.model_validate(s)  for s in data.get("prep_steps", [])]
        opps   = data.get("opportunities", [])

        return issues, prep, opps