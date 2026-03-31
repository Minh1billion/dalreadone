from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import User
from app.models.preprocess_schema import (
    PreprocessRunRequest,
    PreprocessTaskResponse,
    PreprocessResultResponse,
)
from app.services.preprocess_service import (
    create_preprocess_task,
    get_preprocess_task,
    run_preprocess_task,
)

router = APIRouter(prefix="/preprocess", tags=["preprocess"])


@router.post("/run", response_model=PreprocessTaskResponse, status_code=202)
def start_preprocess(
    request: PreprocessRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = create_preprocess_task(db, request, current_user.id)
    background_tasks.add_task(run_preprocess_task, task["task_id"], db)
    return task


@router.get("/status/{task_id}", response_model=PreprocessTaskResponse)
def get_preprocess_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    return get_preprocess_task(task_id, current_user.id)


@router.get("/result/{task_id}", response_model=PreprocessResultResponse)
def get_preprocess_result(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task = get_preprocess_task(task_id, current_user.id)
    return {
        "task_id":        task["task_id"],
        "file_id":        task["file_id"],
        "status":         task["status"],
        "result_s3_key":  task["result_s3_key"] if task["status"] == "done" else None,
        "preview":        task["preview"]        if task["status"] == "done" else None,
        "created_at":     task["created_at"],
    }