import asyncio
import sys
import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import File
from app.services.file_service import get_file_bytes, _load_dataframe
from app.pipelines.eda.pipeline import run_eda
from app.llm.eda_pipeline import EDAReviewPipeline
from app.storage import redis
from app.core.config import Config

EDA_NS    = "eda_task"
REVIEW_NS = "review_task"
EDA_TTL   = Config.EDA_TASK_TTL


def _get_file(db: Session, file_id: int, user_id: int) -> File:
    record = db.query(File).filter(File.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if record.project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return record


def _get_task(ns: str, task_id: str, user_id: int) -> dict:
    task = redis.get(ns, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return task


def _eda_task_dict(task_id: str, file_id: int, user_id: int) -> dict[str, Any]:
    return {
        "task_id":    task_id,
        "file_id":    file_id,
        "user_id":    user_id,
        "status":     "pending",
        "step":       None,
        "progress":   0,
        "result":     None,
        "error":      None,
        "created_at": datetime.utcnow().isoformat(),
    }


def create_eda_task(db: Session, file_id: int, user_id: int) -> dict:
    _get_file(db, file_id, user_id)
    task_id = str(uuid.uuid4())
    task    = _eda_task_dict(task_id, file_id, user_id)
    redis.set(EDA_NS, task_id, task, ttl=EDA_TTL)
    return task


def get_eda_task(db: Session, task_id: str, user_id: int) -> dict:
    return _get_task(EDA_NS, task_id, user_id)


def run_eda_task(task_id: str, db: Session) -> None:
    task = redis.get(EDA_NS, task_id)
    if not task:
        return

    def _update(step: str, progress: int):
        task["status"]   = "running"
        task["step"]     = step
        task["progress"] = progress
        redis.set(EDA_NS, task_id, task, ttl=EDA_TTL)

    try:
        content, filename = get_file_bytes(db, task["file_id"], task["user_id"])
        df                = _load_dataframe(content, filename)
        report            = run_eda(df, source=filename, on_step=_update)

        task["status"]   = "done"
        task["step"]     = "done"
        task["progress"] = 100
        task["result"]   = report
        redis.set(EDA_NS, task_id, task, ttl=EDA_TTL)

    except Exception as e:
        task["status"] = "error"
        task["error"]  = str(e)
        redis.set(EDA_NS, task_id, task, ttl=EDA_TTL)


def _review_task_dict(
    task_id: str, eda_task_id: str, user_id: int
) -> dict[str, Any]:
    return {
        "task_id":     task_id,
        "eda_task_id": eda_task_id,
        "user_id":     user_id,
        "status":      "pending",
        "progress":    0,
        "result":      None,
        "usage":       None,
        "error":       None,
        "created_at":  datetime.utcnow().isoformat(),
    }


def create_review_task(db: Session, eda_task_id: str, user_id: int) -> dict:
    eda_task = _get_task(EDA_NS, eda_task_id, user_id)
    if eda_task["status"] != "done":
        raise HTTPException(
            status_code=409,
            detail=f"EDA task is '{eda_task['status']}', must be 'done' before reviewing",
        )
    if eda_task["result"] is None:
        raise HTTPException(status_code=409, detail="EDA result is empty")

    task_id = str(uuid.uuid4())
    task    = _review_task_dict(task_id, eda_task_id, user_id)
    redis.set(REVIEW_NS, task_id, task, ttl=EDA_TTL)
    return task


def get_review_task(task_id: str, user_id: int) -> dict:
    return _get_task(REVIEW_NS, task_id, user_id)


def run_review_task(task_id: str) -> None:
    task = redis.get(REVIEW_NS, task_id)
    if not task:
        return

    def _update(progress: int):
        task["status"]   = "running"
        task["progress"] = progress
        redis.set(REVIEW_NS, task_id, task, ttl=EDA_TTL)

    try:
        _update(10)

        eda_task = redis.get(EDA_NS, task["eda_task_id"])
        if not eda_task or eda_task["result"] is None:
            raise ValueError("EDA result not found in cache")

        _update(20)

        if sys.platform == "win32":
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

        pipeline      = EDAReviewPipeline()
        review_result = asyncio.run(
            pipeline.arun(eda_task["result"])
        )

        task["status"]   = "done"
        task["progress"] = 100
        task["result"]   = review_result.model_dump(exclude={"usage"})
        task["usage"]    = review_result.usage
        redis.set(REVIEW_NS, task_id, task, ttl=EDA_TTL)

    except Exception as e:
        task["status"] = "error"
        task["error"]  = str(e)
        redis.set(REVIEW_NS, task_id, task, ttl=EDA_TTL)