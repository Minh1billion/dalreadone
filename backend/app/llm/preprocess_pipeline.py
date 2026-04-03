from __future__ import annotations
import logging

from app.llm.context import EDAContextBuilder
from app.llm.chains.preprocess_suggest import PreprocessSuggestChain
from app.llm.cost_tracker import CostTracker
from app.llm.llm_engine import make_engine
from app.llm.schemas import EDAReviewResult, PreprocessSuggestion, SuggestedLayer, CustomLayer
from app.pipelines.preprocess.builder import build_pipeline
from app.pipelines.preprocess.pipeline import Pipeline
from app.sandbox.code_executor import CodeExecutor, CodeExecutionError

logger = logging.getLogger(__name__)

# Strategies that require categorical (str/object) input
_ENCODING_STRATEGIES = frozenset({
    "OneHotStrategy", "OrdinalStrategy", "LabelStrategy",
})
# Strategies that require numeric input
_SCALING_STRATEGIES = frozenset({
    "MinMaxStrategy", "StandardStrategy", "RobustStrategy",
})
# Strategies that must not run on label columns
_OUTLIER_STRATEGIES = frozenset({
    "IQRStrategy", "ZScoreStrategy", "PercentileClipStrategy",
})


def _validate_custom_layers(custom_layers: list[CustomLayer]) -> list[str]:
    executor = CodeExecutor()
    errors: list[str] = []
    for i, layer in enumerate(custom_layers):
        try:
            executor.validate_ast(layer.code)
        except CodeExecutionError as e:
            errors.append(f"custom_layers[{i}]: {e}")
    return errors


def _build_col_meta(slim):
    col_meta = {}

    for entry in slim.get("columns", []):
        if "col" not in entry:
            continue

        if "type" not in entry:
            print("❌ Missing type in EDA entry:", entry)
            col_type = entry.get("dtype", "unknown")
        else:
            col_type = entry["type"]

        col_meta[entry["col"]] = col_type

    return col_meta


def _make_astype_str_layer(cols: list[str]) -> CustomLayer:
    """
    Return a CustomLayer that casts the given columns to str.

    Injected before any encoding layer that targets likely_cat numeric columns,
    because build_pipeline() validates that encoding strategies receive
    categorical (object/str) dtype - not int/float.
    """
    cols_repr = repr(cols)
    code = (
        "def transform(df):\n"
        "    df = df.copy()\n"
        f"    for col in {cols_repr}:\n"
        "        if col in df.columns:\n"
        "            df[col] = df[col].astype(str)\n"
        "    return df"
    )
    return CustomLayer(
        cols=cols,
        code=code,
        rationale=(
            f"Cast {cols} from numeric to str before encoding - "
            "these columns have low cardinality and are categorical labels, "
            "not continuous measurements."
        ),
    )


def _guard_layers(
    layers: list[SuggestedLayer],
    custom_layers: list[CustomLayer],
    col_meta: dict[str, str],
    likely_cat_cols: list[str],
) -> tuple[list[SuggestedLayer], list[CustomLayer], list[str]]:
    """
    Returns (clean_layers, augmented_custom_layers, warning_messages).

    Guards:
    - Encoding on a likely_cat numeric col  -> inject astype-str CustomLayer first
    - Encoding on a pure-numeric col        -> remove that col
    - Scaling on str/category/bool/label cols -> remove those cols
    - Outlier on likely_cat cols            -> remove those cols
    - Layer whose col list empties          -> drop the layer entirely
    """
    clean: list[SuggestedLayer]     = []
    extra_custom: list[CustomLayer] = list(custom_layers)
    warnings: list[str]             = []

    # Track which likely_cat cols already have an astype layer injected
    astype_injected: set[str] = set()

    for layer in layers:
        cols = layer.cols  # None means "all applicable"

        if cols is None:
            clean.append(layer)
            continue

        if layer.strategy in _ENCODING_STRATEGIES:
            need_cast = [
                c for c in cols
                if col_meta.get(c) in ("int", "float") and c in likely_cat_cols
            ]
            bad = [
                c for c in cols
                if col_meta.get(c) in ("int", "float") and c not in likely_cat_cols
            ]

            if need_cast:
                new_cast = [c for c in need_cast if c not in astype_injected]
                if new_cast:
                    cast_layer = _make_astype_str_layer(new_cast)
                    extra_custom.insert(0, cast_layer)
                    astype_injected.update(new_cast)
                    warnings.append(
                        f"[guard] {layer.strategy}: injected astype(str) CustomLayer "
                        f"for likely_cat numeric cols {new_cast}"
                    )

            if bad:
                warnings.append(
                    f"[guard] {layer.strategy}: removed pure-numeric cols {bad} "
                    f"(not likely_cat) - encoding requires categorical input"
                )
                cols = [c for c in cols if c not in bad]

        elif layer.strategy in _SCALING_STRATEGIES:
            bad = [c for c in cols if col_meta.get(c) in ("str", "category", "bool")]
            if bad:
                warnings.append(
                    f"[guard] {layer.strategy}: removed non-numeric cols {bad}"
                )
                cols = [c for c in cols if c not in bad]

            bad_cat = [c for c in cols if c in likely_cat_cols]
            if bad_cat:
                warnings.append(
                    f"[guard] {layer.strategy}: removed likely_cat cols {bad_cat} - "
                    "label columns must not be scaled"
                )
                cols = [c for c in cols if c not in bad_cat]

        elif layer.strategy in _OUTLIER_STRATEGIES:
            bad = [c for c in cols if c in likely_cat_cols]
            if bad:
                warnings.append(
                    f"[guard] {layer.strategy}: removed likely_cat cols {bad} - "
                    "outlier stats are meaningless for label columns"
                )
                cols = [c for c in cols if c not in bad]

        if not cols:
            warnings.append(
                f"[guard] {layer.strategy} dropped - no valid cols remain after filtering"
            )
            continue

        if cols != layer.cols:
            layer = layer.model_copy(update={"cols": cols})

        clean.append(layer)

    return clean, extra_custom, warnings


class PreprocessSuggestPipeline:
    def __init__(self, provider: str | None = None) -> None:
        engine        = make_engine(provider)
        self._tracker = CostTracker()
        self._builder = EDAContextBuilder()
        self._chain   = PreprocessSuggestChain(engine, self._tracker)

    @property
    def tracker(self) -> CostTracker:
        return self._tracker

    async def arun_from_eda(
        self,
        eda_json: dict,
    ) -> tuple[PreprocessSuggestion, Pipeline, list[str]]:
        """
        Run from a raw EDA JSON report.
        Returns (suggestion, pipeline, errors).
        """
        slim           = self._builder.build(eda_json)
        layers, custom = await self._chain.arun(slim)

        col_meta        = _build_col_meta(slim)
        likely_cat_cols = slim.get("col_roles", {}).get("lc_numeric", [])
        layers, custom, guard_warnings = _guard_layers(
            layers, custom, col_meta, likely_cat_cols
        )

        for w in guard_warnings:
            logger.warning(w)

        logger.info(
            "[suggest] %d layers, %d custom | guards: %d | cost $%.8f",
            len(layers), len(custom), len(guard_warnings), self._tracker.total_cost_usd,
        )

        ast_errors = _validate_custom_layers(custom)
        all_errors = guard_warnings + ast_errors

        suggestion = PreprocessSuggestion(
            layers=layers,
            custom_layers=custom,
            usage=self._tracker.to_dict(),
        )
        pipeline = build_pipeline(layers, custom if not ast_errors else [])
        return suggestion, pipeline, all_errors

    async def arun_from_review(
        self,
        review: EDAReviewResult,
        eda_json: dict | None = None,
    ) -> tuple[PreprocessSuggestion, Pipeline, list[str]]:
        """
        Run from an EDAReviewResult.
        Pass eda_json for best results (full numeric/col_roles context).
        Returns (suggestion, pipeline, errors).
        """
        if eda_json:
            slim = self._builder.build(eda_json)
            slim["issues"]     = [i.model_dump() for i in review.issues]
            slim["prep_steps"] = [s.model_dump() for s in review.prep_steps]
        else:
            logger.warning(
                "[suggest] eda_json not provided - running with reduced context. "
                "Pass eda_json to arun_from_review() for best results."
            )
            slim = {
                "overview":   review.overview,
                "col_roles":  {
                    "lc_numeric": review.overview.get(
                        "lc_cols", []
                    ),
                    "datetime": review.overview.get("datetime_cols", []),
                    "boolean":  [],
                    "id_like":  [],
                },
                "columns":    review.overview.get("columns", []),
                "issues":     [i.model_dump() for i in review.issues],
                "prep_steps": [s.model_dump() for s in review.prep_steps],
            }

        layers, custom = await self._chain.arun(slim)

        col_meta        = _build_col_meta(slim)
        likely_cat_cols = slim.get("col_roles", {}).get("lc_numeric", [])
        layers, custom, guard_warnings = _guard_layers(
            layers, custom, col_meta, likely_cat_cols
        )

        for w in guard_warnings:
            logger.warning(w)

        logger.info(
            "[suggest] %d layers, %d custom | guards: %d | cost $%.8f",
            len(layers), len(custom), len(guard_warnings), self._tracker.total_cost_usd,
        )

        ast_errors = _validate_custom_layers(custom)
        all_errors = guard_warnings + ast_errors

        suggestion = PreprocessSuggestion(
            layers=layers,
            custom_layers=custom,
            usage=self._tracker.to_dict(),
        )
        pipeline = build_pipeline(layers, custom if not ast_errors else [])
        return suggestion, pipeline, all_errors