from __future__ import annotations
import json
import logging

from app.llm.context import EDAContextBuilder
from app.llm.chains.preprocess_suggest import PreprocessSuggestChain
from app.llm.cost_tracker import CostTracker
from app.llm.llm_engine import make_engine
from app.llm.schemas import EDAReviewResult, PreprocessSuggestion, CustomLayer
from app.pipelines.preprocess.builder import build_pipeline
from app.pipelines.preprocess.pipeline import Pipeline
from app.sandbox.code_executor import CodeExecutor, CodeExecutionError

logger = logging.getLogger(__name__)


def _validate_custom_layers(custom_layers: list[CustomLayer]) -> list[str]:
    executor = CodeExecutor()
    errors: list[str] = []
    for i, layer in enumerate(custom_layers):
        try:
            executor.validate_ast(layer.code)
        except CodeExecutionError as e:
            errors.append(f"custom_layers[{i}]: {e}")
    return errors


class PreprocessSuggestPipeline:
    def __init__(self, provider: str | None = None) -> None:
        engine        = make_engine(provider)
        self._tracker = CostTracker()
        self._builder = EDAContextBuilder()
        self._chain   = PreprocessSuggestChain(engine, self._tracker)

    @property
    def tracker(self) -> CostTracker:
        return self._tracker

    async def arun_from_eda(self, eda_json: dict) -> tuple[PreprocessSuggestion, Pipeline, list[str]]:
        slim          = self._builder.build(eda_json)
        layers, custom = await self._chain.arun(slim)
        logger.info(
            "[suggest] %d layers, %d custom | cost $%.8f",
            len(layers), len(custom), self._tracker.total_cost_usd,
        )

        ast_errors = _validate_custom_layers(custom)
        suggestion = PreprocessSuggestion(
            layers=layers,
            custom_layers=custom,
            usage=self._tracker.to_dict(),
        )
        pipeline = build_pipeline(layers, custom if not ast_errors else [])
        return suggestion, pipeline, ast_errors

    async def arun_from_review(self, review: EDAReviewResult) -> tuple[PreprocessSuggestion, Pipeline, list[str]]:
        slim = {
            "overview":   review.overview,
            "issues":     [i.model_dump() for i in review.issues],
            "prep_steps": [s.model_dump() for s in review.prep_steps],
        }
        layers, custom = await self._chain.arun(slim)
        logger.info(
            "[suggest] %d layers, %d custom | cost $%.8f",
            len(layers), len(custom), self._tracker.total_cost_usd,
        )

        ast_errors = _validate_custom_layers(custom)
        suggestion = PreprocessSuggestion(
            layers=layers,
            custom_layers=custom,
            usage=self._tracker.to_dict(),
        )
        pipeline = build_pipeline(layers, custom if not ast_errors else [])
        return suggestion, pipeline, ast_errors