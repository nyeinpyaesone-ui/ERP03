from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from datetime import datetime
from decimal import Decimal
from app.domain.finance.model.accounting import (
    Account, AccountType, JournalEntry, JournalLine, Invoice, InvoiceLine, Payment
)

class AccountingService:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_account(self, code: str, name: str, account_type: AccountType, 
                            parent_id: int = None, currency: str = "USD") -> Account:
        account = Account(
            code=code,
            name=name,
            account_type=account_type,
            parent_id=parent_id,
            currency=currency,
            balance=Decimal("0.00")
        )
        self.db.add(account)
        await self.db.flush()
        await self.db.refresh(account)
        return account
    
    async def get_chart_of_accounts(self) -> List[Account]:
        result = await self.db.execute(
            select(Account)
            .options(selectinload(Account.parent))
            .where(Account.is_active == True)
            .order_by(Account.code)
        )
        return list(result.scalars().unique().all())
    
    async def create_journal_entry(self, entry_date: datetime, description: str, 
                                  reference: str, lines: List[Dict[str, Any]], 
                                  created_by: int) -> JournalEntry:
        # Validate debits = credits
        total_debit = sum(Decimal(str(line.get("debit", 0))) for line in lines)
        total_credit = sum(Decimal(str(line.get("credit", 0))) for line in lines)
        
        if total_debit != total_credit:
            raise ValueError(f"Journal entry must balance. Debit: {total_debit}, Credit: {total_credit}")
        
        entry = JournalEntry(
            entry_date=entry_date,
            description=description,
            reference=reference,
            posted=False,
            created_by=created_by
        )
        self.db.add(entry)
        await self.db.flush()
        
        # Add journal lines
        for line_data in lines:
            journal_line = JournalLine(
                entry_id=entry.id,
                account_id=line_data["account_id"],
                debit=Decimal(str(line_data.get("debit", 0))),
                credit=Decimal(str(line_data.get("credit", 0))),
                description=line_data.get("description")
            )
            self.db.add(journal_line)
            
            # Update account balance
            account = await self.db.get(Account, line_data["account_id"])
            if account:
                account.balance += Decimal(str(line_data.get("debit", 0))) - Decimal(str(line_data.get("credit", 0)))
        
        await self.db.refresh(entry)
        return entry
    
    async def post_journal_entry(self, entry_id: int) -> JournalEntry:
        entry = await self.db.get(JournalEntry, entry_id)
        if not entry:
            raise ValueError("Journal entry not found")
        
        entry.posted = True
        await self.db.flush()
        return entry
    
    async def create_invoice(self, invoice_number: str, customer_id: int,
                            issue_date: datetime, due_date: datetime,
                            lines: List[Dict[str, Any]], notes: str = None) -> Invoice:
        # Calculate totals
        subtotal = Decimal("0.00")
        tax_amount = Decimal("0.00")
        
        for line_data in lines:
            qty = Decimal(str(line_data.get("quantity", 1)))
            price = Decimal(str(line_data["unit_price"]))
            tax_rate = Decimal(str(line_data.get("tax_rate", 0)))
            
            line_total = qty * price
            line_tax = line_total * (tax_rate / Decimal("100"))
            
            subtotal += line_total
            tax_amount += line_tax
        
        total_amount = subtotal + tax_amount
        
        invoice = Invoice(
            invoice_number=invoice_number,
            customer_id=customer_id,
            issue_date=issue_date,
            due_date=due_date,
            subtotal=subtotal,
            tax_amount=tax_amount,
            total_amount=total_amount,
            amount_paid=Decimal("0.00"),
            status="draft",
            notes=notes
        )
        self.db.add(invoice)
        await self.db.flush()
        
        # Add invoice lines
        for line_data in lines:
            qty = Decimal(str(line_data.get("quantity", 1)))
            price = Decimal(str(line_data["unit_price"]))
            line_total = qty * price
            
            inv_line = InvoiceLine(
                invoice_id=invoice.id,
                description=line_data["description"],
                quantity=qty,
                unit_price=price,
                tax_rate=Decimal(str(line_data.get("tax_rate", 0))),
                line_total=line_total
            )
            self.db.add(inv_line)
        
        await self.db.refresh(invoice)
        return invoice
    
    async def record_payment(self, payment_number: str, invoice_id: int,
                            amount: Decimal, payment_method: str,
                            reference: str = None, notes: str = None) -> Payment:
        invoice = await self.db.get(Invoice, invoice_id)
        if not invoice:
            raise ValueError("Invoice not found")
        
        if invoice.amount_paid + amount > invoice.total_amount:
            raise ValueError("Payment amount exceeds invoice balance")
        
        payment = Payment(
            payment_number=payment_number,
            invoice_id=invoice_id,
            payment_date=datetime.utcnow(),
            amount=amount,
            payment_method=payment_method,
            reference=reference,
            notes=notes
        )
        self.db.add(payment)
        
        # Update invoice
        invoice.amount_paid += amount
        if invoice.amount_paid >= invoice.total_amount:
            invoice.status = "paid"
        
        await self.db.flush()
        await self.db.refresh(payment)
        return payment
    
    async def get_invoice(self, invoice_id: int) -> Optional[Invoice]:
        result = await self.db.execute(
            select(Invoice)
            .options(selectinload(Invoice.lines), selectinload(Invoice.payments))
            .where(Invoice.id == invoice_id)
        )
        return result.scalar_one_or_none()
    
    async def get_invoices_by_status(self, status: str) -> List[Invoice]:
        result = await self.db.execute(
            select(Invoice).where(Invoice.status == status)
        )
        return list(result.scalars().all())
