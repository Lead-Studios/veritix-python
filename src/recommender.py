"""Item-based collaborative filtering recommender.

Implements cosine-similarity between event co-occurrence vectors using pure
Python (no numpy) as required by issue #159.
"""
import math
from typing import Dict, List, Optional


def build_item_similarity_matrix(
    user_events_dict: Dict[str, List[str]],
) -> Dict[str, Dict[str, float]]:
    """Build an item-item cosine similarity matrix from purchase history.

    Args:
        user_events_dict: Mapping of user_id → list of purchased event IDs.

    Returns:
        Nested dict similarity[event_a][event_b] = cosine similarity score.
    """
    all_events: List[str] = sorted(
        {event for events in user_events_dict.values() for event in events}
    )

    # Each event's co-occurrence vector: user_id → 1 if purchased, else absent.
    event_vectors: Dict[str, Dict[str, int]] = {
        event: {
            user: 1
            for user, events in user_events_dict.items()
            if event in events
        }
        for event in all_events
    }

    def _cosine(v1: Dict[str, int], v2: Dict[str, int]) -> float:
        dot = sum(v1.get(u, 0) * v2.get(u, 0) for u in set(v1) | set(v2))
        mag1 = math.sqrt(sum(x * x for x in v1.values()))
        mag2 = math.sqrt(sum(x * x for x in v2.values()))
        if mag1 == 0.0 or mag2 == 0.0:
            return 0.0
        return dot / (mag1 * mag2)

    similarity: Dict[str, Dict[str, float]] = {e: {} for e in all_events}
    for i, e1 in enumerate(all_events):
        for e2 in all_events[i + 1 :]:
            sim = _cosine(event_vectors[e1], event_vectors[e2])
            similarity[e1][e2] = sim
            similarity[e2][e1] = sim

    return similarity


def get_item_recommendations(
    user_id: str,
    user_events_dict: Dict[str, List[str]],
    similarity_matrix: Dict[str, Dict[str, float]],
    top_n: int = 3,
) -> List[str]:
    """Return top-N item-based recommendations for a user.

    Cold-start: if the user has no purchase history, returns the 3 most
    popular events (highest total purchase count across all users).

    Args:
        user_id: The user to generate recommendations for.
        user_events_dict: Full purchase history mapping.
        similarity_matrix: Pre-built item similarity matrix.
        top_n: Number of recommendations to return.

    Returns:
        List of recommended event IDs, ordered by descending score.
    """
    user_events: List[str] = user_events_dict.get(user_id, [])

    if not user_events:
        # Cold-start — return most popular events the user hasn't purchased.
        event_counts: Dict[str, int] = {}
        for events in user_events_dict.values():
            for e in events:
                event_counts[e] = event_counts.get(e, 0) + 1
        return sorted(event_counts, key=lambda k: event_counts[k], reverse=True)[:top_n]

    # Aggregate similarity scores for unseen events.
    user_set = set(user_events)
    scores: Dict[str, float] = {}
    for purchased in user_set:
        for candidate, sim in similarity_matrix.get(purchased, {}).items():
            if candidate not in user_set:
                scores[candidate] = scores.get(candidate, 0.0) + sim

    return sorted(scores, key=lambda k: scores[k], reverse=True)[:top_n]


def get_user_events_from_db(user_id: Optional[str] = None) -> Dict[str, List[str]]:
    """Retrieve user purchase history from the database.

    Falls back to an empty dict when the DB is unavailable so the cold-start
    path kicks in.  Replace the stub body with a real SQLAlchemy query once
    the user_event_purchases table exists.

    Args:
        user_id: If provided, only fetch history for this user.

    Returns:
        Mapping of user_id → list of purchased event IDs.
    """
    try:
        from src.config import get_settings
        from sqlalchemy import create_engine, text

        engine = create_engine(get_settings().DATABASE_URL, pool_pre_ping=True)
        with engine.connect() as conn:
            if user_id:
                rows = conn.execute(
                    text("SELECT user_id, event_id FROM user_event_purchases WHERE user_id = :uid"),
                    {"uid": user_id},
                ).fetchall()
            else:
                rows = conn.execute(
                    text("SELECT user_id, event_id FROM user_event_purchases")
                ).fetchall()
        result: Dict[str, List[str]] = {}
        for row in rows:
            result.setdefault(row[0], []).append(row[1])
        return result
    except Exception:
        return {}
