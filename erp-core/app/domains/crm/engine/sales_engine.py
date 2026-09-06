"""
ERP-CORE: Sales Pipeline & Lead Scoring Engine
Implements probabilistic sales forecasting and lead qualification algorithms.
Handles deal stage progression, conversion rates, and revenue recognition.
"""
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
import math

class CRMError(Exception):
    pass

class DealStage(Enum):
    PROSPECTING = "prospecting"
    QUALIFICATION = "qualification"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"

class LeadScoreTier(Enum):
    HOT = "hot"
    WARM = "warm"
    COLD = "cold"
    UNQUALIFIED = "unqualified"

class CRMEngine:
    """
    Core algorithm for CRM operations.
    Handles lead scoring, pipeline forecasting, and conversion analytics.
    """
    
    def __init__(self, stage_probabilities: Dict[str, Decimal]):
        """
        Initialize with historical stage-to-close probabilities.
        Example: {"prospecting": 0.1, "qualification": 0.3, "proposal": 0.6, "negotiation": 0.8}
        """
        self.stage_probabilities = {k: Decimal(str(v)) for k, v in stage_probabilities.items()}
        self.precision = 2

    def calculate_lead_score(
        self,
        demographic_factors: Dict[str, int],
        behavioral_factors: Dict[str, int],
        engagement_recency_days: int,
        max_score: int = 100
    ) -> Tuple[int, LeadScoreTier]:
        """
        Algorithm: Calculates lead score based on demographic fit and behavioral engagement.
        Applies recency decay to engagement scores.
        Returns (score, tier).
        """
        # Demographic scoring (max 50 points)
        demo_score = min(sum(demographic_factors.values()), 50)
        
        # Behavioral scoring with recency decay (max 50 points)
        raw_behavioral = sum(behavioral_factors.values())
        
        # Decay factor: older engagement counts less
        # Half-life of 7 days
        decay_factor = Decimal(str(math.exp(-0.693 * engagement_recency_days / 7)))
        behavioral_score = int(Decimal(str(raw_behavioral)) * decay_factor)
        behavioral_score = min(behavioral_score, 50)
        
        total_score = demo_score + behavioral_score
        total_score = min(total_score, max_score)
        
        # Determine tier
        if total_score >= 80:
            tier = LeadScoreTier.HOT
        elif total_score >= 60:
            tier = LeadScoreTier.WARM
        elif total_score >= 40:
            tier = LeadScoreTier.COLD
        else:
            tier = LeadScoreTier.UNQUALIFIED
        
        return total_score, tier

    def calculate_weighted_pipeline_value(
        self,
        deals: List[Dict]
    ) -> Decimal:
        """
        Algorithm: Calculates expected revenue based on deal stage probabilities.
        Weighted Value = Deal Amount × Stage Probability
        """
        total_weighted = Decimal('0.00')
        
        for deal in deals:
            if deal['stage'] in [DealStage.CLOSED_LOST.value, DealStage.CLOSED_WON.value]:
                continue  # Exclude closed deals from pipeline forecast
            
            amount = Decimal(str(deal['amount']))
            stage = deal['stage']
            probability = self.stage_probabilities.get(stage, Decimal('0.0'))
            
            weighted_value = (amount * probability).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
            total_weighted += weighted_value
        
        return total_weighted

    def calculate_conversion_rate(
        self,
        deals_in_stage: int,
        deals_converted: int,
        time_period_days: int = None
    ) -> Decimal:
        """
        Algorithm: Calculates conversion rate from a specific stage.
        Conversion Rate = Converted / Total in Stage
        """
        if deals_in_stage == 0:
            return Decimal('0.00')
        
        rate = (Decimal(str(deals_converted)) / Decimal(str(deals_in_stage)) * Decimal('100')).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return rate

    def forecast_close_date(
        self,
        current_stage: str,
        entry_date: datetime,
        historical_stage_durations: Dict[str, int]
    ) -> datetime:
        """
        Algorithm: Predicts close date based on average time spent in each stage.
        Sums remaining stage durations from current stage to close.
        """
        stage_order = [
            DealStage.PROSPECTING.value,
            DealStage.QUALIFICATION.value,
            DealStage.PROPOSAL.value,
            DealStage.NEGOTIATION.value
        ]
        
        if current_stage not in stage_order:
            raise CRMError(f"Invalid stage: {current_stage}")
        
        current_index = stage_order.index(current_stage)
        remaining_stages = stage_order[current_index:]
        
        total_remaining_days = 0
        for stage in remaining_stages:
            avg_duration = historical_stage_durations.get(stage, 7)  # Default 7 days
            total_remaining_days += avg_duration
        
        predicted_close = entry_date + timedelta(days=total_remaining_days)
        return predicted_close

    def calculate_sales_velocity(
        self,
        num_opportunities: int,
        average_deal_value: Decimal,
        win_rate_percentage: Decimal,
        sales_cycle_days: int
    ) -> Decimal:
        """
        Algorithm: Sales Velocity measures how quickly deals move through pipeline.
        Velocity = (Opportunities × Avg Value × Win Rate) / Cycle Length
        """
        if sales_cycle_days <= 0:
            raise CRMError("Sales cycle must be positive.")
        
        win_rate = win_rate_percentage / Decimal('100')
        
        numerator = Decimal(str(num_opportunities)) * average_deal_value * win_rate
        velocity = (numerator / Decimal(str(sales_cycle_days))).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        return velocity

    def analyze_pipeline_health(
        self,
        deals: List[Dict],
        target_revenue: Decimal
    ) -> Dict[str, any]:
        """
        Algorithm: Comprehensive pipeline health analysis.
        Returns coverage ratio, gaps, and recommendations.
        """
        total_pipeline = self.calculate_weighted_pipeline_value(deals)
        
        # Coverage Ratio = Pipeline / Target
        if target_revenue == 0:
            coverage_ratio = Decimal('0.00')
        else:
            coverage_ratio = (total_pipeline / target_revenue).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        # Gap Analysis
        gap = target_revenue - total_pipeline
        
        # Stage Distribution
        stage_counts = {}
        stage_values = {}
        for deal in deals:
            stage = deal['stage']
            stage_counts[stage] = stage_counts.get(stage, 0) + 1
            stage_values[stage] = stage_values.get(stage, Decimal('0.00')) + Decimal(str(deal['amount']))
        
        # Health Status
        if coverage_ratio >= Decimal('3.0'):
            health_status = "excellent"
        elif coverage_ratio >= Decimal('2.0'):
            health_status = "good"
        elif coverage_ratio >= Decimal('1.0'):
            health_status = "at_risk"
        else:
            health_status = "critical"
        
        return {
            "total_pipeline_value": total_pipeline,
            "target_revenue": target_revenue,
            "coverage_ratio": coverage_ratio,
            "revenue_gap": gap.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP),
            "health_status": health_status,
            "stage_distribution": {
                "counts": stage_counts,
                "values": {k: v.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP) for k, v in stage_values.items()}
            },
            "deal_count": len(deals)
        }

    def calculate_customer_lifetime_value(
        self,
        average_purchase_value: Decimal,
        purchase_frequency_per_year: int,
        customer_lifespan_years: int,
        profit_margin_percentage: Decimal
    ) -> Decimal:
        """
        Algorithm: CLV = (Avg Purchase Value × Frequency × Lifespan) × Profit Margin
        """
        gross_revenue = average_purchase_value * Decimal(str(purchase_frequency_per_year)) * Decimal(str(customer_lifespan_years))
        profit_margin = profit_margin_percentage / Decimal('100')
        
        clv = (gross_revenue * profit_margin).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        return clv
