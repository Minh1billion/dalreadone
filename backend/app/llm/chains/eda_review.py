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
- issues: flag nulls, outliers, type mismatches, duplicates, skew — with exact %
- prep_steps: ordered must → should → optional; dataset-level steps first
- Do NOT flag high cardinality on ID/invoice columns as an issue
- opportunities: concrete analysis ideas enabled by this dataset
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
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        data   = json.loads(raw)
        issues = [IssueItem.model_validate(i) for i in data.get("issues", [])]
        prep   = [PrepStep.model_validate(s)  for s in data.get("prep_steps", [])]
        opps   = data.get("opportunities", [])

        return issues, prep, opps