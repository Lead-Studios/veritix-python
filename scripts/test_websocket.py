import asyncio
import websockets
import json
import requests
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
WS_BASE_URL = "ws://localhost:8000"

async def test_websocket_chat():
    """Test WebSocket chat functionality"""
    
    # First, authenticate and get token
    print("🔐 Authenticating...")
    auth_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    if auth_response.status_code != 200:
        print("❌ Authentication failed")
        return
    
    token = auth_response.json()["access_token"]
    print("✅ Authentication successful")
    
    # Create a chat session
    print("💬 Creating chat session...")
    session_response = requests.post(
        f"{API_BASE_URL}/chat/sessions",
        json={"escalation_id": None},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    if session_response.status_code != 200:
        print("❌ Failed to create chat session")
        return
    
    session_id = session_response.json()["session_id"]
    print(f"✅ Chat session created: {session_id}")
    
    # Connect to WebSocket
    ws_url = f"{WS_BASE_URL}/chat/ws/{session_id}?token={token}"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            print("🔌 WebSocket connected")
            
            # Send a test message
            test_message = {
                "action": "send_message",
                "message": "Hello from WebSocket test!",
                "message_type": "text"
            }
            
            await websocket.send(json.dumps(test_message))
            print("📤 Test message sent")
            
            # Send typing indicator
            typing_message = {"action": "typing"}
            await websocket.send(json.dumps(typing_message))
            print("⌨️ Typing indicator sent")
            
            # Stop typing
            await asyncio.sleep(2)
            stop_typing_message = {"action": "stop_typing"}
            await websocket.send(json.dumps(stop_typing_message))
            print("⌨️ Stop typing sent")
            
            # Listen for messages for 10 seconds
            print("👂 Listening for messages...")
            try:
                while True:
                    message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    data = json.loads(message)
                    print(f"📥 Received: {data['type']} - {data.get('data', {})}")
                    
            except asyncio.TimeoutError:
                print("⏰ Timeout reached")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

async def test_multiple_connections():
    """Test multiple WebSocket connections"""
    print("\n🔄 Testing multiple connections...")
    
    # Authenticate
    auth_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    token = auth_response.json()["access_token"]
    
    # Create session
    session_response = requests.post(
        f"{API_BASE_URL}/chat/sessions",
        json={"escalation_id": None},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    session_id = session_response.json()["session_id"]
    
    async def client_connection(client_id):
        ws_url = f"{WS_BASE_URL}/chat/ws/{session_id}?token={token}"
        
        try:
            async with websockets.connect(ws_url) as websocket:
                print(f"🔌 Client {client_id} connected")
                
                # Send a message
                message = {
                    "action": "send_message",
                    "message": f"Hello from client {client_id}!",
                    "message_type": "text"
                }
                
                await websocket.send(json.dumps(message))
                
                # Listen for a few messages
                for _ in range(3):
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                        data = json.loads(response)
                        print(f"📥 Client {client_id} received: {data['type']}")
                    except asyncio.TimeoutError:
                        break
                        
        except Exception as e:
            print(f"❌ Client {client_id} error: {e}")
    
    # Create multiple concurrent connections
    tasks = [client_connection(i) for i in range(3)]
    await asyncio.gather(*tasks)

def test_rest_api():
    """Test REST API endpoints"""
    print("\n🌐 Testing REST API...")
    
    # Authenticate
    auth_response = requests.post(f"{API_BASE_URL}/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    token = auth_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create session
    session_response = requests.post(
        f"{API_BASE_URL}/chat/sessions",
        json={"escalation_id": None},
        headers=headers
    )
    
    session_id = session_response.json()["session_id"]
    print(f"✅ Session created: {session_id}")
    
    # Send message via REST
    message_response = requests.post(
        f"{API_BASE_URL}/chat/sessions/{session_id}/messages",
        json={
            "content": "Hello from REST API!",
            "message_type": "text"
        },
        headers=headers
    )
    
    if message_response.status_code == 200:
        print("✅ Message sent via REST API")
    else:
        print(f"❌ Failed to send message: {message_response.text}")
    
    # Get messages
    messages_response = requests.get(
        f"{API_BASE_URL}/chat/sessions/{session_id}/messages",
        headers=headers
    )
    
    if messages_response.status_code == 200:
        messages = messages_response.json()
        print(f"✅ Retrieved {len(messages)} messages")
    else:
        print(f"❌ Failed to get messages: {messages_response.text}")
    
    # Get online users
    online_response = requests.get(
        f"{API_BASE_URL}/chat/online-users",
        headers=headers
    )
    
    if online_response.status_code == 200:
        online_users = online_response.json()
        print(f"✅ Online users: {len(online_users)}")
    else:
        print(f"❌ Failed to get online users: {online_response.text}")

async def main():
    """Main test function"""
    print("🚀 Starting WebSocket Chat Tests")
    print("=" * 50)
    
    # Test REST API first
    test_rest_api()
    
    # Test single WebSocket connection
    await test_websocket_chat()
    
    # Test multiple connections
    await test_multiple_connections()
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
