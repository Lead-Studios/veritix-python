"""Tests for revenue sharing service."""
import pytest
from datetime import datetime
from src.revenue_sharing_service import RevenueSharingService
from src.revenue_sharing_models import (
    EventRevenueInput, Stakeholder, RevenueRule, 
    RevenueShareConfig
)


class TestRevenueSharingService:
    """Test the revenue sharing service."""
    
    def test_calculate_revenue_shares_basic(self):
        """Test basic revenue share calculation."""
        service = RevenueSharingService()
        
        input_data = EventRevenueInput(
            event_id="test_event_123",
            total_sales=10000.0,
            ticket_count=100
        )
        
        result = service.calculate_revenue_shares(input_data)
        
        # Check that the result is properly formed
        assert result.event_id == "test_event_123"
        assert result.total_gross_sales == 10000.0
        assert result.net_revenue >= 0
        assert len(result.distributions) > 0
        assert result.calculation_timestamp <= datetime.utcnow()
        
        # Verify that total distributions are reasonable
        total_paid = sum(dist.net_amount for dist in result.distributions)
        assert total_paid <= result.net_revenue
    
    def test_calculate_revenue_shares_with_custom_rules(self):
        """Test revenue calculation with custom rules."""
        service = RevenueSharingService()
        
        custom_rules = [
            RevenueRule(
                id="custom_organizer",
                name="Custom Organizer Share",
                description="Higher organizer share for premium events",
                condition="premium",
                priority=1,
                percentage=85.0,
                applies_to=["organizer"]
            ),
            RevenueRule(
                id="custom_platform",
                name="Custom Platform Fee",
                description="Reduced platform fee for premium events",
                condition="premium",
                priority=2,
                percentage=3.0,
                applies_to=["platform"]
            )
        ]
        
        input_data = EventRevenueInput(
            event_id="premium_event_456",
            total_sales=15000.0,
            ticket_count=150,
            custom_rules=custom_rules
        )
        
        result = service.calculate_revenue_shares(input_data)
        
        # Check that custom rules were applied
        assert "custom_organizer" in result.rules_applied
        assert "custom_platform" in result.rules_applied
        
        # Find the organizer distribution
        organizer_dist = next((dist for dist in result.distributions if dist.role == "organizer"), None)
        assert organizer_dist is not None
        assert organizer_dist.percentage_applied == 85.0  # From custom rule
    
    def test_calculate_revenue_shares_with_additional_fees(self):
        """Test revenue calculation with additional fees."""
        service = RevenueSharingService()
        
        input_data = EventRevenueInput(
            event_id="fee_event_789",
            total_sales=5000.0,
            ticket_count=50,
            additional_fees={"marketing_fee": 200.0, "service_fee": 100.0}
        )
        
        result = service.calculate_revenue_shares(input_data)
        
        # Verify that additional fees were included in total fees
        assert result.total_fees["marketing_fee"] == 200.0
        assert result.total_fees["service_fee"] == 100.0
    
    def test_validate_input_success(self):
        """Test successful input validation."""
        service = RevenueSharingService()
        
        input_data = EventRevenueInput(
            event_id="valid_event",
            total_sales=1000.0,
            ticket_count=10
        )
        
        is_valid, errors = service.validate_input(input_data)
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_input_negative_sales(self):
        """Test input validation with negative sales."""
        service = RevenueSharingService()
        
        input_data = EventRevenueInput(
            event_id="invalid_event",
            total_sales=-100.0,  # Negative sales
            ticket_count=10
        )
        
        is_valid, errors = service.validate_input(input_data)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Total sales must be greater than zero" in errors
    
    def test_validate_input_zero_ticket_count(self):
        """Test input validation with zero ticket count."""
        service = RevenueSharingService()
        
        input_data = EventRevenueInput(
            event_id="invalid_event",
            total_sales=1000.0,
            ticket_count=0  # Zero tickets
        )
        
        is_valid, errors = service.validate_input(input_data)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Ticket count must be greater than zero" in errors
    
    def test_validate_input_percentage_exceeds_limit(self):
        """Test input validation when percentages exceed limit."""
        service = RevenueSharingService()
        
        custom_rules = [
            RevenueRule(
                id="rule1",
                name="Rule 1",
                description="First rule",
                condition="test",
                priority=1,
                percentage=60.0  # 60%
            ),
            RevenueRule(
                id="rule2",
                name="Rule 2", 
                description="Second rule",
                condition="test",
                priority=2,
                percentage=50.0  # 50% - total would be 110%
            )
        ]
        
        input_data = EventRevenueInput(
            event_id="high_percent_event",
            total_sales=1000.0,
            ticket_count=10,
            custom_rules=custom_rules
        )
        
        is_valid, errors = service.validate_input(input_data)
        
        assert is_valid is False
        assert len(errors) > 0
        assert "Total percentage allocation (110.0%) exceeds maximum allowed (100.0%)" in errors
    
    def test_configure_custom_settings(self):
        """Test service with custom configuration."""
        custom_config = RevenueShareConfig(
            default_platform_fee=3.0,
            default_organizer_share=85.0,
            default_venue_fee=7.0,
            processing_fee_rate=2.5,
            minimum_payout_amount=5.0
        )
        
        service = RevenueSharingService(config=custom_config)
        
        input_data = EventRevenueInput(
            event_id="custom_config_event",
            total_sales=2000.0,
            ticket_count=20
        )
        
        result = service.calculate_revenue_shares(input_data)
        
        # Verify the configuration was used
        assert service.config.default_platform_fee == 3.0
        assert service.config.default_organizer_share == 85.0
    
    def test_edge_case_low_revenue(self):
        """Test edge case with very low revenue."""
        service = RevenueSharingService()
        
        input_data = EventRevenueInput(
            event_id="low_revenue_event",
            total_sales=50.0,  # Very low revenue
            ticket_count=2
        )
        
        result = service.calculate_revenue_shares(input_data)
        
        # Should still produce valid results
        assert result.event_id == "low_revenue_event"
        assert result.total_gross_sales == 50.0
        assert len(result.distributions) > 0
    
    def test_edge_case_single_ticket(self):
        """Test edge case with single ticket."""
        service = RevenueSharingService()
        
        input_data = EventRevenueInput(
            event_id="single_ticket_event",
            total_sales=100.0,
            ticket_count=1  # Only one ticket
        )
        
        result = service.calculate_revenue_shares(input_data)
        
        # Should still produce valid results
        assert result.event_id == "single_ticket_event"
        assert result.ticket_count == 1
        assert len(result.distributions) > 0


def test_stakeholder_model():
    """Test Stakeholder Pydantic model."""
    stakeholder = Stakeholder(
        id="org_123",
        name="Test Organizer",
        role="organizer",
        percentage=80.0,
        fixed_amount=100.0,
        min_amount=50.0,
        max_amount=500.0,
        payment_address="0x1234567890abcdef"
    )
    
    assert stakeholder.id == "org_123"
    assert stakeholder.name == "Test Organizer"
    assert stakeholder.role == "organizer"
    assert stakeholder.percentage == 80.0
    assert stakeholder.fixed_amount == 100.0
    assert stakeholder.min_amount == 50.0
    assert stakeholder.max_amount == 500.0
    assert stakeholder.payment_address == "0x1234567890abcdef"


def test_revenue_rule_model():
    """Test RevenueRule Pydantic model."""
    rule = RevenueRule(
        id="rule_1",
        name="Test Rule",
        description="A test revenue rule",
        condition="test_condition",
        priority=1,
        percentage=10.0,
        min_threshold=100.0,
        max_threshold=10000.0,
        applies_to=["organizer", "venue"]
    )
    
    assert rule.id == "rule_1"
    assert rule.name == "Test Rule"
    assert rule.description == "A test revenue rule"
    assert rule.condition == "test_condition"
    assert rule.priority == 1
    assert rule.percentage == 10.0
    assert rule.min_threshold == 100.0
    assert rule.max_threshold == 10000.0
    assert rule.applies_to == ["organizer", "venue"]


def test_event_revenue_input_model():
    """Test EventRevenueInput Pydantic model."""
    input_data = EventRevenueInput(
        event_id="event_abc",
        total_sales=1000.0,
        ticket_count=10,
        currency="EUR",
        additional_fees={"service": 50.0},
        net_revenue=False
    )
    
    assert input_data.event_id == "event_abc"
    assert input_data.total_sales == 1000.0
    assert input_data.ticket_count == 10
    assert input_data.currency == "EUR"
    assert input_data.additional_fees == {"service": 50.0}
    assert input_data.net_revenue is False


def test_revenue_share_config_model():
    """Test RevenueShareConfig Pydantic model."""
    config = RevenueShareConfig(
        default_platform_fee=4.5,
        default_organizer_share=82.0,
        default_venue_fee=8.5,
        default_artist_share=80.0,
        processing_fee_rate=3.0,
        processing_fixed_fee=0.25,
        minimum_payout_amount=20.0,
        maximum_payout_percentage=95.0
    )
    
    assert config.default_platform_fee == 4.5
    assert config.default_organizer_share == 82.0
    assert config.default_venue_fee == 8.5
    assert config.default_artist_share == 80.0
    assert config.processing_fee_rate == 3.0
    assert config.processing_fixed_fee == 0.25
    assert config.minimum_payout_amount == 20.0
    assert config.maximum_payout_percentage == 95.0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])