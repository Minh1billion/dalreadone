from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import Config
from app.routers import auth

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=Config.JWT_SECRET_KEY)

app.include_router(auth.router)


@app.get("/")
def root():
    return {"status": "ok"}