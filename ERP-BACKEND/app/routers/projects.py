from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime, timezone

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

class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    status: str
    priority: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget: Optional[float] = None
    manager_id: Optional[int] = None
    client_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

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

class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    assigned_to: Optional[int] = None
    due_date: Optional[date] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    parent_task_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

@router.post("/projects", response_model=ProjectResponse)
def create_project(data: ProjectCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a project managed by the authenticated user.
    
    Parameters:
    	data (ProjectCreate): Project details used to create the project.
    	current_user: Authenticated user assigned as the project's manager.
    
    Returns:
    	Project: The newly created project.
    """
    project = Project(**data.model_dump(), manager_id=current_user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    log_activity(db, user_id=current_user.id, action="project_created", entity_type="project", entity_id=project.id)
    return project

@router.get("/projects", response_model=List[ProjectResponse])
def list_projects(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List projects, optionally filtered by status.
    
    Parameters:
    	status (Optional[str]): Project status used to filter the results.
    
    Returns:
    	List[Project]: Projects matching the requested status.
    """
    query = db.query(Project)
    if status:
        query = query.filter(Project.status == status)
    return query.all()

@router.get("/projects/{project_id}", response_model=ProjectResponse)
def get_project(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve a project by its identifier.
    
    Parameters:
        project_id (int): The identifier of the project to retrieve.
    
    Returns:
        Project: The matching project.
    
    Raises:
        HTTPException: If the project does not exist.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.put("/projects/{project_id}", response_model=ProjectResponse)
def update_project(project_id: int, data: ProjectCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update a project's supplied fields and refresh its modification timestamp.
    
    Parameters:
    	project_id (int): Identifier of the project to update.
    	data (ProjectCreate): Fields and values to apply to the project.
    
    Raises:
    	HTTPException: If the project does not exist.
    
    Returns:
    	Project: The updated project.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for key, value in data.model_dump().items():
        setattr(project, key, value)
    project.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(project)
    return project

@router.post("/tasks", response_model=TaskResponse)
def create_task(data: TaskCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a task for an existing project.
    
    Parameters:
    	data (TaskCreate): Task details, including the associated project identifier.
    
    Returns:
    	Task: The persisted task.
    """
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    task = Task(**data.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    log_activity(db, user_id=current_user.id, action="task_created", entity_type="task", entity_id=task.id)
    return task

@router.get("/projects/{project_id}/tasks", response_model=List[TaskResponse])
def list_project_tasks(project_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """List all tasks associated with a project.
    
    Parameters:
    	project_id (int): The ID of the project whose tasks are requested.
    
    Returns:
    	list[Task]: The project's tasks.
    """
    return db.query(Task).filter(Task.project_id == project_id).all()

@router.put("/tasks/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, data: dict, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update an existing task with the supplied fields.
    
    Parameters:
    	task_id (int): Identifier of the task to update.
    	data (dict): Field values to apply to the task.
    
    Returns:
    	Task: The updated task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    for key, value in data.items():
        if hasattr(task, key):
            setattr(task, key, value)
    task.updated_at = datetime.now(timezone.utc)
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

