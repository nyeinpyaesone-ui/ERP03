from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Text, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from decimal import Decimal
import enum
from apps.erp.core.database_session import Base

class TransactionType(enum.Enum):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'
    TRANSFER = 'transfer'
    PAYMENT = 'payment'
    RECEIPT = 'receipt'

class BankAccount(Base):
    __tablename__ = 'bank_accounts'
    id = Column(Integer, primary_key=True)
    account_name = Column(String(100), nullable=False)
    account_number = Column(String(50), unique=True, nullable=False)
    bank_name = Column(String(100), nullable=False)
    routing_number = Column(String(20))
    currency = Column(String(3), default='USD')
    current_balance = Column(Numeric(15, 2), default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class CashTransaction(Base):
    __tablename__ = 'cash_transactions'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('bank_accounts.id'), nullable=False)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    description = Column(Text)
    reference = Column(String(50))
    transaction_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_reconciled = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship('BankAccount', backref='transactions')

class BankStatement(Base):
    __tablename__ = 'bank_statements'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('bank_accounts.id'), nullable=False)
    statement_date = Column(DateTime, nullable=False)
    opening_balance = Column(Numeric(15, 2), nullable=False)
    closing_balance = Column(Numeric(15, 2), nullable=False)
    is_reconciled = Column(Boolean, default=False)
    reconciled_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship('BankAccount')

class CashFlowForecast(Base):
    __tablename__ = 'cash_flow_forecasts'
    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('bank_accounts.id'))
    forecast_date = Column(DateTime, nullable=False)
    projected_inflow = Column(Numeric(15, 2), default=0)
    projected_outflow = Column(Numeric(15, 2), default=0)
    net_cash_flow = Column(Numeric(15, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    account = relationship('BankAccount')

class LiquidityRule(Base):
    __tablename__ = 'liquidity_rules'
    id = Column(Integer, primary_key=True)
    rule_name = Column(String(100), nullable=False)
    min_balance = Column(Numeric(15, 2), nullable=False)
    target_balance = Column(Numeric(15, 2))
    alert_email = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
