"""Search utilities for keyword extraction and event filtering using NLP."""
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.config import get_settings


def extract_keywords(query: str) -> Dict[str, Any]:
    """Extract keywords from a natural language search query.

    Args:
        query: Natural language search query
            e.g. "music events in Lagos this weekend"

    Returns:
        Dictionary with keys:
        - event_types: List[str]
        - locations: List[str]
        - time_filter: Optional[str]  one of today/tomorrow/this_weekend/…/None
        - keywords: List[str]  remaining general words
    """
    query_lower = query.lower()

    event_type_keywords: Dict[str, List[str]] = {
        "food": ["food", "culinary", "cooking", "chef"],
        "sports": ["sports", "football", "soccer", "basketball", "marathon", "game", "match", "tournament"],
        "tech": ["tech", "technology", "coding", "programming", "startup", "developer"],
        "conference": ["conference", "summit", "seminar", "workshop", "meetup"],
        "art": ["art", "exhibition", "gallery", "painting", "sculpture"],
        "culture": ["culture", "cultural", "traditional", "heritage"],
        "entertainment": ["comedy", "entertainment", "performance"],
        "music": ["music", "concert", "band", "jazz", "rock", "afrobeats"],
    }

    detected_event_types: List[str] = []
    matched_keywords: set[str] = set()

    for event_type, kws in event_type_keywords.items():
        for kw in kws:
            if kw in query_lower:
                detected_event_types.append(event_type)
                matched_keywords.add(kw)
                break

    known_locations_raw = get_settings().KNOWN_LOCATIONS
    location_keywords: List[str] = [
        loc.strip() for loc in known_locations_raw.split(",") if loc.strip()
    ]

    detected_locations: List[str] = []
    for location in location_keywords:
        if location in query_lower:
            detected_locations.append(location.title())

    # Detect potential unknown-city fuzzy candidates — words following a
    # location preposition that are not already matched to a known location.
    known_lower: set[str] = {loc.lower() for loc in location_keywords}
    fuzzy_locations: List[str] = []
    prep_hits = re.findall(r"\b(?:in|at|near)\s+([a-z][a-z ]+?)(?=\s+(?:this|today|tomorrow|next|week|month|weekend)\b|$)", query_lower)
    for hit in prep_hits:
        hit = hit.strip()
        if hit and hit not in known_lower:
            fuzzy_locations.append(hit)

    time_filter: Optional[str] = None
    if any(word in query_lower for word in ["today", "tonight"]):
        time_filter = "today"
    elif "tomorrow" in query_lower:
        time_filter = "tomorrow"
    elif any(phrase in query_lower for phrase in ["this weekend", "weekend"]):
        time_filter = "this_weekend"
    elif any(phrase in query_lower for phrase in ["this week", "week"]):
        time_filter = "this_week"
    elif any(phrase in query_lower for phrase in ["this month", "month"]):
        time_filter = "this_month"
    elif "next week" in query_lower:
        time_filter = "next_week"
    elif "next month" in query_lower:
        time_filter = "next_month"

    stop_words: set[str] = {
        "in", "at", "the", "a", "an", "and", "or", "for", "to", "of", "on",
        "this", "that", "with", "from", "by", "is", "are", "was", "were",
        "find", "search", "show", "me", "get", "list", "events", "event",
    }

    words = re.findall(r"\b[a-z]+\b", query_lower)
    general_keywords: List[str] = [
        word for word in words if word not in stop_words and len(word) > 2
    ]

    # Price-intent detection
    # "free" / "affordable" / "cheap" / "budget" → max_price hint
    # "premium" / "vip" / "luxury" / "expensive" → min_price hint
    nlp_min_price: Optional[float] = None
    nlp_max_price: Optional[float] = None

    if any(word in query_lower for word in ["free", "no cost", "zero"]):
        nlp_max_price = 0.0
    elif any(word in query_lower for word in ["cheap", "affordable", "budget", "low cost", "low-cost"]):
        nlp_max_price = 5000.0
    elif any(word in query_lower for word in ["premium", "vip", "luxury", "expensive", "high-end"]):
        nlp_min_price = 10000.0

    return {
        "event_types": detected_event_types,
        "locations": detected_locations,
        "fuzzy_locations": fuzzy_locations,
        "time_filter": time_filter,
        "keywords": general_keywords,
        "min_price": nlp_min_price,
        "max_price": nlp_max_price,
        "max_capacity": None,
    }


def filter_events_by_keywords(
    events: List[Dict[str, Any]],
    keywords: Dict[str, Any],
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    max_capacity: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Filter events based on extracted keywords and optional price/capacity filters.

    Args:
        events: List of event dictionaries
        keywords: Dictionary of extracted keywords from extract_keywords()
        min_price: Override/supplement NLP-inferred minimum price filter
        max_price: Override/supplement NLP-inferred maximum price filter
        max_capacity: Maximum venue capacity filter

    Returns:
        List of matching events
    """
    # Merge explicit filter params with NLP-inferred values (explicit takes precedence)
    effective_min_price: Optional[float] = min_price if min_price is not None else keywords.get("min_price")
    effective_max_price: Optional[float] = max_price if max_price is not None else keywords.get("max_price")
    effective_max_capacity: Optional[int] = max_capacity if max_capacity is not None else keywords.get("max_capacity")

    has_price_capacity_filter = (
        effective_min_price is not None
        or effective_max_price is not None
        or effective_max_capacity is not None
    )

    # No filters — return everything
    if not any([keywords["event_types"], keywords["locations"],
                keywords.get("fuzzy_locations"), keywords["time_filter"],
                keywords["keywords"]]):
                keywords["time_filter"], keywords["keywords"],
                has_price_capacity_filter]):
        return events

    filtered_events: List[Dict[str, Any]] = []

    for event in events:
        matches = True

        if keywords["event_types"]:
            if event.get("event_type") not in keywords["event_types"]:
                matches = False

        if keywords["locations"] and matches:
            event_location: str = str(event.get("location", "")).lower()
            event_city: str = str(event.get("city", "")).lower()
            if not any(
                loc.lower() in event_location or loc.lower() in event_city
                for loc in keywords["locations"]
            ):
                matches = False
        elif keywords.get("fuzzy_locations") and matches:
            # Fuzzy match: unknown city — try substring against location/city fields
            event_location = str(event.get("location", "")).lower()
            event_city = str(event.get("city", "")).lower()
            if not any(
                floc in event_location or floc in event_city
                for floc in keywords["fuzzy_locations"]
            ):
                matches = False

        if keywords["time_filter"] and matches:
            event_date_str: str = str(event.get("date", ""))
            time_match = False
            if event_date_str:
                try:
                    event_date = datetime.fromisoformat(event_date_str).date()
                    today = datetime.now().date()

                    tf: str = str(keywords["time_filter"])
                    if tf == "today":
                        time_match = event_date == today
                    elif tf == "tomorrow":
                        time_match = event_date == today + timedelta(days=1)
                    elif tf == "this_weekend":
                        days_until_saturday = (5 - today.weekday()) % 7
                        if days_until_saturday == 0 and today.weekday() == 5:
                            this_saturday = today
                        elif days_until_saturday == 0:
                            this_saturday = today + timedelta(days=7)
                        else:
                            this_saturday = today + timedelta(days=days_until_saturday)
                        this_sunday = this_saturday + timedelta(days=1)
                        time_match = event_date in [this_saturday, this_sunday]
                    elif tf == "this_week":
                        end_of_week = today + timedelta(days=(6 - today.weekday()))
                        time_match = today <= event_date <= end_of_week
                    elif tf == "next_week":
                        next_monday = today + timedelta(days=(7 - today.weekday()))
                        next_sunday = next_monday + timedelta(days=6)
                        time_match = next_monday <= event_date <= next_sunday
                    elif tf == "this_month":
                        time_match = (
                            event_date.year == today.year
                            and event_date.month == today.month
                        )
                    elif tf == "next_month":
                        next_month = today.replace(day=1) + timedelta(days=32)
                        next_month = next_month.replace(day=1)
                        time_match = (
                            event_date.year == next_month.year
                            and event_date.month == next_month.month
                        )
                except Exception:
                    time_match = False

            if not time_match:
                matches = False

        if keywords["keywords"] and matches:
            event_text = (
                f"{event.get('name', '')} {event.get('description', '')}".lower()
            )
            keyword_match = any(kw in event_text for kw in keywords["keywords"])
            if not keyword_match:
                if not (
                    keywords["event_types"]
                    or keywords["locations"]
                    or keywords["time_filter"]
                ):
                    matches = False

        # Price filters
        if matches and effective_min_price is not None:
            try:
                event_price = float(event.get("price", 0))
                if event_price < effective_min_price:
                    matches = False
            except (TypeError, ValueError):
                matches = False

        if matches and effective_max_price is not None:
            try:
                event_price = float(event.get("price", 0))
                if event_price > effective_max_price:
                    matches = False
            except (TypeError, ValueError):
                matches = False

        # Capacity filter
        if matches and effective_max_capacity is not None:
            try:
                event_capacity = int(event.get("capacity", 0))
                if event_capacity > effective_max_capacity:
                    matches = False
            except (TypeError, ValueError):
                matches = False

        if matches:
            filtered_events.append(event)

    return filtered_events