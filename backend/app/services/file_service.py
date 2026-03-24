from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from pathlib import Path

from app.models import File, Project
from app.storage.s3_client import upload_file, delete_file


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
MAX_FILES_PER_PROJECT = 5


def _get_project(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    
def _validate_file(file: UploadFile):
    ext = Path(file.filename).suffix
    
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
def upload_project_file(
    db: Session,
    project_id: int,
    user_id: int,
    file: UploadFile,
) -> File:
    project = _get_project(db, project_id, user_id)
    _validate_file(file)
    
    existing_files = db.query(File).filter(File.project_id == project_id).all()
    existing_map = {f.filename: f for f in existing_files}
    
    is_overwrite = file.filename in existing_map
    if not is_overwrite and len(existing_files) >= MAX_FILES_PER_PROJECT:
        raise HTTPException(
            status_code=400,
            detail=f"Project has reached the limit of {MAX_FILES_PER_PROJECT} files"
        )
        
    s3_key = f"projects/{project_id}/{file.filename}"
    upload_file(file.file, s3_key)
    
    if is_overwrite:
        record = existing_map[file.filename]
        
        db.commit()
        db.refresh(record)
        return record
    
    record = File(
        filename=file.filename,
        s3_key=s3_key,
        uploaded_by_id=user_id,
        project_id=project_id,
    )
    
    db.add(record)
    db.commit()
    db.refresh(record)
    return record

def delete_project_file(
    db: Session,
    project_id: int,
    file_id: int,
    user_id: int,
) -> None:
    _get_project(db, project_id, user_id)
    
    record = db.query(File).filter(File.id == file_id, File.project_id == project_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    
    delete_file(record.s3_key)
    db.delete(record)
    db.commit()
    
def list_project_files(
    db: Session,
    project_id: int,
    user_id: int,
) -> list[File]:
    _get_project(db, project_id, user_id)
    
    return db.query(File).filter(File.project_id == project_id).all()