import pytest

from src.fraud import determine_severity


def test_determine_severity_none():
    assert determine_severity([]) == "none"


def test_determine_severity_high_when_high_rule_present():
    assert determine_severity(["too_many_purchases_same_ip"]) == "high"
    assert determine_severity(["excessive_purchases_user_day"]) == "high"


def test_determine_severity_medium_when_medium_rule_present():
    assert determine_severity(["duplicate_ticket_transfer"]) == "medium"


def test_determine_severity_priority_high_over_medium():
    assert determine_severity(["duplicate_ticket_transfer", "too_many_purchases_same_ip"]) == "high"


def test_determine_severity_low_for_unknown_rules():
    assert determine_severity(["some_new_rule"]) == "low"
