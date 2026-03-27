from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)
    password = Column(String, nullable=True) 
    created_at = Column(DateTime, default=datetime.utcnow)

    projects = relationship("Project", back_populates="created_by")
    files = relationship("File", back_populates="uploaded_by")
    query_results = relationship("QueryResult", back_populates="user")