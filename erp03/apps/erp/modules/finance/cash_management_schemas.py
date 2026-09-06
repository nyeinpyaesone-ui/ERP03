from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from enum import Enum

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRANSFER = "transfer"
    PAYMENT = "payment"
    RECEIPT = "receipt"

class BankAccountCreate(BaseModel):
    account_name: str = Field(..., min_length=1, max_length=100)
    account_number: str = Field(..., min_length=1, max_length=50)
    bank_name: str = Field(..., min_length=1, max_length=100)
    routing_number: Optional[str] = None
    currency: str = 'USD'

class CashTransactionCreate(BaseModel):
    account_id: int
    transaction_type: TransactionType
    amount: Decimal = Field(..., gt=0)
    description: Optional[str] = None
    reference: Optional[str] = None
    transaction_date: Optional[datetime] = None

class BankStatementCreate(BaseModel):
    account_id: int
    statement_date: datetime
    opening_balance: Decimal
    closing_balance: Decimal

class CashFlowForecastCreate(BaseModel):
    account_id: Optional[int] = None
    forecast_date: datetime
    projected_inflow: Decimal = 0
    projected_outflow: Decimal = 0

class LiquidityRuleCreate(BaseModel):
    rule_name: str = Field(..., min_length=1, max_length=100)
    min_balance: Decimal = Field(..., gt=0)
    target_balance: Optional[Decimal] = None
    alert_email: Optional[str] = None
