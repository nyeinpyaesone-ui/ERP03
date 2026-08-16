from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime

from app.database import get_db
from app.models import Project, Task
from app.auth import get_current_user
from app.services.activity_log import log_activity

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None
    status: str = "planning"
    priority: str = "medium"
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    client_id: Optional[int] = None

class TaskCreate(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = None
    status: str = "todo"
    priority: str = "medium"
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    parent_task_id: Optional[int] = None

@router.post("/projects")
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    project = Project(**data.dict(), manager_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    log_activity(db, user_id=current_user.id, action="project_created", entity_type="project", entity_id=project.id)
    return project

@router.get("/projects")
def list_projects(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    return query.all()

@router.get("/projects/{project_id}")
def get_project(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/projects/{project_id}")
def update_project(project_id: int, data: ProjectCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in data.dict().items():
        setattr(project, key, value)
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    return project

@router.post("/tasks")
def create_task(data: TaskCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(**data.dict())
    db.add(task)
    db.commit()
    db.refresh(task)
    log_activity(db, user_id=current_user.id, action="task_created", entity_type="task", entity_id=task.id)
    return task

@router.get("/projects/{project_id}/tasks")
def list_project_tasks(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Task).filter(Task.project_id == project_id).all()

@router.put("/tasks/{task_id}")
def update_task(task_id: int, data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in data.items():
        if hasattr(task, key):
            setattr(task, key, value)
    task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(task)
    return task

@router.get("/dashboard")
def projects_dashboard(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from sqlalchemy import func
    total_projects = db.query(Project).count()
    active_projects = db.query(Project).filter(Project.status == "active").count()
    total_tasks = db.query(Task).count()
    completed_tasks = db.query(Task).filter(Task.status == "done").count()

    return {
        "total_projects": total_projects,
        "active_projects": active_projects,
        "total_tasks": total_tasks,
        "completed_tasks": completed_tasks,
        "completion_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    }

