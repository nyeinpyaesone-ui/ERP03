"""
ERP-CORE Engine Layer
Contains calculation algorithms and business logic engines for all domains.
"""

__all__ = [
    # Finance
    "DoubleEntryEngine",
    "AccountingError",
    "EntryType",
    
    # HRM
    "PayrollEngine",
    "PayrollError",
    "PayPeriod",
    
    # Supply Chain
    "InventoryEngine",
    "InventoryError",
    "CostingMethod",
    "StockMovementType",
    
    # CRM
    "CRMEngine",
    "CRMError",
    "DealStage",
    "LeadScoreTier"
]

# Lazy imports to avoid circular dependencies
def __getattr__(name):
    if name == "DoubleEntryEngine":
        from .finance.engine.accounting_engine import DoubleEntryEngine
        return DoubleEntryEngine
    elif name == "AccountingError":
        from .finance.engine.accounting_engine import AccountingError
        return AccountingError
    elif name == "EntryType":
        from .finance.engine.accounting_engine import EntryType
        return EntryType
    elif name == "PayrollEngine":
        from .hrm.engine.payroll_engine import PayrollEngine
        return PayrollEngine
    elif name == "PayrollError":
        from .hrm.engine.payroll_engine import PayrollError
        return PayrollError
    elif name == "PayPeriod":
        from .hrm.engine.payroll_engine import PayPeriod
        return PayPeriod
    elif name == "InventoryEngine":
        from .supply_chain.engine.inventory_engine import InventoryEngine
        return InventoryEngine
    elif name == "InventoryError":
        from .supply_chain.engine.inventory_engine import InventoryError
        return InventoryError
    elif name == "CostingMethod":
        from .supply_chain.engine.inventory_engine import CostingMethod
        return CostingMethod
    elif name == "StockMovementType":
        from .supply_chain.engine.inventory_engine import StockMovementType
        return StockMovementType
    elif name == "CRMEngine":
        from .crm.engine.sales_engine import CRMEngine
        return CRMEngine
    elif name == "CRMError":
        from .crm.engine.sales_engine import CRMError
        return CRMError
    elif name == "DealStage":
        from .crm.engine.sales_engine import DealStage
        return DealStage
    elif name == "LeadScoreTier":
        from .crm.engine.sales_engine import LeadScoreTier
        return LeadScoreTier
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
