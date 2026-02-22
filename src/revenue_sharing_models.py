"""Pydantic models for revenue sharing service."""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime


class Stakeholder(BaseModel):
    """Represents a stakeholder in the revenue sharing model."""
    id: str
    name: str
    role: str  # "organizer", "venue", "platform", "artist", etc.
    percentage: float = Field(ge=0.0, le=100.0)  # Percentage of revenue
    fixed_amount: Optional[float] = None  # Fixed amount if applicable
    min_amount: Optional[float] = None  # Minimum guaranteed amount
    max_amount: Optional[float] = None  # Maximum cap amount
    payment_address: Optional[str] = None  # Wallet address for crypto payments


class RevenueRule(BaseModel):
    """Represents a smart contract rule for revenue distribution."""
    id: str
    name: str
    description: str
    condition: str  # Condition that triggers this rule
    priority: int = 0  # Priority order for rule evaluation
    percentage: float = Field(ge=0.0, le=100.0)  # Percentage allocated
    min_threshold: Optional[float] = None  # Minimum sales threshold
    max_threshold: Optional[float] = None  # Maximum sales threshold
    applies_to: List[str] = []  # Roles this rule applies to


class EventRevenueInput(BaseModel):
    """Input for revenue calculation."""
    event_id: str
    total_sales: float = Field(gt=0)  # Total sales amount
    ticket_count: int = Field(gt=0)  # Number of tickets sold
    currency: str = "USD"  # Currency code
    additional_fees: Optional[Dict[str, float]] = None  # Additional fees (processing, etc.)
    net_revenue: Optional[bool] = True  # Whether to calculate on net or gross revenue
    custom_rules: Optional[List[RevenueRule]] = None  # Custom rules for this event


class PayoutDistribution(BaseModel):
    """Distribution of payout to a single stakeholder."""
    stakeholder_id: str
    stakeholder_name: str
    role: str
    gross_amount: float  # Amount before fees
    fee_deductions: Dict[str, float]  # Fee breakdown
    net_amount: float  # Amount after fees
    percentage_applied: float  # Percentage used for calculation
    rule_used: Optional[str] = None  # Rule that determined this distribution


class RevenueCalculationResult(BaseModel):
    """Result of revenue calculation."""
    event_id: str
    total_gross_sales: float
    total_fees: float
    net_revenue: float
    distributions: List[PayoutDistribution]
    total_paid_out: float
    remaining_balance: float  # Leftover from rounding differences
    calculation_timestamp: datetime
    rules_applied: List[str]


class RevenueShareConfig(BaseModel):
    """Configuration for revenue sharing rules."""
    default_platform_fee: float = 5.0  # 5%
    default_organizer_share: float = 80.0  # 80%
    default_venue_fee: float = 10.0  # 10%
    default_artist_share: float = 85.0  # 85% of organizer share goes to artist
    processing_fee_rate: float = 2.9  # 2.9% processing fee
    processing_fixed_fee: float = 0.30  # $0.30 per transaction
    minimum_payout_amount: float = 10.0  # Minimum amount for payout
    maximum_payout_percentage: float = 100.0  # Max percentage that can be distributed