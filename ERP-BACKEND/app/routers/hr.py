from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from decimal import Decimal

from app.database import get_db
from app.models import Employee, Department
from app.auth import get_current_user, require_admin
from app.services.activity_log import log_activity

router = APIRouter()

class DepartmentCreate(BaseModel):
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    budget: Optional[float] = None

class EmployeeCreate(BaseModel):
    employee_code: str
    job_title: str
    department_id: Optional[int] = None
    salary: Optional[float] = None
    hire_date: date
    status: str = "active"
    employment_type: str = "full_time"
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None

@router.post("/departments")
def create_department(data: DepartmentCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    dept = Department(**data.dict())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_activity(db, user_id=current_user.id, action="department_created", entity_type="department", entity_id=dept.id)
    return dept

@router.get("/departments")
def list_departments(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    return db.query(Department).all()

@router.post("/employees")
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    existing = db.query(Employee).filter(Employee.employee_code == data.employee_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee code already exists")

    emp = Employee(**data.dict())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    log_activity(db, user_id=current_user.id, action="employee_created", entity_type="employee", entity_id=emp.id)
    return emp

@router.get("/employees")
def list_employees(
    status: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    query = db.query(Employee)
    if status:
        query = query.filter(Employee.status == status)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    return query.all()

@router.get("/employees/{employee_id}")
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.put("/employees/{employee_id}")
def update_employee(employee_id: int, data: EmployeeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in data.dict().items():
        setattr(emp, key, value)
    emp.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(emp)
    return emp

@router.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db), current_user = Depends(require_admin)):
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    db.delete(emp)
    db.commit()
    return {"message": "Employee deleted"}

@router.get("/dashboard")
def hr_dashboard(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    from sqlalchemy import func
    total_employees = db.query(Employee).count()
    active_employees = db.query(Employee).filter(Employee.status == "active").count()
    total_departments = db.query(Department).count()
    total_payroll = db.query(func.sum(Employee.salary)).filter(Employee.status == "active").scalar() or 0

    return {
        "total_employees": total_employees,
        "active_employees": active_employees,
        "total_departments": total_departments,
        "monthly_payroll": float(total_payroll),
        "avg_salary": float(total_payroll / active_employees) if active_employees > 0 else 0
    }

