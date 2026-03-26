from fastapi import APIRouter, Depends, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.oauth_service import google_login_url, google_callback_handler
from app.services.oauth_service import github_login_url, github_callback_handler

router = APIRouter(tags=["oauth"])


@router.get("/auth/google")
async def google_login():
    return RedirectResponse(url=google_login_url())


@router.get("/auth/google/callback")
async def google_callback(
    request: Request, response: Response, code: str, db: Session = Depends(get_db)
):
    return await google_callback_handler(request, response, code, db)


@router.get("/auth/github")
async def github_login():
    return RedirectResponse(url=github_login_url())


@router.get("/auth/github/callback")
async def github_callback(
    request: Request, response: Response, code: str, db: Session = Depends(get_db)
):
    return await github_callback_handler(request, response, code, db)