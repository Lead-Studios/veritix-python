import os
import pytest
from sqlalchemy import create_engine, text
from src.config import get_settings

# Provide a non-default test key so startup validation passes in test environments.
os.environ.setdefault("QR_SIGNING_KEY", "a" * 32)
# Force model training to skip in test environments
os.environ.setdefault("SKIP_MODEL_TRAINING", "true")

@pytest.fixture(scope="session")
def db_engine():
    """Provides a database engine for integration tests."""
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)
    yield engine
    engine.dispose()

@pytest.fixture
def clean_test_db(db_engine):
    """Truncates all tables before/after integration tests."""
    tables = ["event_sales_summary", "daily_ticket_sales", "etl_run_log"]
    with db_engine.begin() as conn:
        for table in tables:
            try:
                conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            except Exception:
                # Tables might not exist yet if it's the first run
                pass
    yield
    with db_engine.begin() as conn:
        for table in tables:
            try:
                conn.execute(text(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE"))
            except Exception:
                pass
