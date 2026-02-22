import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

import src.key_manager as key_manager


def _generate_ed25519_pem_pair():
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return private_pem, public_pem


def test_sha256_fingerprint_is_short_and_stable():
    data = b"fingerprint-me"
    fp1 = key_manager._sha256_fingerprint(data)
    fp2 = key_manager._sha256_fingerprint(data)
    assert fp1 == fp2
    assert len(fp1) == 16


def test_to_bytes_handles_str_and_bytes():
    assert key_manager._to_bytes("hello") == b"hello"
    raw = b"world"
    assert key_manager._to_bytes(raw) == raw


def test_load_private_and_public_keys_from_env(monkeypatch):
    private_pem, public_pem = _generate_ed25519_pem_pair()
    monkeypatch.setattr(key_manager.settings, "PRIVATE_KEY_PEM", private_pem, raising=False)
    monkeypatch.setattr(key_manager.settings, "PUBLIC_KEY_PEM", public_pem, raising=False)

    private_key = key_manager.load_private_key_from_env()
    public_key = key_manager.load_public_key_from_env()

    assert private_key is not None
    assert public_key is not None


def test_load_keys_return_none_when_env_missing(monkeypatch):
    monkeypatch.setattr(key_manager.settings, "PRIVATE_KEY_PEM", None, raising=False)
    monkeypatch.setattr(key_manager.settings, "PUBLIC_KEY_PEM", None, raising=False)

    assert key_manager.load_private_key_from_env() is None
    assert key_manager.load_public_key_from_env() is None


def test_load_private_key_invalid_value_raises(monkeypatch):
    monkeypatch.setattr(key_manager.settings, "PRIVATE_KEY_PEM", "not-a-valid-private-key", raising=False)

    with pytest.raises(key_manager.KeyLoadError, match="Invalid private key"):
        key_manager.load_private_key_from_env()


def test_load_public_key_invalid_value_raises(monkeypatch):
    monkeypatch.setattr(key_manager.settings, "PUBLIC_KEY_PEM", "not-a-valid-public-key", raising=False)

    with pytest.raises(key_manager.KeyLoadError, match="Invalid public key"):
        key_manager.load_public_key_from_env()
