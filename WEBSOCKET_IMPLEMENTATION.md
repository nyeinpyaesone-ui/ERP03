# WebSocket Implementation - Production Guide

## Overview

This document describes the production-grade WebSocket implementation for the ERP03 system, providing real-time bidirectional communication between the backend (FastAPI) and mobile clients (React Native/Expo).

## Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Mobile Client  │◄───────►│   FastAPI Server │◄───────►│   Redis Pub/Sub │
│  (WebSocketService)      │  (ConnectionManager)       │  (Cross-instance)│
└─────────────────┘         └──────────────────┘         └─────────────────┘
        │                           │                           │
        │ JWT Auth                  │ Channel Routing           │ Event Fanout
        │ Heartbeat                 │ Message Persistence       │ Multi-instance
        │ Auto-reconnect            │ Stats & Monitoring        │ Support
```

## Features

### Backend (FastAPI)

- **JWT Authentication**: Secure token-based authentication for all WebSocket connections
- **Redis Pub/Sub Integration**: Cross-instance messaging for horizontal scaling
- **Channel-based Subscription**: Topic-based pub/sub with automatic fanout
- **Heartbeat Monitoring**: Automatic ping/pong with timeout detection
- **Connection Management**: Graceful handling of connect/disconnect events
- **Message Acknowledgments**: Delivery confirmation with correlation IDs
- **Structured Logging**: Comprehensive logging for debugging and monitoring
- **Statistics Endpoint**: Real-time connection metrics via `/ws/stats`
- **REST Broadcast API**: Send messages via HTTP POST to `/ws/broadcast`

### Frontend (React Native)

- **JWT Authentication**: Secure connection with Bearer token in headers
- **Automatic Reconnection**: Exponential backoff with configurable limits
- **Message Queuing**: Offline message support with queue flushing on reconnect
- **Channel Management**: Subscribe/unsubscribe with automatic resubscription
- **Heartbeat/Ping-Pong**: Connection health monitoring
- **Event-driven Architecture**: Typed listeners for different message types
- **App State Handling**: Reconnect on foreground/background transitions
- **Connection Statistics**: Real-time stats via `getStats()` method
- **Error Handling**: Comprehensive error listeners and recovery

## Quick Start

### Backend Setup

1. **Install Dependencies** (already in requirements.txt):
```bash
pip install redis.asyncio fastapi uvicorn
```

2. **Configure Redis** in environment variables:
```bash
export REDIS_URL=redis://localhost:6379
```

3. **Run the Server**:
```bash
cd /workspace/erp-core/modules/completed
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

4. **Verify WebSocket Endpoint**:
- URL: `ws://localhost:8000/ws/`
- Auth: Bearer token in Authorization header
- Stats: `GET http://localhost:8000/ws/stats`

### Frontend Setup

1. **Import the Service**:
```typescript
import { websocketService, MessageType } from './src/utils/websocket';
```

2. **Connect with Authentication**:
```typescript
// Get auth token from your auth system
const authToken = await SecureStore.getItemAsync('authToken');

// Connect to WebSocket
await websocketService.connect(authToken);

// Listen for connection changes
websocketService.onConnectionChange((connected) => {
  console.log('Connection state:', connected);
});

// Listen for errors
websocketService.onError((error) => {
  console.error('WebSocket error:', error);
});
```

3. **Subscribe to Channels**:
```typescript
// Subscribe to notifications channel
websocketService.subscribe('notifications', (message) => {
  console.log('Notification received:', message.payload);
});

// Subscribe to multiple channels
websocketService.subscribe('orders');
websocketService.subscribe('inventory');
```

4. **Send Messages**:
```typescript
// Send a message to a channel
websocketService.sendMessage('general', {
  text: 'Hello from mobile!',
  timestamp: new Date().toISOString()
}, 'unique-correlation-id');

// Manually send ping (usually automatic)
websocketService.ping();
```

5. **Handle Incoming Messages**:
```typescript
// Listen for specific message types
websocketService.on(MessageType.MESSAGE, (message) => {
  console.log('Message received:', message);
});

// Listen for acknowledgments
websocketService.on(MessageType.ACK, (message) => {
  if (message.payload.action === 'sent') {
    console.log(`Message delivered to ${message.payload.recipients} recipients`);
  }
});

// Listen for channel-specific messages
websocketService.on('channel:notifications', (message) => {
  // Handle notification-specific logic
  showNotification(message.payload);
});
```

6. **Disconnect**:
```typescript
// Graceful disconnect
websocketService.disconnect();
```

## Message Protocol

### Message Structure

All messages follow this envelope structure:

```json
{
  "message_id": "uuid-string",
  "message_type": "message|ping|pong|subscribe|unsubscribe|ack|error",
  "channel": "channel-name",
  "payload": { ... },
  "sender_id": "user-id",
  "timestamp": "2024-01-15T10:30:00Z",
  "correlation_id": "optional-correlation-id"
}
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `ping` | Client → Server | Keep-alive heartbeat |
| `pong` | Server → Client | Heartbeat response |
| `subscribe` | Client → Server | Subscribe to channel |
| `unsubscribe` | Client → Server | Unsubscribe from channel |
| `message` | Both | Regular message payload |
| `broadcast` | Server → Client | Broadcast to all subscribers |
| `ack` | Both | Acknowledgment with status |
| `error` | Server → Client | Error notification |

### Example Flows

#### Connection Flow
```
Client → Server: [HTTP Upgrade with Bearer Token]
Server → Client: {"type":"ack","payload":{"status":"connected","connection_id":"...",...}}
```

#### Subscribe Flow
```
Client → Server: {"type":"subscribe","channel":"notifications"}
Server → Client: {"type":"ack","payload":{"action":"subscribed","channel":"notifications"}}
```

#### Message Flow
```
Client → Server: {"type":"message","channel":"general","payload":{"text":"Hello"}}
Server → Client: {"type":"ack","payload":{"action":"sent","message_id":"...","recipients":5}}
Server → Other Clients: {"type":"message","channel":"general","payload":{"text":"Hello"},...}
```

## Configuration

### Backend Configuration

Edit `/workspace/erp-core/modules/completed/config.py`:

```python
class Settings(BaseSettings):
    # Redis connection
    REDIS_URL: str = "redis://localhost:6379"
    
    # Heartbeat settings (seconds)
    # Configured in websocket.py ConnectionManager
    # _heartbeat_interval = 30
    # _heartbeat_timeout = 90
```

### Frontend Configuration

Edit `/workspace/mobile/src/utils/websocket.ts`:

```typescript
const WS_CONFIG = {
  // URLs
  devBaseUrl: {
    ios: 'ws://localhost:8000/ws',
    android: 'ws://10.0.2.2:8000/ws',
    web: 'ws://localhost:8000/ws',
  },
  prodBaseUrl: 'wss://api.your-domain.com/ws',
  
  // Reconnection
  maxReconnectAttempts: 10,
  initialReconnectDelay: 1000,
  maxReconnectDelay: 30000,
  reconnectBackoffMultiplier: 1.5,
  
  // Heartbeat
  heartbeatInterval: 25000,
  pongTimeout: 5000,
  
  // Queue
  maxQueueSize: 100,
  flushOnReconnect: true,
};
```

## Monitoring & Debugging

### Backend Stats Endpoint

```bash
curl http://localhost:8000/ws/stats
```

Response:
```json
{
  "total_connections": 15,
  "unique_users": 10,
  "active_channels": 5,
  "redis_connected": true
}
```

### Frontend Stats

```typescript
const stats = websocketService.getStats();
console.log(stats);
// { isConnected, connectionId, userId, channels, reconnectAttempts, queuedMessages }
```

### Logging

Backend logs include:
- Connection events (connect/disconnect)
- Subscription events
- Message delivery status
- Heartbeat timeouts
- Redis connection status
- Errors with stack traces

Frontend logs include:
- Connection state changes
- Message queue status
- Reconnection attempts
- App state transitions
- Listener errors

## Production Deployment

### Backend

1. **Use WSS (WebSocket Secure)** in production
2. **Configure Redis** for production (cluster/sentinel if needed)
3. **Set up load balancer** with WebSocket support (sticky sessions not required due to Redis pub/sub)
4. **Monitor connection counts** and set up alerts
5. **Configure firewall** to allow WebSocket traffic

### Frontend

1. **Update `prodBaseUrl`** to your production WSS endpoint
2. **Test reconnection** in various network conditions
3. **Implement proper cleanup** in component unmount
4. **Handle authentication refresh** before token expiry
5. **Test background/foreground** transitions thoroughly

## Security Considerations

1. **Always use WSS** (WebSocket over TLS) in production
2. **Validate JWT tokens** on every connection
3. **Implement rate limiting** per connection (use existing SlowRateLimiter)
4. **Sanitize message payloads** before broadcasting
5. **Limit message size** to prevent DoS attacks
6. **Monitor for abuse patterns** (excessive subscriptions, messages)
7. **Implement proper CORS** for WebSocket upgrades
8. **Use secure token storage** on mobile (SecureStore)

## Troubleshooting

### Common Issues

**Connection Fails Immediately**
- Check Redis is running and accessible
- Verify JWT token is valid
- Check network connectivity
- Review server logs for errors

**Messages Not Delivered**
- Verify channel subscription succeeded
- Check message type matches listener
- Ensure payload is JSON-serializable
- Review acknowledgment responses

**Frequent Disconnections**
- Adjust heartbeat interval/timeout
- Check network stability
- Review app background behavior
- Monitor Redis connection health

**Memory Leaks**
- Ensure listeners are removed on unmount
- Check message queue doesn't grow indefinitely
- Verify connections are properly closed

## API Reference

### WebSocketService Class

| Method | Parameters | Returns | Description |
|--------|------------|---------|-------------|
| `connect(authToken)` | `string` | `Promise<void>` | Establish connection |
| `disconnect()` | - | `void` | Close connection |
| `subscribe(channel, onMessage?)` | `string`, `Function?` | `void` | Subscribe to channel |
| `unsubscribe(channel)` | `string` | `void` | Unsubscribe from channel |
| `sendMessage(channel, payload, correlationId?)` | `string`, `object`, `string?` | `void` | Send message |
| `ping()` | - | `void` | Send heartbeat |
| `on(type, callback)` | `string`, `Function` | `void` | Add listener |
| `off(type, callback?)` | `string`, `Function?` | `void` | Remove listener |
| `onError(callback)` | `Function` | `void` | Add error listener |
| `onConnectionChange(callback)` | `Function` | `void` | Add connection listener |
| `getStats()` | - | `ConnectionStats` | Get connection stats |
| `isConnectionActive()` | - | `boolean` | Check connection state |

## Testing

### Backend Tests

```python
# Test WebSocket connection
async def test_websocket_connection():
    async with AsyncClient() as client:
        async with client.websocket_connect("/ws/", headers={"Authorization": "Bearer token"}) as ws:
            data = await ws.receive_json()
            assert data["message_type"] == "ack"
            assert data["payload"]["status"] == "connected"
```

### Frontend Tests

```typescript
// Test connection
test('should connect successfully', async () => {
  await websocketService.connect('valid-token');
  expect(websocketService.isConnectionActive()).toBe(true);
});

// Test message sending
test('should send message to channel', () => {
  websocketService.sendMessage('test-channel', { text: 'hello' });
  // Assert message was sent or queued
});
```

## Future Enhancements

- [ ] Message persistence and history retrieval
- [ ] Typing indicators for chat channels
- [ ] Read receipts and delivery tracking
- [ ] File/media transfer over WebSocket
- [ ] End-to-end encryption for sensitive channels
- [ ] Presence system (online/offline status)
- [ ] Rate limiting per user/channel
- [ ] Message compression for large payloads

## Support

For issues or questions:
1. Check logs (backend and frontend)
2. Review this documentation
3. Check existing GitHub issues
4. Contact the development team

---

**Version**: 1.0.0  
**Last Updated**: 2024  
**Maintainers**: ERP03 Development Team
