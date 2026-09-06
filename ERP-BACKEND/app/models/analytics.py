"""
Analytics and Reporting models
Handles reports, forecasts, and analytics data
"""
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Date, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.models.base import Base, TimestampMixin


class ActivityLog(Base):
    """User activity logging for audit trail"""
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    user = relationship("User", back_populates="activity_logs")

    def __repr__(self):
        return f"<ActivityLog(id={self.id}, user_id={self.user_id}, action='{self.action}')>"


class Notification(Base):
    """User notifications"""
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    type = Column(String(50), nullable=False, server_default="info")
    is_read = Column(Boolean, nullable=False, server_default="false")
    link = Column(String(500), nullable=True)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="notifications")

    def __repr__(self):
        return f"<Notification(id={self.id}, user_id={self.user_id}, title='{self.title}')>"


class Report(Base):
    """Generated reports"""
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    report_type = Column(String(100), nullable=False)
    filters = Column(JSONB, nullable=True)
    file_path = Column(String(500), nullable=True)
    file_format = Column(String(20), nullable=True)
    chart_data = Column(JSONB, nullable=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    creator = relationship("User", foreign_keys=[created_by])

    def __repr__(self):
        return f"<Report(id={self.id}, name='{self.name}', type='{self.report_type}')>"


class Forecast(Base):
    """Predictive forecasts for business metrics"""
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    forecast_type = Column(String(100), nullable=False)  # revenue, inventory, churn
    entity_id = Column(Integer, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    predicted_value = Column(Float, nullable=False)
    confidence_low = Column(Float, nullable=True)
    confidence_high = Column(Float, nullable=True)
    confidence_score = Column(Float, nullable=True)
    trend = Column(String(50), nullable=True)  # increasing, decreasing, stable
    growth_rate = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    insights = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Forecast(id={self.id}, type='{self.forecast_type}', period='{self.period_start} to {self.period_end}')>"
