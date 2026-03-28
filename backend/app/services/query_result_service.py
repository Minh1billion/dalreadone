import math
import json
from sqlalchemy.orm import Session

from app.models.query_result import QueryResult
from app.models.schemas import QueryResultOut, QueryResultListItem

DEFAULT_LIMIT = 50


def _sanitize(obj):
    """Recursively replace NaN/Inf with None for JSON compatibility."""
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    return obj


def save_result(
    db: Session,
    *,
    user_id: int,
    project_id: int,
    file_id: int,
    filename: str,
    question: str | None,
    result_json: dict,
) -> QueryResult:
    row = QueryResult(
        user_id=user_id,
        project_id=project_id,
        file_id=file_id,
        filename=filename,
        question=question or None,
        result_json=_sanitize(result_json),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_results(
    db: Session,
    *,
    user_id: int,
    limit: int = DEFAULT_LIMIT,
    offset: int = 0,
) -> list[QueryResult]:
    return (
        db.query(QueryResult)
        .filter(QueryResult.user_id == user_id)
        .order_by(QueryResult.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )


def get_result(db: Session, *, result_id: int, user_id: int) -> QueryResult | None:
    return (
        db.query(QueryResult)
        .filter(QueryResult.id == result_id, QueryResult.user_id == user_id)
        .first()
    )


def delete_result(db: Session, *, result_id: int, user_id: int) -> bool:
    row = get_result(db, result_id=result_id, user_id=user_id)
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True


def to_list_item(row: QueryResult) -> QueryResultListItem:
    insight = row.result_json.get("insight", "") if isinstance(row.result_json, dict) else ""
    return QueryResultListItem(
        id=row.id,
        project_id=row.project_id,
        file_id=row.file_id,
        filename=row.filename,
        question=row.question,
        insight=insight[:160],
        created_at=row.created_at,
    )