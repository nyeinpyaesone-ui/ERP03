"""Initial seed data for ERP-CORE system"""
from datetime import datetime
from decimal import Decimal

# Identity & Access Management Seeds
ROLES = [
    {"name": "superadmin", "description": "System administrator with full access"},
    {"name": "admin", "description": "Administrator with management access"},
    {"name": "manager", "description": "Department manager"},
    {"name": "user", "description": "Standard user"},
    {"name": "viewer", "description": "Read-only access"},
]

PERMISSIONS = [
    # User Management
    {"name": "users_create", "resource": "users", "action": "create", "description": "Create new users"},
    {"name": "users_read", "resource": "users", "action": "read", "description": "View user details"},
    {"name": "users_update", "resource": "users", "action": "update", "description": "Update user information"},
    {"name": "users_delete", "resource": "users", "action": "delete", "description": "Delete users"},
    
    # Role Management
    {"name": "roles_create", "resource": "roles", "action": "create", "description": "Create new roles"},
    {"name": "roles_read", "resource": "roles", "action": "read", "description": "View roles"},
    {"name": "roles_update", "resource": "roles", "action": "update", "description": "Update roles"},
    {"name": "roles_delete", "resource": "roles", "action": "delete", "description": "Delete roles"},
    
    # Finance
    {"name": "finance_accounts_create", "resource": "finance_accounts", "action": "create", "description": "Create chart of accounts"},
    {"name": "finance_accounts_read", "resource": "finance_accounts", "action": "read", "description": "View accounts"},
    {"name": "finance_journal_create", "resource": "finance_journal", "action": "create", "description": "Create journal entries"},
    {"name": "finance_journal_read", "resource": "finance_journal", "action": "read", "description": "View journal entries"},
    {"name": "finance_invoice_create", "resource": "finance_invoice", "action": "create", "description": "Create invoices"},
    {"name": "finance_invoice_read", "resource": "finance_invoice", "action": "read", "description": "View invoices"},
    {"name": "finance_payment_create", "resource": "finance_payment", "action": "create", "description": "Record payments"},
]

# Default role-permission mappings
ROLE_PERMISSIONS = {
    "superadmin": ["all"],  # All permissions
    "admin": [p["name"] for p in PERMISSIONS if not p["name"].startswith("users_delete")],
    "manager": [p["name"] for p in PERMISSIONS if p["action"] in ["read", "create", "update"]],
    "user": [p["name"] for p in PERMISSIONS if p["action"] == "read"],
    "viewer": [p["name"] for p in PERMISSIONS if p["action"] == "read" and "invoice" in p["resource"] or "account" in p["resource"]],
}

# Finance - Chart of Accounts Seeds
CHART_OF_ACCOUNTS = [
    # Assets (1000-1999)
    {"code": "1000", "name": "Assets", "account_type": "ASSET"},
    {"code": "1100", "name": "Current Assets", "account_type": "ASSET", "parent_code": "1000"},
    {"code": "1110", "name": "Cash", "account_type": "ASSET", "parent_code": "1100"},
    {"code": "1120", "name": "Bank Account", "account_type": "ASSET", "parent_code": "1100"},
    {"code": "1130", "name": "Accounts Receivable", "account_type": "ASSET", "parent_code": "1100"},
    {"code": "1200", "name": "Inventory", "account_type": "ASSET", "parent_code": "1100"},
    {"code": "1500", "name": "Fixed Assets", "account_type": "ASSET", "parent_code": "1000"},
    {"code": "1510", "name": "Equipment", "account_type": "ASSET", "parent_code": "1500"},
    {"code": "1520", "name": "Buildings", "account_type": "ASSET", "parent_code": "1500"},
    
    # Liabilities (2000-2999)
    {"code": "2000", "name": "Liabilities", "account_type": "LIABILITY"},
    {"code": "2100", "name": "Current Liabilities", "account_type": "LIABILITY", "parent_code": "2000"},
    {"code": "2110", "name": "Accounts Payable", "account_type": "LIABILITY", "parent_code": "2100"},
    {"code": "2120", "name": "Accrued Expenses", "account_type": "LIABILITY", "parent_code": "2100"},
    {"code": "2200", "name": "Long-term Liabilities", "account_type": "LIABILITY", "parent_code": "2000"},
    {"code": "2210", "name": "Bank Loans", "account_type": "LIABILITY", "parent_code": "2200"},
    
    # Equity (3000-3999)
    {"code": "3000", "name": "Equity", "account_type": "EQUITY"},
    {"code": "3100", "name": "Owner's Equity", "account_type": "EQUITY", "parent_code": "3000"},
    {"code": "3200", "name": "Retained Earnings", "account_type": "EQUITY", "parent_code": "3000"},
    
    # Revenue (4000-4999)
    {"code": "4000", "name": "Revenue", "account_type": "REVENUE"},
    {"code": "4100", "name": "Sales Revenue", "account_type": "REVENUE", "parent_code": "4000"},
    {"code": "4200", "name": "Service Revenue", "account_type": "REVENUE", "parent_code": "4000"},
    
    # Expenses (5000-5999)
    {"code": "5000", "name": "Expenses", "account_type": "EXPENSE"},
    {"code": "5100", "name": "Cost of Goods Sold", "account_type": "EXPENSE", "parent_code": "5000"},
    {"code": "5200", "name": "Operating Expenses", "account_type": "EXPENSE", "parent_code": "5000"},
    {"code": "5210", "name": "Salaries Expense", "account_type": "EXPENSE", "parent_code": "5200"},
    {"code": "5220", "name": "Rent Expense", "account_type": "EXPENSE", "parent_code": "5200"},
    {"code": "5230", "name": "Utilities Expense", "account_type": "EXPENSE", "parent_code": "5200"},
]

def get_seed_data():
    return {
        "roles": ROLES,
        "permissions": PERMISSIONS,
        "role_permissions": ROLE_PERMISSIONS,
        "chart_of_accounts": CHART_OF_ACCOUNTS,
    }
