# tests/test_sign_verify.py
import tempfile
import os
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from src.signer import sign, verify
from importlib import reload
import src.key_manager as key_manager

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
