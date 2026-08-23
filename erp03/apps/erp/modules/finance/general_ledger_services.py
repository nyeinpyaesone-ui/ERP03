from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from apps.erp.modules.finance.general_ledger_models import ChartOfAccount, JournalEntry, JournalLine
from apps.erp.modules.finance.general_ledger_schemas import JournalEntryCreate, ChartOfAccountCreate

class GeneralLedgerService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_account(self, data: ChartOfAccountCreate) -> ChartOfAccount:
        account = ChartOfAccount(**data.dict())
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account
    
    async def get_account_balance(self, account_id: int) -> Decimal:
        result = await self.db.execute(
            select(func.sum(JournalLine.debit - JournalLine.credit))
            .join(JournalEntry)
            .where(JournalLine.account_id == account_id)
            .where(JournalEntry.is_posted == True)
        )
        balance = result.scalar() or Decimal(0)
        return balance
    
    async def create_journal_entry(self, data: JournalEntryCreate) -> JournalEntry:
        entry = JournalEntry(
            entry_date=data.entry_date,
            description=data.description,
            reference=data.reference,
            is_posted=False
        )
        self.db.add(entry)
        await self.db.flush()
        
        for line_data in data.lines:
            line = JournalLine(
                journal_entry_id=entry.id,
                account_id=line_data.account_id,
                debit=line_data.debit,
                credit=line_data.credit,
                description=line_data.description
            )
            self.db.add(line)
        
        await self.db.commit()
        await self.db.refresh(entry)
        return entry
    
    async def post_journal_entry(self, entry_id: int) -> JournalEntry:
        entry = await self.db.get(JournalEntry, entry_id)
        if not entry:
            raise ValueError('Journal entry not found')
        
        # Verify balance before posting
        result = await self.db.execute(
            select(func.sum(JournalLine.debit), func.sum(JournalLine.credit))
            .where(JournalLine.journal_entry_id == entry_id)
        )
        total_debit, total_credit = result.one()
        
        if total_debit != total_credit:
            raise ValueError('Cannot post unbalanced journal entry')
        
        entry.is_posted = True
        entry.posted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(entry)
        return entry
    
    async def get_trial_balance(self, date_from: datetime, date_to: datetime) -> List[dict]:
        result = await self.db.execute(
            select(
                ChartOfAccount.account_code,
                ChartOfAccount.account_name,
                func.sum(JournalLine.debit).label('total_debit'),
                func.sum(JournalLine.credit).label('total_credit')
            )
            .join(JournalLine, ChartOfAccount.id == JournalLine.account_id)
            .join(JournalEntry, JournalLine.journal_entry_id == JournalEntry.id)
            .where(JournalEntry.is_posted == True)
            .where(JournalEntry.entry_date >= date_from)
            .where(JournalEntry.entry_date <= date_to)
            .group_by(ChartOfAccount.id)
        )
        return [
            {
                'account_code': row.account_code,
                'account_name': row.account_name,
                'debit': row.total_debit or Decimal(0),
                'credit': row.total_credit or Decimal(0),
                'balance': (row.total_debit or 0) - (row.total_credit or 0)
            }
            for row in result.all()
        ]
