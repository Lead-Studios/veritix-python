import hashlib
import hmac
import json
import os
from typing import Any, Dict, Tuple

from src.config import get_settings

MIN_QR_SIGNING_KEY_LENGTH = 32


def _lazy_import_ml() -> Tuple[Any, Any, Any, Any, Any]:
    """Lazily import heavy ML packages to avoid slow startup in test mode.

    Returns (numpy, LogisticRegression, train_test_split, StandardScaler, Pipeline).

    NOTE: Return type is Tuple[Any, ...] because numpy/sklearn have no bundled
    stubs and the types are only available at runtime.
    """
    import numpy as np  # type: ignore[import-untyped]
    from sklearn.linear_model import LogisticRegression  # type: ignore[import-untyped]
    from sklearn.model_selection import train_test_split  # type: ignore[import-untyped]
    from sklearn.pipeline import Pipeline  # type: ignore[import-untyped]
    from sklearn.preprocessing import StandardScaler  # type: ignore[import-untyped]

    return np, LogisticRegression, train_test_split, StandardScaler, Pipeline


def generate_synthetic_event_data(
    num_samples: int = 2000,
    random_seed: int = 42,
) -> Tuple[Any, Any]:
    """Generate synthetic data for scalper detection.

    Returns (X, y) as numpy arrays.

    NOTE: Return type uses Any because numpy ndarray stubs are not available
    without numpy type stubs package.
    """
    np, _, _, _, _ = _lazy_import_ml()
    rng = np.random.default_rng(random_seed)

    tickets_per_txn = rng.integers(1, 13, size=num_samples)
    txns_per_min = rng.uniform(0, 10, size=num_samples)
    avg_price_ratio = rng.uniform(0.5, 2.0, size=num_samples)
    account_age_days = rng.integers(0, 3651, size=num_samples)
    zip_mismatch = rng.integers(0, 2, size=num_samples)
    device_changes = rng.integers(0, 7, size=num_samples)

    X = np.column_stack([
        tickets_per_txn,
        txns_per_min,
        avg_price_ratio,
        account_age_days,
        zip_mismatch,
        device_changes,
    ])

    weights = np.array([0.35, 0.45, 0.25, -0.002, 0.4, 0.3])
    bias = -2.0
    logits = X @ weights + bias
    probs = 1 / (1 + np.exp(-logits))
    y = rng.binomial(1, probs)
    return X.astype(float), y.astype(int)


def train_logistic_regression_pipeline() -> Any:
    """Train a standardize+logistic-regression pipeline on synthetic data.

    Returns a fitted sklearn Pipeline.

    NOTE: Return type is Any because sklearn Pipeline has no bundled stubs.
    """
    np, LogisticRegression, train_test_split, StandardScaler, Pipeline = _lazy_import_ml()
    X, y = generate_synthetic_event_data()
    X_train, _, y_train, _ = train_test_split(X, y, test_size=0.2, random_state=123)
    pipeline = Pipeline(
        steps=[
            ("scaler", StandardScaler()),
            ("clf", LogisticRegression(max_iter=1000, solver="lbfgs")),
        ]
    )
    pipeline.fit(X_train, y_train)
    return pipeline


def validate_qr_signing_key_from_env() -> int:
    """Validate that QR_SIGNING_KEY meets minimum length requirements.

    Returns the key length on success; raises RuntimeError otherwise.
    """
    key = os.getenv("QR_SIGNING_KEY")
    if key is None or not key.strip():
        raise RuntimeError(
            "QR_SIGNING_KEY must be explicitly set at startup and be at least "
            f"{MIN_QR_SIGNING_KEY_LENGTH} characters long."
        )
    if len(key) < MIN_QR_SIGNING_KEY_LENGTH:
        raise RuntimeError(
            "QR_SIGNING_KEY is too short. Minimum length is "
            f"{MIN_QR_SIGNING_KEY_LENGTH} characters."
        )
    return len(key)


def get_signing_key() -> bytes:
    """Return the QR signing key as UTF-8 bytes."""
    validate_qr_signing_key_from_env()
    key = get_settings().QR_SIGNING_KEY
    return key.encode("utf-8")


def compute_signature(data: Dict[str, Any]) -> str:
    """Compute an HMAC-SHA256 hex digest for the given data dict."""
    canonical = json.dumps(data, separators=(",", ":"), sort_keys=True).encode("utf-8")
    digest = hmac.new(get_signing_key(), canonical, hashlib.sha256).hexdigest()
    return digest