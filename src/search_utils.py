"""Search utilities for keyword extraction and event filtering using NLP."""
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


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

    location_keywords: List[str] = [
        "lagos",
        "abuja",
        "port harcourt",
        "kano",
        "ibadan",
        "benin",
        "kaduna",
        "jos",
        "enugu",
        "calabar",
    ]

    detected_locations: List[str] = []
    for location in location_keywords:
        if location in query_lower:
            detected_locations.append(location.title())

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

    return {
        "event_types": detected_event_types,
        "locations": detected_locations,
        "time_filter": time_filter,
        "keywords": general_keywords,
    }


def filter_events_by_keywords(
    events: List[Dict[str, Any]],
    keywords: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Filter events based on extracted keywords.

    Args:
        events: List of event dictionaries
        keywords: Dictionary of extracted keywords from extract_keywords()

    Returns:
        List of matching events
    """
    # No filters — return everything
    if not any([keywords["event_types"], keywords["locations"],
                keywords["time_filter"], keywords["keywords"]]):
        return events

    filtered_events: List[Dict[str, Any]] = []

    for event in events:
        matches = True

        if keywords["event_types"]:
            if event.get("event_type") not in keywords["event_types"]:
                matches = False

        if keywords["locations"] and matches:
            event_location: str = str(event.get("location", "")).lower()
            if not any(loc.lower() in event_location for loc in keywords["locations"]):
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

        if matches:
            filtered_events.append(event)

    return filtered_events