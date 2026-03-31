import uuid
from datetime import datetime
from typing import Any, Dict

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import File
from app.services.file_service import get_file_bytes, _load_dataframe
from app.pipelines.preprocess.pipeline import (
    run_preprocess,
    MissingStep,
    EncodingStep,
    OutlierStep,
    ScalingStep,
    PipelineStep,
)
from app.pipelines.preprocess import (
    preprocess_01_missing as m01,
    preprocess_02_encoding as m02,
    preprocess_03_scaling as m03,
    preprocess_04_outlier as m04,
)
from app.storage import redis
from app.core.config import Config

PREPROCESS_NS = "preprocess_task"
PREPROCESS_TTL = Config.PREPROCESS_TASK_TTL


def _task_dict(task_id: str, file_id: int, user_id: int, raw_steps: list[Dict]) -> dict[str, Any]:
    return {
        "task_id":    task_id,
        "file_id":    file_id,
        "user_id":    user_id,
        "raw_steps":  raw_steps,
        "status":     "pending",
        "step":       None,
        "progress":   0,
        "result":     None,
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


def _build_steps(raw_steps: list[Dict]) -> list[PipelineStep]:
    steps: list[PipelineStep] = []
    for raw in raw_steps:
        name = raw["name"]
        p = raw.get("params", {})

        if name == "missing":
            overrides = {
                col: {k: v for k, v in cfg.items()}
                for col, cfg in p.get("column_overrides", {}).items()
            }
            steps.append(MissingStep(params=m01.MissingParams(
                num_strategy=p.get("num_strategy", "median"),
                cat_strategy=p.get("cat_strategy", "mode"),
                num_fill_value=p.get("num_fill_value", 0),
                cat_fill_value=p.get("cat_fill_value", "unknown"),
                drop_col_threshold=p.get("drop_col_threshold", 0.5),
                drop_row_subset=p.get("drop_row_subset"),
                column_overrides=overrides,
            )))

        elif name == "encoding":
            col_overrides: Dict[str, m02.ColumnEncodeParams] = {
                col: m02.ColumnEncodeParams(
                    strategy=cfg["strategy"],
                    ordinal_categories=cfg.get("ordinal_categories"),
                    max_onehot_cardinality=cfg.get("max_onehot_cardinality", 20),
                )
                for col, cfg in p.get("column_overrides", {}).items()
            }
            steps.append(EncodingStep(params=m02.EncodingParams(
                default_strategy=p.get("default_strategy", "onehot"),
                max_onehot_cardinality=p.get("max_onehot_cardinality", 20),
                column_overrides=col_overrides,
                skip_cols=p.get("skip_cols"),
            )))

        elif name == "outlier":
            col_overrides: Dict[str, m04.ColumnOutlierParams] = {
                col: m04.ColumnOutlierParams(
                    strategy=cfg["strategy"],
                    iqr_k=cfg.get("iqr_k", 1.5),
                    winsorize_bounds=tuple(cfg.get("winsorize_bounds", [0.01, 0.99])),
                )
                for col, cfg in p.get("column_overrides", {}).items()
            }
            steps.append(OutlierStep(params=m04.OutlierParams(
                default_strategy=p.get("default_strategy", "clip"),
                iqr_k=p.get("iqr_k", 1.5),
                winsorize_bounds=tuple(p.get("winsorize_bounds", [0.01, 0.99])),
                column_overrides=col_overrides,
                skip_cols=p.get("skip_cols"),
            )))

        elif name == "scaling":
            col_overrides: Dict[str, m03.ColumnScaleParams] = {
                col: m03.ColumnScaleParams(
                    strategy=cfg["strategy"],
                    feature_range=tuple(cfg.get("feature_range", [0.0, 1.0])),
                )
                for col, cfg in p.get("column_overrides", {}).items()
            }
            steps.append(ScalingStep(params=m03.ScalingParams(
                default_strategy=p.get("default_strategy", "standard"),
                feature_range=tuple(p.get("feature_range", [0.0, 1.0])),
                column_overrides=col_overrides,
                skip_cols=p.get("skip_cols"),
            )))

        else:
            raise ValueError(f"Unknown step: {name}")

    return steps


def create_preprocess_task(
    db: Session,
    file_id: int,
    user_id: int,
    raw_steps: list[Dict],
) -> dict:
    _get_file(db, file_id, user_id)
    _build_steps(raw_steps)

    task_id = str(uuid.uuid4())
    task = _task_dict(task_id, file_id, user_id, raw_steps)
    redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)
    return task


def get_preprocess_task(db: Session, task_id: str, user_id: int) -> dict:
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
        content, filename = get_file_bytes(db, task["file_id"], task["user_id"])
        df = _load_dataframe(content, filename)
        steps = _build_steps(task["raw_steps"])

        _df_out, report = run_preprocess(df, source=filename, steps=steps, on_step=_update)

        task["status"]   = "done"
        task["step"]     = "done"
        task["progress"] = 100
        task["result"]   = report
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)

    except Exception as e:
        task["status"] = "error"
        task["error"]  = str(e)
        redis.set(PREPROCESS_NS, task_id, task, ttl=PREPROCESS_TTL)