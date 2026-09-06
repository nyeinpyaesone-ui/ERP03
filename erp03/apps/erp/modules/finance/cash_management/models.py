"""
Cash Management Domain Models
Handles Bank Accounts, Cash Transactions, Reconciliation, and Liquidity
"""
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, Enum as SQLEnum, Text, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

from ...core.database.session import Base

class AccountType(str, enum.Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    PETTY_CASH = "petty_cash"
    MONEY_MARKET = "money_market"

class ReconciliationStatus(str, enum.Enum):
    PENDING = "pending"
    RECONCILED = "reconciled"
    DISPUTED = "disputed"

class BankAccount(Base):
    __tablename__ = "bank_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_name = Column(String(100), nullable=False)
    account_number = Column(String(50), unique=True, nullable=False)
    bank_name = Column(String(100), nullable=False)
    routing_number = Column(String(20))
    currency = Column(String(3), default="USD")
    account_type = Column(SQLEnum(AccountType), default=AccountType.CHECKING)
    
    # Financial State
    current_balance = Column(Float, default=0.0)
    available_balance = Column(Float, default=0.0)  # Less holds/unsettled
    last_reconciled_date = Column(DateTime)
    last_reconciled_balance = Column(Float)
    
    # Metadata
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    transactions = relationship("CashTransaction", back_populates="account", cascade="all, delete-orphan")
    statements = relationship("BankStatement", back_populates="account", cascade="all, delete-orphan")

class CashTransaction(Base):
    __tablename__ = "cash_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False)
    transaction_date = Column(DateTime, nullable=False)
    description = Column(Text)
    reference_number = Column(String(50))  # Check number, Wire ID, etc.
    
    # Amounts
    debit_amount = Column(Float, default=0.0)
    credit_amount = Column(Float, default=0.0)
    balance_after = Column(Float)  # Running balance
    
    # Categorization
    category = Column(String(50))  # Deposit, Withdrawal, Transfer, Fee
    counterparty_name = Column(String(100))
    counterparty_account = Column(String(50))
    
    # Reconciliation
    is_reconciled = Column(Boolean, default=False)
    reconciled_statement_id = Column(Integer, ForeignKey("bank_statements.id"))
    reconciliation_status = Column(SQLEnum(ReconciliationStatus), default=ReconciliationStatus.PENDING)
    discrepancy_notes = Column(Text)
    
    # Links to other modules
    linked_journal_entry_id = Column(Integer)  # Link to General Ledger
    linked_invoice_id = Column(Integer)        # Link to AR/AP
    linked_payment_id = Column(Integer)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    account = relationship("BankAccount", back_populates="transactions")

class BankStatement(Base):
    __tablename__ = "bank_statements"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=False)
    statement_date = Column(DateTime, nullable=False)
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    opening_balance = Column(Float, nullable=False)
    closing_balance = Column(Float, nullable=False)
    total_debits = Column(Float, default=0.0)
    total_credits = Column(Float, default=0.0)
    
    # Import metadata
    import_source = Column(String(50))  # CSV, OFX, API
    import_file_name = Column(String(200))
    imported_at = Column(DateTime(timezone=True))
    
    account = relationship("BankAccount", back_populates="statements")
    transactions = relationship("CashTransaction", back_populates="reconciled_statement")

class CashFlowForecast(Base):
    __tablename__ = "cash_flow_forecasts"
    
    id = Column(Integer, primary_key=True, index=True)
    forecast_date = Column(DateTime, nullable=False, index=True)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)  # Null for consolidated
    
    # Projected Flows
    projected_inflow = Column(Float, default=0.0)
    projected_outflow = Column(Float, default=0.0)
    net_flow = Column(Float, default=0.0)
    projected_balance = Column(Float, default=0.0)
    
    # Confidence & Sources
    confidence_level = Column(Float)  # 0.0 to 1.0
    source_breakdown = Column(JSON)   # JSON dict of sources (AR, Loans, etc.)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LiquidityRule(Base):
    __tablename__ = "liquidity_rules"
    
    id = Column(Integer, primary_key=True, index=True)
    rule_name = Column(String(100), nullable=False)
    account_id = Column(Integer, ForeignKey("bank_accounts.id"), nullable=True)  # Null for global
    
    # Thresholds
    minimum_balance = Column(Float, nullable=False)
    target_balance = Column(Float)
    alert_threshold_percent = Column(Float, default=10.0)  # Alert when below X% of target
    
    # Actions
    action_type = Column(String(50))  # email, webhook, auto_transfer
    action_config = Column(JSON)      # Recipient emails, webhook URLs, transfer accounts
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
