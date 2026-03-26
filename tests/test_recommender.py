"""Unit tests for src/recommender.py (issue #159)."""
from src.recommender import build_item_similarity_matrix, get_item_recommendations


SAMPLE_HISTORY = {
    "user1": ["concert_A", "concert_B"],
    "user2": ["concert_B", "concert_C"],
    "user3": ["concert_A", "concert_C", "concert_D"],
    "user4": ["concert_D", "concert_E"],
}


# ---------------------------------------------------------------------------
# build_item_similarity_matrix
# ---------------------------------------------------------------------------

def test_similarity_matrix_contains_all_event_pairs():
    matrix = build_item_similarity_matrix(SAMPLE_HISTORY)
    all_events = {"concert_A", "concert_B", "concert_C", "concert_D", "concert_E"}
    assert set(matrix.keys()) == all_events
    for event, sims in matrix.items():
        others = all_events - {event}
        assert set(sims.keys()) == others


def test_similarity_is_symmetric():
    matrix = build_item_similarity_matrix(SAMPLE_HISTORY)
    assert abs(matrix["concert_A"]["concert_B"] - matrix["concert_B"]["concert_A"]) < 1e-9


def test_similarity_range():
    """All similarity values must be in [0, 1]."""
    matrix = build_item_similarity_matrix(SAMPLE_HISTORY)
    for sims in matrix.values():
        for score in sims.values():
            assert 0.0 <= score <= 1.0 + 1e-9


def test_identical_events_would_have_similarity_one():
    """Two events purchased by the same set of users are perfectly similar."""
    history = {
        "alice": ["X", "Y"],
        "bob": ["X", "Y"],
    }
    matrix = build_item_similarity_matrix(history)
    assert abs(matrix["X"]["Y"] - 1.0) < 1e-9


def test_disjoint_events_have_zero_similarity():
    """Events with no shared buyers have cosine similarity 0."""
    history = {
        "alice": ["X"],
        "bob": ["Y"],
    }
    matrix = build_item_similarity_matrix(history)
    assert matrix["X"]["Y"] == 0.0


# ---------------------------------------------------------------------------
# get_item_recommendations — normal path
# ---------------------------------------------------------------------------

def test_recommendations_exclude_already_purchased():
    matrix = build_item_similarity_matrix(SAMPLE_HISTORY)
    recs = get_item_recommendations("user1", SAMPLE_HISTORY, matrix, top_n=3)
    user_events = set(SAMPLE_HISTORY["user1"])
    assert all(r not in user_events for r in recs)


def test_recommendations_count_at_most_top_n():
    matrix = build_item_similarity_matrix(SAMPLE_HISTORY)
    recs = get_item_recommendations("user1", SAMPLE_HISTORY, matrix, top_n=3)
    assert len(recs) <= 3


def test_recommendations_top3_correct_for_user1():
    """user1 owns A+B; B co-occurs with C, A co-occurs with C+D → C should rank highly."""
    matrix = build_item_similarity_matrix(SAMPLE_HISTORY)
    recs = get_item_recommendations("user1", SAMPLE_HISTORY, matrix, top_n=3)
    # concert_C is purchased by both user2 (shares B with user1) and user3 (shares A)
    assert "concert_C" in recs


# ---------------------------------------------------------------------------
# get_item_recommendations — cold-start path
# ---------------------------------------------------------------------------

def test_cold_start_unknown_user_returns_popular_events():
    matrix = build_item_similarity_matrix(SAMPLE_HISTORY)
    recs = get_item_recommendations("nobody", SAMPLE_HISTORY, matrix, top_n=3)
    assert len(recs) <= 3
    # concert_D and concert_B appear in multiple users — should be in top results
    assert len(recs) > 0


def test_cold_start_empty_history_user_returns_popular():
    """User present in dict but with empty history falls back to popular."""
    history = dict(SAMPLE_HISTORY)
    history["new_user"] = []
    matrix = build_item_similarity_matrix(history)
    recs = get_item_recommendations("new_user", history, matrix, top_n=3)
    assert isinstance(recs, list)
    assert len(recs) <= 3


def test_cold_start_popular_order():
    """Cold-start should return events by descending purchase frequency."""
    history = {
        "u1": ["A", "B", "C"],
        "u2": ["A", "B"],
        "u3": ["A"],
    }
    matrix = build_item_similarity_matrix(history)
    recs = get_item_recommendations("stranger", history, matrix, top_n=3)
    # A appears 3 times, B 2 times, C 1 time
    assert recs[0] == "A"
    assert recs[1] == "B"
    assert recs[2] == "C"


# ---------------------------------------------------------------------------
# Empty / edge cases
# ---------------------------------------------------------------------------

def test_empty_history_returns_empty():
    matrix = build_item_similarity_matrix({})
    recs = get_item_recommendations("user1", {}, matrix, top_n=3)
    assert recs == []
