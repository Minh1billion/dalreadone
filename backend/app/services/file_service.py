from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import io

from app.models import File, Project
from app.storage.s3_client import upload_file, delete_file, get_file_bytes as s3_get_file_bytes
from app.llm.text_detector import is_text_heavy


ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
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

def get_file_preview(db: Session, file_id: int, user_id: int) -> dict:
    """
    Return lightweight DataFrame statistics for the file preview panel.
    No LLM involved — pure pandas.
    """
    file_bytes, filename = get_file_bytes(db, file_id, user_id)
    
    buf = io.BytesIO(file_bytes)
    if filename.endswith(".csv"):
        df = pd.read_csv(buf)
    else:
        df = pd.read_excel(buf)

    n_rows, n_cols = df.shape

    # Missing value stats 
    missing = []
    for col in df.columns:
        null_count = int(df[col].isna().sum())
        missing.append({
            "column":     col,
            "dtype":      str(df[col].dtype),
            "null_count": null_count,
            "null_pct":   round(null_count / n_rows * 100, 1) if n_rows > 0 else 0.0,
        })

    # Numeric describe 
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    describe_rows = []
    if numeric_cols:
        desc = df[numeric_cols].describe().round(3)
        for col in numeric_cols:
            s = desc[col]
            describe_rows.append({
                "column": col,
                "count":  s.get("count"),
                "mean":   s.get("mean"),
                "std":    s.get("std"),
                "min":    s.get("min"),
                "25%":    s.get("25%"),
                "50%":    s.get("50%"),
                "75%":    s.get("75%"),
                "max":    s.get("max"),
            })

    # Sample rows 
    sample = df.head(5).replace({np.nan: None}).to_dict(orient="records")
    
    
    heavy, text_cols = is_text_heavy(df)

    return {
        "filename":      filename,
        "shape":         {"rows": n_rows, "cols": n_cols},
        "columns":       list(df.columns),
        "missing":       missing,
        "describe":      describe_rows,
        "sample":        sample,
        "dtypes":        {col: str(dtype) for col, dtype in df.dtypes.items()},
        "strategy":   "nlp" if heavy else "structured",
        "text_cols":  text_cols,
    }