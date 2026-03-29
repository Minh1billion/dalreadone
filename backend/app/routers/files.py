from fastapi import APIRouter, Depends, UploadFile, File as FastAPIFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.models import User
from app.models.schemas import FileResponse
from app.services.file_service import (
    upload_project_file,
    delete_project_file,
    list_project_files,
    get_file_preview
)

router = APIRouter(prefix="/projects/{project_id}/files", tags=["files"])

@router.post("", response_model=FileResponse, status_code=201)
def upload_file(
    project_id: int,
    file: UploadFile = FastAPIFile(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return upload_project_file(db, project_id, current_user.id, file)


@router.get("", response_model=list[FileResponse])
def list_files(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_project_files(db, project_id, current_user.id)


@router.delete("/{file_id}", status_code=204)
def delete_file(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return delete_project_file(db, project_id, file_id, current_user.id)

@router.get("/{file_id}/preview")
def preview_file(
    project_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_file_preview(db, file_id, current_user.id)