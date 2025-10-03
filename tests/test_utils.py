import os
import json

from src.utils import compute_signature, generate_synthetic_event_data


def test_compute_signature_consistency():
    d = {"a": 1, "b": "x"}
    s1 = compute_signature(d)
    s2 = compute_signature(d)
    assert isinstance(s1, str)
    assert s1 == s2


def test_generate_synthetic_event_data_returns_shapes():
    X, y = generate_synthetic_event_data(num_samples=100, random_seed=0)
    # Expect 100 rows and 6 features
    assert X.shape[0] == 100
    assert X.shape[1] == 6
    assert y.shape[0] == 100
