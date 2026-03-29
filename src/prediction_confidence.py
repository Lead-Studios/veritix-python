"""Model prediction confidence threshold with an 'uncertain' classification band.

Wraps a fitted sklearn pipeline and maps raw probabilities to three labels:
  - 'scalper'   — probability >= high_threshold
  - 'uncertain' — probability is between low_threshold and high_threshold
  - 'not_scalper' — probability < low_threshold
"""
from typing import Any, Dict

# Default thresholds — tune these based on desired precision/recall trade-off
DEFAULT_HIGH_THRESHOLD = 0.70  # above this -> scalper
DEFAULT_LOW_THRESHOLD = 0.40   # below this -> not_scalper; between -> uncertain


def classify_with_confidence(
    pipeline: Any,
    features: Any,
    high_threshold: float = DEFAULT_HIGH_THRESHOLD,
    low_threshold: float = DEFAULT_LOW_THRESHOLD,
) -> Dict[str, Any]:
    """Run the pipeline on *features* and return a labelled prediction dict.

    Parameters
    ----------
    pipeline:
        A fitted sklearn Pipeline exposing ``predict_proba``.
    features:
        A 2-D array-like of shape (1, n_features).
    high_threshold:
        Probability at or above which the prediction is 'scalper'.
    low_threshold:
        Probability below which the prediction is 'not_scalper'.

    Returns
    -------
    dict with keys:
        - ``label``       : 'scalper' | 'uncertain' | 'not_scalper'
        - ``probability`` : float, the model's scalper-class probability
    """
    probability = float(pipeline.predict_proba(features)[0, 1])

    if probability >= high_threshold:
        label = "scalper"
    elif probability < low_threshold:
        label = "not_scalper"
    else:
        label = "uncertain"

    return {"label": label, "probability": probability}
