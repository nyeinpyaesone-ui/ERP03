from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from apps.erp.core.database_session import get_db
from apps.erp.modules.finance.cash_management_models import BankAccount, CashTransaction, BankStatement, CashFlowForecast
from apps.erp.modules.finance.cash_management_schemas import BankAccountCreate, CashTransactionCreate, BankStatementCreate
from apps.erp.modules.finance.cash_management_services import CashManagementService

router = APIRouter(prefix='/cash-management', tags=['Finance - Cash Management'])

@router.post('/accounts', response_model=BankAccount)
async def create_account(data: BankAccountCreate, db: AsyncSession = Depends(get_db)):
    service = CashManagementService(db)
    return await service.create_account(data)

@router.get('/accounts/{account_id}/balance')
async def get_balance(account_id: int, db: AsyncSession = Depends(get_db)):
    service = CashManagementService(db)
    balance = await service.get_balance(account_id)
    return {'account_id': account_id, 'balance': balance}

@router.post('/transactions', response_model=CashTransaction)
async def record_transaction(data: CashTransactionCreate, db: AsyncSession = Depends(get_db)):
    service = CashManagementService(db)
    return await service.record_transaction(data)

@router.post('/statements/{statement_id}/reconcile')
async def reconcile_statement(statement_id: int, transaction_ids: List[int], db: AsyncSession = Depends(get_db)):
    service = CashManagementService(db)
    try:
        return await service.reconcile_statement(statement_id, transaction_ids)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post('/forecasts/generate')
async def generate_forecast(account_id: int = None, days: int = 30, db: AsyncSession = Depends(get_db)):
    service = CashManagementService(db)
    return await service.generate_cash_flow_forecast(account_id, days)

@router.get('/liquidity/alerts')
async def check_liquidity(db: AsyncSession = Depends(get_db)):
    service = CashManagementService(db)
    return await service.check_liquidity_rules()
