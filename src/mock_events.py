"""Mock events data for search functionality."""
from datetime import datetime, timedelta
from typing import Any, Dict, List


def get_mock_events() -> List[Dict[str, Any]]:
    """Return a list of mock events with various attributes for search testing.

    Each event contains:
    - id: Unique identifier
    - name: Event name
    - description: Event description
    - event_type: Category (music, sports, tech, conference, etc.)
    - location: City/venue
    - date: Event date (ISO 8601 string)
    - price: Ticket price
    - capacity: Venue capacity
    """
    today = datetime.now()

    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0 and today.weekday() == 5:
        days_until_saturday = 0
    elif days_until_saturday == 0:
        days_until_saturday = 7

    this_saturday = today + timedelta(days=days_until_saturday)
    this_sunday = this_saturday + timedelta(days=1)
    next_week = today + timedelta(days=7)
    next_month = today + timedelta(days=30)

    mock_events: List[Dict[str, Any]] = [
        # Music events in Lagos
        {
            "id": "evt_001",
            "name": "Afrobeats Night Lagos",
            "description": "Experience the best of Afrobeats music with top Nigerian artists",
            "event_type": "music",
            "location": "Lagos",
            "date": this_saturday.isoformat(),
            "price": 5000.0,
            "capacity": 500,
        },
        {
            "id": "evt_002",
            "name": "Lagos Jazz Festival",
            "description": "Annual jazz festival featuring international and local artists",
            "event_type": "music",
            "location": "Lagos",
            "date": this_sunday.isoformat(),
            "price": 8000.0,
            "capacity": 1000,
        },
        {
            "id": "evt_003",
            "name": "Rock Concert Lagos",
            "description": "Rock music concert with live bands",
            "event_type": "music",
            "location": "Lagos",
            "date": next_week.isoformat(),
            "price": 6000.0,
            "capacity": 800,
        },
        # Music events in other locations
        {
            "id": "evt_004",
            "name": "Abuja Music Festival",
            "description": "Multi-genre music festival in the capital",
            "event_type": "music",
            "location": "Abuja",
            "date": this_saturday.isoformat(),
            "price": 7000.0,
            "capacity": 1500,
        },
        {
            "id": "evt_005",
            "name": "Port Harcourt Jazz Night",
            "description": "Intimate jazz performance",
            "event_type": "music",
            "location": "Port Harcourt",
            "date": next_month.isoformat(),
            "price": 4000.0,
            "capacity": 300,
        },
        # Sports events
        {
            "id": "evt_006",
            "name": "Lagos Marathon",
            "description": "Annual marathon event through Lagos city",
            "event_type": "sports",
            "location": "Lagos",
            "date": this_sunday.isoformat(),
            "price": 2000.0,
            "capacity": 5000,
        },
        {
            "id": "evt_007",
            "name": "Football Match: Lagos vs Abuja",
            "description": "Exciting football match between city rivals",
            "event_type": "sports",
            "location": "Lagos",
            "date": this_saturday.isoformat(),
            "price": 3000.0,
            "capacity": 2000,
        },
        {
            "id": "evt_008",
            "name": "Basketball Tournament",
            "description": "Inter-state basketball championship",
            "event_type": "sports",
            "location": "Abuja",
            "date": next_week.isoformat(),
            "price": 1500.0,
            "capacity": 1000,
        },
        # Tech/Conference events
        {
            "id": "evt_009",
            "name": "TechCon Lagos 2025",
            "description": "Leading technology conference in West Africa",
            "event_type": "tech",
            "location": "Lagos",
            "date": next_week.isoformat(),
            "price": 15000.0,
            "capacity": 500,
        },
        {
            "id": "evt_010",
            "name": "Startup Pitch Night",
            "description": "Startups pitching to investors",
            "event_type": "tech",
            "location": "Lagos",
            "date": this_saturday.isoformat(),
            "price": 5000.0,
            "capacity": 200,
        },
        {
            "id": "evt_011",
            "name": "AI & Machine Learning Summit",
            "description": "Conference on artificial intelligence and ML",
            "event_type": "conference",
            "location": "Abuja",
            "date": next_month.isoformat(),
            "price": 20000.0,
            "capacity": 300,
        },
        # Art & Culture events
        {
            "id": "evt_012",
            "name": "Lagos Art Exhibition",
            "description": "Contemporary African art showcase",
            "event_type": "art",
            "location": "Lagos",
            "date": this_sunday.isoformat(),
            "price": 2500.0,
            "capacity": 150,
        },
        {
            "id": "evt_013",
            "name": "Cultural Dance Festival",
            "description": "Traditional Nigerian dance performances",
            "event_type": "culture",
            "location": "Lagos",
            "date": next_week.isoformat(),
            "price": 3000.0,
            "capacity": 400,
        },
        # Food & Entertainment
        {
            "id": "evt_014",
            "name": "Lagos Food Festival",
            "description": "Culinary experience with top chefs",
            "event_type": "food",
            "location": "Lagos",
            "date": this_saturday.isoformat(),
            "price": 4000.0,
            "capacity": 600,
        },
        {
            "id": "evt_015",
            "name": "Comedy Night Lagos",
            "description": "Stand-up comedy with famous comedians",
            "event_type": "entertainment",
            "location": "Lagos",
            "date": this_sunday.isoformat(),
            "price": 3500.0,
            "capacity": 300,
        },
    ]

    return mock_events