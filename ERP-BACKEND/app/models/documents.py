"""
Document Management models
Handles file uploads, storage, and metadata
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """Document model for file management"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    entity_type = Column(String(50), nullable=True)  # contact, company, project, etc.
    entity_id = Column(Integer, nullable=True)
    embedding_id = Column(String(255), nullable=True)
    extracted_text = Column(Text, nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', filename='{self.filename}')>"
