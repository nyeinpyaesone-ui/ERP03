"""
Cash Management Pydantic Schemas
Validation models for API requests and responses
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AccountType(str, Enum):
    CHECKING = "checking"
    SAVINGS = "savings"
    PETTY_CASH = "petty_cash"
    MONEY_MARKET = "money_market"

class ReconciliationStatus(str, Enum):
    PENDING = "pending"
    RECONCILED = "reconciled"
    DISPUTED = "disputed"

# === Bank Account Schemas ===
class BankAccountBase(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=50)
    bank_name: str = Field(..., min_length=1, max_length=100)
    routing_number: Optional[str] = Field(None, max_length=20)
    currency: str = Field("USD", min_length=3, max_length=3)
    account_type: AccountType = AccountType.CHECKING

class BankAccountCreate(BankAccountBase):
    pass

class BankAccountUpdate(BaseModel):
    account_name: Optional[str] = None
    bank_name: Optional[str] = None
    routing_number: Optional[str] = None
    is_active: Optional[bool] = None

class BankAccountResponse(BankAccountBase):
    id: int
    current_balance: float
    available_balance: float
    last_reconciled_date: Optional[datetime]
    last_reconciled_balance: Optional[float]
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True

# === Cash Transaction Schemas ===
class CashTransactionBase(BaseModel):
    transaction_date: datetime
    description: str
    reference_number: Optional[str] = Field(None, max_length=50)
    debit_amount: float = Field(0.0, ge=0)
    credit_amount: float = Field(0.0, ge=0)
    category: Optional[str] = Field(None, max_length=50)
    counterparty_name: Optional[str] = Field(None, max_length=100)
    counterparty_account: Optional[str] = Field(None, max_length=50)
    
    @validator('debit_amount', 'credit_amount')
    def validate_amounts(cls, v):
        if v < 0:
            raise ValueError("Amounts cannot be negative")
        return v
    
    @validator('debit_amount', 'credit_amount')
    def one_amount_required(cls, v, values):
        # At least one of debit or credit should be non-zero
        debit = values.get('debit_amount', 0)
        credit = values.get('credit_amount', 0)
        if debit == 0 and credit == 0:
            raise ValueError("Either debit_amount or credit_amount must be non-zero")
        return v

class CashTransactionCreate(CashTransactionBase):
    account_id: int

class CashTransactionUpdate(BaseModel):
    description: Optional[str] = None
    category: Optional[str] = None
    reconciliation_status: Optional[ReconciliationStatus] = None
    discrepancy_notes: Optional[str] = None
    is_reconciled: Optional[bool] = None

class CashTransactionResponse(CashTransactionBase):
    id: int
    account_id: int
    balance_after: Optional[float]
    is_reconciled: bool
    reconciliation_status: ReconciliationStatus
    linked_journal_entry_id: Optional[int]
    linked_invoice_id: Optional[int]
    linked_payment_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True

# === Bank Statement Schemas ===
class BankStatementBase(BaseModel):
    statement_date: datetime
    period_start: datetime
    period_end: datetime
    opening_balance: float
    closing_balance: float
    total_debits: float = 0.0
    total_credits: float = 0.0

class BankStatementCreate(BankStatementBase):
    account_id: int
    import_source: Optional[str] = None

class BankStatementResponse(BankStatementBase):
    id: int
    account_id: int
    import_source: Optional[str]
    import_file_name: Optional[str]
    imported_at: Optional[datetime]

    class Config:
        from_attributes = True

# === Cash Flow Forecast Schemas ===
class CashFlowForecastBase(BaseModel):
    forecast_date: datetime
    projected_inflow: float = 0.0
    projected_outflow: float = 0.0
    confidence_level: Optional[float] = Field(None, ge=0.0, le=1.0)
    source_breakdown: Optional[Dict[str, Any]] = None

class CashFlowForecastCreate(CashFlowForecastBase):
    account_id: Optional[int] = None

class CashFlowForecastResponse(CashFlowForecastBase):
    id: int
    account_id: Optional[int]
    net_flow: float
    projected_balance: float
    created_at: datetime

    class Config:
        from_attributes = True

# === Liquidity Rule Schemas ===
class LiquidityRuleBase(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    minimum_balance: float = Field(..., gt=0)
    target_balance: Optional[float] = None
    alert_threshold_percent: float = Field(10.0, ge=0, le=100)
    action_type: str  # email, webhook, auto_transfer
    action_config: Dict[str, Any]

class LiquidityRuleCreate(LiquidityRuleBase):
    account_id: Optional[int] = None

class LiquidityRuleResponse(LiquidityRuleBase):
    id: int
    account_id: Optional[int]
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# === Aggregated Response Schemas ===
class CashPositionSummary(BaseModel):
    account_id: int
    account_name: str
    current_balance: float
    available_balance: float
    pending_transactions_count: int
    last_reconciled_date: Optional[datetime]
    liquidity_status: str  # healthy, warning, critical

class ReconciliationReport(BaseModel):
    account_id: int
    statement_id: int
    statement_period_start: datetime
    statement_period_end: datetime
    statement_closing_balance: float
    system_closing_balance: float
    difference: float
    reconciled_transactions: int
    pending_transactions: int
    discrepancies: List[str]
