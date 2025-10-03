import pytest
import time
from service import TicketService, TICKET_DB
from cache import Cache

@pytest.fixture
def ticket_service():
    cache = Cache(ttl=2)  # use shorter TTL for testing
    return TicketService(cache)

def test_validate_ticket_caching(ticket_service):
    ticket_id = "ticket_123"

    # First call -> cache miss
    result1 = ticket_service.validate_ticket(ticket_id)
    assert result1["valid"] is True

    # Second call -> cache hit
    result2 = ticket_service.validate_ticket(ticket_id)
    assert result2 == result1

def test_cache_expiry(ticket_service):
    ticket_id = "ticket_123"

    result1 = ticket_service.validate_ticket(ticket_id)
    assert result1["valid"] is True

    # Wait for TTL to expire
    time.sleep(3)

    # Should be cache miss now
    result2 = ticket_service.validate_ticket(ticket_id)
    assert result2 == result1  # still same DB result

def test_update_ticket_invalidates_cache(ticket_service):
    ticket_id = "ticket_123"

    # Populate cache
    result1 = ticket_service.validate_ticket(ticket_id)
    assert result1["valid"] is True

    # Update ticket validity
    ticket_service.update_ticket(ticket_id, False)

    # New validation should reflect update
    result2 = ticket_service.validate_ticket(ticket_id)
    assert result2["valid"] is False
    assert result2 != result1
