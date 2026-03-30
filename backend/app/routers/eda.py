from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.eda_service import create_eda_task, get_eda_task, run_eda_task

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
    task = get_eda_task(db, task_id, current_user.id)
    return {
        "task_id":  task["task_id"],
        "status":   task["status"],
        "step":     task["step"],
        "progress": task["progress"],
        "result":   task["result"] if task["status"] == "done" else None,
        "error":    task["error"]  if task["status"] == "error" else None,
    }