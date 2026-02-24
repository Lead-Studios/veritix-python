import os
from slowapi import Limiter
from slowapi.util import get_remote_address

# Disable rate limiting during normal tests to prevent test flakiness, 
# unless we explicitly want to test the rate limiter.
is_testing = os.getenv("TESTING", "False").lower() == "true"

limiter = Limiter(
    key_func=get_remote_address,
    enabled=not is_testing
)