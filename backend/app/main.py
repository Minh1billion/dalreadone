from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.core.config import Config
from app.routers import auth, files, projects

app = FastAPI()

app.add_middleware(SessionMiddleware, secret_key=Config.JWT_SECRET_KEY)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(files.router)


@app.get("/")
def root():
    return {"status": "ok"}