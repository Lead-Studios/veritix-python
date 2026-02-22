# Revenue Sharing Service Documentation

## Overview

The Revenue Sharing Service calculates organizer revenue shares based on ticket sales and smart contract rules. It handles the distribution of revenue among multiple stakeholders according to predefined rules and configurations.

## Features

- **Smart Contract Rules**: Define revenue distribution rules that can be applied to different events
- **Multiple Stakeholders**: Support for organizers, venues, platforms, artists, and other stakeholders
- **Flexible Configuration**: Configurable fee structures, percentages, and constraints
- **Validation**: Input validation to ensure data integrity
- **Batch Processing**: Support for calculating revenue shares for multiple events at once
- **Detailed Output**: Comprehensive breakdown of distributions and calculations

## Components

### Models

#### Stakeholder
Represents a party involved in revenue sharing:
- `id`: Unique identifier for the stakeholder
- `name`: Name of the stakeholder
- `role`: Role (organizer, venue, platform, artist, etc.)
- `percentage`: Percentage of revenue allocated
- `fixed_amount`: Fixed amount if applicable
- `min_amount`: Minimum guaranteed amount
- `max_amount`: Maximum cap amount
- `payment_address`: Wallet address for crypto payments

#### RevenueRule
Defines a smart contract rule for revenue distribution:
- `id`: Unique identifier for the rule
- `name`: Name of the rule
- `description`: Description of the rule
- `condition`: Condition that triggers the rule
- `priority`: Priority order for rule evaluation
- `percentage`: Percentage allocated by this rule
- `min_threshold`: Minimum sales threshold
- `max_threshold`: Maximum sales threshold
- `applies_to`: Roles this rule applies to

#### EventRevenueInput
Input for revenue calculation:
- `event_id`: Unique identifier for the event
- `total_sales`: Total sales amount
- `ticket_count`: Number of tickets sold
- `currency`: Currency code (default: USD)
- `additional_fees`: Additional fees (processing, etc.)
- `net_revenue`: Whether to calculate on net or gross revenue
- `custom_rules`: Custom rules for this event

#### RevenueCalculationResult
Output of revenue calculation:
- `event_id`: Event identifier
- `total_gross_sales`: Gross sales amount
- `total_fees`: Total fees deducted
- `net_revenue`: Net revenue after fees
- `distributions`: List of payout distributions
- `total_paid_out`: Total amount paid out to stakeholders
- `remaining_balance`: Leftover from rounding differences
- `calculation_timestamp`: Time of calculation
- `rules_applied`: List of rules that were applied

## API Endpoints

### Calculate Revenue Share
```
POST /calculate-revenue-share
```
Calculate revenue shares for stakeholders based on event sales and smart contract rules.

**Request Body:**
```json
{
  "event_id": "event_123",
  "total_sales": 10000.0,
  "ticket_count": 100,
  "currency": "USD",
  "additional_fees": {
    "service_fee": 50.0
  },
  "net_revenue": true,
  "custom_rules": [
    {
      "id": "custom_rule_1",
      "name": "Premium Event Rule",
      "description": "Special rule for premium events",
      "condition": "premium",
      "priority": 1,
      "percentage": 85.0,
      "applies_to": ["organizer"]
    }
  ]
}
```

**Response:**
```json
{
  "event_id": "event_123",
  "total_gross_sales": 10000.0,
  "total_fees": {
    "processing": 290.0,
    "platform": 500.0,
    "service_fee": 50.0
  },
  "net_revenue": 9210.0,
  "distributions": [
    {
      "stakeholder_id": "organizer_event_123",
      "stakeholder_name": "Event Organizer",
      "role": "organizer",
      "gross_amount": 7368.0,
      "fee_deductions": {},
      "net_amount": 7368.0,
      "percentage_applied": 80.0,
      "rule_used": "organizer_share_rule"
    }
  ],
  "total_paid_out": 9210.0,
  "remaining_balance": 0.0,
  "calculation_timestamp": "2024-01-15T10:30:45.123456",
  "rules_applied": ["platform_fee_rule", "organizer_share_rule", "venue_fee_rule"]
}
```

### Batch Calculate Revenue Share
```
POST /calculate-revenue-share/batch
```
Calculate revenue shares for multiple events.

### Get Configuration
```
GET /revenue-share/config
```
Retrieve the current revenue sharing configuration.

### Get Example Input
```
GET /revenue-share/example
```
Get an example revenue calculation input.

## Configuration

The service uses a `RevenueShareConfig` object with the following defaults:

- `default_platform_fee`: 5.0% (platform commission)
- `default_organizer_share`: 80.0% (organizer share)
- `default_venue_fee`: 10.0% (venue commission)
- `default_artist_share`: 85.0% (artist share of organizer portion)
- `processing_fee_rate`: 2.9% (payment processor percentage)
- `processing_fixed_fee`: $0.30 (payment processor fixed fee)
- `minimum_payout_amount`: $10.00 (minimum payout threshold)
- `maximum_payout_percentage`: 100.0% (max percentage that can be distributed)

## Smart Contract Rules

Revenue distribution is controlled by smart contract rules that determine how revenue is split among stakeholders. Rules have:

- **Priority**: Determines the order in which rules are applied
- **Conditions**: Triggers for when rules apply
- **Percentages**: Allocation percentages for different stakeholders
- **Thresholds**: Minimum and maximum sales thresholds for rule applicability

## Validation

The service validates input data to ensure:

- Total sales are greater than zero
- Ticket count is greater than zero
- Total percentage allocation does not exceed maximum allowed
- Sales amounts are reasonable relative to ticket counts

## Usage Examples

### Python Client
```python
from src.revenue_sharing_service import RevenueSharingService
from src.revenue_sharing_models import EventRevenueInput

# Create service instance
service = RevenueSharingService()

# Prepare input data
input_data = EventRevenueInput(
    event_id="my_event_456",
    total_sales=5000.0,
    ticket_count=50
)

# Calculate revenue shares
result = service.calculate_revenue_shares(input_data)

# Print distribution details
for distribution in result.distributions:
    print(f"{distribution.stakeholder_name}: ${distribution.net_amount}")
```

### API Call Example
```bash
curl -X POST "http://localhost:8000/calculate-revenue-share" \
  -H "Content-Type: application/json" \
  -d '{
    "event_id": "event_789",
    "total_sales": 15000.0,
    "ticket_count": 150
  }'
```

## Business Logic

The revenue calculation follows these steps:

1. **Fee Calculation**: Calculate processing fees, platform fees, and additional fees
2. **Net Revenue Determination**: Subtract fees from gross sales to get net revenue
3. **Rule Application**: Apply smart contract rules in priority order
4. **Stakeholder Distribution**: Distribute revenue according to stakeholder rules
5. **Constraint Application**: Apply minimum/maximum constraints
6. **Final Adjustment**: Handle rounding differences

## Testing

Run the test suite:
```bash
pytest tests/test_revenue_sharing.py -v
```

## Error Handling

The service handles various error conditions:

- Invalid input data
- Percentage allocation exceeding limits
- Insufficient revenue for minimum payouts
- System errors during calculation

Errors are logged using the structured logging system and appropriate HTTP status codes are returned.