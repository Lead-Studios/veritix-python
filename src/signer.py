# src/signer.py
import base64
import logging
from typing import Optional, Union

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa

from .key_manager import PRIVATE_KEY, PUBLIC_KEY, _sha256_fingerprint

# Type aliases mirroring key_manager
_PrivateKey = Union[ed25519.Ed25519PrivateKey, rsa.RSAPrivateKey]
_PublicKey = Union[ed25519.Ed25519PublicKey, rsa.RSAPublicKey]

logger = logging.getLogger(__name__)


def _b64u_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64u_decode(s: str) -> bytes:
    padding_needed = (-len(s)) % 4
    s_padded = s + ("=" * padding_needed)
    return base64.urlsafe_b64decode(s_padded.encode("ascii"))


def sign(payload: bytes, private_key: Optional[_PrivateKey] = None) -> str:
    """Sign payload bytes and return a base64url signature string.

    Uses PRIVATE_KEY from key_manager by default.
    """
    key: _PrivateKey = private_key or PRIVATE_KEY  # type: ignore[assignment]
    if key is None:
        raise RuntimeError("No private key available for signing (service misconfigured).")

    if isinstance(key, ed25519.Ed25519PrivateKey):
        sig = key.sign(payload)
        logger.debug(
            "Signed payload with Ed25519 key (pub fingerprint=%s)",
            _safe_pub_fingerprint(key),
        )
        return _b64u_encode(sig)

    # RSA fallback (PKCS#1 v1.5 + SHA-256)
    try:
        rsa_key: rsa.RSAPrivateKey = key  # type: ignore[assignment]
        sig = rsa_key.sign(payload, padding.PKCS1v15(), hashes.SHA256())
        logger.debug(
            "Signed payload with RSA key (pub fingerprint=%s)",
            _safe_pub_fingerprint(key),
        )
        return _b64u_encode(sig)
    except Exception:
        logger.exception("Signing failed (sanitized).")
        raise


def verify(
    payload: bytes,
    signature_b64u: str,
    public_key: Optional[_PublicKey] = None,
) -> bool:
    """Verify a base64url signature against payload bytes.

    Returns True if verification succeeds, False otherwise.
    """
    key: _PublicKey = public_key or PUBLIC_KEY  # type: ignore[assignment]
    if key is None:
        raise RuntimeError("No public key available for verification (service misconfigured).")

    sig = _b64u_decode(signature_b64u)

    if isinstance(key, ed25519.Ed25519PublicKey):
        try:
            key.verify(sig, payload)
            logger.debug(
                "Ed25519 verification success (pub fingerprint=%s)",
                _safe_pub_fingerprint(key),
            )
            return True
        except Exception:
            logger.debug(
                "Ed25519 verification failed (pub fingerprint=%s)",
                _safe_pub_fingerprint(key),
            )
            return False

    # RSA fallback
    try:
        rsa_pub: rsa.RSAPublicKey = key  # type: ignore[assignment]
        rsa_pub.verify(sig, payload, padding.PKCS1v15(), hashes.SHA256())
        logger.debug(
            "RSA verification success (pub fingerprint=%s)",
            _safe_pub_fingerprint(key),
        )
        return True
    except Exception:
        logger.debug(
            "RSA verification failed (pub fingerprint=%s)",
            _safe_pub_fingerprint(key),
        )
        return False


def _safe_pub_fingerprint(key: Union[_PrivateKey, _PublicKey]) -> str:
    """Return a short public fingerprint for safe logging.

    Falls back to 'unknown' if obtaining bytes fails.
    """
    try:
        if isinstance(key, (ed25519.Ed25519PrivateKey, rsa.RSAPrivateKey)):
            pub = key.public_key()  # type: ignore[union-attr]
        else:
            pub = key
        pub_bytes = pub.public_bytes(  # type: ignore[union-attr]
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return _sha256_fingerprint(pub_bytes)
    except Exception:
        return "unknown"