"""
Cash Management API Endpoints
RESTful interface for banking operations, reconciliation, and liquidity monitoring
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from datetime import datetime

from ...core.database.session import get_db
from .models import BankAccount, CashTransaction, BankStatement, CashFlowForecast
from .schemas import (
    BankAccountCreate, BankAccountUpdate, BankAccountResponse,
    CashTransactionCreate, CashTransactionUpdate, CashTransactionResponse,
    BankStatementCreate, BankStatementResponse,
    CashFlowForecastCreate, CashFlowForecastResponse,
    LiquidityRuleCreate, LiquidityRuleResponse,
    CashPositionSummary, ReconciliationReport
)
from .service import CashManagementService

router = APIRouter(prefix="/cash-management", tags=["Finance - Cash Management"])

# === Bank Account Endpoints ===

@router.post("/accounts", response_model=BankAccountResponse, status_code=status.HTTP_201_CREATED)
async def create_bank_account(
    account_data: BankAccountCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new bank account"""
    service = CashManagementService(db)
    try:
        return await service.create_account(account_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/accounts", response_model=List[BankAccountResponse])
async def list_bank_accounts(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List all bank accounts"""
    from sqlalchemy import select
    query = select(BankAccount)
    if active_only:
        query = query.where(BankAccount.is_active == True)
    
    result = await db.execute(query)
    return result.scalars().all()

@router.get("/accounts/{account_id}", response_model=BankAccountResponse)
async def get_bank_account(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get specific bank account details"""
    from sqlalchemy import select
    result = await db.execute(select(BankAccount).where(BankAccount.id == account_id))
    account = result.scalar_one_or_none()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/accounts/{account_id}/balance")
async def get_account_balance(
    account_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get real-time balance calculation for an account"""
    service = CashManagementService(db)
    try:
        return await service.get_account_balance(account_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# === Transaction Endpoints ===

@router.post("/transactions", response_model=CashTransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    tx_data: CashTransactionCreate,
    db: AsyncSession = Depends(get_db)
):
    """Record a new cash transaction (deposit/withdrawal)"""
    service = CashManagementService(db)
    try:
        return await service.record_transaction(tx_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/transactions", response_model=List[CashTransactionResponse])
async def list_transactions(
    account_id: Optional[int] = Query(None),
    is_reconciled: Optional[bool] = Query(None),
    limit: int = Query(50, le=200),
    db: AsyncSession = Depends(get_db)
):
    """List cash transactions with filters"""
    from sqlalchemy import select
    query = select(CashTransaction)
    
    if account_id:
        query = query.where(CashTransaction.account_id == account_id)
    if is_reconciled is not None:
        query = query.where(CashTransaction.is_reconciled == is_reconciled)
    
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()

# === Reconciliation Endpoints ===

@router.post("/reconcile/{statement_id}")
async def perform_reconciliation(
    statement_id: int,
    matched_transaction_ids: List[int],
    db: AsyncSession = Depends(get_db)
):
    """
    Perform bank reconciliation for a statement period.
    Provide list of transaction IDs that match the bank statement lines.
    """
    service = CashManagementService(db)
    try:
        report = await service.reconcile_statement(statement_id, matched_transaction_ids)
        return {
            "success": True,
            "report": report,
            "status": "reconciled" if report.difference == 0 else "discrepancy_found"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/reconciliation/reports/{statement_id}")
async def get_reconciliation_report(
    statement_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Get reconciliation report for a statement"""
    from sqlalchemy import select
    result = await db.execute(
        select(BankStatement).where(BankStatement.id == statement_id)
    )
    statement = result.scalar_one_or_none()
    if not statement:
        raise HTTPException(status_code=404, detail="Statement not found")
    
    # Calculate report data
    service = CashManagementService(db)
    # In production, store reports; here we recalculate
    # This is a simplified version
    return {
        "statement_id": statement_id,
        "account_id": statement.account_id,
        "period_start": statement.period_start,
        "period_end": statement.period_end,
        "statement_balance": statement.closing_balance,
        "status": "pending_reconciliation"
    }

# === Cash Flow Forecasting ===

@router.post("/forecast/generate")
async def generate_forecast(
    days_ahead: int = Query(30, le=90),
    account_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Generate cash flow forecast for upcoming days"""
    service = CashManagementService(db)
    forecasts = await service.generate_cash_flow_forecast(account_id, days_ahead)
    return {
        "generated_at": datetime.now(),
        "days_forecasted": days_ahead,
        "records_count": len(forecasts),
        "forecasts": forecasts
    }

@router.get("/forecast", response_model=List[CashFlowForecastResponse])
async def list_forecasts(
    account_id: Optional[int] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve cached cash flow forecasts"""
    from sqlalchemy import select
    query = select(CashFlowForecast)
    
    if account_id:
        query = query.where(CashFlowForecast.account_id == account_id)
    if start_date:
        query = query.where(CashFlowForecast.forecast_date >= start_date)
    if end_date:
        query = query.where(CashFlowForecast.forecast_date <= end_date)
    
    result = await db.execute(query)
    return result.scalars().all()

# === Liquidity Monitoring ===

@router.get("/liquidity/check")
async def check_liquidity_alerts(
    db: AsyncSession = Depends(get_db)
):
    """Check all liquidity rules and return active alerts"""
    service = CashManagementService(db)
    alerts = await service.check_liquidity_rules()
    return {
        "checked_at": datetime.now(),
        "alerts_count": len(alerts),
        "alerts": alerts
    }

@router.post("/liquidity/rules", response_model=LiquidityRuleResponse)
async def create_liquidity_rule(
    rule_data: LiquidityRuleCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new liquidity monitoring rule"""
    from .models import LiquidityRule
    db_rule = LiquidityRule(**rule_data.model_dump())
    db.add(db_rule)
    await db.commit()
    await db.refresh(db_rule)
    return db_rule

@router.get("/liquidity/rules", response_model=List[LiquidityRuleResponse])
async def list_liquidity_rules(
    active_only: bool = True,
    db: AsyncSession = Depends(get_db)
):
    """List liquidity monitoring rules"""
    from sqlalchemy import select
    from .models import LiquidityRule
    
    query = select(LiquidityRule)
    if active_only:
        query = query.where(LiquidityRule.is_active == True)
    
    result = await db.execute(query)
    return result.scalars().all()

# === Dashboard Summary ===

@router.get("/dashboard/cash-position")
async def get_cash_position_summary(
    db: AsyncSession = Depends(get_db)
):
    """Get consolidated cash position across all accounts"""
    from sqlalchemy import select, func
    
    # Get all active accounts
    accounts_result = await db.execute(
        select(BankAccount).where(BankAccount.is_active == True)
    )
    accounts = accounts_result.scalars().all()
    
    summaries = []
    total_balance = 0.0
    
    for account in accounts:
        # Simple balance calc (use service in production)
        stmt = select(
            func.sum(CashTransaction.debit_amount - CashTransaction.credit_amount)
        ).where(CashTransaction.account_id == account.id)
        tx_result = await db.execute(stmt)
        net_change = tx_result.scalar() or 0.0
        
        current = account.current_balance + net_change
        total_balance += current
        
        # Determine status
        if current < 0:
            status = "critical"
        elif current < account.current_balance * 0.2:
            status = "warning"
        else:
            status = "healthy"
        
        summaries.append(CashPositionSummary(
            account_id=account.id,
            account_name=account.account_name,
            current_balance=current,
            available_balance=account.available_balance,
            pending_transactions_count=0,  # Would need count query
            last_reconciled_date=account.last_reconciled_date,
            liquidity_status=status
        ))
    
    return {
        "total_cash_position": total_balance,
        "accounts_count": len(summaries),
        "accounts": summaries
    }
