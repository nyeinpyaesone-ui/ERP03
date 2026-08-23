"""
ERP-CORE: Payroll Calculation Engine
Implements complex payroll logic including tax brackets, deductions, and prorations.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional
from datetime import date
from enum import Enum

class PayrollError(Exception):
    pass

class PayPeriod(Enum):
    MONTHLY = "monthly"
    BIWEEKLY = "biweekly"
    WEEKLY = "weekly"

class PayrollEngine:
    """
    Core algorithm for calculating employee net pay.
    Handles gross-to-net calculations, tax withholdings, and deductions.
    """
    
    def __init__(self, tax_brackets: List[Dict], social_security_rate: Decimal):
        self.tax_brackets = sorted(tax_brackets, key=lambda x: x['min_income'])
        self.ss_rate = social_security_rate
        self.precision = 2

    def calculate_gross_pay(
        self, 
        base_salary: Decimal, 
        hours_worked: Decimal, 
        standard_hours: Decimal,
        overtime_rate: Decimal = Decimal('1.5'),
        bonuses: List[Decimal] = None,
        commissions: List[Decimal] = None
    ) -> Decimal:
        """
        Algorithm: Calculates total gross pay including regular, overtime, bonuses, and commissions.
        """
        if hours_worked <= standard_hours:
            regular_pay = base_salary
            overtime_pay = Decimal('0.00')
        else:
            hourly_rate = base_salary / standard_hours
            regular_pay = hourly_rate * standard_hours
            overtime_hours = hours_worked - standard_hours
            overtime_pay = (hourly_rate * overtime_hours * overtime_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        total_bonus = sum(bonuses) if bonuses else Decimal('0.00')
        total_commission = sum(commissions) if commissions else Decimal('0.00')
        
        gross_pay = (regular_pay + overtime_pay + total_bonus + total_commission).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return gross_pay

    def calculate_progressive_tax(self, taxable_income: Decimal, filing_status: str) -> Decimal:
        """
        Algorithm: Applies progressive tax brackets to calculate income tax withholding.
        Only taxes income within each bracket at that bracket's rate.
        """
        total_tax = Decimal('0.00')
        remaining_income = taxable_income
        
        # Filter brackets for filing status
        applicable_brackets = [b for b in self.tax_brackets if b['status'] == filing_status]
        
        for i, bracket in enumerate(applicable_brackets):
            bracket_min = Decimal(str(bracket['min_income']))
            bracket_max = Decimal(str(bracket['max_income'])) if bracket.get('max_income') else Decimal('999999999')
            rate = Decimal(str(bracket['rate']))
            
            if remaining_income <= 0:
                break
                
            # Calculate income within this bracket
            income_in_bracket = min(remaining_income, bracket_max - bracket_min)
            if income_in_bracket > 0:
                tax_for_bracket = (income_in_bracket * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                total_tax += tax_for_bracket
                remaining_income -= income_in_bracket
        
        return total_tax

    def calculate_social_security(self, gross_pay: Decimal, wage_base_limit: Decimal) -> Decimal:
        """
        Algorithm: Calculates Social Security tax with wage base cap.
        """
        if gross_pay > wage_base_limit:
            # Already hit the cap
            return Decimal('0.00')
        
        taxable_amount = min(gross_pay, wage_base_limit - gross_pay)
        if taxable_amount <= 0:
            return Decimal('0.00')
            
        ss_tax = (taxable_amount * self.ss_rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return ss_tax

    def calculate_prorated_salary(
        self, 
        monthly_salary: Decimal, 
        days_in_month: int, 
        days_worked: int,
        unpaid_leave_days: int = 0
    ) -> Decimal:
        """
        Algorithm: Prorates salary based on actual days worked.
        """
        effective_days = days_worked - unpaid_leave_days
        if effective_days < 0:
            raise PayrollError("Unpaid leave days cannot exceed days worked.")
            
        daily_rate = (monthly_salary / Decimal(str(days_in_month))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        prorated_amount = (daily_rate * Decimal(str(effective_days))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return prorated_amount

    def calculate_net_pay(
        self,
        gross_pay: Decimal,
        tax_withholding: Decimal,
        social_security: Decimal,
        medicare: Decimal,
        pre_tax_deductions: List[Decimal] = None,
        post_tax_deductions: List[Decimal] = None
    ) -> Dict[str, Decimal]:
        """
        Algorithm: Final net pay calculation after all deductions.
        Returns breakdown of all components.
        """
        total_pre_tax = sum(pre_tax_deductions) if pre_tax_deductions else Decimal('0.00')
        total_post_tax = sum(post_tax_deductions) if post_tax_deductions else Decimal('0.00')
        
        taxable_income = gross_pay - total_pre_tax
        
        total_deductions = (
            tax_withholding + 
            social_security + 
            medicare + 
            total_pre_tax + 
            total_post_tax
        ).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        net_pay = (gross_pay - total_deductions).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        if net_pay < 0:
            raise PayrollError(f"Net pay cannot be negative. Gross: {gross_pay}, Deductions: {total_deductions}")
        
        return {
            "gross_pay": gross_pay,
            "pre_tax_deductions": total_pre_tax,
            "taxable_income": taxable_income,
            "income_tax": tax_withholding,
            "social_security": social_security,
            "medicare": medicare,
            "post_tax_deductions": total_post_tax,
            "total_deductions": total_deductions,
            "net_pay": net_pay
        }
