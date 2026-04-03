from __future__ import annotations
import asyncio
import json
import logging
from pathlib import Path

from app.llm.context import EDAContextBuilder
from app.llm.chains.eda_review import EDAReviewChain
from app.llm.assembler import ReportAssembler
from app.llm.cost_tracker import CostTracker
from app.llm.llm_engine import make_engine
from app.llm.schemas import EDAReviewResult

logger = logging.getLogger(__name__)


class EDAReviewPipeline:
    def __init__(self, provider: str | None = None) -> None:
        engine          = make_engine(provider)
        self._tracker   = CostTracker()
        self._builder   = EDAContextBuilder()
        self._chain     = EDAReviewChain(engine, self._tracker)
        self._assembler = ReportAssembler()

    @property
    def tracker(self) -> CostTracker:
        """Expose tracker for callers that need to inspect cost after run."""
        return self._tracker

    async def arun(self, eda_json: dict) -> EDAReviewResult:
        slim     = self._builder.build(eda_json)
        overview = slim["overview"]

        logger.info(
            "[1/2] Context built: %d chars | likely_cat cols: %s",
            len(json.dumps(slim)),
            slim.get("col_roles", {}).get("likely_categorical_numeric", []),
        )

        issues, prep_steps, opps = await self._chain.arun(slim)

        logger.info(
            "[2/2] Issues: %d | Prep: %d | Opportunities: %d | Cost: $%.8f",
            len(issues), len(prep_steps), len(opps), self._tracker.total_cost_usd,
        )

        return EDAReviewResult(
            overview      = overview,
            issues        = issues,
            prep_steps    = prep_steps,
            opportunities = opps,
            usage         = self._tracker.to_dict(),
        )

    async def run_and_save(
        self,
        eda_json: dict,
        out_dir: Path,
    ) -> EDAReviewResult:
        result = await self.arun(eda_json)
        out_dir.mkdir(parents=True, exist_ok=True)

        (out_dir / "review.json").write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )
        (out_dir / "review.md").write_text(
            self._assembler.to_markdown(result), encoding="utf-8"
        )
        return result