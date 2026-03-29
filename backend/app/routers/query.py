from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.core.security import get_current_user
from app.models import User, File
from app.services.query_service import run_query
from app.services import query_result_service

router = APIRouter(prefix="/projects/{project_id}/files/{file_id}", tags=["query"])


class StopwordsConfig(BaseModel):
    add:      list[str] = []
    remove:   list[str] = []
    

class QueryRequest(BaseModel):
    question:  str = ""
    stopwords: StopwordsConfig = StopwordsConfig()


@router.post("/query")
def query_file(
    project_id: int,
    file_id: int,
    body: QueryRequest = QueryRequest(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = db.query(File).filter(
        File.id == file_id,
        File.project_id == project_id,
    ).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    try:
        response = run_query(
            db=db,
            project_id=project_id,
            file_id=file_id,
            user_id=current_user.id,
            user_question=body.question,
            stopwords_config=body.stopwords.model_dump(),
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    result_dict = response if isinstance(response, dict) else response.model_dump()

    query_result_service.save_result(
        db,
        user_id=current_user.id,
        project_id=project_id,
        file_id=file_id,
        filename=file.filename,
        question=body.question or None,
        result_json=result_dict,
    )

    return response