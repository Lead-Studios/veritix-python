import pytest
from pydantic import ValidationError

from src.config import get_settings


def _set_minimum_valid_env(monkeypatch):
    monkeypatch.setenv("QR_SIGNING_KEY", "a" * 32)
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./settings-test.db")
    monkeypatch.setenv("NEST_API_BASE_URL", "https://api.example.test")


def test_get_settings_is_cached(monkeypatch):
    _set_minimum_valid_env(monkeypatch)
    get_settings.cache_clear()

    s1 = get_settings()
    s2 = get_settings()

    assert s1 is s2


@pytest.mark.parametrize(
    "missing_key",
    ["QR_SIGNING_KEY", "DATABASE_URL", "NEST_API_BASE_URL"],
)
def test_missing_required_fields_raise_validation_error(monkeypatch, missing_key):
    _set_minimum_valid_env(monkeypatch)
    monkeypatch.delenv(missing_key, raising=False)
    get_settings.cache_clear()

    with pytest.raises(ValidationError):
        get_settings()


def test_qr_signing_key_min_length_is_validated(monkeypatch):
    _set_minimum_valid_env(monkeypatch)
    monkeypatch.setenv("QR_SIGNING_KEY", "short-key")
    get_settings.cache_clear()

    with pytest.raises(ValidationError):
        get_settings()
