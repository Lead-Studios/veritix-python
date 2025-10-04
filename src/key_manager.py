# src/key_manager.py
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
from cryptography.exceptions import UnsupportedAlgorithm
from typing import Optional, Tuple
from .config import settings
import hashlib
import logging

logger = logging.getLogger(__name__)

class KeyLoadError(Exception):
    pass

def _sha256_fingerprint(data: bytes) -> str:
    """Return a short safe fingerprint string for logging (hex)."""
    h = hashlib.sha256(data).hexdigest()
    # return short fingerprint to avoid leaking too much
    return h[:16]

def _to_bytes(pem_str: str) -> bytes:
    if isinstance(pem_str, str):
        return pem_str.encode("utf-8")
    return pem_str

def load_private_key_from_env() -> Optional[serialization.PrivateFormat]:
    pem = settings.PRIVATE_KEY_PEM
    if not pem:
        logger.debug("No PRIVATE_KEY_PEM provided in environment.")
        return None
    try:
        pem_bytes = _to_bytes(pem)
        # pass password if using encrypted PEM in production (not covered here)
        key = load_pem_private_key(pem_bytes, password=None)
        # log only fingerprint
        try:
            pub_bytes = key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            )
            logger.info("Private key loaded, public fingerprint=%s", _sha256_fingerprint(pub_bytes))
        except Exception:
            logger.info("Private key loaded (public fingerprint unavailable).")
        return key
    except (ValueError, TypeError, UnsupportedAlgorithm) as e:
        # sanitize error so we don't leak key contents
        logger.exception("Failed loading private key from environment (sanitized).")
        raise KeyLoadError("Invalid private key in environment") from e

def load_public_key_from_env() -> Optional[serialization.PublicFormat]:
    pem = settings.PUBLIC_KEY_PEM
    if not pem:
        logger.debug("No PUBLIC_KEY_PEM provided in environment.")
        return None
    try:
        pem_bytes = _to_bytes(pem)
        key = load_pem_public_key(pem_bytes)
        # log only fingerprint
        try:
            pub_bytes = key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo
            )
            logger.info("Public key loaded, fingerprint=%s", _sha256_fingerprint(pub_bytes))
        except Exception:
            logger.info("Public key loaded.")
        return key
    except (ValueError, TypeError, UnsupportedAlgorithm) as e:
        logger.exception("Failed loading public key from environment (sanitized).")
        raise KeyLoadError("Invalid public key in environment") from e

# Single place to fetch keys — you can cache them if needed
PRIVATE_KEY = load_private_key_from_env()
PUBLIC_KEY = load_public_key_from_env()
