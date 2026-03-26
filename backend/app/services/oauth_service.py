from urllib.parse import urlencode

import httpx
from fastapi import HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.config import Config
from app.services.auth_service import get_or_create_oauth_user, issue_tokens


# Google

def google_login_url() -> str:
    params = urlencode({
        "client_id": Config.GOOGLE_CLIENT_ID,
        "redirect_uri": Config.GOOGLE_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "prompt": "select_account",
    })
    return f"https://accounts.google.com/o/oauth2/v2/auth?{params}"


async def google_callback_handler(
    request: Request, response: Response, code: str, db: Session
) -> RedirectResponse:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": Config.GOOGLE_CLIENT_ID,
                "client_secret": Config.GOOGLE_CLIENT_SECRET,
                "redirect_uri": Config.GOOGLE_REDIRECT_URI,
                "grant_type": "authorization_code",
            },
        )
    token_data = token_resp.json()
    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail=f"Google token exchange failed: {token_data}")

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://www.googleapis.com/oauth2/v2/userinfo",
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
    user_info = user_resp.json()

    user = get_or_create_oauth_user(db, email=user_info["email"], username=user_info["name"])
    tokens = issue_tokens(response, user.id)
    return RedirectResponse(url=f"{Config.FRONTEND_URL}?access_token={tokens['access_token']}")


# GitHub

def github_login_url() -> str:
    params = urlencode({
        "client_id": Config.GITHUB_CLIENT_ID,
        "redirect_uri": Config.GITHUB_REDIRECT_URI,
        "scope": "user:email",
    })
    return f"https://github.com/login/oauth/authorize?{params}"


async def github_callback_handler(
    request: Request, response: Response, code: str, db: Session
) -> RedirectResponse:
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "code": code,
                "client_id": Config.GITHUB_CLIENT_ID,
                "client_secret": Config.GITHUB_CLIENT_SECRET,
                "redirect_uri": Config.GITHUB_REDIRECT_URI,
            },
            headers={"Accept": "application/json"},
        )
    token_data = token_resp.json()
    if "access_token" not in token_data:
        raise HTTPException(status_code=400, detail=f"GitHub token exchange failed: {token_data}")

    access_token = token_data["access_token"]

    async with httpx.AsyncClient() as client:
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}"},
        )
    user_info = user_resp.json()

    email = user_info.get("email")
    if not email:
        async with httpx.AsyncClient() as client:
            emails_resp = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {access_token}"},
            )
        primary = next((e for e in emails_resp.json() if e["primary"]), None)
        email = primary["email"] if primary else None

    if not email:
        raise HTTPException(status_code=400, detail="Could not retrieve email from GitHub")

    user = get_or_create_oauth_user(db, email=email, username=user_info["login"])
    tokens = issue_tokens(response, user.id)
    return RedirectResponse(url=f"{Config.FRONTEND_URL}?access_token={tokens['access_token']}")