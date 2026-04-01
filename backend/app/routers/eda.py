from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.eda_service import (
    create_eda_task, get_eda_task, run_eda_task,
    create_review_task, get_review_task, run_review_task,
)

router = APIRouter(prefix="/eda", tags=["eda"])


@router.post("/files/{file_id}", status_code=202)
def start_eda(
    file_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = create_eda_task(db, file_id, current_user.id)
    background_tasks.add_task(run_eda_task, task["task_id"], db)
    return {"task_id": task["task_id"]}


@router.get("/{task_id}")
def get_eda_status(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task  = get_eda_task(db, task_id, current_user.id)
    done  = task["status"] == "done"
    error = task["status"] == "error"
    return {
        "task_id":  task["task_id"],
        "status":   task["status"],
        "step":     task["step"],
        "progress": task["progress"],
        "result":   task["result"] if done  else None,
        "error":    task["error"]  if error else None,
    }


@router.post("/{eda_task_id}/review", status_code=202)
def start_review(
    eda_task_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = create_review_task(db, eda_task_id, current_user.id)
    background_tasks.add_task(run_review_task, task["task_id"])
    return {"task_id": task["task_id"]}


@router.get("/{eda_task_id}/review/{review_task_id}")
def get_review_status(
    eda_task_id: str,
    review_task_id: str,
    current_user: User = Depends(get_current_user),
):
    task  = get_review_task(review_task_id, current_user.id)
    done  = task["status"] == "done"
    error = task["status"] == "error"
    return {
        "task_id":     task["task_id"],
        "eda_task_id": task["eda_task_id"],
        "status":      task["status"],
        "progress":    task["progress"],
        "result":      task["result"] if done  else None,
        "usage":       task["usage"]  if done  else None,
        "error":       task["error"]  if error else None,
    }