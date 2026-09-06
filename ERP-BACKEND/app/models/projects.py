"""Project Management Models"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.base import TimestampMixin


class Project(Base, TimestampMixin):
    """Project management model"""
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

    manager = relationship("User", back_populates="projects_managed", foreign_keys=[manager_id])
    client = relationship("Contact", foreign_keys=[client_id])
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}', status='{self.status}')>"


class Task(Base, TimestampMixin):
    """Task management with subtasks support"""
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

    project = relationship("Project", back_populates="tasks")
    assigned_user = relationship("User", back_populates="tasks", foreign_keys=[assigned_to])
    subtasks = relationship("Task", backref="parent", remote_side=[id])

    def __repr__(self):
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status}')>"


class TimeEntry(Base, TimestampMixin):
    """Time tracking for tasks"""
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_hours = Column(Numeric(8, 2), nullable=True)
    description = Column(Text, nullable=True)
    billable = Column(Boolean, nullable=False, server_default="true")

    task = relationship("Task")
    user = relationship("User")

    def __repr__(self):
        return f"<TimeEntry(id={self.id}, task_id={self.task_id}, duration={self.duration_hours}h)>"


class ProjectMilestone(Base, TimestampMixin):
    """Project milestones for tracking major deliverables"""
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(Date, nullable=False)
    completed_date = Column(Date, nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")  # pending, completed, overdue

    project = relationship("Project", backref="milestones")

    def __repr__(self):
        return f"<ProjectMilestone(id={self.id}, title='{self.title}', status='{self.status}')>"


class ProjectDocument(Base, TimestampMixin):
    """Documents attached to projects"""
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)
    mime_type = Column(String(100), nullable=True)
    uploaded_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    project = relationship("Project", backref="documents")
    uploader = relationship("User", foreign_keys=[uploaded_by])

    def __repr__(self):
        return f"<ProjectDocument(id={self.id}, project_id={self.project_id}, filename='{self.filename}')>"
