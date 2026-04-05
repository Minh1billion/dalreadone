from typing import Any, Literal, Annotated
from pydantic import BaseModel, model_validator, Field


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

class CustomCodeStrategyConfig(BaseModel):
    type: Literal["custom_code"]
    code: str

class DropColumnsStrategyConfig(BaseModel):
    type: Literal["drop_columns"]

class DropDuplicatesStrategyConfig(BaseModel):
    type: Literal["drop_duplicates"]
    keep: Literal["first", "last"] = "first"

class CastStrategyConfig(BaseModel):
    type: Literal["cast"]
    dtype_map: dict[str, str]

class LambdaStrategyConfig(BaseModel):
    type: Literal["lambda"]
    expressions: list[dict[str, Any]]

class BinningStrategyConfig(BaseModel):
    type: Literal["binning"]
    bins_map: dict[str, dict]


MissingStrategyConfig  = (
    MeanStrategyConfig | MedianStrategyConfig | ModeStrategyConfig |
    ConstantStrategyConfig | DropRowStrategyConfig | DropColStrategyConfig
)
EncodingStrategyConfig = OneHotStrategyConfig | OrdinalStrategyConfig | LabelStrategyConfig
OutlierStrategyConfig  = IQRStrategyConfig | ZScoreStrategyConfig | PercentileClipStrategyConfig
ScalingStrategyConfig  = MinMaxStrategyConfig | StandardStrategyConfig | RobustStrategyConfig
DropStrategyConfig     = DropColumnsStrategyConfig | DropDuplicatesStrategyConfig
FeatureStrategyConfig  = LambdaStrategyConfig | BinningStrategyConfig


class MissingOperationConfig(BaseModel):
    operation: Literal["missing"]
    strategy: Annotated[MissingStrategyConfig, Field(discriminator="type")]
    cols: list[str] | None = None

class EncodingOperationConfig(BaseModel):
    operation: Literal["encoding"]
    strategy: Annotated[EncodingStrategyConfig, Field(discriminator="type")]
    cols: list[str] | None = None

class OutlierOperationConfig(BaseModel):
    operation: Literal["outlier"]
    strategy: Annotated[OutlierStrategyConfig, Field(discriminator="type")]
    cols: list[str] | None = None

class ScalingOperationConfig(BaseModel):
    operation: Literal["scaling"]
    strategy: Annotated[ScalingStrategyConfig, Field(discriminator="type")]
    cols: list[str] | None = None

class CustomCodeOperationConfig(BaseModel):
    operation: Literal["custom_code"]
    strategy: CustomCodeStrategyConfig
    cols: None = None

class DropOperationConfig(BaseModel):
    operation: Literal["drop"]
    strategy: Annotated[DropStrategyConfig, Field(discriminator="type")]
    cols: list[str] | None = None

class CastOperationConfig(BaseModel):
    operation: Literal["cast"]
    strategy: CastStrategyConfig
    cols: list[str]

class FeatureOperationConfig(BaseModel):
    operation: Literal["feature"]
    strategy: Annotated[FeatureStrategyConfig, Field(discriminator="type")]
    cols: list[str] | None = None


OperationConfig = Annotated[
    MissingOperationConfig | EncodingOperationConfig | OutlierOperationConfig
    | ScalingOperationConfig | CustomCodeOperationConfig
    | DropOperationConfig | CastOperationConfig | FeatureOperationConfig,
    Field(discriminator="operation"),
]


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
    preview: list[dict] | None = None
    error: str | None = None
    created_at: str


class PreprocessResultResponse(BaseModel):
    task_id: str
    file_id: int
    status: str
    preview: list[dict] | None
    created_at: str


class PreprocessConfirmResponse(BaseModel):
    file_id: int
    filename: str
    project_id: int