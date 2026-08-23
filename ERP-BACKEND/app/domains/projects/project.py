"""Project and Task models."""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default="planning")
    priority = Column(String(50), nullable=False, server_default="medium")
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    budget = Column(Numeric(15, 2), nullable=True)
    actual_cost = Column(Numeric(15, 2), nullable=True)
    progress = Column(Integer, nullable=False, server_default="0")
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    client_id = Column(Integer, ForeignKey("contacts.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    manager = relationship("User", back_populates="projects_managed", foreign_keys=[manager_id])
    client = relationship("Contact", foreign_keys=[client_id])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default="todo")
    priority = Column(String(50), nullable=False, server_default="medium")
    assigned_to = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    due_date = Column(Date, nullable=True)
    estimated_hours = Column(Numeric(8, 2), nullable=True)
    actual_hours = Column(Numeric(8, 2), nullable=True)
    parent_task_id = Column(Integer, ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    project = relationship("Project", back_populates="tasks")
    assigned_user = relationship("User", back_populates="tasks", foreign_keys=[assigned_to])
    subtasks = relationship("Task", backref="parent", remote_side=[id])
