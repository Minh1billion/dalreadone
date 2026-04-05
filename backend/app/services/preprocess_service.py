from __future__ import annotations

import io
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session
from starlette.datastructures import Headers

from app.core.config import Config
from app.models import File
from app.services.file_service import get_file_bytes, _load_dataframe, upload_project_file
from app.storage import redis
from app.pipelines.preprocess import (
    Pipeline,
    MissingOperation, MeanStrategy, MedianStrategy, ModeStrategy,
    ConstantStrategy, DropRowStrategy, DropColStrategy,
    EncodingOperation, OneHotStrategy, OrdinalStrategy, LabelStrategy,
    OutlierOperation, IQRStrategy, ZScoreStrategy, PercentileClipStrategy,
    ScalingOperation, MinMaxStrategy, StandardStrategy, RobustStrategy,
    DropOperation, DropColumnsStrategy, DropDuplicatesStrategy,
    CastOperation, CastStrategy,
    FeatureOperation, LambdaStrategy, BinningStrategy,
    CustomCodeOperation, CustomCodeStrategy,
)
from app.models.preprocess_schema import PreprocessRunRequest, OperationConfig

PREPROCESS_NS  = "preprocess_task"
PREPROCESS_TTL = Config.PREPROCESS_TASK_TTL

RESULT_NS  = "preprocess_result"
RESULT_TTL = 60 * 30

REVIEW_NS  = "review_task"
EDA_NS     = "eda_task"
SUGGEST_NS = "suggest_task"
SUGGEST_TTL = Config.PREPROCESS_TASK_TTL

PREVIEW_ROWS = 50


def _task_dict(task_id: str, file_id: int, user_id: int, steps_raw: list[dict]) -> dict[str, Any]:
    return {
        "task_id":    task_id,
        "file_id":    file_id,
        "user_id":    user_id,
        "steps":      steps_raw,
        "status":     "pending",
        "step":       None,
        "progress":   0,
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

        case "drop":
            strategy = {
                "drop_columns":    lambda: DropColumnsStrategy(),
                "drop_duplicates": lambda: DropDuplicatesStrategy(keep=s.keep),
            }[s.type]()
            return DropOperation(strategy, cols=cols)

        case "cast":
            return CastOperation(CastStrategy(dtype_map=s.dtype_map), cols=cols)

        case "feature":
            strategy = {
                "lambda":  lambda: LambdaStrategy(expressions=s.expressions),
                "binning": lambda: BinningStrategy(bins_map=s.bins_map),
            }[s.type]()
            return FeatureOperation(strategy, cols=cols)

        case "custom_code":
            return CustomCodeOperation(CustomCodeStrategy(code=s.code), cols=None)


def _build_pipeline(steps_raw: list[dict]) -> Pipeline:
    from pydantic import TypeAdapter
    adapter  = TypeAdapter(OperationConfig)
    pipeline = Pipeline()
    for raw in steps_raw:
        cfg = adapter.validate_python(raw)
        pipeline.add(_build_operation(cfg))
    return pipeline


def _sanitize_preview(df: pd.DataFrame, n: int) -> list[dict]:
    import math
    import numpy as np

    def _clean(v: Any) -> Any:
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else f
        if isinstance(v, np.bool_):
            return bool(v)
        return v

    return [{k: _clean(v) for k, v in row.items()} for row in df.head(n).to_dict(orient="records")]


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

        _update("saving_result", 85)
        buf = io.BytesIO()
        df_out.to_csv(buf, index=False)
        buf.seek(0)
        redis.set(RESULT_NS, task_id, buf.read().decode("utf-8"), ttl=RESULT_TTL)

        task["status"]   = "done"
        task["step"]     = "done"
        task["progress"] = 100
        task["preview"]  = _sanitize_preview(df_out, PREVIEW_ROWS)
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)

    except (TypeError, ValueError) as e:
        task["status"] = "error"
        task["error"]  = f"Pipeline config error: {e}"
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)

    except Exception as e:
        task["status"] = "error"
        task["error"]  = str(e)
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)


def confirm_preprocess_task(task_id: str, user_id: int, db: Session) -> File:
    task = get_preprocess_task(task_id, user_id)

    if task["status"] != "done":
        raise HTTPException(status_code=400, detail="Task is not done yet")

    csv_str = redis.get(RESULT_NS, task_id)
    if not csv_str:
        raise HTTPException(status_code=410, detail="Result expired, please rerun")

    source_file = _get_file(db, task["file_id"], user_id)
    project_id  = source_file.project_id

    stem            = Path(source_file.filename).stem
    output_filename = f"{stem}_preprocessed.csv"

    csv_bytes = csv_str.encode("utf-8") if isinstance(csv_str, str) else csv_str

    upload = UploadFile(
        filename=output_filename,
        file=io.BytesIO(csv_bytes),
        headers=Headers({"content-type": "text/csv"}),
    )
    file_record = upload_project_file(db, project_id, user_id, upload)

    redis.delete(RESULT_NS, task_id)

    return file_record