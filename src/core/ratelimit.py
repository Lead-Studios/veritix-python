import os

from slowapi import Limiter  # type: ignore[import-untyped]
from slowapi.util import get_remote_address  # type: ignore[import-untyped]

# Disable rate limiting during tests to prevent flakiness unless explicitly enabled.
is_testing: bool = os.getenv("TESTING", "False").lower() == "true"

limiter: Limiter = Limiter(
    key_func=get_remote_address,
    enabled=not is_testing,
)