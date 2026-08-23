from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict
from apps.erp.modules.finance.cash_management_models import (
    BankAccount, CashTransaction, BankStatement, 
    CashFlowForecast, LiquidityRule, TransactionType
)
from apps.erp.modules.finance.cash_management_schemas import (
    BankAccountCreate, CashTransactionCreate, BankStatementCreate,
    CashFlowForecastCreate, LiquidityRuleCreate
)

class CashManagementService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_account(self, data: BankAccountCreate) -> BankAccount:
        account = BankAccount(**data.dict())
        self.db.add(account)
        await self.db.commit()
        await self.db.refresh(account)
        return account
    
    async def get_balance(self, account_id: int) -> Decimal:
        result = await self.db.execute(
            select(func.sum(
                CashTransaction.amount * 
                (1 if CashTransaction.transaction_type.in_([TransactionType.DEPOSIT, TransactionType.RECEIPT, TransactionType.TRANSFER]) else -1)
            ))
            .where(CashTransaction.account_id == account_id)
            .where(CashTransaction.is_reconciled == True)
        )
        balance = result.scalar() or Decimal(0)
        
        result2 = await self.db.get(BankAccount, account_id)
        if result2:
            result2.current_balance = balance
            await self.db.commit()
        
        return balance
    
    async def record_transaction(self, data: CashTransactionCreate) -> CashTransaction:
        transaction = CashTransaction(**data.dict(exclude={'transaction_date'}))
        transaction.transaction_date = data.transaction_date or datetime.utcnow()
        
        self.db.add(transaction)
        await self.db.flush()
        
        await self.get_balance(data.account_id)
        
        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction
    
    async def reconcile_statement(self, statement_id: int, transaction_ids: List[int]) -> BankStatement:
        statement = await self.db.get(BankStatement, statement_id)
        if not statement:
            raise ValueError('Bank statement not found')
        
        transactions = []
        for tid in transaction_ids:
            txn = await self.db.get(CashTransaction, tid)
            if txn:
                txn.is_reconciled = True
                transactions.append(txn)
        
        total_reconciled = sum(
            txn.amount * (1 if txn.transaction_type in [TransactionType.DEPOSIT, TransactionType.RECEIPT, TransactionType.TRANSFER] else -1)
            for txn in transactions
        )
        
        discrepancy = abs(statement.closing_balance - (statement.opening_balance + total_reconciled))
        
        statement.is_reconciled = True
        statement.reconciled_at = datetime.utcnow()
        
        await self.db.commit()
        await self.db.refresh(statement)
        return statement
    
    async def generate_cash_flow_forecast(self, account_id: Optional[int], days: int = 30) -> List[CashFlowForecast]:
        forecasts = []
        start_date = datetime.utcnow()
        
        historical_inflows = await self.db.execute(
            select(func.sum(CashTransaction.amount))
            .where(CashTransaction.transaction_type.in_([TransactionType.DEPOSIT, TransactionType.RECEIPT]))
            .where(CashTransaction.transaction_date >= start_date - timedelta(days=days))
        )
        avg_inflow = (historical_inflows.scalar() or 0) / days
        
        historical_outflows = await self.db.execute(
            select(func.sum(CashTransaction.amount))
            .where(CashTransaction.transaction_type.in_([TransactionType.WITHDRAWAL, TransactionType.PAYMENT]))
            .where(CashTransaction.transaction_date >= start_date - timedelta(days=days))
        )
        avg_outflow = (historical_outflows.scalar() or 0) / days
        
        for i in range(days):
            forecast_date = start_date + timedelta(days=i+1)
            forecast = CashFlowForecast(
                account_id=account_id,
                forecast_date=forecast_date,
                projected_inflow=avg_inflow,
                projected_outflow=avg_outflow,
                net_cash_flow=avg_inflow - avg_outflow
            )
            forecasts.append(forecast)
            self.db.add(forecast)
        
        await self.db.commit()
        return forecasts
    
    async def check_liquidity_rules(self) -> List[Dict]:
        rules = await self.db.execute(select(LiquidityRule).where(LiquidityRule.is_active == True))
        alerts = []
        
        for rule in rules.scalars().all():
            accounts = await self.db.execute(
                select(BankAccount).where(BankAccount.is_active == True)
            )
            for account in accounts.scalars().all():
                balance = await self.get_balance(account.id)
                if balance < rule.min_balance:
                    alerts.append({
                        'rule_name': rule.rule_name,
                        'account': account.account_name,
                        'current_balance': balance,
                        'min_required': rule.min_balance,
                        'shortfall': rule.min_balance - balance,
                        'alert_email': rule.alert_email
                    })
        
        return alerts
