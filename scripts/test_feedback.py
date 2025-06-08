"""
Test script for the feedback collection system
"""

import asyncio
import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

def test_feedback_api():
    """Test feedback API endpoints"""
    print("🧪 Testing Feedback API...")
    
    # Authenticate
    auth_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if auth_response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    print("✅ Authentication successful")
    
    # Create a chat session
    session_response = requests.post(
        f"{API_BASE_URL}/chat/sessions",
        json={"escalation_id": None},
        headers=headers
    )
    
    if session_response.status_code != 200:
        print("❌ Failed to create chat session")
        return
    
    session_id = session_response.json()["session_id"]
    print(f"✅ Chat session created: {session_id}")
    
    # Send a message to simulate chat activity
    message_response = requests.post(
        f"{API_BASE_URL}/chat/sessions/{session_id}/messages",
        json={
            "content": "Hello, I need help with my account",
            "message_type": "text"
        },
        headers=headers
    )
    
    if message_response.status_code == 200:
        print("✅ Test message sent")
    
    # Test feedback creation
    feedback_data = {
        "rating": 5,
        "thumbs_rating": True,
        "feedback_text": "Great service! Very helpful agent.",
        "feedback_tags": ["Quick Response", "Helpful Agent", "Problem Solved"],
        "resolution_helpful": True,
        "response_time_rating": 4
    }
    
    feedback_response = requests.post(
        f"{API_BASE_URL}/chat/sessions/{session_id}/feedback",
        json=feedback_data,
        headers=headers
    )
    
    if feedback_response.status_code == 200:
        feedback = feedback_response.json()
        print(f"✅ Feedback created: ID {feedback['id']}")
        print(f"   Rating: {feedback['rating']}/5")
        print(f"   Thumbs: {'👍' if feedback['thumbs_rating'] else '👎'}")
        print(f"   Text: {feedback['feedback_text']}")
    else:
        print(f"❌ Failed to create feedback: {feedback_response.text}")
        return
    
    # Test getting feedback
    get_feedback_response = requests.get(
        f"{API_BASE_URL}/chat/sessions/{session_id}/feedback",
        headers=headers
    )
    
    if get_feedback_response.status_code == 200:
        print("✅ Retrieved session feedback")
    
    # Test feedback update
    update_data = {
        "rating": 4,
        "feedback_text": "Updated: Good service, could be faster."
    }
    
    update_response = requests.put(
        f"{API_BASE_URL}/chat/feedback/{feedback['id']}",
        json=update_data,
        headers=headers
    )
    
    if update_response.status_code == 200:
        print("✅ Feedback updated successfully")
    
    # Test getting predefined tags
    tags_response = requests.get(
        f"{API_BASE_URL}/chat/feedback/tags",
        headers=headers
    )
    
    if tags_response.status_code == 200:
        tags = tags_response.json()
        print(f"✅ Retrieved {len(tags)} predefined tags")
    
    # Test feedback statistics (admin only)
    stats_response = requests.get(
        f"{API_BASE_URL}/chat/feedback/stats?days=30",
        headers=headers
    )
    
    if stats_response.status_code == 200:
        stats = stats_response.json()
        print("✅ Feedback statistics:")
        print(f"   Total feedback: {stats['total_feedback']}")
        print(f"   Average rating: {stats['average_rating']}")
        print(f"   Thumbs up %: {stats['thumbs_up_percentage']}")
    
    # Test feedback history
    history_response = requests.get(
        f"{API_BASE_URL}/chat/feedback/my-history",
        headers=headers
    )
    
    if history_response.status_code == 200:
        history = history_response.json()
        print(f"✅ Retrieved {len(history)} feedback entries from history")
    
    # Test requesting feedback
    request_response = requests.post(
        f"{API_BASE_URL}/chat/sessions/{session_id}/request-feedback",
        headers=headers
    )
    
    if request_response.status_code == 200:
        print("✅ Feedback request sent successfully")
    
    print("\n🎉 All feedback API tests completed!")

def test_feedback_scenarios():
    """Test different feedback scenarios"""
    print("\n🎭 Testing Feedback Scenarios...")
    
    scenarios = [
        {
            "name": "Excellent Experience",
            "data": {
                "rating": 5,
                "thumbs_rating": True,
                "feedback_text": "Outstanding support! Resolved my issue quickly.",
                "feedback_tags": ["Quick Response", "Problem Solved", "Professional Service"],
                "resolution_helpful": True,
                "response_time_rating": 5
            }
        },
        {
            "name": "Good Experience",
            "data": {
                "rating": 4,
                "thumbs_rating": True,
                "feedback_text": "Good help, took a bit longer than expected.",
                "feedback_tags": ["Helpful Agent", "Clear Communication"],
                "resolution_helpful": True,
                "response_time_rating": 3
            }
        },
        {
            "name": "Poor Experience",
            "data": {
                "rating": 2,
                "thumbs_rating": False,
                "feedback_text": "Agent was not very helpful, issue not resolved.",
                "feedback_tags": [],
                "resolution_helpful": False,
                "response_time_rating": 2
            }
        },
        {
            "name": "Minimal Feedback",
            "data": {
                "thumbs_rating": True
            }
        }
    ]
    
    # Authenticate
    auth_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    for scenario in scenarios:
        print(f"\n📝 Testing: {scenario['name']}")
        
        # Create session for each scenario
        session_response = requests.post(
            f"{API_BASE_URL}/chat/sessions",
            json={"escalation_id": None},
            headers=headers
        )
        
        session_id = session_response.json()["session_id"]
        
        # Submit feedback
        feedback_response = requests.post(
            f"{API_BASE_URL}/chat/sessions/{session_id}/feedback",
            json=scenario["data"],
            headers=headers
        )
        
        if feedback_response.status_code == 200:
            print(f"   ✅ {scenario['name']} feedback submitted")
        else:
            print(f"   ❌ Failed to submit {scenario['name']} feedback")

if __name__ == "__main__":
    print("🚀 Starting Feedback System Tests")
    print("=" * 50)
    
    # Test basic API functionality
    test_feedback_api()
    
    # Test different feedback scenarios
    test_feedback_scenarios()
    
    print("\n✅ All tests completed!")
