"""Search utilities for keyword extraction and event filtering using NLP."""
from datetime import datetime, timedelta
from typing import Dict, List, Any
import re


def extract_keywords(query: str) -> Dict[str, Any]:
    """
    Extract keywords from a natural language search query using simple NLP.
    
    Args:
        query: Natural language search query (e.g., "music events in Lagos this weekend")
        
    Returns:
        Dictionary containing extracted keywords:
        - event_types: List of event type keywords
        - locations: List of location keywords
        - time_filter: 'today', 'tomorrow', 'this_weekend', 'this_week', 'this_month', or None
        - keywords: All other relevant keywords
    """
    # Convert to lowercase for easier matching
    query_lower = query.lower()
    
    # Extract event types with priority (more specific keywords have higher priority)
    # Order matters - check more specific types first
    event_type_keywords = {
        'food': ['food', 'culinary', 'cooking', 'chef'],  # Check food first
        'sports': ['sports', 'football', 'soccer', 'basketball', 'marathon', 'game', 'match', 'tournament'],
        'tech': ['tech', 'technology', 'coding', 'programming', 'startup', 'developer'],
        'conference': ['conference', 'summit', 'seminar', 'workshop', 'meetup'],
        'art': ['art', 'exhibition', 'gallery', 'painting', 'sculpture'],
        'culture': ['culture', 'cultural', 'traditional', 'heritage'],
        'entertainment': ['comedy', 'entertainment', 'performance'],  # Comedy is specific
        'music': ['music', 'concert', 'band', 'jazz', 'rock', 'afrobeats'],  # Removed generic words
    }
    
    detected_event_types = []
    matched_keywords = set()
    
    # First pass: match specific keywords
    for event_type, keywords in event_type_keywords.items():
        for keyword in keywords:
            if keyword in query_lower:
                detected_event_types.append(event_type)
                matched_keywords.add(keyword)
                break  # Only add each event type once
    
    # Extract locations (Nigerian cities and common venues)
    location_keywords = [
        'lagos', 'abuja', 'port harcourt', 'kano', 'ibadan', 
        'benin', 'kaduna', 'jos', 'enugu', 'calabar'
    ]
    
    detected_locations = []
    for location in location_keywords:
        if location in query_lower:
            detected_locations.append(location.title())
    
    # Extract time filters
    time_filter = None
    today = datetime.now().date()
    
    # Check for time-related keywords
    if any(word in query_lower for word in ['today', 'tonight']):
        time_filter = 'today'
    elif 'tomorrow' in query_lower:
        time_filter = 'tomorrow'
    elif any(phrase in query_lower for phrase in ['this weekend', 'weekend']):
        time_filter = 'this_weekend'
    elif any(phrase in query_lower for phrase in ['this week', 'week']):
        time_filter = 'this_week'
    elif any(phrase in query_lower for phrase in ['this month', 'month']):
        time_filter = 'this_month'
    elif 'next week' in query_lower:
        time_filter = 'next_week'
    elif 'next month' in query_lower:
        time_filter = 'next_month'
    
    # Extract general keywords (filter out common words and already detected terms)
    stop_words = {
        'in', 'at', 'the', 'a', 'an', 'and', 'or', 'for', 'to', 'of', 'on',
        'this', 'that', 'with', 'from', 'by', 'is', 'are', 'was', 'were',
        'find', 'search', 'show', 'me', 'get', 'list', 'events', 'event'
    }
    
    words = re.findall(r'\b[a-z]+\b', query_lower)
    general_keywords = [
        word for word in words 
        if word not in stop_words and len(word) > 2
    ]
    
    return {
        'event_types': detected_event_types,
        'locations': detected_locations,
        'time_filter': time_filter,
        'keywords': general_keywords
    }


def filter_events_by_keywords(events: List[Dict[str, Any]], keywords: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Filter events based on extracted keywords.
    
    Args:
        events: List of event dictionaries
        keywords: Dictionary of extracted keywords from search query
        
    Returns:
        List of matching events
    """
    filtered_events = []
    
    # If there are no specific filters, return all events
    if not any([keywords['event_types'], keywords['locations'], 
               keywords['time_filter'], keywords['keywords']]):
        return events
    
    for event in events:
        matches = True
        
        # Check event type match (must match if specified)
        if keywords['event_types']:
            if event.get('event_type') not in keywords['event_types']:
                matches = False
        
        # Check location match (must match if specified)
        if keywords['locations'] and matches:
            event_location = event.get('location', '').lower()
            if not any(loc.lower() in event_location for loc in keywords['locations']):
                matches = False
        
        # Check time filter (must match if specified)
        if keywords['time_filter'] and matches:
            event_date_str = event.get('date', '')
            time_match = False
            if event_date_str:
                try:
                    event_date = datetime.fromisoformat(event_date_str).date()
                    today = datetime.now().date()
                    
                    if keywords['time_filter'] == 'today':
                        time_match = event_date == today
                    elif keywords['time_filter'] == 'tomorrow':
                        time_match = event_date == today + timedelta(days=1)
                    elif keywords['time_filter'] == 'this_weekend':
                        # Weekend is Saturday and Sunday
                        days_until_saturday = (5 - today.weekday()) % 7
                        if days_until_saturday == 0 and today.weekday() == 5:
                            this_saturday = today
                        elif days_until_saturday == 0:
                            this_saturday = today + timedelta(days=7)
                        else:
                            this_saturday = today + timedelta(days=days_until_saturday)
                        this_sunday = this_saturday + timedelta(days=1)
                        
                        time_match = event_date in [this_saturday, this_sunday]
                    elif keywords['time_filter'] == 'this_week':
                        end_of_week = today + timedelta(days=(6 - today.weekday()))
                        time_match = today <= event_date <= end_of_week
                    elif keywords['time_filter'] == 'next_week':
                        next_monday = today + timedelta(days=(7 - today.weekday()))
                        next_sunday = next_monday + timedelta(days=6)
                        time_match = next_monday <= event_date <= next_sunday
                    elif keywords['time_filter'] == 'this_month':
                        time_match = event_date.year == today.year and event_date.month == today.month
                    elif keywords['time_filter'] == 'next_month':
                        next_month = today.replace(day=1) + timedelta(days=32)
                        next_month = next_month.replace(day=1)
                        time_match = event_date.year == next_month.year and event_date.month == next_month.month
                except Exception:
                    time_match = False
            
            if not time_match:
                matches = False
        
        # Check general keyword matches in name and description (optional enhancement)
        # If there are other general keywords, they add to relevance but don't filter out
        if keywords['keywords'] and matches:
            event_text = f"{event.get('name', '')} {event.get('description', '')}".lower()
            # For general keywords, if they exist, at least one should match
            keyword_match = any(keyword in event_text for keyword in keywords['keywords'])
            if not keyword_match:
                # Only filter out if no other specific filters matched
                if not (keywords['event_types'] or keywords['locations'] or keywords['time_filter']):
                    matches = False
        
        if matches:
            filtered_events.append(event)
    
    # Sort by match score (events added in order, so maintain that order)
    return filtered_events
