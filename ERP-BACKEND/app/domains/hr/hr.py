"""HR models: Department, Employee."""
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    budget = Column(Numeric(15, 2), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    manager = relationship("User", foreign_keys=[manager_id])
    employees = relationship("Employee", back_populates="department")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    employee_code = Column(String(50), unique=True, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True)
    job_title = Column(String(100), nullable=False)
    salary = Column(Numeric(15, 2), nullable=True)
    hire_date = Column(Date, nullable=False)
    status = Column(String(50), nullable=False, server_default="active")
    employment_type = Column(String(50), nullable=False, server_default="full_time")
    address = Column(Text, nullable=True)
    emergency_contact = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationships
    department = relationship("Department", back_populates="employees")
    user = relationship("User", foreign_keys=[user_id])
