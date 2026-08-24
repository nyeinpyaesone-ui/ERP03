"""
Integration Adapter Layer for ERP-BACKEND.

This module provides adapters to convert between internal ERP schemas
and the standardized integration contract schemas defined in INTEGRATION/contracts.

This ensures compatible communication between ERP-BACKEND and AI-BACKEND.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
import sys
import os

# Add INTEGRATION directory to path for contract imports
INTEGRATION_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', 'INTEGRATION')
)
if INTEGRATION_PATH not in sys.path:
    sys.path.insert(0, INTEGRATION_PATH)

try:
    from contracts.schemas.crm import (
        CustomerSchema as ContractCustomerSchema,
        CustomerCreateSchema as ContractCustomerCreateSchema,
        CustomerUpdateSchema as ContractCustomerUpdateSchema,
        ContactSchema as ContractContactSchema,
        ContactCreateSchema as ContractContactCreateSchema,
        OpportunitySchema as ContractOpportunitySchema,
        OpportunityCreateSchema as ContractOpportunityCreateSchema,
        OpportunityUpdateSchema as ContractOpportunityUpdateSchema,
    )

    from contracts.schemas.inventory import (
        ProductSchema as ContractProductSchema,
        ProductCreateSchema as ContractProductCreateSchema,
        ProductUpdateSchema as ContractProductUpdateSchema,
        CategorySchema as ContractCategorySchema,
        StockLevelSchema as ContractStockLevelSchema,
    )
    CONTRACTS_AVAILABLE = True
except ImportError:
    # Fallback: define minimal schemas if contracts not available
    class ContractCustomerSchema:
        pass
    class ContractContactSchema:
        pass
    class ContractOpportunitySchema:
        pass
    class ContractProductSchema:
        pass
    class ContractCategorySchema:
        pass
    CONTRACTS_AVAILABLE = False


class CRMAdapter:
    """Adapter for converting between internal CRM models and integration contracts."""
    
    @staticmethod
    def company_to_customer(company: Any) -> ContractCustomerSchema:
        """
        Convert an internal company model to a customer contract schema.

        Parameters:
            company (Any): Company data containing identity, contact, address, and audit fields.

        Returns:
            ContractCustomerSchema: Customer data mapped from the company.
        """
        return ContractCustomerSchema(
            id=company.id,
            name=company.name,
            email=getattr(company, 'email', None),
            phone=company.phone,
            company=company.name,
            address=company.address,
            city=None,  # Extract from address if needed
            state=None,
            country=None,
            postal_code=None,
            status="active",
            notes=getattr(company, 'notes', None),
            created_at=company.created_at,
            updated_at=company.updated_at,
            created_by=getattr(company, 'created_by', None),
            tags=getattr(company, 'tags', [])
        )
    
    @staticmethod
    def contact_to_contract(contact: Any) -> ContractContactSchema:
        """
        Convert an internal contact into the standardized contact contract schema.

        Parameters:
            contact (Any): Internal contact object containing personal, company, and contact details.

        Returns:
            ContractContactSchema: Contact data mapped to the integration contract schema.
        """
        return ContractContactSchema(
            id=contact.id,
            customer_id=contact.company_id if hasattr(contact, 'company_id') else None,
            first_name=contact.first_name,
            last_name=contact.last_name,
            email=contact.email,
            phone=contact.phone,
            position=contact.title,
            is_primary=False,  # Determine based on business logic
            notes=contact.notes,
            created_at=contact.created_at,
            updated_at=contact.updated_at
        )
    
    @staticmethod
    def deal_to_opportunity(deal: Any) -> ContractOpportunitySchema:
        """
        Convert an internal deal into an integration opportunity.

        Parameters:
            deal (Any): Internal deal containing opportunity details and ownership information.

        Returns:
            ContractOpportunitySchema: Opportunity populated from the deal, using USD as the currency and an empty tag list.
        """
        return ContractOpportunitySchema(
            id=deal.id,
            customer_id=deal.company_id if hasattr(deal, 'company_id') else None,
            title=deal.title,
            description=deal.description,
            stage=deal.stage,
            value=deal.value,
            currency="USD",  # Default or get from deal
            probability=deal.probability,
            expected_close_date=deal.expected_close_date,
            actual_close_date=getattr(deal, 'actual_close_date', None),
            owner_id=deal.assigned_to,
            created_at=deal.created_at,
            updated_at=deal.updated_at,
            tags=[]
        )


class InventoryAdapter:
    """Adapter for converting between internal Inventory models and integration contracts."""
    
    @staticmethod
    def product_to_contract(product: Any) -> ContractProductSchema:
        """
        Convert an internal product model into an integration product schema.

        Parameters:
            product (Any): Internal product model containing product identity, pricing, inventory, and status data.

        Returns:
            ContractProductSchema: Product data mapped to the integration contract, with defaults for missing optional attributes.
        """
        return ContractProductSchema(
            id=product.id,
            sku=getattr(product, 'sku', f'PRD-{product.id}'),
            name=product.name,
            description=getattr(product, 'description', None),
            category_id=getattr(product, 'category_id', None),
            unit_price=getattr(product, 'unit_price', 0.0),
            cost_price=getattr(product, 'cost_price', None),
            quantity_on_hand=getattr(product, 'quantity_on_hand', 0),
            quantity_reserved=getattr(product, 'quantity_reserved', 0),
            quantity_available=getattr(product, 'quantity_available', 
                                       getattr(product, 'quantity_on_hand', 0)),
            reorder_point=getattr(product, 'reorder_point', None),
            reorder_quantity=getattr(product, 'reorder_quantity', None),
            unit_of_measure=getattr(product, 'unit_of_measure', 'unit'),
            is_active=getattr(product, 'is_active', True),
            created_at=product.created_at,
            updated_at=getattr(product, 'updated_at', None),
            tags=getattr(product, 'tags', [])
        )
    
    @staticmethod
    def category_to_contract(category: Any) -> ContractCategorySchema:
        """Convert internal Category model to integration CategorySchema."""
        return ContractCategorySchema(
            id=category.id,
            name=category.name,
            parent_id=getattr(category, 'parent_id', None),
            description=getattr(category, 'description', None),
            is_active=getattr(category, 'is_active', True),
            created_at=category.created_at,
            updated_at=getattr(category, 'updated_at', None),
            product_count=getattr(category, 'product_count', 0)
        )
