from fastapi import FastAPI

from app.routers import auth, files, projects, query, oauth

app = FastAPI()

# Oauth routes
app.include_router(oauth.router)

# API routes
app.include_router(auth.router, prefix="/api")
app.include_router(projects.router, prefix="/api")
app.include_router(files.router, prefix="/api")
app.include_router(query.router, prefix="/api")


@app.get("/")
def root():
    return {"status": "ok"}