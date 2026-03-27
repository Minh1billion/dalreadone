from fastapi import FastAPI
from app.routers import auth, files, projects, query, oauth, history
from app.db.session import engine
from app.models import Base

app = FastAPI()

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Oauth routes
app.include_router(oauth.router)

# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(query.router, prefix="/api")
app.include_router(history.router, prefix="/api")

@app.get("/")
def root():
    return {"status": "ok"}