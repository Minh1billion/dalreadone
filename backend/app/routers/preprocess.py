from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db, SessionLocal
from app.models import User
from app.models.preprocess_schema import (
    PreprocessRunRequest,
    PreprocessTaskResponse,
    PreprocessConfirmResponse,
)
from app.services.preprocess_service import (
    create_preprocess_task,
    get_preprocess_task,
    run_preprocess_task,
    confirm_preprocess_task,
    create_suggest_task,
    get_suggest_task,
    run_suggest_task,
    PREPROCESS_NS,
    RESULT_NS,
    SUGGEST_NS,
)
from app.storage import redis

router = APIRouter(prefix="/preprocess", tags=["preprocess"])


def _run_with_new_session(task_id: str) -> None:
    db = SessionLocal()
    try:
        run_preprocess_task(task_id, db)
    finally:
        db.close()


@router.post("/run", response_model=PreprocessTaskResponse, status_code=202)
def start_preprocess(
    request: PreprocessRunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    task = create_preprocess_task(db, request, current_user.id)
    background_tasks.add_task(_run_with_new_session, task["task_id"])
    return task


@router.get("/status/{task_id}", response_model=PreprocessTaskResponse)
def get_preprocess_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    return get_preprocess_task(task_id, current_user.id)


@router.post("/confirm/{task_id}", response_model=PreprocessConfirmResponse)
def confirm_preprocess(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = confirm_preprocess_task(task_id, current_user.id, db)
    return PreprocessConfirmResponse(
        file_id=file_record.id,
        filename=file_record.filename,
        project_id=file_record.project_id,
    )


@router.delete("/cancel/{task_id}", status_code=204)
def cancel_preprocess(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task = redis.get(PREPROCESS_NS, task_id)
    if task and task["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    redis.delete(PREPROCESS_NS, task_id)
    redis.delete(RESULT_NS, task_id)


@router.post("/suggest/{review_task_id}", status_code=202)
def start_suggest(
    review_task_id: str,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
):
    task = create_suggest_task(review_task_id, current_user.id)
    background_tasks.add_task(run_suggest_task, task["task_id"])
    return {"task_id": task["task_id"]}


@router.get("/suggest/status/{task_id}")
def get_suggest_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task  = get_suggest_task(task_id, current_user.id)
    done  = task["status"] == "done"
    error = task["status"] == "error"
    return {
        "task_id":        task["task_id"],
        "review_task_id": task["review_task_id"],
        "status":         task["status"],
        "progress":       task["progress"],
        "steps":          task["result"]     if done  else None,
        "usage":          task["usage"]      if done  else None,
        "ast_errors":     task["ast_errors"] if done  else None,
        "error":          task["error"]      if error else None,
    }


@router.delete("/suggest/{task_id}", status_code=204)
def cancel_suggest(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    task = redis.get(SUGGEST_NS, task_id)
    if task and task["user_id"] != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    redis.delete(SUGGEST_NS, task_id)