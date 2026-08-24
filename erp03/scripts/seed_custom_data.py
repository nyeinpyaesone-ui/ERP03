#!/usr/bin/env python3
"""
ERP03 Customized Seed Data Script
Populates the database with realistic business data for Finance, HCM, SCM, Manufacturing, and CRM.
"""
import asyncio
import os
from datetime import date, timedelta
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.future import select
from sqlalchemy import text

# Import Models
from apps.erp.modules.finance.models import (
    Account, JournalEntry, JournalLine, Vendor, Customer, Invoice, Payment,
    BankAccount, CashTransaction, FixedAsset, Budget
)
from apps.erp.modules.hcm.models import Employee, Department, PayrollRun, LeaveBalance
from apps.erp.modules.scm.models import Product, Warehouse, StockLevel, PurchaseOrder, SalesOrder
from apps.erp.modules.manufacturing.models import BillOfMaterials, WorkOrder, Routing
from apps.erp.modules.crm.models import Contact, Opportunity, Case

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://erp_user:erp_pass@localhost:5432/erp03_db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_finance(db: AsyncSession):
    print("Seeding Finance Module...")
    
    # Chart of Accounts (Standard GAAP)
    accounts_data = [
        {"code": "1000", "name": "Cash", "type": "ASSET", "balance": Decimal("50000.00")},
        {"code": "1100", "name": "Accounts Receivable", "type": "ASSET", "balance": Decimal("15000.00")},
        {"code": "1200", "name": "Inventory", "type": "ASSET", "balance": Decimal("25000.00")},
        {"code": "1500", "name": "Fixed Assets", "type": "ASSET", "balance": Decimal("100000.00")},
        {"code": "2000", "name": "Accounts Payable", "type": "LIABILITY", "balance": Decimal("12000.00")},
        {"code": "2100", "name": "Accrued Expenses", "type": "LIABILITY", "balance": Decimal("5000.00")},
        {"code": "3000", "name": "Common Stock", "type": "EQUITY", "balance": Decimal("100000.00")},
        {"code": "3100", "name": "Retained Earnings", "type": "EQUITY", "balance": Decimal("50000.00")},
        {"code": "4000", "name": "Sales Revenue", "type": "REVENUE", "balance": Decimal("0.00")},
        {"code": "5000", "name": "Cost of Goods Sold", "type": "EXPENSE", "balance": Decimal("0.00")},
        {"code": "6000", "name": "Operating Expenses", "type": "EXPENSE", "balance": Decimal("0.00")},
    ]
    
    accounts = []
    for acc in accounts_data:
        account = Account(**acc)
        accounts.append(account)
    
    db.add_all(accounts)
    await db.commit()
    print(f"  - Created {len(accounts)} Chart of Accounts")

    # Vendors
    vendors = [
        Vendor(name="Office Supplies Inc", email="billing@office supplies.com", currency="USD"),
        Vendor(name="Tech Hardware Ltd", email="sales@techhardware.com", currency="USD"),
        Vendor(name="Logistics Partners", email="invoices@logisticspartners.com", currency="USD"),
    ]
    db.add_all(vendors)
    await db.commit()

    # Customers
    customers = [
        Customer(name="Acme Corp", email="accounts@acme.com", currency="USD"),
        Customer(name="Global Industries", email="payables@globalind.com", currency="USD"),
        Customer(name="StartUp LLC", email="finance@startup.io", currency="USD"),
    ]
    db.add_all(customers)
    await db.commit()

    # Bank Accounts
    bank_accounts = [
        BankAccount(name="Main Operating Account", account_number="****1234", bank_name="First National", balance=Decimal("45000.00")),
        BankAccount(name="Payroll Account", account_number="****5678", bank_name="First National", balance=Decimal("15000.00")),
    ]
    db.add_all(bank_accounts)
    await db.commit()

    # Sample Journal Entry (Double Entry Verification)
    je = JournalEntry(description="Initial Capital Injection", date=date.today(), status="POSTED")
    db.add(je)
    await db.flush()
    
    cash_acc = await db.execute(select(Account).where(Account.code == "1000"))
    cash = cash_acc.scalars().first()
    equity_acc = await db.execute(select(Account).where(Account.code == "3000"))
    equity = equity_acc.scalars().first()

    lines = [
        JournalLine(journal_entry_id=je.id, account_id=cash.id, debit=Decimal("50000.00"), credit=Decimal("0.00")),
        JournalLine(journal_entry_id=je.id, account_id=equity.id, debit=Decimal("0.00"), credit=Decimal("50000.00")),
    ]
    db.add_all(lines)
    await db.commit()
    print("  - Created sample Journal Entry with balanced double-entry")

async def seed_hcm(db: AsyncSession):
    print("Seeding HCM Module...")
    
    depts = [
        Department(name="Engineering", code="ENG"),
        Department(name="Sales", code="SLS"),
        Department(name="HR", code="HRM"),
        Department(name="Finance", code="FIN"),
    ]
    db.add_all(depts)
    await db.commit()

    eng_dept = await db.execute(select(Department).where(Department.code == "ENG"))
    engineering = eng_dept.scalars().first()

    employees = [
        Employee(first_name="John", last_name="Doe", email="john.doe@erp03.com", department_id=engineering.id, position="Senior Engineer", hire_date=date.today() - timedelta(days=365), salary=Decimal("95000.00")),
        Employee(first_name="Jane", last_name="Smith", email="jane.smith@erp03.com", department_id=engineering.id, position="CTO", hire_date=date.today() - timedelta(days=730), salary=Decimal("150000.00")),
    ]
    db.add_all(employees)
    await db.commit()
    print(f"  - Created {len(employees)} employees")

async def seed_scm(db: AsyncSession):
    print("Seeding SCM Module...")
    
    warehouse = Warehouse(name="Main Warehouse", code="WH-01", address="123 Industrial Pkwy", capacity=10000)
    db.add(warehouse)
    await db.commit()

    products = [
        Product(sku="PROD-001", name="Laptop Pro 15", description="High performance laptop", unit_price=Decimal("1299.00"), cost=Decimal("800.00"), type="GOODS"),
        Product(sku="PROD-002", name="Wireless Mouse", description="Ergonomic wireless mouse", unit_price=Decimal("49.00"), cost=Decimal("20.00"), type="GOODS"),
        Product(sku="SERV-001", name="Consulting Hour", description="Professional consulting service", unit_price=Decimal("200.00"), cost=Decimal("0.00"), type="SERVICE"),
    ]
    db.add_all(products)
    await db.commit()

    # Initial Stock
    laptop = await db.execute(select(Product).where(Product.sku == "PROD-001"))
    lp = laptop.scalars().first()
    
    stock = StockLevel(product_id=lp.id, warehouse_id=warehouse.id, quantity=50, reserved=5)
    db.add(stock)
    await db.commit()
    print("  - Created products and initial inventory")

async def seed_manufacturing(db: AsyncSession):
    print("Seeding Manufacturing Module...")
    
    # BOM for Laptop
    laptop = await db.execute(select(Product).where(Product.sku == "PROD-001"))
    lp = laptop.scalars().first()
    mouse = await db.execute(select(Product).where(Product.sku == "PROD-002"))
    ms = mouse.scalars().first()

    bom = BillOfMaterials(product_id=lp.id, version="1.0", status="ACTIVE")
    db.add(bom)
    await db.flush()
    
    # Assume we add components (simplified for seed)
    print("  - Created Bill of Materials for Laptop Pro")

async def seed_crm(db: AsyncSession):
    print("Seeding CRM Module...")
    
    contact = Contact(first_name="Alice", last_name="Johnson", email="alice@acme.com", phone="+1-555-0100")
    db.add(contact)
    await db.commit()

    opp = Opportunity(name="Acme Enterprise Deal", stage="PROPOSAL", amount=Decimal("50000.00"), close_date=date.today() + timedelta(days=30), contact_id=contact.id)
    db.add(opp)
    await db.commit()
    print("  - Created sales opportunity")

async def main():
    print("Starting ERP03 Database Seeding...")
    async with AsyncSessionLocal() as session:
        try:
            await seed_finance(session)
            await seed_hcm(session)
            await seed_scm(session)
            await seed_manufacturing(session)
            await seed_crm(session)
            print("\n✅ ERP03 Database Seeding Completed Successfully!")
        except Exception as e:
            print(f"\n❌ Seeding failed: {e}")
            await session.rollback()
            raise

if __name__ == "__main__":
    asyncio.run(main())
