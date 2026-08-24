from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from apps.erp.core.database_session import Base

class ChartOfAccount(Base):
    __tablename__ = 'chart_of_accounts'
    id = Column(Integer, primary_key=True)
    account_code = Column(String(20), unique=True, nullable=False)
    account_name = Column(String(100), nullable=False)
    account_type = Column(String(50), nullable=False)  # Asset, Liability, Equity, Revenue, Expense
    parent_id = Column(Integer, ForeignKey('chart_of_accounts.id'))
    currency = Column(String(3), default='USD')
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class JournalEntry(Base):
    __tablename__ = 'journal_entries'
    id = Column(Integer, primary_key=True)
    entry_date = Column(DateTime, nullable=False)
    description = Column(Text)
    reference = Column(String(50))
    is_posted = Column(Boolean, default=False)
    created_by = Column(Integer, ForeignKey('users.id'))
    posted_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    
class JournalLine(Base):
    __tablename__ = 'journal_lines'
    id = Column(Integer, primary_key=True)
    journal_entry_id = Column(Integer, ForeignKey('journal_entries.id'), nullable=False)
    account_id = Column(Integer, ForeignKey('chart_of_accounts.id'), nullable=False)
    debit = Column(Numeric(15, 2), default=0)
    credit = Column(Numeric(15, 2), default=0)
    description = Column(Text)
    
    journal_entry = relationship('JournalEntry', backref='lines')
    account = relationship('ChartOfAccount')
