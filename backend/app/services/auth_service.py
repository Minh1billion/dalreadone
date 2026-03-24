from fastapi import HTTPException, Response
from sqlalchemy.orm import Session

from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    set_refresh_token_cookie,
)
from app.models import User


def issue_tokens(response: Response, user_id: int) -> dict:
    access_token = create_access_token(user_id)
    refresh_token = create_refresh_token(user_id)
    set_refresh_token_cookie(response, refresh_token)
    return {"access_token": access_token, "token_type": "bearer"}


def register_user(db: Session, username: str, password: str) -> User:
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Username already taken")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    user = User(username=username, password=hash_password(password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def login_user(db: Session, username: str, password: str) -> User:
    user = db.query(User).filter(User.username == username).first()
    if not user or not user.password or not verify_password(password, user.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return user


def get_or_create_oauth_user(db: Session, email: str, username: str) -> User:
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user

    base = username
    counter = 1
    while db.query(User).filter(User.username == username).first():
        username = f"{base}_{counter}"
        counter += 1

    user = User(username=username, email=email, password=None)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user