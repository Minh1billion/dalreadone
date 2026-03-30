import uuid
from datetime import datetime
from typing import Any

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import File
from app.services.file_service import get_file_bytes, _load_dataframe
from app.pipelines.eda.pipeline import run_eda
from app.storage import redis

EDA_NS  = "eda_task"
from app.core.config import Config
EDA_TTL = Config.EDA_TASK_TTL  # 24h


def _task_dict(task_id: str, file_id: int, user_id: int) -> dict[str, Any]:
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


def _get_file(db: Session, file_id: int, user_id: int) -> File:
    record = db.query(File).filter(File.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if record.project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return record


def create_eda_task(db: Session, file_id: int, user_id: int) -> dict:
    _get_file(db, file_id, user_id)

    task_id = str(uuid.uuid4())
    task    = _task_dict(task_id, file_id, user_id)
    redis.set(EDA_NS, task_id, task, ttl=EDA_TTL)
    return task


def get_eda_task(db: Session, task_id: str, user_id: int) -> dict:
    task = redis.get(EDA_NS, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if task["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return task


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
        df = _load_dataframe(content, filename)

        report = run_eda(df, source=filename, on_step=_update)

        task["status"]   = "done"
        task["step"]     = "data_quality_score"
        task["progress"] = 100
        task["result"]   = report
        redis.set(EDA_NS, task_id, task, ttl=EDA_TTL)

    except Exception as e:
        task["status"] = "error"
        task["error"]  = str(e)
        redis.set(EDA_NS, task_id, task, ttl=EDA_TTL)