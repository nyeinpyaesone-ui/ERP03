"""
Double-Entry Accounting Engine
Ensures Assets = Liabilities + Equity
"""
from typing import List, Tuple
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

class DoubleEntryValidator:
    """Validates debits == credits for every transaction"""
    
    @staticmethod
    def validate(lines: List[dict]) -> bool:
        total_debit = sum(line.get('debit', 0) for line in lines)
        total_credit = sum(line.get('credit', 0) for line in lines)
        
        if total_debit != total_credit:
            raise ValueError(f"Unbalanced: Dr={total_debit}, Cr={total_credit}")
        return True

class DepreciationCalculator:
    """Straight-line and declining balance depreciation"""
    
    @staticmethod
    def straight_line(cost: Decimal, salvage: Decimal, life_years: int) -> Decimal:
        """Annual depreciation = (Cost - Salvage) / Life"""
        return ((cost - salvage) / life_years).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def declining_balance(cost: Decimal, rate: float, year: int) -> Decimal:
        """Book Value * Rate"""
        bv = cost
        for _ in range(year):
            bv -= (bv * Decimal(str(rate))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return (bv * Decimal(str(rate))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class TaxWithholdingEngine:
    """Progressive tax calculation"""
    
    BRACKETS_2024 = [
        (Decimal('0'), Decimal('0.10')),
        (Decimal('11000'), Decimal('0.12')),
        (Decimal('44725'), Decimal('0.22')),
        (Decimal('95375'), Decimal('0.24')),
        (Decimal('182050'), Decimal('0.32')),
        (Decimal('231250'), Decimal('0.35')),
        (Decimal('578125'), Decimal('0.37')),
    ]
    
    @classmethod
    def calculate_federal_tax(cls, taxable_income: Decimal) -> Decimal:
        tax = Decimal('0')
        prev_bracket = Decimal('0')
        
        for bracket_min, rate in cls.BRACKETS_2024:
            if taxable_income <= bracket_min:
                break
            
            taxable_in_bracket = min(taxable_income, bracket_min) - prev_bracket
            if taxable_in_bracket > 0:
                tax += taxable_in_bracket * rate
            
            prev_bracket = bracket_min
        
        # Handle top bracket
        if taxable_income > prev_bracket:
            top_rate = cls.BRACKETS_2024[-1][1]
            tax += (taxable_income - prev_bracket) * top_rate
            
        return tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class InventoryCostingEngine:
    """FIFO, LIFO, Weighted Average"""
    
    @staticmethod
    def fifo(layers: List[Tuple[int, Decimal]], qty_sold: int) -> Decimal:
        """First-In First-Out costing"""
        cost = Decimal('0')
        remaining = qty_sold
        
        for qty, unit_cost in layers:
            if remaining <= 0:
                break
            take = min(qty, remaining)
            cost += take * unit_cost
            remaining -= take
        
        return cost.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def weighted_average(total_qty: int, total_cost: Decimal) -> Decimal:
        """Average cost per unit"""
        if total_qty == 0:
            return Decimal('0')
        return (total_cost / total_qty).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class PayrollEngine:
    """Gross-to-Net payroll calculation"""
    
    @staticmethod
    def calculate_net_pay(gross: Decimal, federal_tax: Decimal, state_tax: Decimal, 
                         social_security: Decimal, medicare: Decimal, 
                         benefits: Decimal) -> Decimal:
        """Net = Gross - All Deductions"""
        deductions = federal_tax + state_tax + social_security + medicare + benefits
        return (gross - deductions).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_social_security(gross: Decimal, limit: Decimal = Decimal('168600')) -> Decimal:
        """6.2% up to annual limit"""
        rate = Decimal('0.062')
        if gross >= limit:
            return (limit * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return (gross * rate).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def calculate_medicare(gross: Decimal) -> Decimal:
        """1.45% with no limit"""
        return (gross * Decimal('0.0145')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)

class PipelineAnalyticsEngine:
    """Sales pipeline calculations"""
    
    @staticmethod
    def weighted_value(opportunities: List[dict]) -> Decimal:
        """Sum(Amount * Probability)"""
        total = Decimal('0')
        for opp in opportunities:
            amount = Decimal(str(opp['amount']))
            prob = Decimal(str(opp['probability'])) / 100
            total += amount * prob
        return total.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def conversion_rate(won: int, total: int) -> Decimal:
        if total == 0:
            return Decimal('0')
        return (Decimal(won) / Decimal(total) * 100).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    @staticmethod
    def sales_velocity(opportunities: List[dict]) -> Decimal:
        """(Num Opps * Avg Value * Win Rate) / Sales Cycle Days"""
        if not opportunities:
            return Decimal('0')
        
        num_opps = len(opportunities)
        avg_value = sum(Decimal(str(o['amount'])) for o in opportunities) / num_opps
        win_rate = Decimal(str(sum(1 for o in opportunities if o['status'] == 'won') / num_opps))
        avg_cycle = sum(o.get('cycle_days', 30) for o in opportunities) / num_opps
        
        if avg_cycle == 0:
            return Decimal('0')
            
        velocity = (num_opps * avg_value * win_rate) / avg_cycle
        return velocity.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
