from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Config
from app.core.oauth import oauth
from app.core.security import decode_token, clear_refresh_token_cookie, get_db
from app.models.schemas import RegisterRequest, LoginRequest
from app.services import auth as auth_service

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


@router.get("/google")
async def google_login(request: Request):
    return await oauth.google.authorize_redirect(request, Config.GOOGLE_REDIRECT_URI)


@router.get("/google/callback")
async def google_callback(request: Request, response: Response, db: Session = Depends(get_db)):
    token = await oauth.google.authorize_access_token(request)
    user_info = token.get("userinfo")
    user = auth_service.get_or_create_oauth_user(db, email=user_info["email"], username=user_info["name"])
    tokens = auth_service.issue_tokens(response, user.id)
    return RedirectResponse(url=f"{Config.FRONTEND_URL}?access_token={tokens['access_token']}")


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

    user = auth_service.get_or_create_oauth_user(db, email=email, username=user_info["login"])
    tokens = auth_service.issue_tokens(response, user.id)
    return RedirectResponse(url=f"{Config.FRONTEND_URL}?access_token={tokens['access_token']}")