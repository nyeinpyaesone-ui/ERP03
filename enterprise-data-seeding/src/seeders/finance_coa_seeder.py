"""
Finance Chart of Accounts seeder.

Seeds:
- Standard chart of accounts (COA)
- Account categories and hierarchies
- Default tax codes
- Payment terms
"""

import json
import logging
from pathlib import Path
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from .base_seeder import BaseSeeder, SeederResult

logger = logging.getLogger(__name__)


# Standard Chart of Accounts (US GAAP style)
STANDARD_COA = [
    # Assets (1000-1999)
    {"code": "1000", "name": "Cash and Cash Equivalents", "type": "asset", "parent_code": None},
    {"code": "1010", "name": "Petty Cash", "type": "asset", "parent_code": "1000"},
    {"code": "1020", "name": "Main Operating Account", "type": "asset", "parent_code": "1000"},
    {"code": "1030", "name": "Payroll Account", "type": "asset", "parent_code": "1000"},
    
    {"code": "1100", "name": "Accounts Receivable", "type": "asset", "parent_code": None},
    {"code": "1110", "name": "Trade Receivables", "type": "asset", "parent_code": "1100"},
    {"code": "1120", "name": "Allowance for Doubtful Accounts", "type": "asset", "parent_code": "1100"},
    
    {"code": "1200", "name": "Inventory", "type": "asset", "parent_code": None},
    {"code": "1210", "name": "Raw Materials", "type": "asset", "parent_code": "1200"},
    {"code": "1220", "name": "Work in Progress", "type": "asset", "parent_code": "1200"},
    {"code": "1230", "name": "Finished Goods", "type": "asset", "parent_code": "1200"},
    
    {"code": "1300", "name": "Fixed Assets", "type": "asset", "parent_code": None},
    {"code": "1310", "name": "Land and Buildings", "type": "asset", "parent_code": "1300"},
    {"code": "1320", "name": "Machinery and Equipment", "type": "asset", "parent_code": "1300"},
    {"code": "1330", "name": "Office Equipment", "type": "asset", "parent_code": "1300"},
    {"code": "1340", "name": "Accumulated Depreciation", "type": "asset", "parent_code": "1300"},
    
    # Liabilities (2000-2999)
    {"code": "2000", "name": "Accounts Payable", "type": "liability", "parent_code": None},
    {"code": "2010", "name": "Trade Payables", "type": "liability", "parent_code": "2000"},
    {"code": "2020", "name": "Accrued Expenses", "type": "liability", "parent_code": "2000"},
    
    {"code": "2100", "name": "Short-term Debt", "type": "liability", "parent_code": None},
    {"code": "2110", "name": "Bank Loans", "type": "liability", "parent_code": "2100"},
    {"code": "2120", "name": "Credit Cards", "type": "liability", "parent_code": "2100"},
    
    {"code": "2200", "name": "Long-term Debt", "type": "liability", "parent_code": None},
    {"code": "2210", "name": "Mortgages", "type": "liability", "parent_code": "2200"},
    {"code": "2220", "name": "Bonds Payable", "type": "liability", "parent_code": "2200"},
    
    # Equity (3000-3999)
    {"code": "3000", "name": "Owner's Equity", "type": "equity", "parent_code": None},
    {"code": "3010", "name": "Common Stock", "type": "equity", "parent_code": "3000"},
    {"code": "3020", "name": "Retained Earnings", "type": "equity", "parent_code": "3000"},
    {"code": "3030", "name": "Current Year Earnings", "type": "equity", "parent_code": "3000"},
    
    # Revenue (4000-4999)
    {"code": "4000", "name": "Revenue", "type": "revenue", "parent_code": None},
    {"code": "4010", "name": "Product Sales", "type": "revenue", "parent_code": "4000"},
    {"code": "4020", "name": "Service Revenue", "type": "revenue", "parent_code": "4000"},
    {"code": "4030", "name": "Consulting Revenue", "type": "revenue", "parent_code": "4000"},
    {"code": "4040", "name": "Other Income", "type": "revenue", "parent_code": "4000"},
    
    # Cost of Goods Sold (5000-5999)
    {"code": "5000", "name": "Cost of Goods Sold", "type": "expense", "parent_code": None},
    {"code": "5010", "name": "Materials", "type": "expense", "parent_code": "5000"},
    {"code": "5020", "name": "Direct Labor", "type": "expense", "parent_code": "5000"},
    {"code": "5030", "name": "Manufacturing Overhead", "type": "expense", "parent_code": "5000"},
    
    # Expenses (6000-6999)
    {"code": "6000", "name": "Operating Expenses", "type": "expense", "parent_code": None},
    {"code": "6010", "name": "Salaries and Wages", "type": "expense", "parent_code": "6000"},
    {"code": "6020", "name": "Employee Benefits", "type": "expense", "parent_code": "6000"},
    {"code": "6030", "name": "Rent Expense", "type": "expense", "parent_code": "6000"},
    {"code": "6040", "name": "Utilities", "type": "expense", "parent_code": "6000"},
    {"code": "6050", "name": "Office Supplies", "type": "expense", "parent_code": "6000"},
    {"code": "6060", "name": "Professional Fees", "type": "expense", "parent_code": "6000"},
    {"code": "6070", "name": "Marketing and Advertising", "type": "expense", "parent_code": "6000"},
    {"code": "6080", "name": "Depreciation Expense", "type": "expense", "parent_code": "6000"},
    {"code": "6090", "name": "Insurance", "type": "expense", "parent_code": "6000"},
    {"code": "6100", "name": "Travel and Entertainment", "type": "expense", "parent_code": "6000"},
]

# Standard payment terms
PAYMENT_TERMS = [
    {"code": "NET00", "name": "Due on Receipt", "days": 0},
    {"code": "NET15", "name": "Net 15 Days", "days": 15},
    {"code": "NET30", "name": "Net 30 Days", "days": 30},
    {"code": "NET45", "name": "Net 45 Days", "days": 45},
    {"code": "NET60", "name": "Net 60 Days", "days": 60},
    {"code": "NET90", "name": "Net 90 Days", "days": 90},
    {"code": "EOM", "name": "End of Month", "days": 0, "is_end_of_month": True},
]

# Tax codes
TAX_CODES = [
    {"code": "TAX00", "name": "No Tax", "rate": 0.0, "description": "Tax exempt"},
    {"code": "TAX05", "name": "5% Tax", "rate": 5.0, "description": "Standard 5% tax"},
    {"code": "TAX08", "name": "8% Tax", "rate": 8.0, "description": "Standard 8% tax"},
    {"code": "TAX10", "name": "10% Tax", "rate": 10.0, "description": "Standard 10% tax"},
    {"code": "TAX15", "name": "15% Tax", "rate": 15.0, "description": "Standard 15% tax"},
    {"code": "TAX20", "name": "20% Tax", "rate": 20.0, "description": "Standard 20% tax"},
]


class FinanceCOASeeder(BaseSeeder):
    """Seeder for Chart of Accounts and finance reference data."""
    
    def __init__(
        self,
        session: AsyncSession,
        dry_run: bool = False,
        batch_size: int = 100,
    ):
        """Initialize the finance chart-of-accounts seeder.
        
        Parameters:
            dry_run (bool): Whether to simulate seeding without persisting changes.
            batch_size (int): Maximum number of records processed in each batch.
        """
        super().__init__(session, dry_run, batch_size)
    
    async def get_seed_data(self) -> list[dict[str, Any]]:
        """Return standard COA data."""
        return STANDARD_COA
    
    async def seed(self) -> SeederResult:
        """
        Seed the chart of accounts, payment terms, and tax codes.
        
        Returns:
            SeederResult containing creation counts, warnings, errors, completion status,
            and elapsed time. Seeding is skipped with a warning when finance models are
            unavailable.
        """
        import time
        start_time = time.time()
        
        result = SeederResult(success=True)
        
        try:
            # Dynamically import models
            import sys
            from pathlib import Path
            backend_path = Path(__file__).parent.parent.parent.parent / "ERP-BACKEND"
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            
            try:
                from app.models.finance import Account, PaymentTerm, TaxCode
            except ImportError:
                result.warnings.append(
                    "ERP-BACKEND finance models not found. Skipping actual seeding."
                )
                return result
            
            # Seed Chart of Accounts
            self.log_info("Seeding Chart of Accounts...")
            coa_created = await self._seed_accounts(result)
            
            # Seed Payment Terms
            self.log_info("Seeding Payment Terms...")
            terms_created = await self._seed_payment_terms(result, PaymentTerm)
            
            # Seed Tax Codes
            self.log_info("Seeding Tax Codes...")
            taxes_created = await self._seed_tax_codes(result, TaxCode)
            
            result.records_created = coa_created + terms_created + taxes_created
            result.success = len(result.errors) == 0
            
            self.log_info(
                f"Finance seeding complete: {coa_created} accounts, "
                f"{terms_created} payment terms, {taxes_created} tax codes"
            )
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Seeding failed: {str(e)}")
            logger.exception("Unexpected error during seeding")
        
        result.duration_seconds = time.time() - start_time
        
        return result
    
    async def _seed_accounts(self, result: SeederResult) -> int:
        """
        Seed chart-of-accounts entries and establish their parent account relationships.
        
        Parameters:
        	result (SeederResult): Result object updated with account-seeding errors and parent-assignment warnings.
        
        Returns:
        	int: Number of newly created accounts.
        """
        created_count = 0
        account_map = {}  # code -> id mapping for parent references
        
        # First pass: create all accounts without parent references
        for account_data in STANDARD_COA:
            try:
                account_info = {
                    "account_code": account_data["code"],
                    "account_name": account_data["name"],
                    "account_type": account_data["type"],
                    "balance": 0.0,
                    "currency": "USD",
                    "is_active": True,
                }
                
                account, is_new = await self.upsert(Account, account_info, "account_code")
                
                if is_new:
                    created_count += 1
                    account_map[account_data["code"]] = account.id
                
            except Exception as e:
                result.errors.append(
                    f"Failed to seed account {account_data['code']}: {str(e)}"
                )
        
        # Second pass: update parent references
        for account_data in STANDARD_COA:
            if account_data.get("parent_code"):
                try:
                    from sqlalchemy import select
                    stmt = select(Account).where(
                        Account.account_code == account_data["code"]
                    )
                    res = await self.session.execute(stmt)
                    account = res.scalar_one_or_none()
                    
                    if account and account_data["parent_code"] in account_map:
                        account.parent_account_id = account_map[account_data["parent_code"]]
                        await self.session.flush()
                        
                except Exception as e:
                    result.warnings.append(
                        f"Failed to set parent for {account_data['code']}: {str(e)}"
                    )
        
        return created_count
    
    async def _seed_payment_terms(self, result: SeederResult, model) -> int:
        """Seed payment terms and record the number of newly created terms.
        
        Parameters:
            result (SeederResult): Result object for recording seeding errors.
            model: Payment-term model used for persistence.
        
        Returns:
            int: Number of newly created payment terms.
        """
        created_count = 0
        
        for term_data in PAYMENT_TERMS:
            try:
                term_info = {
                    "code": term_data["code"],
                    "name": term_data["name"],
                    "days": term_data["days"],
                    "description": term_data["name"],
                }
                
                _, is_new = await self.upsert(model, term_info, "code")
                
                if is_new:
                    created_count += 1
                    
            except Exception as e:
                result.errors.append(
                    f"Failed to seed payment term {term_data['code']}: {str(e)}"
                )
        
        return created_count
    
    async def _seed_tax_codes(self, result: SeederResult, model) -> int:
        """
        Seed finance tax codes and count newly created records.
        
        Parameters:
            result (SeederResult): Result object to receive errors encountered during seeding.
            model: Tax code model used for persistence.
        
        Returns:
            int: Number of newly created tax codes.
        """
        created_count = 0
        
        for tax_data in TAX_CODES:
            try:
                tax_info = {
                    "code": tax_data["code"],
                    "name": tax_data["name"],
                    "rate": tax_data["rate"],
                    "description": tax_data["description"],
                    "is_active": True,
                }
                
                _, is_new = await self.upsert(model, tax_info, "code")
                
                if is_new:
                    created_count += 1
                    
            except Exception as e:
                result.errors.append(
                    f"Failed to seed tax code {tax_data['code']}: {str(e)}"
                )
        
        return created_count
    
    @property
    def seeding_config(self):
        """Return the seeding configuration for continuing after individual errors.
        
        Returns:
        	SeedingConfig: Configuration that allows seeding to continue when an error occurs.
        """
        from ..config import SeedingConfig
        return SeedingConfig(stop_on_error=False)  # Continue on errors for COA
