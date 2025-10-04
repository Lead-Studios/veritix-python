# src/signer.py
from .key_manager import PRIVATE_KEY, PUBLIC_KEY, _sha256_fingerprint
from cryptography.hazmat.primitives.asymmetric import ed25519, padding
from cryptography.hazmat.primitives import hashes
import base64
import logging
from typing import Optional

logger = logging.getLogger(__name__)

def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")

def _b64u_decode(s: str) -> bytes:
    padding_needed = (-len(s)) % 4
    s_padded = s + ("=" * padding_needed)
    return base64.urlsafe_b64decode(s_padded.encode("ascii"))

def sign(payload: bytes, private_key=None) -> str:
    """Sign payload bytes and return base64url signature string.
       Will use PRIVATE_KEY from key_manager by default.
    """
    key = private_key or PRIVATE_KEY
    if key is None:
        raise RuntimeError("No private key available for signing (service misconfigured).")
    # Ed25519
    if isinstance(key, ed25519.Ed25519PrivateKey):
        sig = key.sign(payload)
        logger.debug("Signed payload with Ed25519 key (pub fingerprint=%s)",
                     _safe_pub_fingerprint(key))
        return _b64u_encode(sig)

    # RSA fallback (PKCS#1 v1.5 + SHA256)
    try:
        sig = key.sign(
            payload,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        logger.debug("Signed payload with RSA key (pub fingerprint=%s)", _safe_pub_fingerprint(key))
        return _b64u_encode(sig)
    except Exception as e:
        logger.exception("Signing failed (sanitized).")
        raise

def verify(payload: bytes, signature_b64u: str, public_key=None) -> bool:
    key = public_key or PUBLIC_KEY
    if key is None:
        raise RuntimeError("No public key available for verification (service misconfigured).")
    sig = _b64u_decode(signature_b64u)
    # Ed25519
    if isinstance(key, ed25519.Ed25519PublicKey):
        try:
            key.verify(sig, payload)
            logger.debug("Ed25519 verification success (pub fingerprint=%s)", _safe_pub_fingerprint(key))
            return True
        except Exception:
            logger.debug("Ed25519 verification failed (pub fingerprint=%s)", _safe_pub_fingerprint(key))
            return False

    # RSA fallback
    try:
        key.verify(
            sig,
            payload,
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        logger.debug("RSA verification success (pub fingerprint=%s)", _safe_pub_fingerprint(key))
        return True
    except Exception:
        logger.debug("RSA verification failed (pub fingerprint=%s)", _safe_pub_fingerprint(key))
        return False

def _safe_pub_fingerprint(key) -> str:
    """Return a short public fingerprint for safe logging. If obtaining bytes fails, return 'unknown'."""
    try:
        pub_bytes = key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        return _sha256_fingerprint(pub_bytes)
    except Exception:
        return "unknown"
