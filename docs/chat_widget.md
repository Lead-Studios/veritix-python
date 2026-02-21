# Chat Widget Implementation

## Overview

This document describes the real-time chat widget implementation for the Veritix platform. The chat system enables users to communicate with support agents through a responsive web widget with real-time messaging capabilities.

## Architecture

### Backend Components

1. **Chat Manager** (`src/chat.py`)
   - Manages WebSocket connections
   - Handles message routing and broadcasting
   - Maintains message history
   - Tracks conversation escalations

2. **FastAPI Endpoints** (`src/main.py`)
   - WebSocket endpoint for real-time communication
   - HTTP endpoints for message history and management
   - Escalation handling APIs

### Frontend Components

1. **Chat Widget** (`static/chat-widget.html`)
   - Self-contained HTML/CSS/JS widget
   - Real-time WebSocket communication
   - Message history display
   - Escalation notifications
   - Responsive design

2. **Demo Page** (`static/demo.html`)
   - Interactive demonstration
   - API endpoint testing
   - Connection status monitoring

## API Endpoints

### WebSocket Endpoints

```
WebSocket: /ws/chat/{conversation_id}/{user_id}
```
- **Purpose**: Real-time bidirectional communication
- **Parameters**:
  - `conversation_id`: Unique conversation identifier
  - `user_id`: User identifier
- **Message Format**:
```json
{
  "content": "Hello support!",
  "sender_type": "user",
  "metadata": {
    "timestamp": "2023-12-07T10:30:00Z"
  }
}
```

### HTTP Endpoints

#### Send Message
```
POST /chat/{conversation_id}/messages
```
**Request Body**:
```json
{
  "sender_id": "user_123",
  "sender_type": "user",
  "content": "Hello support!",
  "metadata": {}
}
```

#### Get Message History
```
GET /chat/{conversation_id}/history?limit=50
```
**Response**:
```json
{
  "conversation_id": "conv_123",
  "messages": [
    {
      "id": "msg_1",
      "sender_id": "user_123",
      "sender_type": "user",
      "content": "Hello!",
      "timestamp": "2023-12-07T10:30:00Z",
      "conversation_id": "conv_123"
    }
  ],
  "count": 1
}
```

#### Escalate Conversation
```
POST /chat/{conversation_id}/escalate
```
**Request Body**:
```json
{
  "reason": "complex_query",
  "metadata": {
    "user_feedback": "Need human assistance"
  }
}
```

#### Get Escalations
```
GET /chat/{conversation_id}/escalations
```

#### Get User Conversations
```
GET /chat/user/{user_id}/conversations
```

## Frontend Widget Features

### Core Functionality
- **Real-time Messaging**: WebSocket-based instant communication
- **Message History**: Automatic loading of previous conversations
- **User Identification**: Persistent user IDs via localStorage
- **Connection Management**: Automatic reconnection on disconnect
- **Responsive Design**: Works on desktop and mobile devices

### UI Components
- **Chat Trigger**: Floating bubble button to open chat
- **Message Display**: Different styling for user vs agent messages
- **Input Area**: Text input with send button
- **Typing Indicators**: Shows when support is typing
- **Escalation Banners**: Notifications for conversation escalation
- **Connection Status**: Visual feedback for connection state

### JavaScript API

```javascript
// Initialize chat widget
const chatWidget = new ChatWidget();

// Open/close chat
chatWidget.openChat();
chatWidget.closeChat();

// Send message programmatically
chatWidget.sendMessage("Hello support!");

// Escalate conversation
chatWidget.escalateConversation("complex_query");

// Check connection status
console.log(chatWidget.isConnected);
```

## Implementation Details

### Conversation Management
- Each user session creates a unique conversation ID
- User IDs are persisted in localStorage
- Message history is maintained per conversation
- Automatic cleanup of disconnected WebSocket connections

### Message Flow
1. User opens chat widget
2. WebSocket connection established
3. Message history loaded via HTTP
4. Real-time messages sent via WebSocket
5. Messages broadcast to all connected participants
6. Escalation events trigger notifications

### Error Handling
- **Connection Failures**: Automatic reconnection attempts
- **Message Failures**: Local queue with retry logic
- **Network Issues**: Graceful degradation to HTTP polling
- **Server Errors**: User-friendly error notifications

## Security Considerations

### Authentication
- User IDs should be tied to authenticated sessions
- Messages should include authentication tokens
- Rate limiting on message sending

### Data Protection
- Message encryption in transit (WebSocket over TLS)
- Input sanitization to prevent XSS
- Session timeout for inactive conversations

### Access Control
- Users can only access their own conversations
- Support agents need proper authorization
- Escalation requires appropriate permissions

## Testing

### Unit Tests
Located in `tests/test_chat.py`:
- ChatManager functionality
- Message routing and broadcasting
- Connection management
- Escalation handling
- API endpoint validation

### Integration Tests
- End-to-end message flow
- WebSocket connection lifecycle
- Concurrent user scenarios
- Error recovery scenarios

## Deployment

### Backend Requirements
- FastAPI with WebSocket support
- ASGI server (Uvicorn/Gunicorn)
- Proper CORS configuration
- Reverse proxy for production (Nginx)

### Frontend Integration
The widget can be integrated in two ways:

1. **Direct HTML Include**:
```html
<script src="/static/chat-widget.html"></script>
```

2. **Framework Integration**:
```javascript
// React/Vue component
import ChatWidget from './ChatWidget';

function App() {
  return (
    <div>
      <ChatWidget />
    </div>
  );
}
```

## Configuration

### Environment Variables
```env
# Backend
CHAT_HISTORY_LIMIT=50
CHAT_MAX_MESSAGE_LENGTH=1000
CHAT_CONNECTION_TIMEOUT=30

# Frontend
CHAT_BACKEND_URL=ws://localhost:8000
CHAT_RECONNECT_INTERVAL=3000
CHAT_TYPING_TIMEOUT=1000
```

## Monitoring and Analytics

### Key Metrics
- Active conversations
- Message volume
- Response times
- Escalation rates
- Connection success rates

### Logging
- Connection events
- Message transmission
- Error occurrences
- Escalation triggers

## Future Enhancements

### Planned Features
- **Rich Media Support**: Images, files, emojis
- **Typing Indicators**: Real-time typing status
- **Message Reactions**: Like/feedback system
- **Conversation Transfer**: Between support agents
- **Chat Bots**: AI-powered initial responses
- **Multi-language Support**: Internationalization

### Performance Improvements
- **Message Pagination**: Efficient history loading
- **Connection Pooling**: Optimized WebSocket usage
- **Caching**: Frequently accessed conversations
- **Compression**: Message payload optimization

## Troubleshooting

### Common Issues

1. **WebSocket Connection Failures**
   - Check backend URL configuration
   - Verify CORS settings
   - Ensure WebSocket support in reverse proxy

2. **Message Delivery Issues**
   - Monitor network connectivity
   - Check message size limits
   - Review server logs for errors

3. **History Loading Problems**
   - Verify database connectivity
   - Check conversation ID validity
   - Review API endpoint availability

### Debugging Steps
```bash
# Check backend health
curl http://localhost:8000/health

# Test WebSocket connection
# Use browser developer tools to monitor WebSocket traffic

# Check logs
tail -f logs/app.log | grep chat
```

## Example Usage

### Basic Integration
```html
<!DOCTYPE html>
<html>
<head>
    <title>Chat Demo</title>
</head>
<body>
    <!-- Your content -->
    
    <!-- Chat Widget -->
    <script src="/static/chat-widget.html"></script>
    
    <script>
        // Widget initializes automatically
        // Access via window.chatWidget if needed
    </script>
</body>
</html>
```

### Advanced Customization
```javascript
// Custom configuration
const chatWidget = new ChatWidget({
    backendUrl: 'wss://your-domain.com',
    theme: 'dark',
    position: 'bottom-left',
    autoOpen: false
});

// Event listeners
chatWidget.on('message', (message) => {
    console.log('New message:', message);
});

chatWidget.on('escalation', (escalation) => {
    console.log('Conversation escalated:', escalation);
});
```

This implementation provides a robust, scalable chat solution that can be easily integrated into the Veritix platform.