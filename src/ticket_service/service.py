from cache import Cache
import time

# Simulated database
TICKET_DB = {
    "ticket_123": {"id": "ticket_123", "valid": True, "updated_at": time.time()},
    "ticket_456": {"id": "ticket_456", "valid": False, "updated_at": time.time()},
}

class TicketService:
    def __init__(self, cache: Cache):
        self.cache = cache

    def validate_ticket(self, ticket_id: str) -> dict:
        # 1. Check cache first
        cached = self.cache.get(ticket_id)
        if cached:
            print(f"[CACHE HIT] {ticket_id}")
            return cached

        print(f"[CACHE MISS] {ticket_id}")
        # 2. Fallback to "database"
        ticket = TICKET_DB.get(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")

        # 3. Store result in cache
        self.cache.set(ticket_id, ticket)
        return ticket

    def update_ticket(self, ticket_id: str, valid: bool):
        if ticket_id not in TICKET_DB:
            raise ValueError("Ticket not found")

        # Update DB
        TICKET_DB[ticket_id]["valid"] = valid
        TICKET_DB[ticket_id]["updated_at"] = time.time()

        # Invalidate cache so next read is fresh
        self.cache.invalidate(ticket_id)
