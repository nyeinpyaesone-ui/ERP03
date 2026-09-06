from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.database import get_db
from app.models import Workflow, WorkflowStep, WorkflowExecution
from app.auth import get_current_user, require_admin
from app.services.activity_log import log_activity

router = APIRouter()

class StepConfig(BaseModel):
    step_type: str
    approvers: Optional[List[int]] = None
    condition: Optional[str] = None
    action: Optional[str] = None
    notification_template: Optional[str] = None
    delay_minutes: Optional[int] = None

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    entity_type: str
    trigger_type: str
    trigger_condition: Optional[Dict[str, Any]] = None
    steps: List[StepConfig]

@router.post("/workflows")
def create_workflow(data: WorkflowCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    workflow = Workflow(
        name=data.name,
        description=data.description,
        entity_type=data.entity_type,
        trigger_type=data.trigger_type,
        trigger_condition=data.trigger_condition,
        created_by=current_user.id
    )
    db.add(workflow)
    db.flush()

    for idx, step_data in enumerate(data.steps):
        step = WorkflowStep(
            workflow_id=workflow.id,
            name=f"Step {idx + 1}",
            step_type=step_data.step_type,
            step_order=idx,
            config=step_data.dict()
        )
        db.add(step)

    db.commit()
    db.refresh(workflow)
    log_activity(db, user_id=current_user.id, action="workflow_created", entity_type="workflow", entity_id=workflow.id)
    return workflow

@router.get("/workflows")
def list_workflows(
    entity_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Workflow)
    if entity_type:
        query = query.filter(Workflow.entity_type == entity_type)
    return query.all()

@router.get("/workflows/{workflow_id}")
def get_workflow(workflow_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow

@router.put("/workflows/{workflow_id}/toggle")
def toggle_workflow(workflow_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    workflow.is_active = not workflow.is_active
    db.commit()
    return workflow

@router.delete("/workflows/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    db.delete(workflow)
    db.commit()
    return {"message": "Workflow deleted"}

@router.get("/executions")
def list_executions(
    workflow_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(WorkflowExecution)
    if workflow_id:
        query = query.filter(WorkflowExecution.workflow_id == workflow_id)
    return query.order_by(WorkflowExecution.started_at.desc()).all()

@router.post("/workflows/{workflow_id}/execute")
def execute_workflow(
    workflow_id: int,
    entity_type: str,
    entity_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
    if not workflow or not workflow.is_active:
        raise HTTPException(status_code=404, detail="Workflow not found or inactive")

    execution = WorkflowExecution(
        workflow_id=workflow_id,
        entity_type=entity_type,
        entity_id=entity_id,
        status="running",
        current_step=0,
        context={"triggered_by": current_user.id}
    )
    db.add(execution)
    db.commit()
    db.refresh(execution)

    log_activity(db, user_id=current_user.id, action="workflow_executed", entity_type="workflow_execution", entity_id=execution.id)
    return execution

