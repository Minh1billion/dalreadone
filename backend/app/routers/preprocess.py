from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel, Field, model_validator
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Literal

from app.core.security import get_current_user, get_db
from app.models import User
from app.models.schemas import FileResponse
from app.services.preprocess_service import (
    create_preprocess_task,
    get_preprocess_task,
    run_preprocess_task,
    save_preprocess_result,
)

router = APIRouter(prefix="/preprocess", tags=["preprocess"])

StepName = Literal["missing", "encoding", "outlier", "scaling"]


class MissingColumnOverride(BaseModel):
    strategy: Literal["mean", "median", "mode", "constant", "drop_row", "drop_col"] | None = None
    fill_value: Any = None
    drop_col_threshold: float | None = None


class MissingStepParams(BaseModel):
    num_strategy: Literal["mean", "median", "mode", "constant", "drop_row", "drop_col"] = "median"
    cat_strategy: Literal["mean", "median", "mode", "constant", "drop_row", "drop_col"] = "mode"
    num_fill_value: Any = 0
    cat_fill_value: Any = "unknown"
    drop_col_threshold: float = Field(0.5, ge=0.0, le=1.0)
    drop_row_subset: List[str] | None = None
    column_overrides: Dict[str, MissingColumnOverride] = Field(default_factory=dict)


class EncodingColumnOverride(BaseModel):
    strategy: Literal["onehot", "ordinal", "binary", "frequency", "skip"]
    ordinal_categories: List[Any] | None = None
    max_onehot_cardinality: int = 20


class EncodingStepParams(BaseModel):
    default_strategy: Literal["onehot", "ordinal", "binary", "frequency", "skip"] = "onehot"
    max_onehot_cardinality: int = Field(20, ge=2)
    column_overrides: Dict[str, EncodingColumnOverride] = Field(default_factory=dict)
    skip_cols: List[str] | None = None


class OutlierColumnOverride(BaseModel):
    strategy: Literal["clip", "winsorize", "drop_row", "impute_median", "skip"]
    iqr_k: float = Field(1.5, gt=0)
    winsorize_bounds: tuple[float, float] = (0.01, 0.99)


class OutlierStepParams(BaseModel):
    default_strategy: Literal["clip", "winsorize", "drop_row", "impute_median", "skip"] = "clip"
    iqr_k: float = Field(1.5, gt=0)
    winsorize_bounds: tuple[float, float] = (0.01, 0.99)
    column_overrides: Dict[str, OutlierColumnOverride] = Field(default_factory=dict)
    skip_cols: List[str] | None = None


class ScalingColumnOverride(BaseModel):
    strategy: Literal["standard", "minmax", "robust", "log1p", "skip"]
    feature_range: tuple[float, float] = (0.0, 1.0)


class ScalingStepParams(BaseModel):
    default_strategy: Literal["standard", "minmax", "robust", "log1p", "skip"] = "standard"
    feature_range: tuple[float, float] = (0.0, 1.0)
    column_overrides: Dict[str, ScalingColumnOverride] = Field(default_factory=dict)
    skip_cols: List[str] | None = None


_PARAMS_MODEL: Dict[str, type[BaseModel]] = {
    "missing":  MissingStepParams,
    "encoding": EncodingStepParams,
    "outlier":  OutlierStepParams,
    "scaling":  ScalingStepParams,
}


class StepConfig(BaseModel):
    name: StepName
    params: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_params(self) -> "StepConfig":
        model_cls = _PARAMS_MODEL[self.name]
        model_cls(**self.params)
        return self

    def to_raw(self) -> Dict[str, Any]:
        return {"name": self.name, "params": self.params}


class CreateTaskRequest(BaseModel):
    file_id: int
    steps: List[StepConfig] = Field(
        default_factory=lambda: [
            StepConfig(name="missing"),
            StepConfig(name="encoding"),
            StepConfig(name="outlier"),
            StepConfig(name="scaling"),
        ]
    )


@router.post("/tasks", summary="Create a preprocessing task")
def create_task(
    body: CreateTaskRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    raw_steps = [s.to_raw() for s in body.steps]
    task = create_preprocess_task(db, file_id=body.file_id, user_id=user.id, raw_steps=raw_steps)
    background_tasks.add_task(run_preprocess_task, task["task_id"], db)
    return task


@router.get("/tasks/{task_id}", summary="Get preprocessing task status / result")
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    return get_preprocess_task(db, task_id=task_id, user_id=user.id)


@router.post("/tasks/{task_id}/save", response_model=FileResponse, summary="Save preprocessed file into project")
def save_task(
    task_id: str,
    db: Session = Depends(get_db),
    user: User  = Depends(get_current_user),
):
    return save_preprocess_result(db, task_id=task_id, user_id=user.id)