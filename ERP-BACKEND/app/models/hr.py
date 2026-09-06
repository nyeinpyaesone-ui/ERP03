"""Human Resources Models"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, Date, Numeric, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.base import TimestampMixin


class Department(Base, TimestampMixin):
    """Organizational departments"""
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    manager_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    budget = Column(Numeric(15, 2), nullable=True)

    manager = relationship("User", foreign_keys=[manager_id])
    employees = relationship("Employee", back_populates="department")

    def __repr__(self):
        return f"<Department(id={self.id}, name='{self.name}')>"


class Employee(Base, TimestampMixin):
    """Employee records"""
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

    department = relationship("Department", back_populates="employees")
    user = relationship("User", foreign_keys=[user_id])

    def __repr__(self):
        return f"<Employee(id={self.id}, code='{self.employee_code}', name='{self.user.full_name if self.user else 'N/A'}')>"


class LeaveRequest(Base, TimestampMixin):
    """Employee leave/time-off requests"""
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    leave_type = Column(String(50), nullable=False)  # vacation, sick, personal, maternity, paternity
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Numeric(5, 1), nullable=False)
    reason = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default="pending")  # pending, approved, rejected, cancelled
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)

    employee = relationship("Employee")
    approver = relationship("User", foreign_keys=[approved_by])

    def __repr__(self):
        return f"<LeaveRequest(id={self.id}, employee_id={self.employee_id}, status='{self.status}')>"


class LeaveBalance(Base, TimestampMixin):
    """Annual leave balances per employee"""
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    year = Column(Integer, nullable=False)
    leave_type = Column(String(50), nullable=False)
    opening_balance = Column(Numeric(5, 1), nullable=False, server_default="0")
    accrued = Column(Numeric(5, 1), nullable=False, server_default="0")
    taken = Column(Numeric(5, 1), nullable=False, server_default="0")
    adjusted = Column(Numeric(5, 1), nullable=False, server_default="0")

    employee = relationship("Employee")

    def __repr__(self):
        return f"<LeaveBalance(employee_id={self.employee_id}, year={self.year}, type='{self.leave_type}')>"


class Attendance(Base, TimestampMixin):
    """Daily attendance records"""
    __tablename__ = "attendance"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(DateTime(timezone=True), nullable=True)
    check_out = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, server_default="present")  # present, absent, late, half_day
    notes = Column(Text, nullable=True)

    employee = relationship("Employee")

    def __repr__(self):
        return f"<Attendance(id={self.id}, employee_id={self.employee_id}, date={self.date})>"


class PerformanceReview(Base, TimestampMixin):
    """Employee performance reviews"""
    __tablename__ = "performance_reviews"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    review_period_start = Column(Date, nullable=False)
    review_period_end = Column(Date, nullable=False)
    rating = Column(Numeric(3, 2), nullable=True)  # 1.00 to 5.00
    comments = Column(Text, nullable=True)
    goals = Column(Text, nullable=True)
    status = Column(String(50), nullable=False, server_default="draft")  # draft, in_progress, completed

    employee = relationship("Employee")
    reviewer = relationship("User", foreign_keys=[reviewer_id])

    def __repr__(self):
        return f"<PerformanceReview(id={self.id}, employee_id={self.employee_id}, rating={self.rating})>"


class Payroll(Base, TimestampMixin):
    """Payroll records"""
    __tablename__ = "payroll"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False)
    pay_period_start = Column(Date, nullable=False)
    pay_period_end = Column(Date, nullable=False)
    pay_date = Column(Date, nullable=False)
    gross_salary = Column(Numeric(15, 2), nullable=False)
    deductions = Column(Numeric(15, 2), nullable=False, server_default="0")
    bonuses = Column(Numeric(15, 2), nullable=False, server_default="0")
    net_salary = Column(Numeric(15, 2), nullable=False)
    status = Column(String(50), nullable=False, server_default="pending")  # pending, processed, paid
    notes = Column(Text, nullable=True)

    employee = relationship("Employee")

    def __repr__(self):
        return f"<Payroll(id={self.id}, employee_id={self.employee_id}, net={self.net_salary})>"
