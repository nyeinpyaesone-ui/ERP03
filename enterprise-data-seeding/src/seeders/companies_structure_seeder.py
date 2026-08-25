"""
Companies and organizational structure seeder.

Seeds:
- Sample companies with hierarchies
- Branch offices
- Warehouse locations
- Department structures
"""

import logging
from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession

from .base_seeder import BaseSeeder, SeederResult

logger = logging.getLogger(__name__)


# Sample companies for testing/demo
SAMPLE_COMPANIES = [
    {
        "name": "Acme Corporation",
        "code": "ACME",
        "industry": "Manufacturing",
        "is_active": True,
        "branches": [
            {
                "name": "Headquarters",
                "code": "HQ",
                "city": "New York",
                "country": "USA",
                "warehouses": [
                    {"name": "Main Warehouse", "code": "MW-001"},
                    {"name": "Distribution Center", "code": "DC-001"},
                ]
            },
            {
                "name": "West Coast Branch",
                "code": "WC",
                "city": "San Francisco",
                "country": "USA",
                "warehouses": [
                    {"name": "West Warehouse", "code": "WW-001"},
                ]
            }
        ]
    },
    {
        "name": "TechStart Inc",
        "code": "TECH",
        "industry": "Technology",
        "is_active": True,
        "branches": [
            {
                "name": "Main Office",
                "code": "MO",
                "city": "Austin",
                "country": "USA",
                "warehouses": []
            }
        ]
    },
    {
        "name": "Global Trading Ltd",
        "code": "GTL",
        "industry": "Retail",
        "is_active": True,
        "branches": [
            {
                "name": "London Office",
                "code": "LDN",
                "city": "London",
                "country": "UK",
                "warehouses": [
                    {"name": "London Warehouse", "code": "LW-001"},
                ]
            },
            {
                "name": "Singapore Office",
                "code": "SGP",
                "city": "Singapore",
                "country": "Singapore",
                "warehouses": [
                    {"name": "Singapore Hub", "code": "SH-001"},
                ]
            }
        ]
    }
]


class CompaniesStructureSeeder(BaseSeeder):
    """Seeder for companies, branches, and warehouses."""
    
    def __init__(
        self,
        session: AsyncSession,
        dry_run: bool = False,
        batch_size: int = 50,
    ):
        """Initialize the companies-structure seeder.
        
        Parameters:
        	session (AsyncSession): Database session used for seeding.
        	dry_run (bool): Whether to simulate seeding without persisting changes.
        	batch_size (int): Maximum number of records processed in one batch.
        """
        super().__init__(session, dry_run, batch_size)
    
    async def get_seed_data(self) -> list[dict[str, Any]]:
        """Return sample companies data."""
        return SAMPLE_COMPANIES
    
    async def seed(self) -> SeederResult:
        """
        Seed companies, branches, and warehouses from the configured hierarchy.
        
        Returns:
            SeederResult containing creation, skip, warning, error, success, and
            duration statistics for the seeding operation.
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
                from app.models import Company, Branch, Warehouse
            except ImportError:
                result.warnings.append(
                    "ERP-BACKEND models not found. Skipping actual seeding."
                )
                return result
            
            companies_data = await self.get_seed_data()
            companies_created = 0
            branches_created = 0
            warehouses_created = 0
            
            for company_data in companies_data:
                try:
                    # Create company
                    company_info = {
                        "name": company_data["name"],
                        "code": company_data["code"],
                        "is_active": company_data.get("is_active", True),
                    }
                    
                    company, is_new = await self.upsert(Company, company_info, "code")
                    
                    if is_new:
                        companies_created += 1
                        self.log_info(f"Created company: {company.name}")
                    else:
                        result.records_skipped += 1
                        self.log_info(f"Company exists: {company.name}")
                    
                    # Create branches
                    for branch_data in company_data.get("branches", []):
                        branch_info = {
                            "company_id": company.id,
                            "name": branch_data["name"],
                            "code": branch_data["code"],
                            "is_active": True,
                        }
                        
                        # Check for existing branch with same company_id and code
                        existing_branch = await self.check_exists_by复合_key(
                            Branch,
                            ["company_id", "code"],
                            branch_info["company_id"],
                            branch_info["code"]
                        )
                        
                        if existing_branch:
                            result.records_skipped += 1
                            branch = existing_branch
                        else:
                            branch = Branch(**branch_info)
                            self.session.add(branch)
                            await self.session.flush()
                            branches_created += 1
                            self.log_info(f"Created branch: {branch.name}")
                        
                        # Create warehouses
                        for warehouse_data in branch_data.get("warehouses", []):
                            warehouse_info = {
                                "branch_id": branch.id,
                                "name": warehouse_data["name"],
                                "code": warehouse_data["code"],
                                "is_active": True,
                            }
                            
                            existing_wh = await self.check_exists_by复合_key(
                                Warehouse,
                                ["branch_id", "code"],
                                warehouse_info["branch_id"],
                                warehouse_info["code"]
                            )
                            
                            if existing_wh:
                                result.records_skipped += 1
                            else:
                                warehouse = Warehouse(**warehouse_info)
                                self.session.add(warehouse)
                                await self.session.flush()
                                warehouses_created += 1
                                self.log_info(f"Created warehouse: {warehouse.name}")
                                
                except Exception as e:
                    result.errors.append(
                        f"Failed to seed company {company_data['name']}: {str(e)}"
                    )
                    if self.seeding_config.stop_on_error:
                        raise
            
            result.records_created = companies_created + branches_created + warehouses_created
            result.success = len(result.errors) == 0
            
            self.log_info(
                f"Seeding complete: {companies_created} companies, "
                f"{branches_created} branches, {warehouses_created} warehouses"
            )
            
        except Exception as e:
            result.success = False
            result.errors.append(f"Seeding failed: {str(e)}")
            logger.exception("Unexpected error during seeding")
        
        result.duration_seconds = time.time() - start_time
        
        return result
    
    async def check_exists_by复合_key(self, model, fields: list[str], *values):
        """
        Find a record matching the specified composite key values.
        
        Parameters:
            model: The model class to query.
            fields (list[str]): Names of the fields that form the composite key.
            *values: Values corresponding to the fields.
        
        Returns:
            The matching record, or `None` if no record matches.
        """
        from sqlalchemy import select, and_
        
        conditions = [getattr(model, field) == value for field, value in zip(fields, values)]
        stmt = select(model).where(and_(*conditions))
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    @property
    def seeding_config(self):
        """Get seeding config."""
        from ..config import SeedingConfig
        return SeedingConfig(stop_on_error=True)
