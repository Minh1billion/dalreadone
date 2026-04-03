from __future__ import annotations
from app.llm.schemas import SuggestedLayer, CustomLayer
from app.pipelines.preprocess.pipeline import Pipeline
from app.pipelines.preprocess import (
    MissingOperation, MeanStrategy, MedianStrategy, ModeStrategy,
    ConstantStrategy, DropRowStrategy, DropColStrategy,
    OutlierOperation, IQRStrategy, ZScoreStrategy, PercentileClipStrategy,
    ScalingOperation, MinMaxStrategy, StandardStrategy, RobustStrategy,
    EncodingOperation, OneHotStrategy, OrdinalStrategy, LabelStrategy,
    CustomCodeOperation, CustomCodeStrategy,
)

_STRATEGY_MAP = {
    "MeanStrategy":           lambda p: MeanStrategy(),
    "MedianStrategy":         lambda p: MedianStrategy(),
    "ModeStrategy":           lambda p: ModeStrategy(),
    "ConstantStrategy":       lambda p: ConstantStrategy(**p),
    "DropRowStrategy":        lambda p: DropRowStrategy(),
    "DropColStrategy":        lambda p: DropColStrategy(),
    "IQRStrategy":            lambda p: IQRStrategy(**p),
    "ZScoreStrategy":         lambda p: ZScoreStrategy(**p),
    "PercentileClipStrategy": lambda p: PercentileClipStrategy(**p),
    "MinMaxStrategy":         lambda p: MinMaxStrategy(**p),
    "StandardStrategy":       lambda p: StandardStrategy(),
    "RobustStrategy":         lambda p: RobustStrategy(),
    "OneHotStrategy":         lambda p: OneHotStrategy(),
    "OrdinalStrategy":        lambda p: OrdinalStrategy(**p),
    "LabelStrategy":          lambda p: LabelStrategy(),
}

_OPERATION_MAP = {
    "missing":  MissingOperation,
    "outlier":  OutlierOperation,
    "scaling":  ScalingOperation,
    "encoding": EncodingOperation,
}

# Encoding strategies that require str/object dtype at runtime.
# For these, any CustomLayer targeting the same cols must run first.
_ENCODING_STRATEGIES = frozenset({
    "OneHotStrategy", "OrdinalStrategy", "LabelStrategy",
})


def build_pipeline(
    layers: list[SuggestedLayer],
    custom_layers: list[CustomLayer] | None = None,
) -> Pipeline:
    """
    Build a Pipeline from suggested layers and optional custom layers.

    Ordering guarantee:
    - astype-cast CustomLayers (injected by _guard_layers) MUST run immediately
      before the encoding step that targets the same cols.
    - This handles both explicit cols and cols=None (wildcard) encoding layers.

    A CustomLayer is classified as a "pre-cast" if:
      (a) Any explicit encoding layer shares at least one col with it, OR
      (b) Any encoding layer has cols=None (wildcard) — in that case ALL
          custom layers whose cols overlap with likely_cat numeric cols
          are treated as pre-casts and flushed before the first encoding step.

    All remaining custom layers (non-cast) are appended at the end.
    """
    pipeline      = Pipeline()
    custom_layers = list(custom_layers or [])

    encoding_col_sets: list[set[str]] = [
        set(layer.cols)
        for layer in layers
        if layer.strategy in _ENCODING_STRATEGIES and layer.cols
    ]

    has_wildcard_encoding = any(
        layer.strategy in _ENCODING_STRATEGIES and layer.cols is None
        for layer in layers
    )

    # ── Bucket custom layers ──────────────────────────────────────────────────
    pre_cast_layers:    list[CustomLayer] = []
    post_custom_layers: list[CustomLayer] = []

    for custom in custom_layers:
        if has_wildcard_encoding:
            pre_cast_layers.append(custom)
            continue

        if custom.cols:
            col_set     = set(custom.cols)
            is_pre_cast = any(col_set & enc_set for enc_set in encoding_col_sets)
        else:
            is_pre_cast = False

        if is_pre_cast:
            pre_cast_layers.append(custom)
        else:
            post_custom_layers.append(custom)

    flushed:              set[int] = set()
    pre_cast_all_flushed: bool     = False   # for wildcard-encoding case

    for layer in layers:
        strategy_fn = _STRATEGY_MAP.get(layer.strategy)
        if strategy_fn is None:
            raise ValueError(f"Unknown strategy: {layer.strategy}")
        operation_cls = _OPERATION_MAP.get(layer.operation)
        if operation_cls is None:
            raise ValueError(f"Unknown operation type: {layer.operation}")

        is_encoding = layer.strategy in _ENCODING_STRATEGIES

        if is_encoding:
            if has_wildcard_encoding and not pre_cast_all_flushed:
                # Flush ALL pre-cast layers before the first encoding step.
                for i, cast in enumerate(pre_cast_layers):
                    if i not in flushed:
                        pipeline.add(CustomCodeOperation(
                            strategy=CustomCodeStrategy(code=cast.code),
                            cols=cast.cols,
                        ))
                        flushed.add(i)
                pre_cast_all_flushed = True

            elif not has_wildcard_encoding and layer.cols:
                # Flush only the pre-cast layers that overlap this encoding step.
                layer_col_set = set(layer.cols)
                for i, cast in enumerate(pre_cast_layers):
                    if i in flushed:
                        continue
                    cast_cols = set(cast.cols) if cast.cols else set()
                    if cast_cols & layer_col_set:
                        pipeline.add(CustomCodeOperation(
                            strategy=CustomCodeStrategy(code=cast.code),
                            cols=cast.cols,
                        ))
                        flushed.add(i)

        pipeline.add(operation_cls(
            strategy=strategy_fn(layer.params),
            cols=layer.cols,
        ))

    for custom in post_custom_layers:
        pipeline.add(CustomCodeOperation(
            strategy=CustomCodeStrategy(code=custom.code),
            cols=custom.cols,
        ))

    for i, cast in enumerate(pre_cast_layers):
        if i not in flushed:
            pipeline.add(CustomCodeOperation(
                strategy=CustomCodeStrategy(code=cast.code),
                cols=cast.cols,
            ))

    return pipeline