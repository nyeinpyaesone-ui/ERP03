from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from apps.erp.core.database_session import get_db
from apps.erp.modules.finance.general_ledger_models import ChartOfAccount, JournalEntry
from apps.erp.modules.finance.general_ledger_schemas import ChartOfAccountCreate, JournalEntryCreate
from apps.erp.modules.finance.general_ledger_services import GeneralLedgerService

router = APIRouter(prefix='/general-ledger', tags=['Finance - General Ledger'])

@router.post('/accounts', response_model=ChartOfAccount)
async def create_account(data: ChartOfAccountCreate, db: AsyncSession = Depends(get_db)):
    service = GeneralLedgerService(db)
    return await service.create_account(data)

@router.get('/accounts/{account_id}/balance')
async def get_account_balance(account_id: int, db: AsyncSession = Depends(get_db)):
    service = GeneralLedgerService(db)
    balance = await service.get_account_balance(account_id)
    return {'account_id': account_id, 'balance': balance}

@router.post('/journal-entries', response_model=JournalEntry)
async def create_journal_entry(data: JournalEntryCreate, db: AsyncSession = Depends(get_db)):
    service = GeneralLedgerService(db)
    return await service.create_journal_entry(data)

@router.post('/journal-entries/{entry_id}/post')
async def post_journal_entry(entry_id: int, db: AsyncSession = Depends(get_db)):
    service = GeneralLedgerService(db)
    try:
        return await service.post_journal_entry(entry_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get('/trial-balance')
async def get_trial_balance(date_from: str, date_to: str, db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    service = GeneralLedgerService(db)
    return await service.get_trial_balance(
        datetime.fromisoformat(date_from),
        datetime.fromisoformat(date_to)
    )
