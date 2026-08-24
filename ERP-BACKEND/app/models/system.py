"""System models: ActivityLog, Notification, Report, Forecast, Setting."""
from sqlalchemy import Column, Integer, String, Text, Boolean, Numeric, Float, ForeignKey, DateTime, Date, Index, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# Use JSON universally for compatibility across SQLite (tests) and PostgreSQL (production)
# SQLAlchemy handles JSON type appropriately for each database dialect
JSONB = JSON


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=True)
    entity_id = Column(Integer, nullable=True)
    details = Column(JSONB, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    correlation_id = Column(String(100), nullable=True, index=True)
    request_id = Column(String(100), nullable=True)
    status = Column(String(50), nullable=False, server_default="SUCCESS")  # SUCCESS, FAILURE, ROLLBACK
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="activity_logs")
    
    __table_args__ = (
        Index('idx_activity_entity', 'entity_type', 'entity_id'),
        Index('idx_activity_user', 'user_id', 'created_at'),
        Index('idx_activity_action', 'action'),
    )


class Notification(Base):
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

    # Relationships
    user = relationship("User", back_populates="notifications")


class Report(Base):
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

    # Relationships
    creator = relationship("User", foreign_keys=[created_by])


class Forecast(Base):
    __tablename__ = "forecasts"

    id = Column(Integer, primary_key=True, index=True)
    forecast_type = Column(String(100), nullable=False)  # revenue, inventory, churn
    entity_id = Column(Integer, nullable=True)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    predicted_value = Column(Numeric(15, 2), nullable=False)
    confidence_low = Column(Numeric(15, 2), nullable=True)
    confidence_high = Column(Numeric(15, 2), nullable=True)
    confidence_score = Column(Float, nullable=True)
    trend = Column(String(50), nullable=True)  # increasing, decreasing, stable
    growth_rate = Column(Float, nullable=True)
    model_used = Column(String(100), nullable=True)
    insights = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Setting(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, nullable=False)
    value = Column(Text, nullable=True)
    category = Column(String(100), nullable=False, server_default="general")
    is_encrypted = Column(Boolean, nullable=False, server_default="false")
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
