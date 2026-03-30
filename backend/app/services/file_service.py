from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import io

from app.models import File, Project
from app.storage.s3_client import upload_file, delete_file, get_file_bytes as s3_get_file_bytes


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls", ".json", ".jsonl", ".parquet"}
MAX_FILES_PER_PROJECT = 5


def _get_project(db: Session, project_id: int, user_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return project


def _validate_file(file: UploadFile):
    ext = Path(file.filename).suffix
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Accepted: {', '.join(ALLOWED_EXTENSIONS)}"
        )


def _validate_file_content(file: UploadFile) -> bytes:
    content = file.file.read()
    file.file.seek(0)

    filename = file.filename
    try:
        buf = io.BytesIO(content)
        if filename.endswith(".csv"):
            pd.read_csv(buf, nrows=5)
        else:
            pd.read_excel(buf, nrows=5)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"File appears to be corrupt or unreadable: {str(e)}"
        )
    return content


def _load_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(content)
    if filename.endswith(".csv"):
        return pd.read_csv(buf, low_memory=False)
    return pd.read_excel(buf)


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

    _validate_file_content(file)
    s3_key = f"projects/{project_id}/{file.filename}"
    upload_file(file.file, s3_key)

    if is_overwrite:
        record = existing_map[file.filename]
        record.uploaded_at = datetime.utcnow()
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


def get_file_bytes(db: Session, file_id: int, user_id: int) -> tuple[bytes, str]:
    record = db.query(File).filter(File.id == file_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="File not found")
    if record.project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return s3_get_file_bytes(record.s3_key), record.filename


def get_file_preview(db: Session, file_id: int, user_id: int, n_rows: int = 100) -> dict:
    content, filename = get_file_bytes(db, file_id, user_id)
    df = _load_dataframe(content, filename)

    preview_df = df.head(n_rows).replace({np.nan: None})

    return {
        "filename": filename,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": df.columns.tolist(),
        "rows": preview_df.to_dict(orient="records"),
    }