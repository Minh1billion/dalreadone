from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.core.security import decode_token, clear_refresh_token_cookie
from app.db.session import get_db
from app.models.schemas import RegisterRequest, LoginRequest
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.register_user(db, body.username, body.password)
    return auth_service.issue_tokens(response, user.id)


@router.post("/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = auth_service.login_user(db, body.username, body.password)
    return auth_service.issue_tokens(response, user.id)


@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    user_id = decode_token(token, expected_type="refresh")
    return auth_service.issue_tokens(response, user_id)


@router.post("/logout")
def logout(response: Response):
    clear_refresh_token_cookie(response)
    return {"message": "Logged out"}