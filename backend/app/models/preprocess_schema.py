from typing import Any, Literal
from pydantic import BaseModel, model_validator


class MeanStrategyConfig(BaseModel):
    type: Literal["mean"]

class MedianStrategyConfig(BaseModel):
    type: Literal["median"]

class ModeStrategyConfig(BaseModel):
    type: Literal["mode"]

class ConstantStrategyConfig(BaseModel):
    type: Literal["constant"]
    fill_value: Any = 0

class DropRowStrategyConfig(BaseModel):
    type: Literal["drop_row"]

class DropColStrategyConfig(BaseModel):
    type: Literal["drop_col"]

class OneHotStrategyConfig(BaseModel):
    type: Literal["onehot"]

class OrdinalStrategyConfig(BaseModel):
    type: Literal["ordinal"]
    order: dict[str, list] | None = None

class LabelStrategyConfig(BaseModel):
    type: Literal["label"]

class IQRStrategyConfig(BaseModel):
    type: Literal["iqr"]
    action: Literal["clip", "drop"] = "clip"

class ZScoreStrategyConfig(BaseModel):
    type: Literal["zscore"]
    threshold: float = 3.0
    action: Literal["clip", "drop"] = "clip"

class PercentileClipStrategyConfig(BaseModel):
    type: Literal["percentile_clip"]
    lower: float = 0.05
    upper: float = 0.95

class MinMaxStrategyConfig(BaseModel):
    type: Literal["minmax"]
    feature_range: tuple[float, float] = (0.0, 1.0)

class StandardStrategyConfig(BaseModel):
    type: Literal["standard"]

class RobustStrategyConfig(BaseModel):
    type: Literal["robust"]


MissingStrategyConfig = (
    MeanStrategyConfig | MedianStrategyConfig | ModeStrategyConfig |
    ConstantStrategyConfig | DropRowStrategyConfig | DropColStrategyConfig
)
EncodingStrategyConfig = OneHotStrategyConfig | OrdinalStrategyConfig | LabelStrategyConfig
OutlierStrategyConfig  = IQRStrategyConfig | ZScoreStrategyConfig | PercentileClipStrategyConfig
ScalingStrategyConfig  = MinMaxStrategyConfig | StandardStrategyConfig | RobustStrategyConfig


class MissingOperationConfig(BaseModel):
    operation: Literal["missing"]
    strategy: MissingStrategyConfig
    cols: list[str] | None = None

class EncodingOperationConfig(BaseModel):
    operation: Literal["encoding"]
    strategy: EncodingStrategyConfig
    cols: list[str] | None = None

class OutlierOperationConfig(BaseModel):
    operation: Literal["outlier"]
    strategy: OutlierStrategyConfig
    cols: list[str] | None = None

class ScalingOperationConfig(BaseModel):
    operation: Literal["scaling"]
    strategy: ScalingStrategyConfig
    cols: list[str] | None = None


OperationConfig = (
    MissingOperationConfig | EncodingOperationConfig |
    OutlierOperationConfig | ScalingOperationConfig
)


class PreprocessRunRequest(BaseModel):
    file_id: int
    steps: list[OperationConfig]

    @model_validator(mode="after")
    def at_least_one_step(self) -> "PreprocessRunRequest":
        if not self.steps:
            raise ValueError("steps must not be empty")
        return self


class PreprocessTaskResponse(BaseModel):
    task_id: str
    file_id: int
    status: str
    step: str | None
    progress: int
    error: str | None = None
    created_at: str


class PreprocessResultResponse(BaseModel):
    task_id: str
    file_id: int
    status: str
    result_s3_key: str | None
    preview: list[dict] | None
    created_at: str