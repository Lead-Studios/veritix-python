# tests/test_sign_verify.py
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
from src.signer import sign, verify
import src.signer as signer_module
from importlib import reload
import src.key_manager as key_manager
import pytest

def test_ed25519_sign_verify_ephemeral(monkeypatch):
    # generate ephemeral keys
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    ).decode("utf-8")
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode("utf-8")

    # monkeypatch environment variables for the config loader
    monkeypatch.setenv("PRIVATE_KEY_PEM", priv_pem)
    monkeypatch.setenv("PUBLIC_KEY_PEM", pub_pem)

    # reload modules to pick up monkeypatched env
    reload(key_manager)
    from src import signer as signer_module

    payload = b"unit test payload"
    signature = signer_module.sign(payload)
    assert signer_module.verify(payload, signature) is True

    # tamper payload -> verify should fail
    assert signer_module.verify(payload + b"x", signature) is False


def test_rsa_sign_verify_ephemeral():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()

    payload = b"rsa payload"
    signature = sign(payload, private_key=private_key)

    assert verify(payload, signature, public_key=public_key) is True
    assert verify(payload + b"-tampered", signature, public_key=public_key) is False


def test_sign_and_verify_require_keys(monkeypatch):
    monkeypatch.setattr(signer_module, "PRIVATE_KEY", None)
    monkeypatch.setattr(signer_module, "PUBLIC_KEY", None)

    with pytest.raises(RuntimeError, match="No private key available"):
        sign(b"payload", private_key=None)

    encoded_sig = signer_module._b64u_encode(b"sig")
    with pytest.raises(RuntimeError, match="No public key available"):
        verify(b"payload", encoded_sig, public_key=None)


def test_base64url_helpers_roundtrip():
    original = b"abc123+/="
    encoded = signer_module._b64u_encode(original)
    decoded = signer_module._b64u_decode(encoded)
    assert decoded == original
