from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models import User
from app.services.query_service import run_query

router = APIRouter(prefix="/projects/{project_id}/files/{file_id}", tags=["query"])


@router.post("/query")
def query_file(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return run_query(db, project_id, file_id, current_user.id)