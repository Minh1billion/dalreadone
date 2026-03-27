from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import Base


class QueryResult(Base):
    __tablename__ = "query_results"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False, index=True)
    file_id    = Column(Integer, ForeignKey("files.id"), nullable=False)
    filename   = Column(String, nullable=False)
    question   = Column(String, nullable=True)
    result_json = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="query_results")
    project = relationship("Project", back_populates="query_results")
    file = relationship("File", back_populates="query_results")