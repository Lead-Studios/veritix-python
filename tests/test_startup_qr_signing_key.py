import pytest

from src.main import on_startup


def test_startup_raises_when_qr_signing_key_missing(monkeypatch):
    monkeypatch.setenv("SKIP_MODEL_TRAINING", "true")
    monkeypatch.delenv("QR_SIGNING_KEY", raising=False)

    with pytest.raises(RuntimeError, match="QR_SIGNING_KEY"):
        on_startup()


def test_startup_raises_when_qr_signing_key_too_short(monkeypatch):
    monkeypatch.setenv("SKIP_MODEL_TRAINING", "true")
    monkeypatch.setenv("QR_SIGNING_KEY", "short_key")

    with pytest.raises(RuntimeError, match="Minimum length is 32"):
        on_startup()
