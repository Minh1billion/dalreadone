from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.session import get_db
from app.models import User
from app.models.schemas import QueryResultOut, QueryResultListItem
from app.services import query_result_service

router = APIRouter(prefix="/history", tags=["history"])


@router.get("", response_model=list[QueryResultListItem])
def list_history(
    limit:  int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db:     Session = Depends(get_db),
    user:   User    = Depends(get_current_user),
):
    rows = query_result_service.list_results(
        db, user_id=user.id, limit=limit, offset=offset
    )
    return [query_result_service.to_list_item(r) for r in rows]


@router.get("/{result_id}", response_model=QueryResultOut)
def get_history_item(
    result_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    row = query_result_service.get_result(db, result_id=result_id, user_id=user.id)
    if not row:
        raise HTTPException(status_code=404, detail="Result not found")
    return row


@router.delete("/{result_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_history_item(
    result_id: int,
    db:   Session = Depends(get_db),
    user: User    = Depends(get_current_user),
):
    deleted = query_result_service.delete_result(db, result_id=result_id, user_id=user.id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Result not found")