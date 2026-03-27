from datetime import datetime
from typing import Any
from pydantic import BaseModel


class RegisterRequest(BaseModel):
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class FileResponse(BaseModel):
    id: int
    filename: str
    s3_key: str
    uploaded_by_id: int
    project_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    name: str


class ProjectUpdate(BaseModel):
    name: str


class ProjectResponse(BaseModel):
    id: int
    name: str
    user_id: int
    created_at: datetime
    files: list[FileResponse] = []

    class Config:
        from_attributes = True
        
class QueryResultOut(BaseModel):
    id:          int
    project_id:  int
    file_id:     int
    filename:    str
    question:    str | None
    result_json: dict[str, Any]
    created_at:  datetime
 
    model_config = {"from_attributes": True}
 
 
class QueryResultListItem(BaseModel):
    """Lightweight item for the history list — no full result_json."""
    id:         int
    project_id: int
    file_id:    int
    filename:   str
    question:   str | None
    insight:    str        # pulled from result_json for preview
    created_at: datetime
 
    model_config = {"from_attributes": True}