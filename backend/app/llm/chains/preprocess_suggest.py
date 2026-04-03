from __future__ import annotations
import json

from app.llm.llm_engine import BaseLLMEngine
from app.llm.schemas import SuggestedLayer, CustomLayer
from app.llm.cost_tracker import CostTracker

_SYSTEM = """\
You are a senior data engineer. Respond ONLY with valid JSON — no markdown, \
no explanation outside the JSON object.\
"""

_HUMAN = """\
Given the EDA context below, suggest an ordered list of preprocessing layers.
Each layer maps directly to a concrete strategy class in the codebase.

## EDA Context
{eda_json}

## Available strategies per operation type
missing   : MeanStrategy | MedianStrategy | ModeStrategy | ConstantStrategy | DropRowStrategy | DropColStrategy
outlier   : IQRStrategy(action="clip"|"drop") | ZScoreStrategy(threshold, action) | PercentileClipStrategy(lower, upper)
scaling   : MinMaxStrategy(feature_range) | StandardStrategy | RobustStrategy
encoding  : OneHotStrategy | OrdinalStrategy(order) | LabelStrategy
custom    : use ONLY when no existing strategy can handle the transformation

## Response schema
{{
  "layers": [
    {{
      "operation":  "missing | outlier | scaling | encoding",
      "strategy":   "<StrategyName>",
      "cols":       ["col1", "col2"] or null for all applicable cols,
      "params":     {{}},
      "rationale":  "one sentence"
    }}
  ],
  "custom_layers": [
    {{
      "operation":  "custom",
      "cols":       ["col1"] or null,
      "code":       "def transform(df):\\n    df = df.copy()\\n    # transformation here\\n    return df",
      "rationale":  "one sentence — why no existing strategy covers this"
    }}
  ]
}}

## Rules
- Order: missing → outlier → encoding → scaling → custom
- Only suggest layers for issues actually evidenced in the EDA numbers
- cols must only contain column names present in overview.column_names
- For encoding: never suggest scaling on the same cols
- For scaling: only numeric cols that are not encoded in a prior layer
- params must match the strategy constructor exactly
- custom_layers: only when transformation logic cannot be expressed by any available strategy
- custom code must define exactly `transform(df: pd.DataFrame) -> pd.DataFrame`, no imports allowed
- If no custom logic is needed, return custom_layers as an empty array
- Return ONLY the JSON object, nothing else
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