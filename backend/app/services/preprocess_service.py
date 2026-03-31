import io
import uuid
from datetime import datetime
from typing import Any

import pandas as pd
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import Config
from app.models import File
from app.services.file_service import get_file_bytes, _load_dataframe
from app.storage import redis, s3
from app.pipelines.preprocess import (
    Pipeline,
    MissingOperation, MeanStrategy, MedianStrategy, ModeStrategy,
    ConstantStrategy, DropRowStrategy, DropColStrategy,
    EncodingOperation, OneHotStrategy, OrdinalStrategy, LabelStrategy,
    OutlierOperation, IQRStrategy, ZScoreStrategy, PercentileClipStrategy,
    ScalingOperation, MinMaxStrategy, StandardStrategy, RobustStrategy,
)
from app.models.preprocess_schema import PreprocessRunRequest, OperationConfig

PREPROCESS_NS  = "preprocess_task"
PREPROCESS_TTL = Config.PREPROCESS_TASK_TTL
PREVIEW_ROWS   = 10


def _task_dict(task_id: str, file_id: int, user_id: int, steps_raw: list[dict]) -> dict[str, Any]:
    return {
        "task_id":    task_id,
        "file_id":    file_id,
        "user_id":    user_id,
        "steps":      steps_raw,
        "status":     "pending",
        "step":       None,
        "progress":   0,
        "result_s3_key": None,
        "preview":    None,
        "error":      None,
        "created_at": datetime.utcnow().isoformat(),
    }


def _get_file(db: Session, file_id: int, user_id: int) -> File:
    record = db.query(File).filter(File.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if record.project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return record


def _build_operation(cfg: OperationConfig):
    cols = cfg.cols
    s    = cfg.strategy

    match cfg.operation:
        case "missing":
            strategy = {
                "mean":      lambda: MeanStrategy(),
                "median":    lambda: MedianStrategy(),
                "mode":      lambda: ModeStrategy(),
                "constant":  lambda: ConstantStrategy(fill_value=s.fill_value),
                "drop_row":  lambda: DropRowStrategy(),
                "drop_col":  lambda: DropColStrategy(),
            }[s.type]()
            return MissingOperation(strategy, cols=cols)

        case "encoding":
            strategy = {
                "onehot":  lambda: OneHotStrategy(),
                "ordinal": lambda: OrdinalStrategy(order=s.order),
                "label":   lambda: LabelStrategy(),
            }[s.type]()
            return EncodingOperation(strategy, cols=cols)

        case "outlier":
            strategy = {
                "iqr":             lambda: IQRStrategy(action=s.action),
                "zscore":          lambda: ZScoreStrategy(threshold=s.threshold, action=s.action),
                "percentile_clip": lambda: PercentileClipStrategy(lower=s.lower, upper=s.upper),
            }[s.type]()
            return OutlierOperation(strategy, cols=cols)

        case "scaling":
            strategy = {
                "minmax":   lambda: MinMaxStrategy(feature_range=s.feature_range),
                "standard": lambda: StandardStrategy(),
                "robust":   lambda: RobustStrategy(),
            }[s.type]()
            return ScalingOperation(strategy, cols=cols)


def _build_pipeline(steps_raw: list[dict]) -> Pipeline:
    from app.models.preprocess_schema import OperationConfig
    from pydantic import TypeAdapter

    adapter = TypeAdapter(OperationConfig)
    pipeline = Pipeline()
    for raw in steps_raw:
        cfg = adapter.validate_python(raw)
        pipeline.add(_build_operation(cfg))
    return pipeline


def create_preprocess_task(db: Session, request: PreprocessRunRequest, user_id: int) -> dict:
    _get_file(db, request.file_id, user_id)

    task_id   = str(uuid.uuid4())
    steps_raw = [step.model_dump() for step in request.steps]
    task      = _task_dict(task_id, request.file_id, user_id, steps_raw)
    redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)
    return task


def get_preprocess_task(task_id: str, user_id: int) -> dict:
    task = redis.get(PREPROCESS_NS, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return task


def run_preprocess_task(task_id: str, db: Session) -> None:
    task = redis.get(PREPROCESS_NS, task_id)
    if not task:
        return

    def _update(step: str, progress: int) -> None:
        task["status"]   = "running"
        task["step"]     = step
        task["progress"] = progress
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)

    try:
        _update("loading_file", 5)
        content, filename = get_file_bytes(db, task["file_id"], task["user_id"])
        df: pd.DataFrame  = _load_dataframe(content, filename)

        _update("building_pipeline", 15)
        pipeline = _build_pipeline(task["steps"])

        _update("running_pipeline", 30)
        df_out = pipeline.fit_transform(df)

        _update("uploading_result", 85)
        buf = io.BytesIO()
        df_out.to_csv(buf, index=False)
        buf.seek(0)

        result_key = f"preprocess/{task_id}/result.csv"
        s3.upload_file(buf, result_key)

        task["status"]        = "done"
        task["step"]          = "done"
        task["progress"]      = 100
        task["result_s3_key"] = result_key
        task["preview"]       = df_out.head(PREVIEW_ROWS).to_dict(orient="records")
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)

    except (TypeError, ValueError) as e:
        task["status"] = "error"
        task["error"]  = f"Pipeline config error: {e}"
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)

    except Exception as e:
        task["status"] = "error"
        task["error"]  = str(e)
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)