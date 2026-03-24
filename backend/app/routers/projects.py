from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, get_db
from app.models import User
from app.models.schemas import ProjectCreate, ProjectUpdate, ProjectResponse
from app.services.project_service import (
    create_project,
    list_projects,
    get_project,
    update_project,
    delete_project,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create(
    body: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return create_project(db, current_user.id, body.name)


@router.get("", response_model=list[ProjectResponse])
def list_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return list_projects(db, current_user.id)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_one(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_project(db, project_id, current_user.id)


@router.patch("/{project_id}", response_model=ProjectResponse)
def update(
    project_id: int,
    body: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return update_project(db, project_id, current_user.id, body.name)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    delete_project(db, project_id, current_user.id)