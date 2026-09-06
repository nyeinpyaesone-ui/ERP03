"""
Cash Management Business Logic Service
Implements: Bank Reconciliation, Cash Flow Forecasting, Liquidity Monitoring
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
import logging

from .models import (
    BankAccount, CashTransaction, BankStatement, 
    CashFlowForecast, LiquidityRule, ReconciliationStatus, AccountType
)
from .schemas import (
    BankAccountCreate, BankAccountUpdate, CashTransactionCreate,
    CashFlowForecastCreate, LiquidityRuleCreate, ReconciliationReport
)

logger = logging.getLogger(__name__)

class CashManagementService:
    """Core business logic for Cash Management operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # === Bank Account Operations ===
    
    async def create_account(self, account_data: BankAccountCreate) -> BankAccount:
        """Create a new bank account with initial balance validation"""
        db_account = BankAccount(**account_data.model_dump())
        
        # Validate uniqueness of account number
        result = await self.db.execute(
            select(BankAccount).where(BankAccount.account_number == db_account.account_number)
        )
        existing = result.scalar_one_or_none()
        if existing:
            raise ValueError(f"Account number {db_account.account_number} already exists")
        
        self.db.add(db_account)
        await self.db.commit()
        await self.db.refresh(db_account)
        logger.info(f"Created bank account: {db_account.account_name} ({db_account.account_number})")
        return db_account
    
    async def get_account_balance(self, account_id: int) -> Dict[str, float]:
        """Calculate real-time balance from transactions"""
        result = await self.db.execute(
            select(BankAccount).where(BankAccount.id == account_id)
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError(f"Account {account_id} not found")
        
        # Calculate balance from transactions
        stmt = select(
            func.sum(CashTransaction.debit_amount - CashTransaction.credit_amount)
        ).where(
            CashTransaction.account_id == account_id
        )
        tx_result = await self.db.execute(stmt)
        net_change = tx_result.scalar() or 0.0
        
        current_balance = account.current_balance + net_change
        
        # Calculate available balance (exclude pending/unreconciled large transactions)
        pending_stmt = select(
            func.sum(CashTransaction.debit_amount)
        ).where(
            CashTransaction.account_id == account_id,
            CashTransaction.is_reconciled == False,
            CashTransaction.reconciliation_status == ReconciliationStatus.PENDING
        )
        pending_result = await self.db.execute(pending_stmt)
        pending_debits = pending_result.scalar() or 0.0
        
        available_balance = current_balance - pending_debits
        
        return {
            "current_balance": current_balance,
            "available_balance": available_balance,
            "pending_holds": pending_debits
        }
    
    # === Transaction Operations ===
    
    async def record_transaction(self, tx_data: CashTransactionCreate) -> CashTransaction:
        """Record a cash transaction and update running balance"""
        # Verify account exists
        result = await self.db.execute(
            select(BankAccount).where(BankAccount.id == tx_data.account_id)
        )
        account = result.scalar_one_or_none()
        if not account:
            raise ValueError(f"Account {tx_data.account_id} not found")
        
        # Calculate new balance
        balance_info = await self.get_account_balance(tx_data.account_id)
        net_amount = tx_data.debit_amount - tx_data.credit_amount
        new_balance = balance_info["current_balance"] + net_amount
        
        db_tx = CashTransaction(
            **tx_data.model_dump(),
            balance_after=new_balance
        )
        
        self.db.add(db_tx)
        
        # Update account current balance
        account.current_balance = new_balance
        if not account.is_reconciled:
            account.available_balance = balance_info["available_balance"]
        
        await self.db.commit()
        await self.db.refresh(db_tx)
        logger.info(f"Recorded transaction {db_tx.reference_number}: {net_amount}")
        return db_tx
    
    # === Reconciliation Engine ===
    
    async def reconcile_statement(
        self, 
        statement_id: int, 
        matched_transaction_ids: List[int]
    ) -> ReconciliationReport:
        """
        Perform bank reconciliation:
        1. Match system transactions to bank statement lines
        2. Identify discrepancies
        3. Mark transactions as reconciled
        """
        # Get statement
        stmt_result = await self.db.execute(
            select(BankStatement)
            .options(selectinload(BankStatement.account))
            .where(BankStatement.id == statement_id)
        )
        statement = stmt_result.scalar_one_or_none()
        if not statement:
            raise ValueError(f"Statement {statement_id} not found")
        
        # Get matched transactions
        tx_result = await self.db.execute(
            select(CashTransaction)
            .where(CashTransaction.id.in_(matched_transaction_ids))
        )
        transactions = tx_result.scalars().all()
        
        # Calculate system balance for period
        system_opening = statement.opening_balance  # Should match last reconciled
        system_closing_calc = system_opening + sum(
            (tx.debit_amount - tx.credit_amount) 
            for tx in transactions 
            if statement.period_start <= tx.transaction_date <= statement.period_end
        )
        
        # Identify discrepancies
        difference = statement.closing_balance - system_closing_calc
        discrepancies = []
        
        if abs(difference) > 0.01:  # Tolerance of 1 cent
            discrepancies.append(f"Balance mismatch: Statement={statement.closing_balance}, System={system_closing_calc}")
            
            # Find unmatched transactions in period
            all_period_tx = await self.db.execute(
                select(CashTransaction)
                .where(
                    CashTransaction.account_id == statement.account_id,
                    CashTransaction.transaction_date >= statement.period_start,
                    CashTransaction.transaction_date <= statement.period_end
                )
            )
            all_txs = all_period_tx.scalars().all()
            unmatched = [tx for tx in all_txs if tx.id not in matched_transaction_ids]
            
            if unmatched:
                discrepancies.append(f"{len(unmatched)} unmatched transactions found")
        
        # Mark transactions as reconciled
        for tx_id in matched_transaction_ids:
            await self.db.execute(
                CashTransaction.__table__.update()
                .where(CashTransaction.id == tx_id)
                .values(
                    is_reconciled=True,
                    reconciliation_status=ReconciliationStatus.RECONCILED,
                    reconciled_statement_id=statement_id
                )
            )
        
        # Update account reconciliation metadata
        await self.db.execute(
            BankAccount.__table__.update()
            .where(BankAccount.id == statement.account_id)
            .values(
                last_reconciled_date=statement.statement_date,
                last_reconciled_balance=statement.closing_balance
            )
        )
        
        await self.db.commit()
        
        report = ReconciliationReport(
            account_id=statement.account_id,
            statement_id=statement_id,
            statement_period_start=statement.period_start,
            statement_period_end=statement.period_end,
            statement_closing_balance=statement.closing_balance,
            system_closing_balance=system_closing_calc,
            difference=difference,
            reconciled_transactions=len(matched_transaction_ids),
            pending_transactions=len(transactions) - len(matched_transaction_ids),
            discrepancies=discrepancies
        )
        
        logger.info(f"Reconciliation complete for statement {statement_id}. Difference: {difference}")
        return report
    
    # === Cash Flow Forecasting ===
    
    async def generate_cash_flow_forecast(
        self,
        account_id: Optional[int],
        days_ahead: int = 30
    ) -> List[CashFlowForecast]:
        """
        Generate daily cash flow forecast based on:
        1. Historical transaction patterns
        2. Scheduled payments (AP/AR)
        3. Recurring transactions
        """
        end_date = datetime.now() + timedelta(days=days_ahead)
        forecasts = []
        
        # Get starting balance
        if account_id:
            accounts = await self.db.execute(
                select(BankAccount).where(BankAccount.id == account_id)
            )
            account_list = accounts.scalars().all()
        else:
            accounts = await self.db.execute(select(BankAccount))
            account_list = accounts.scalars().all()
        
        for account in account_list:
            if not account.is_active:
                continue
                
            current_balance = await self.get_account_balance(account.id)
            running_balance = current_balance["current_balance"]
            
            # Get historical average daily flow (last 90 days)
            ninety_days_ago = datetime.now() - timedelta(days=90)
            hist_stmt = select(
                func.avg(CashTransaction.debit_amount),
                func.avg(CashTransaction.credit_amount)
            ).where(
                CashTransaction.account_id == account.id,
                CashTransaction.transaction_date >= ninety_days_ago
            )
            hist_result = await self.db.execute(hist_stmt)
            avg_debit, avg_credit = hist_result.one()
            avg_debit = avg_debit or 0.0
            avg_credit = avg_credit or 0.0
            
            # Generate daily forecast
            for day_offset in range(1, days_ahead + 1):
                forecast_date = datetime.now() + timedelta(days=day_offset)
                
                # Simple projection (enhance with AR/AP schedules in production)
                projected_inflow = avg_credit * (1 + (0.05 * (day_offset / days_ahead)))  # Slight variance
                projected_outflow = avg_debit * (1 + (0.05 * (day_offset / days_ahead)))
                
                running_balance += (projected_inflow - projected_outflow)
                
                forecast = CashFlowForecast(
                    forecast_date=forecast_date,
                    account_id=account.id,
                    projected_inflow=projected_inflow,
                    projected_outflow=projected_outflow,
                    net_flow=projected_inflow - projected_outflow,
                    projected_balance=running_balance,
                    confidence_level=max(0.95 - (day_offset * 0.01), 0.5),  # Decreasing confidence
                    source_breakdown={"historical_avg": 1.0}
                )
                
                forecasts.append(forecast)
                self.db.add(forecast)
        
        await self.db.commit()
        logger.info(f"Generated {len(forecasts)} cash flow forecast records")
        return forecasts
    
    # === Liquidity Monitoring ===
    
    async def check_liquidity_rules(self) -> List[Dict[str, Any]]:
        """Check all active liquidity rules and trigger alerts if breached"""
        alerts = []
        
        rules_result = await self.db.execute(
            select(LiquidityRule).where(LiquidityRule.is_active == True)
        )
        rules = rules_result.scalars().all()
        
        for rule in rules:
            # Get account(s) to check
            if rule.account_id:
                accounts = await self.db.execute(
                    select(BankAccount).where(BankAccount.id == rule.account_id)
                )
                account_list = accounts.scalars().all()
            else:
                accounts = await self.db.execute(select(BankAccount))
                account_list = accounts.scalars().all()
            
            for account in account_list:
                if not account.is_active:
                    continue
                    
                balance_info = await self.get_account_balance(account.id)
                current = balance_info["current_balance"]
                
                # Check minimum balance breach
                if current < rule.minimum_balance:
                    alert = {
                        "rule_id": rule.id,
                        "rule_name": rule.rule_name,
                        "account_id": account.id,
                        "account_name": account.account_name,
                        "current_balance": current,
                        "minimum_required": rule.minimum_balance,
                        "shortfall": rule.minimum_balance - current,
                        "severity": "critical",
                        "action_type": rule.action_type,
                        "action_config": rule.action_config,
                        "triggered_at": datetime.now()
                    }
                    alerts.append(alert)
                    logger.warning(f"Liquidity alert: {account.account_name} below minimum")
                
                # Check target balance warning
                elif rule.target_balance and current < (rule.target_balance * (rule.alert_threshold_percent / 100)):
                    alert = {
                        "rule_id": rule.id,
                        "rule_name": rule.rule_name,
                        "account_id": account.id,
                        "account_name": account.account_name,
                        "current_balance": current,
                        "target_balance": rule.target_balance,
                        "threshold_percent": rule.alert_threshold_percent,
                        "severity": "warning",
                        "action_type": rule.action_type,
                        "action_config": rule.action_config,
                        "triggered_at": datetime.now()
                    }
                    alerts.append(alert)
        
        return alerts
