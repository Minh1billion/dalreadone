from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    set_refresh_token_cookie, clear_refresh_token_cookie,
    get_db, get_current_user,
)
from app.core.oauth import oauth
from app.core.config import Config
from app.models import User

router = APIRouter(prefix="/auth", tags=["auth"])


# Schemas  
class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str


# Helpers  
def _get_or_create_oauth_user(db: Session, email: str, username: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # username có thể trùng với user thường, thêm suffix nếu cần
        base_username = username
        counter = 1
        while db.query(User).filter(User.username == username).first():
            username = f"{base_username}_{counter}"
            counter += 1
        user = User(username=username, email=email, password=None)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def _issue_tokens(response: Response, user_id: int) -> dict:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    set_refresh_token_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}


# Register / Login  
@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = User(
        username=body.username,
        password=hash_password(body.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(response, user.id)


@router.post("/login")
def login(body: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not user.password or not verify_password(body.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _issue_tokens(response, user.id)


# Refresh  
@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="Missing refresh token")
    user_id = decode_token(token, expected_type="refresh")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _issue_tokens(response, user.id)


# Logout  
@router.post("/logout")
def logout(response: Response):
    clear_refresh_token_cookie(response)
    return {"message": "Logged out"}


# OAuth Google  
@router.get("/google")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, Config.GOOGLE_REDIRECT_URI)

@router.get("/google/callback")
async def google_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    user = _get_or_create_oauth_user(db, email=user_info["email"], username=user_info["name"])
    tokens = _issue_tokens(response, user.id)
    return RedirectResponse(url=f"{Config.FRONTEND_URL}?access_token={tokens['access_token']}")


# OAuth Github  
@router.get("/github")
async def github_login(request: Request):
    return await oauth.github.authorize_redirect(request, Config.GITHUB_REDIRECT_URI)

@router.get("/github/callback")
async def github_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    token = await oauth.github.authorize_access_token(request)
    resp = await oauth.github.get("user", token=token)
    user_info = resp.json()

    email = user_info.get("email")
    if not email:
        emails_resp = await oauth.github.get("user/emails", token=token)
        primary = next((e for e in emails_resp.json() if e["primary"]), None)
        email = primary["email"] if primary else None
    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from Github")

    user = _get_or_create_oauth_user(db, email=email, username=user_info["login"])
    tokens = _issue_tokens(response, user.id)
    return RedirectResponse(url=f"{Config.FRONTEND_URL}?access_token={tokens['access_token']}")