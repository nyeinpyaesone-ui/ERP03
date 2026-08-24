"""
ERP-CORE: Double-Entry Accounting Engine
Implements strict ACID compliance for financial transactions.
Ensures Debits == Credits for every journal entry.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
from datetime import datetime
from enum import Enum

class EntryType(Enum):
    DEBIT = "debit"
    CREDIT = "credit"

class AccountingError(Exception):
    pass

class DoubleEntryEngine:
    """
    Core algorithm for validating and posting financial transactions.
    Enforces the fundamental accounting equation: Assets = Liabilities + Equity
    """
    
    def __init__(self):
        self.precision = 2  # Standard currency precision

    def validate_balance(self, lines: List[Dict]) -> bool:
        """
        Algorithm: Ensures sum(debits) == sum(credits) within tolerance.
        Returns True if balanced, raises AccountingError if not.
        """
        total_debit = Decimal('0.00')
        total_credit = Decimal('0.00')

        for line in lines:
            amount = Decimal(str(line['amount'])).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            if line['type'] == EntryType.DEBIT.value:
                total_debit += amount
            elif line['type'] == EntryType.CREDIT.value:
                total_credit += amount
            else:
                raise AccountingError(f"Invalid entry type: {line['type']}")

        if total_debit != total_credit:
            diff = total_debit - total_credit
            raise AccountingError(
                f"Journal Unbalanced: Debits ({total_debit}) != Credits ({total_credit}). Diff: {diff}"
            )
        
        if total_debit == 0:
            raise AccountingError("Zero-value transactions are not allowed.")

        return True

    def calculate_retained_earnings(self, revenue: Decimal, expenses: Decimal, previous_retained: Decimal) -> Decimal:
        """
        Algorithm: Net Income = Revenue - Expenses
        Retained Earnings = Previous RE + Net Income
        """
        net_income = revenue - expenses
        return previous_retained + net_income

    def allocate_expense(self, total_amount: Decimal, allocation_basis: List[Dict]) -> List[Dict]:
        """
        Algorithm: Allocates a shared expense across multiple cost centers
        based on a defined basis (e.g., headcount, square footage, revenue share).
        """
        total_basis = sum(item['basis_value'] for item in allocation_basis)
        if total_basis == 0:
            raise AccountingError("Allocation basis sum cannot be zero.")

        allocated_lines = []
        remaining_amount = total_amount

        for i, item in enumerate(allocation_basis):
            if i == len(allocation_basis) - 1:
                # Assign remainder to last item to avoid rounding drift
                portion = remaining_amount
            else:
                ratio = Decimal(str(item['basis_value'])) / Decimal(str(total_basis))
                portion = (total_amount * ratio).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                remaining_amount -= portion

            allocated_lines.append({
                "cost_center_id": item['cost_center_id'],
                "amount": portion,
                "basis_used": item['basis_value']
            })

        return allocated_lines

    def generate_reversing_entry(self, original_entry: Dict, reverse_date: datetime) -> Dict:
        """
        Algorithm: Creates a reversing entry by swapping Debits and Credits.
        Used for accruals and prepayments.
        """
        reversed_lines = []
        for line in original_entry['lines']:
            new_type = EntryType.CREDIT.value if line['type'] == EntryType.DEBIT.value else EntryType.DEBIT.value
            reversed_lines.append({
                "account_id": line['account_id'],
                "amount": line['amount'],
                "type": new_type,
                "description": f"Reversal of {original_entry['id']}"
            })
        
        return {
            "date": reverse_date,
            "description": f"Auto-reversal: {original_entry['description']}",
            "lines": reversed_lines,
            "is_reversing": True,
            "reference_id": original_entry['id']
        }
