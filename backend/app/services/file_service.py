from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
import math
import io
import json

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
        elif filename.endswith((".xlsx", ".xls")):
            pd.read_excel(buf, nrows=5)
        elif filename.endswith(".json"):
            pd.read_json(buf)
        elif filename.endswith(".jsonl"):
            pd.read_json(buf, lines=True, nrows=5)
        elif filename.endswith(".parquet"):
            pd.read_parquet(buf)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"File appears to be corrupt or unreadable: {str(e)}"
        )
    return content


def _load_json_dataframe(buf: io.BytesIO) -> pd.DataFrame:
    raw = json.load(buf)
    if isinstance(raw, list):
        df = pd.json_normalize(raw)
    elif isinstance(raw, dict):
        for val in raw.values():
            if isinstance(val, list):
                df = pd.json_normalize(val)
                break
        else:
            df = pd.json_normalize([raw])
    else:
        raise ValueError("JSON root must be an array or object")

    for col in df.columns:
        if df[col].apply(lambda x: isinstance(x, list)).any():
            df[col] = df[col].apply(
                lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x
            )
    return df


def _load_dataframe(content: bytes, filename: str) -> pd.DataFrame:
    buf = io.BytesIO(content)
    if filename.endswith(".csv"):
        return pd.read_csv(buf, low_memory=False)
    elif filename.endswith((".xlsx", ".xls")):
        return pd.read_excel(buf)
    elif filename.endswith(".json"):
        return _load_json_dataframe(buf)
    elif filename.endswith(".jsonl"):
        records = [json.loads(line) for line in buf.read().decode().splitlines() if line.strip()]
        df = pd.json_normalize(records)
        df = df.dropna(axis=1, how="all")
        for col in df.columns:
            if df[col].apply(lambda x: isinstance(x, list)).any():
                df[col] = df[col].apply(
                    lambda x: json.dumps(x, ensure_ascii=False) if isinstance(x, list) else x
                )
        return df
    elif filename.endswith(".parquet"):
        return pd.read_parquet(buf)
    raise ValueError(f"Unsupported file format: {filename}")


def _sanitize_rows(rows: list[dict]) -> list[dict]:
    def _clean(v):
        if isinstance(v, float) and (math.isnan(v) or math.isinf(v)):
            return None
        if isinstance(v, np.integer):
            return int(v)
        if isinstance(v, np.floating):
            f = float(v)
            return None if (math.isnan(f) or math.isinf(f)) else f
        if isinstance(v, np.bool_):
            return bool(v)
        return v
    return [{k: _clean(v) for k, v in row.items()} for row in rows]


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

    rows = _sanitize_rows(df.head(n_rows).to_dict(orient="records"))

    return {
        "filename": filename,
        "n_rows": len(df),
        "n_cols": len(df.columns),
        "columns": df.columns.tolist(),
        "rows": rows,
    }