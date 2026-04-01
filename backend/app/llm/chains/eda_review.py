from __future__ import annotations
import json

from app.llm.llm_engine import BaseLLMEngine
from app.llm.schemas import IssueItem, PrepStep
from app.llm.cost_tracker import CostTracker

_SYSTEM = """\
You are a senior data analyst. Respond ONLY with valid JSON — no markdown, \
no explanation outside the JSON object.\
"""

_HUMAN = """\
Review this EDA summary. Identify data quality issues and recommend \
preprocessing steps (description only, no code).

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
      "rationale": "one sentence — why this step, what it fixes"
    }}
  ],
  "opportunities": [
    "brief analytical opportunity (3-5 items)"
  ]
}}

## Rules
- Read `overview.column_names` first to understand the dataset domain \
(e.g. time-series, retail transactions, sensor data) — tailor all \
observations and opportunities to that domain
- issues: only flag problems actually evidenced by the numbers \
(null_pct > 0, outlier_pct > 5, duplicate_pct > 1, negative values \
in quantity/price columns, etc.)
- Do NOT flag issues for columns/stats that are absent simply because \
the dataset has few columns — absence of correlations or distributions \
in a 2-column dataset is expected, not an issue
- Do NOT flag high cardinality on ID/invoice/date columns as an issue
- prep_steps: ordered must → should → optional; dataset-level steps first; \
only recommend steps that address a real detected issue above
- opportunities: 3-5 concrete analysis ideas specific to the column names \
and inferred domain (e.g. Date + Price → time-series forecasting, \
seasonality decomposition)
- Return ONLY the JSON object, nothing else
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