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


def build_pipeline(
    layers: list[SuggestedLayer],
    custom_layers: list[CustomLayer] | None = None,
) -> Pipeline:
    pipeline = Pipeline()

    for layer in layers:
        strategy_fn = _STRATEGY_MAP.get(layer.strategy)
        if strategy_fn is None:
            raise ValueError(f"Unknown strategy: {layer.strategy}")
        operation_cls = _OPERATION_MAP.get(layer.operation)
        if operation_cls is None:
            raise ValueError(f"Unknown operation type: {layer.operation}")
        pipeline.add(operation_cls(
            strategy=strategy_fn(layer.params),
            cols=layer.cols,
        ))

    for custom in (custom_layers or []):
        pipeline.add(CustomCodeOperation(
            strategy=CustomCodeStrategy(code=custom.code),
            cols=custom.cols,
        ))

    return pipeline