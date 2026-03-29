"""Utilities to persist and reload the scalper-detection model from disk."""
import logging
import os
from typing import Any, Optional

MODEL_PATH = os.environ.get("SCALPER_MODEL_PATH", "scalper_model.pkl")

logger = logging.getLogger("veritix.model_persistence")


def save_model(pipeline: Any, path: str = MODEL_PATH) -> None:
    """Serialize *pipeline* to *path* using joblib."""
    import joblib  # type: ignore[import-untyped]

    joblib.dump(pipeline, path)
    logger.info("Scalper model saved to %s", path)


def load_model(path: str = MODEL_PATH) -> Optional[Any]:
    """Load and return the model from *path*, or None if the file does not exist."""
    import joblib  # type: ignore[import-untyped]

    if not os.path.exists(path):
        logger.info("No saved model found at %s; will train from scratch", path)
        return None
    pipeline = joblib.load(path)
    logger.info("Scalper model loaded from %s", path)
    return pipeline


def get_or_train_model(path: str = MODEL_PATH) -> Any:
    """Return the persisted model if available, otherwise train, save, and return it."""
    from src.utils import train_logistic_regression_pipeline

    pipeline = load_model(path)
    if pipeline is None:
        pipeline = train_logistic_regression_pipeline()
        save_model(pipeline, path)
    return pipeline
