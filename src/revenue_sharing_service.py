"""Revenue sharing service for calculating organizer revenue shares based on ticket sales and smart contract rules."""
from typing import List, Dict, Optional, Tuple
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import logging
from src.revenue_sharing_models import (
    Stakeholder, RevenueRule, EventRevenueInput, PayoutDistribution, 
    RevenueCalculationResult, RevenueShareConfig
)
from src.logging_config import log_info, log_error


class RevenueSharingService:
    """Service to calculate revenue shares based on smart contract rules."""
    
    def __init__(self, config: Optional[RevenueShareConfig] = None):
        self.config = config or RevenueShareConfig()
        self.logger = logging.getLogger("veritix.revenue_sharing")
    
    def calculate_revenue_shares(self, input_data: EventRevenueInput) -> RevenueCalculationResult:
        """
        Calculate revenue shares for stakeholders based on event sales and smart contract rules.
        
        Args:
            input_data: Input containing event ID, total sales, and other parameters
            
        Returns:
            RevenueCalculationResult with detailed distribution breakdown
        """
        log_info("Starting revenue share calculation", {
            "event_id": input_data.event_id,
            "total_sales": input_data.total_sales,
            "ticket_count": input_data.ticket_count
        })
        
        # Start with gross sales
        gross_sales = input_data.total_sales
        net_revenue = gross_sales
        
        # Calculate fees based on configuration
        fees = self._calculate_fees(input_data, gross_sales)
        total_fees = sum(fees.values())
        
        # Calculate net revenue after fees
        if input_data.net_revenue:
            net_revenue = gross_sales - total_fees
        
        # Get stakeholders for this event (in a real implementation, this would come from DB)
        stakeholders = self._get_default_stakeholders(input_data.event_id)
        
        # Apply custom rules if provided
        rules = input_data.custom_rules or self._get_default_rules()
        
        # Calculate distributions
        distributions, remaining_balance = self._calculate_distributions(
            net_revenue, stakeholders, rules
        )
        
        # Calculate total paid out
        total_paid_out = sum(dist.net_amount for dist in distributions)
        
        result = RevenueCalculationResult(
            event_id=input_data.event_id,
            total_gross_sales=gross_sales,
            total_fees=total_fees,
            net_revenue=net_revenue,
            distributions=distributions,
            total_paid_out=total_paid_out,
            remaining_balance=remaining_balance,
            calculation_timestamp=datetime.utcnow(),
            rules_applied=[rule.id for rule in rules]
        )
        
        log_info("Revenue share calculation completed", {
            "event_id": input_data.event_id,
            "gross_sales": gross_sales,
            "net_revenue": net_revenue,
            "total_fees": total_fees,
            "total_paid_out": total_paid_out,
            "stakeholder_count": len(distributions)
        })
        
        return result
    
    def _calculate_fees(self, input_data: EventRevenueInput, gross_sales: float) -> Dict[str, float]:
        """Calculate various fees that need to be deducted."""
        fees = {}
        
        # Processing fees (percentage + fixed)
        processing_percentage = (gross_sales * self.config.processing_fee_rate) / 100
        processing_fixed = input_data.ticket_count * self.config.processing_fixed_fee
        fees["processing"] = processing_percentage + processing_fixed
        
        # Platform fee
        fees["platform"] = (gross_sales * self.config.default_platform_fee) / 100
        
        # Additional fees from input
        if input_data.additional_fees:
            for fee_name, fee_amount in input_data.additional_fees.items():
                fees[fee_name] = fee_amount
        
        return fees
    
    def _get_default_stakeholders(self, event_id: str) -> List[Stakeholder]:
        """Get default stakeholders for an event."""
        return [
            Stakeholder(
                id=f"organizer_{event_id}",
                name="Event Organizer",
                role="organizer",
                percentage=self.config.default_organizer_share
            ),
            Stakeholder(
                id=f"platform_{event_id}",
                name="Platform",
                role="platform",
                percentage=self.config.default_platform_fee
            ),
            Stakeholder(
                id=f"venue_{event_id}",
                name="Venue",
                role="venue",
                percentage=self.config.default_venue_fee
            )
        ]
    
    def _get_default_rules(self) -> List[RevenueRule]:
        """Get default revenue sharing rules."""
        return [
            RevenueRule(
                id="platform_fee_rule",
                name="Platform Fee",
                description="Standard platform commission fee",
                condition="default",
                priority=1,
                percentage=self.config.default_platform_fee
            ),
            RevenueRule(
                id="organizer_share_rule",
                name="Organizer Share",
                description="Standard organizer revenue share",
                condition="default",
                priority=2,
                percentage=self.config.default_organizer_share
            ),
            RevenueRule(
                id="venue_fee_rule",
                name="Venue Fee",
                description="Standard venue commission fee",
                condition="default",
                priority=3,
                percentage=self.config.default_venue_fee
            )
        ]
    
    def _calculate_distributions(
        self, 
        net_revenue: float, 
        stakeholders: List[Stakeholder], 
        rules: List[RevenueRule]
    ) -> Tuple[List[PayoutDistribution], float]:
        """Calculate the distribution of net revenue to stakeholders."""
        distributions = []
        remaining_balance = net_revenue
        applied_rules = set()
        
        # Sort stakeholders by priority based on rules
        sorted_stakeholders = self._sort_stakeholders_by_rules(stakeholders, rules)
        
        for stakeholder in sorted_stakeholders:
            # Find applicable rule for this stakeholder
            rule = self._find_rule_for_stakeholder(stakeholder, rules)
            
            if rule:
                applied_rules.add(rule.id)
                
                # Calculate gross amount based on percentage
                gross_amount = (net_revenue * rule.percentage) / 100
                
                # Apply constraints
                if stakeholder.min_amount and gross_amount < stakeholder.min_amount:
                    gross_amount = stakeholder.min_amount
                elif stakeholder.max_amount and gross_amount > stakeholder.max_amount:
                    gross_amount = stakeholder.max_amount
                
                # Calculate fees for this stakeholder (if any)
                fee_deductions = {}
                if gross_amount > remaining_balance:
                    gross_amount = remaining_balance
                
                # Create distribution
                distribution = PayoutDistribution(
                    stakeholder_id=stakeholder.id,
                    stakeholder_name=stakeholder.name,
                    role=stakeholder.role,
                    gross_amount=round(gross_amount, 2),
                    fee_deductions=fee_deductions,
                    net_amount=round(gross_amount, 2),  # For simplicity, net = gross in this example
                    percentage_applied=rule.percentage,
                    rule_used=rule.id
                )
                
                distributions.append(distribution)
                remaining_balance -= gross_amount
        
        # Handle rounding differences
        total_distributed = sum(dist.net_amount for dist in distributions)
        actual_remaining = net_revenue - total_distributed
        
        # Adjust the largest distribution to account for rounding differences
        if distributions and abs(actual_remaining) > 0.01:  # More than 1 cent difference
            largest_dist = max(distributions, key=lambda x: x.net_amount)
            adjustment = round(actual_remaining, 2)
            original_net = largest_dist.net_amount
            largest_dist.net_amount = round(largest_dist.net_amount + adjustment, 2)
            actual_remaining = net_revenue - sum(dist.net_amount for dist in distributions)
        
        return distributions, actual_remaining
    
    def _sort_stakeholders_by_rules(self, stakeholders: List[Stakeholder], rules: List[RevenueRule]) -> List[Stakeholder]:
        """Sort stakeholders based on rule priorities."""
        # Create a mapping of role to priority from rules
        priority_map = {rule.id: rule.priority for rule in rules}
        
        # Sort stakeholders based on their role's priority
        def get_priority(stakeholder: Stakeholder) -> int:
            # Find the rule that applies to this stakeholder's role
            for rule in rules:
                if stakeholder.role in rule.applies_to or stakeholder.role.lower() in rule.name.lower().replace(" ", "").lower():
                    return rule.priority
            return 999  # Lowest priority for unknown roles
        
        return sorted(stakeholders, key=get_priority)
    
    def _find_rule_for_stakeholder(self, stakeholder: Stakeholder, rules: List[RevenueRule]) -> Optional[RevenueRule]:
        """Find the appropriate rule for a stakeholder."""
        for rule in rules:
            # Check if rule applies to this stakeholder's role
            if (stakeholder.role in rule.applies_to or 
                stakeholder.role.lower() in rule.name.lower().replace(" ", "").lower() or
                not rule.applies_to):  # If rule applies to all
                return rule
        return None
    
    def validate_input(self, input_data: EventRevenueInput) -> Tuple[bool, List[str]]:
        """Validate input data."""
        errors = []
        
        if input_data.total_sales <= 0:
            errors.append("Total sales must be greater than zero")
        
        if input_data.ticket_count <= 0:
            errors.append("Ticket count must be greater than zero")
        
        if input_data.total_sales < input_data.ticket_count:
            errors.append("Total sales should be at least equal to ticket count (minimum $1 per ticket)")
        
        # Check if percentages exceed maximum allowed
        if input_data.custom_rules:
            total_percentage = sum(rule.percentage for rule in input_data.custom_rules)
            if total_percentage > self.config.maximum_payout_percentage:
                errors.append(f"Total percentage allocation ({total_percentage}%) exceeds maximum allowed ({self.config.maximum_payout_percentage}%)")
        
        return len(errors) == 0, errors


# Global instance
revenue_sharing_service = RevenueSharingService()