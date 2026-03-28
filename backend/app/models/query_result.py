from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base


class QueryResult(Base):
    __tablename__ = "query_results"

    id         = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    file_id    = Column(Integer, ForeignKey("files.id",    ondelete="CASCADE"), nullable=False)
    user_id    = Column(Integer, ForeignKey("users.id",    ondelete="CASCADE"), nullable=False, index=True)
    filename   = Column(String, nullable=False)
    question   = Column(String, nullable=True)
    result_json = Column(JSON, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="query_results")
    project = relationship("Project", back_populates="query_results")
    file = relationship("File", back_populates="query_results")