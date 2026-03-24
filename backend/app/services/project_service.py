from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.projects import Project
from app.models.files import File
from app.storage.s3_client import delete_file as s3_delete_file


def _get_project_or_404(db: Session, project_id: int) -> Project:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


def _assert_owner(project: Project, user_id: int):
    if project.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")


def create_project(db: Session, user_id: int, name: str) -> Project:
    project = Project(name=name, user_id=user_id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


def list_projects(db: Session, user_id: int) -> list[Project]:
    return db.query(Project).filter(Project.user_id == user_id).all()


def get_project(db: Session, project_id: int, user_id: int) -> Project:
    project = _get_project_or_404(db, project_id)
    _assert_owner(project, user_id)
    return project


def update_project(db: Session, project_id: int, user_id: int, name: str) -> Project:
    project = _get_project_or_404(db, project_id)
    _assert_owner(project, user_id)
    project.name = name
    db.commit()
    db.refresh(project)
    return project


def delete_project(db: Session, project_id: int, user_id: int) -> None:
    project = _get_project_or_404(db, project_id)
    _assert_owner(project, user_id)

    files = db.query(File).filter(File.project_id == project_id).all()
    for file in files:
        s3_delete_file(file.s3_key)

    db.delete(project)
    db.commit()