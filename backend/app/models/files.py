from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.models.base import Base


class File(Base):
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    s3_key = Column(String, unique=True, nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    uploaded_by = relationship("User", back_populates="files")
    project = relationship("Project", back_populates="files")
    query_results = relationship(
        "QueryResult",
        back_populates="file",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )