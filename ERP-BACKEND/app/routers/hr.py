from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date, datetime, timezone
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

class DepartmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    description: Optional[str] = None
    manager_id: Optional[int] = None
    budget: Optional[float] = None
    created_at: datetime

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

class EmployeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: Optional[int] = None
    employee_code: str
    department_id: Optional[int] = None
    job_title: str
    salary: Optional[float] = None
    hire_date: date
    status: str
    employment_type: str
    address: Optional[str] = None
    emergency_contact: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    created_at: datetime
    updated_at: datetime

@router.post("/departments", response_model=DepartmentResponse)
def create_department(data: DepartmentCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create a department from the supplied data.
    
    Parameters:
    	data (DepartmentCreate): Department details used to create the record.
    
    Returns:
    	Department: The newly created department.
    """
    dept = Department(**data.model_dump())
    db.add(dept)
    db.commit()
    db.refresh(dept)
    log_activity(db, user_id=current_user.id, action="department_created", entity_type="department", entity_id=dept.id)
    return dept

@router.get("/departments", response_model=List[DepartmentResponse])
def list_departments(db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Return all departments accessible to the authenticated user."""
    return db.query(Department).all()

@router.post("/employees", response_model=EmployeeResponse)
def create_employee(data: EmployeeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Create an employee record after confirming that its employee code is unique.
    
    Parameters:
    	data (EmployeeCreate): Employee details used to create the record.
    
    Returns:
    	Employee: The persisted employee record.
    """
    existing = db.query(Employee).filter(Employee.employee_code == data.employee_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Employee code already exists")

    emp = Employee(**data.model_dump())
    db.add(emp)
    db.commit()
    db.refresh(emp)
    log_activity(db, user_id=current_user.id, action="employee_created", entity_type="employee", entity_id=emp.id)
    return emp

@router.get("/employees", response_model=List[EmployeeResponse])
def list_employees(
    status: Optional[str] = None,
    department_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """
    List employees with optional status and department filters.
    
    Parameters:
    	status (str, optional): Employee status used to filter the results.
    	department_id (int, optional): Department ID used to filter the results.
    
    Returns:
    	list[Employee]: Employees matching the supplied filters.
    """
    query = db.query(Employee)
    if status:
        query = query.filter(Employee.status == status)
    if department_id:
        query = query.filter(Employee.department_id == department_id)
    return query.all()

@router.get("/employees/{employee_id}", response_model=EmployeeResponse)
def get_employee(employee_id: int, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Retrieve an employee by ID.
    
    Parameters:
        employee_id (int): The ID of the employee to retrieve.
    
    Returns:
        Employee: The matching employee record.
    
    Raises:
        HTTPException: If no employee exists with the specified ID.
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    return emp

@router.put("/employees/{employee_id}", response_model=EmployeeResponse)
def update_employee(employee_id: int, data: EmployeeCreate, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """
    Update an employee's information and record the modification time.
    
    Parameters:
        employee_id (int): The identifier of the employee to update.
        data (EmployeeCreate): The employee fields to apply.
    
    Returns:
        Employee: The updated employee record.
    """
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    if not emp:
        raise HTTPException(status_code=404, detail="Employee not found")
    for key, value in data.model_dump().items():
        setattr(emp, key, value)
    emp.updated_at = datetime.now(timezone.utc)
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

