# src/key_manager.py
import hashlib
import logging
from typing import Optional, Union

from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from cryptography.hazmat.primitives.serialization import (
    load_pem_private_key,
    load_pem_public_key,
)

from .config import get_settings

logger = logging.getLogger(__name__)

# Union type covering the two private-key variants the codebase uses.
_PrivateKey = Union[ed25519.Ed25519PrivateKey, rsa.RSAPrivateKey]
# Union type covering the two public-key variants.
_PublicKey = Union[ed25519.Ed25519PublicKey, rsa.RSAPublicKey]


class KeyLoadError(Exception):
    pass


def _sha256_fingerprint(data: bytes) -> str:
    """Return a short safe fingerprint string for logging (hex)."""
    h = hashlib.sha256(data).hexdigest()
    return h[:16]


def _to_bytes(pem_str: str) -> bytes:
    if isinstance(pem_str, str):
        return pem_str.encode("utf-8")
    return pem_str  # type: ignore[return-value]  # defensive; callers always pass str


def load_private_key_from_env() -> Optional[_PrivateKey]:
    """Load the private key from the PRIVATE_KEY_PEM environment variable.

    Returns None if the variable is not set.
    Raises KeyLoadError if the PEM is invalid.
    """
    pem = get_settings().PRIVATE_KEY_PEM
    if not pem:
        logger.debug("No PRIVATE_KEY_PEM provided in environment.")
        return None
    try:
        pem_bytes = _to_bytes(pem)
        key = load_pem_private_key(pem_bytes, password=None)
        try:
            pub_bytes = key.public_key().public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            logger.info("Private key loaded, public fingerprint=%s", _sha256_fingerprint(pub_bytes))
        except Exception:
            logger.info("Private key loaded (public fingerprint unavailable).")
        # load_pem_private_key may return other types; we cast to the union.
        return key  # type: ignore[return-value]
    except (ValueError, TypeError, UnsupportedAlgorithm) as e:
        logger.exception("Failed loading private key from environment (sanitized).")
        raise KeyLoadError("Invalid private key in environment") from e


def load_public_key_from_env() -> Optional[_PublicKey]:
    """Load the public key from the PUBLIC_KEY_PEM environment variable.

    Returns None if the variable is not set.
    Raises KeyLoadError if the PEM is invalid.
    """
    pem = get_settings().PUBLIC_KEY_PEM
    if not pem:
        logger.debug("No PUBLIC_KEY_PEM provided in environment.")
        return None
    try:
        pem_bytes = _to_bytes(pem)
        key = load_pem_public_key(pem_bytes)
        try:
            pub_bytes = key.public_bytes(
                serialization.Encoding.PEM,
                serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            logger.info("Public key loaded, fingerprint=%s", _sha256_fingerprint(pub_bytes))
        except Exception:
            logger.info("Public key loaded.")
        return key  # type: ignore[return-value]
    except (ValueError, TypeError, UnsupportedAlgorithm) as e:
        logger.exception("Failed loading public key from environment (sanitized).")
        raise KeyLoadError("Invalid public key in environment") from e


# Module-level singletons; may be None when keys are not configured.
PRIVATE_KEY: Optional[_PrivateKey] = load_private_key_from_env()
PUBLIC_KEY: Optional[_PublicKey] = load_public_key_from_env()