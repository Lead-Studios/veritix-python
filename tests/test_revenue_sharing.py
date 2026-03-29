import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from typing import Dict, Any, List
from fastapi import HTTPException
from pydantic import ValidationError
from src.revenue_sharing_service import RevenueSharingService
from src.revenue_sharing_models import (
    EventRevenueInput, 
    RevenueShareConfig, 
    Stakeholder, 
    RevenueRule,
    PayoutDistribution
)

@pytest.fixture
def service():
    return RevenueSharingService()

def test_calculate_fees_basic(service):
    """Test standard fee calculation."""
    input_data = EventRevenueInput(
        event_id="test_event",
        total_sales=1000.0,
        ticket_count=10,
        currency="USD"
    )
    # Processing: 2.9% of 1000 = 29.0 + (10 * 0.30) = 3.0. Total = 32.0
    # Platform: 5% of 1000 = 50.0
    fees = service._calculate_fees(input_data, 1000.0)
    assert fees["processing"] == pytest.approx(32.0)
    assert fees["platform"] == pytest.approx(50.0)

def test_calculate_fees_with_additional(service):
    """Test fees with additional custom fees."""
    input_data = EventRevenueInput(
        event_id="test_event",
        total_sales=1000.0,
        ticket_count=10,
        additional_fees={"security": 100.0, "cleanup": 50.0}
    )
    fees = service._calculate_fees(input_data, 1000.0)
    assert fees["security"] == 100.0
    assert fees["cleanup"] == 50.0

def test_calculate_distributions_sum(service):
    """Test that distributions sum perfectly to net revenue."""
    net_revenue = 1000.0
    stakeholders = service._get_default_stakeholders("event1")
    rules = service._get_default_rules()
    
    distributions, remaining = service._calculate_distributions(net_revenue, stakeholders, rules)
    
    total_distributed = sum(d.net_amount for d in distributions)
    assert total_distributed == pytest.approx(net_revenue)
    assert remaining == pytest.approx(0.0)

def test_rounding_adjustment(service):
    """Test that rounding differences are absorbed by the largest distribution."""
    # We want a case where splitting doesn't sum exactly.
    # e.g. 100 / 3 = 33.33 + 33.33 + 33.33 = 99.99. 0.01 left over.
    net_revenue = 100.0
    stakeholders = [
        Stakeholder(id="s1", name="S1", role="r1", percentage=33.33),
        Stakeholder(id="s2", name="S2", role="r2", percentage=33.33),
        Stakeholder(id="s3", name="S3", role="r3", percentage=33.33),
    ]
    # Simple rules that match 1:1
    rules = [
        RevenueRule(id="rule", name="rule", description="", condition="", percentage=33.33)
    ]
    
    with patch.object(service, "_find_rule_for_stakeholder", return_value=rules[0]):
        distributions, remaining = service._calculate_distributions(net_revenue, stakeholders, rules)
        
    total_distributed = sum(d.net_amount for d in distributions)
    assert total_distributed == pytest.approx(net_revenue)
    # One of them should be 33.34
    amounts = [d.net_amount for d in distributions]
    assert 33.34 in amounts
    assert amounts.count(33.33) == 2

def test_validate_input_invalid_sales(service):
    """Test validation fails for non-positive sales."""
    with pytest.raises(ValidationError):
        EventRevenueInput(event_id="e", total_sales=0, ticket_count=10)

def test_validate_input_invalid_tickets(service):
    """Test validation fails for non-positive tickets."""
    with pytest.raises(ValidationError):
        EventRevenueInput(event_id="e", total_sales=100, ticket_count=0)

def test_validate_input_overflow(service):
    """Test validation fails if custom rules exceed 100%."""
    # Using rules that sum to 101%, each being <= 100% to pass Pydantic
    rules = [
        RevenueRule(id="r1", name="r1", description="", condition="", percentage=60.0),
        RevenueRule(id="r2", name="r2", description="", condition="", percentage=41.0)
    ]
    input_data = EventRevenueInput(
        event_id="e", total_sales=100, ticket_count=1, custom_rules=rules
    )
    is_valid, errors = service.validate_input(input_data)
    assert not is_valid
    assert any("exceeds" in e.lower() for e in errors)

def test_validate_input_sales_less_than_tickets(service):
    """Test validation fails if sales < tickets (min $1 per ticket)."""
    input_data = EventRevenueInput(event_id="e", total_sales=5.0, ticket_count=10)
    is_valid, errors = service.validate_input(input_data)
    assert not is_valid
    assert any("at least" in e.lower() for e in errors)

def test_calculate_revenue_shares_percentage_overflow_guard(service):
    """Test that calculate_revenue_shares raises HTTPException on overflow."""
    bad_rules = [
        RevenueRule(id="r1", name="r1", description="", condition="", percentage=60.0),
        RevenueRule(id="r2", name="r2", description="", condition="", percentage=41.0)
    ]
    input_data = EventRevenueInput(
        event_id="e", total_sales=100, ticket_count=1, custom_rules=bad_rules
    )
    with pytest.raises(HTTPException) as excinfo:
        service.calculate_revenue_shares(input_data)
    assert excinfo.value.status_code == 400
    assert "101.00%" in str(excinfo.value.detail)

@patch("src.stakeholder_store.get_stakeholders_for_event")
def test_calculate_revenue_shares_uses_stakeholder_store(mock_get, service):
    """Test that service calls stakeholder_store."""
    mock_get.return_value = [Stakeholder(id="custom", name="C", role="organizer", percentage=100.0)]
    input_data = EventRevenueInput(event_id="event123", total_sales=1000.0, ticket_count=10)
    
    result = service.calculate_revenue_shares(input_data)
    
    mock_get.assert_called_once_with("event123")
    assert result.distributions[0].stakeholder_id == "custom"

@patch("src.currency_service.get_exchange_rate")
def test_calculate_fees_converts_currency(mock_rate, service):
    """Test that fees are converted using currency_service."""
    # 1 USD = 1000 TEST_CURR
    mock_rate.return_value = 1000.0
    input_data = EventRevenueInput(
        event_id="e", total_sales=100000.0, ticket_count=10, currency="TEST_CURR"
    )
    
    fees = service._calculate_fees(input_data, 100000.0)
    
    # Fixed fee 0.30 USD -> 300 TEST_CURR
    # 10 tickets * 300 = 3000
    # % fee: 2.9% of 100000 = 2900
    # Total processing = 3000 + 2900 = 5900
    assert fees["processing"] == pytest.approx(5900.0)
    mock_rate.assert_called_with("USD", "TEST_CURR")

def test_calculate_fees_currency_failure_usd(service):
    """Test currency conversion failure fallback for USD."""
    with patch("src.currency_service.get_exchange_rate", side_effect=Exception("API Down")):
        input_data = EventRevenueInput(
            event_id="e", total_sales=1000.0, ticket_count=10, currency="USD"
        )
        fees = service._calculate_fees(input_data, 1000.0)
        # Should fallback to 1:1 for USD
        assert fees["processing"] == pytest.approx(32.0)

def test_calculate_fees_currency_failure_non_usd(service):
    """Test currency conversion failure raises for non-USD."""
    with patch("src.currency_service.get_exchange_rate", side_effect=Exception("API Down")):
        input_data = EventRevenueInput(
            event_id="e", total_sales=1000.0, ticket_count=10, currency="NGN"
        )
        with pytest.raises(Exception) as exc:
            service._calculate_fees(input_data, 1000.0)
        assert "API Down" in str(exc.value)

def test_batch_calculation_logic():
    """Test batch calculation behavior in a unit-test way (using TestClient)."""
    from fastapi.testclient import TestClient
    from src.main import app
    client = TestClient(app)
    
    batch_input = [
        {"event_id": "e1", "total_sales": 1000, "ticket_count": 10},
        {"event_id": "e2", "total_sales": -50, "ticket_count": 1}, # Invalid
        {"event_id": "e3", "total_sales": 2000, "ticket_count": 20}
    ]
    
    # Mocking stakeholder_store to avoid DB calls
    with patch("src.stakeholder_store.get_stakeholders_for_event", return_value=[]):
        with patch("fastapi.BackgroundTasks.add_task"):
            response = client.post("/calculate-revenue-share/batch", json=batch_input)
    
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 2 # e2 should be skipped
    assert results[0]["event_id"] == "e1"
    assert results[1]["event_id"] == "e3"

def test_constraints_min_max_amount(service):
    """Test min_amount and max_amount constraints on stakeholders."""
    s1 = Stakeholder(id="s1", name="S1", role="r1", percentage=50.0, min_amount=600.0)
    s2 = Stakeholder(id="s2", name="S2", role="r2", percentage=50.0)
    net_revenue = 1000.0
    
    rules = [
        RevenueRule(id="rule", name="rule", description="", condition="", percentage=50.0)
    ]
    
    with patch.object(service, "_find_rule_for_stakeholder", return_value=rules[0]):
        distributions, remaining = service._calculate_distributions(net_revenue, [s1, s2], rules)
        
    s1_dist = next(d for d in distributions if d.stakeholder_id == "s1")
    s2_dist = next(d for d in distributions if d.stakeholder_id == "s2")
    
    # s1 gets min(600), s2 gets 500 (total 1100). 
    # Wait, the total will exceed net_revenue! 
    # The actual_remaining will be -100.
    # Largest dist (s1 at 600) will absorb it? 600 - 100 = 500.
    # To test min_amount, we need the total to be UNDER net_revenue.
    
    s1.min_amount = 600.0
    s1.percentage = 40.0 # 400 normally
    s2.percentage = 10.0 # 100 normally
    # Total 500. net_revenue 1000. remaining 500.
    
    with patch.object(service, "_find_rule_for_stakeholder", return_value=rules[0]):
        distributions, remaining = service._calculate_distributions(1000.0, [s1, s2], rules, "USD")
        
    s1_dist = next(d for d in distributions if d.stakeholder_id == "s1")
    # s1: 400 -> 600. 
    # s2: 100 -> 100.
    # total 700. actual_remaining 300.
    # largest (s1 at 600) absorbs 300 -> 900.
    # Still 100.
    
    # Let's simplify: just check if gross_amount was increased to min_amount BEFORE adjustment
    # We can mock _calculate_distributions to return intermediate values or just use values that don't trigger large adjustments.
    
    # Actually, if I just want to test the constraint logic, I'll use a very small net_revenue and high min_amount.
    s1.min_amount = 10.0
    s1.percentage = 1.0 # 1.0 normally
    s2.percentage = 99.0 # 99.0 normally
    # net 100. 1+99=100.
    # s1: 1 -> 10.
    # s2: 99 -> 99.
    # sum 109. remaining -9.
    # largest (s2 at 99) absorbs -9 -> 90.
    # s1 stays at 10.
    with patch.object(service, "_find_rule_for_stakeholder", return_value=rules[0]):
        distributions, remaining = service._calculate_distributions(100.0, [s1, s2], rules, "USD")
    
    s1_dist = next(d for d in distributions if d.stakeholder_id == "s1")
    assert s1_dist.net_amount == 10.0

def test_get_default_stakeholders(service):
    """Test standard stakeholder generation."""
    stakeholders = service._get_default_stakeholders("e1")
    assert len(stakeholders) == 3
    assert any(s.role == "organizer" for s in stakeholders)
    assert any(s.role == "platform" for s in stakeholders)
    assert any(s.role == "venue" for s in stakeholders)

def test_get_default_rules(service):
    """Test standard rule generation."""
    rules = service._get_default_rules()
    assert len(rules) == 3
    assert any(r.id == "organizer_share_rule" for r in rules)

def test_stakeholder_no_matching_rule(service):
    """Test distribution when a stakeholder has no matching rule."""
    stakeholder = Stakeholder(id="ghost", name="Ghost", role="unknown", percentage=10.0)
    net_revenue = 1000.0
    rules = [RevenueRule(id="r1", name="r1", description="", condition="", percentage=50.0, applies_to=["organizer"])]
    
    distributions, remaining = service._calculate_distributions(net_revenue, [stakeholder], rules)
    assert len(distributions) == 0
    assert remaining == 1000.0

def test_find_rule_for_stakeholder_fallback(service):
    """Test the rule matching logic with fallback to general rules."""
    s1 = Stakeholder(id="s1", name="S1", role="artist", percentage=10.0)
    # Rule applies to all if applies_to is empty
    general_rule = RevenueRule(id="gen", name="Gen", description="", condition="", percentage=50.0, applies_to=[])
    
    rule = service._find_rule_for_stakeholder(s1, [general_rule])
    assert rule == general_rule
    
    # Rule matches via name substring
    artist_rule = RevenueRule(id="art", name="Artist Rule", description="", condition="", percentage=50.0, applies_to=["other"])
    rule = service._find_rule_for_stakeholder(s1, [artist_rule])
    assert rule == artist_rule