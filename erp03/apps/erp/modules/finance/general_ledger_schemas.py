from pydantic import BaseModel, Field, validator
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

class ChartOfAccountCreate(BaseModel):
    account_code: str = Field(..., min_length=1, max_length=20)
    account_name: str = Field(..., min_length=1, max_length=100)
    account_type: str
    parent_id: Optional[int] = None
    currency: str = 'USD'

class JournalLineCreate(BaseModel):
    account_id: int
    debit: Decimal = 0
    credit: Decimal = 0
    description: Optional[str] = None
    
    @validator('debit', 'credit')
    def non_negative(cls, v):
        if v < 0:
            raise ValueError('Amount must be non-negative')
        return v

class JournalEntryCreate(BaseModel):
    entry_date: datetime
    description: str
    reference: Optional[str] = None
    lines: List[JournalLineCreate]
    
    @validator('lines')
    def validate_balanced(cls, lines):
        total_debit = sum(line.debit for line in lines)
        total_credit = sum(line.credit for line in lines)
        if total_debit != total_credit:
            raise ValueError(f'Journal entry must balance. Debit: {total_debit}, Credit: {total_credit}')
        if len(lines) < 2:
            raise ValueError('Journal entry must have at least 2 lines')
        return lines
