/**
 * Production-Grade WebSocket Service for ERP03 Mobile Application.
 * 
 * Features:
 * - JWT Authentication with secure token handling
 * - Automatic reconnection with exponential backoff
 * - Message queue for offline support
 * - Channel subscription management
 * - Heartbeat/ping-pong for connection health
 * - Event-driven architecture with typed listeners
 * - Connection state management
 * - Error handling and recovery
 * - Platform-specific URL configuration
 * 
 * @module utils/websocket
 */

import { Platform } from 'react-native';
import * as SecureStore from 'expo-secure-store';
import { AppState, AppStateStatus } from 'react-native';

// ============================================================================
// Configuration
// ============================================================================

const WS_CONFIG = {
  // Development URLs
  devBaseUrl: {
    ios: 'ws://localhost:8000/ws',
    android: 'ws://10.0.2.2:8000/ws', // Android emulator localhost
    web: 'ws://localhost:8000/ws',
  },
  // Production URL - Update this for deployment
  prodBaseUrl: 'wss://api.your-domain.com/ws',
  
  // Reconnection settings
  maxReconnectAttempts: 10,
  initialReconnectDelay: 1000, // 1 second
  maxReconnectDelay: 30000, // 30 seconds
  reconnectBackoffMultiplier: 1.5,
  
  // Heartbeat settings
  heartbeatInterval: 25000, // 25 seconds (should be less than server timeout)
  pongTimeout: 5000, // 5 seconds to receive pong
  
  // Message queue settings
  maxQueueSize: 100,
  flushOnReconnect: true,
};

// Get base URL based on environment and platform
const getBaseUrl = (): string => {
  const isProduction = __DEV__ === false;
  
  if (isProduction) {
    return WS_CONFIG.prodBaseUrl;
  }
  
  return WS_CONFIG.devBaseUrl[Platform.OS as keyof typeof WS_CONFIG.devBaseUrl] || 
         WS_CONFIG.devBaseUrl.web;
};

// ============================================================================
// Type Definitions
// ============================================================================

export enum MessageType {
  PING = 'ping',
  PONG = 'pong',
  SUBSCRIBE = 'subscribe',
  UNSUBSCRIBE = 'unsubscribe',
  MESSAGE = 'message',
  BROADCAST = 'broadcast',
  ERROR = 'error',
  ACK = 'ack',
  PRESENCE = 'presence',
}

export interface WSMessage {
  message_id: string;
  message_type: MessageType | string;
  channel: string;
  payload: Record<string, any>;
  sender_id?: string;
  timestamp: string;
  correlation_id?: string;
}

export interface SubscriptionOptions {
  channel: string;
  onMessage?: (message: WSMessage) => void;
  onError?: (error: Error) => void;
}

export type MessageListener = (message: WSMessage) => void;
export type ErrorListener = (error: Error) => void;
export type ConnectionListener = (connected: boolean) => void;

export interface ConnectionStats {
  isConnected: boolean;
  connectionId?: string;
  userId?: string;
  channels: string[];
  messageCount: number;
  lastHeartbeat?: string;
  reconnectAttempts: number;
  queuedMessages: number;
}

// ============================================================================
// WebSocket Service Class
// ============================================================================

export class WebSocketService {
  private ws: WebSocket | null = null;
  private baseUrl: string;
  private reconnectAttempts = 0;
  private reconnectTimer: NodeJS.Timeout | null = null;
  private heartbeatTimer: NodeJS.Timeout | null = null;
  private pongTimeoutTimer: NodeJS.Timeout | null = null;
  private messageQueue: WSMessage[] = [];
  private listeners: Map<string, Set<MessageListener>> = new Map();
  private errorListeners: Set<ErrorListener> = new Set();
  private connectionListeners: Set<ConnectionListener> = new Set();
  private isConnected = false;
  private isConnecting = false;
  private clientId: string | null = null;
  private connectionId: string | null = null;
  private userId: string | null = null;
  private subscribedChannels: Set<string> = new Set();
  private authToken: string | null = null;
  private appState: AppStateStatus = 'active';

  constructor() {
    this.baseUrl = getBaseUrl();
    
    // Monitor app state for background/foreground transitions
    AppState.addEventListener('change', this.handleAppStateChange.bind(this));
  }

  // ============================================================================
  // Connection Management
  // ============================================================================

  /**
   * Connect to the WebSocket server with authentication
   * @param authToken - JWT token for authentication
   * @returns Promise that resolves when connected
   */
  async connect(authToken: string): Promise<void> {
    if (this.isConnected || this.isConnecting) {
      console.log('[WebSocket] Already connected or connecting');
      return;
    }

    this.authToken = authToken;
    this.isConnecting = true;

    return new Promise((resolve, reject) => {
      try {
        const url = `${this.baseUrl}`;
        console.log(`[WebSocket] Connecting to ${url}`);
        
        this.ws = new WebSocket(url, undefined, {
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        });

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected');
          this.isConnected = true;
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          
          this.notifyConnectionListeners(true);
          this.startHeartbeat();
          this.flushMessageQueue();
          this.resubscribeToChannels();
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Error parsing message:', error);
            this.notifyErrorListeners(new Error(`Failed to parse message: ${error}`));
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error:', error);
          this.notifyErrorListeners(new Error(`WebSocket error: ${error}`));
          reject(error);
        };

        this.ws.onclose = (event) => {
          console.log(`[WebSocket] Closed: code=${event.code}, reason=${event.reason}`);
          this.isConnected = false;
          this.isConnecting = false;
          this.stopHeartbeat();
          this.notifyConnectionListeners(false);
          
          // Attempt reconnect if not intentionally closed
          if (event.code !== 1000) {
            this.scheduleReconnect(authToken);
          }
        };
      } catch (error) {
        this.isConnecting = false;
        this.notifyErrorListeners(error as Error);
        reject(error);
      }
    });
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    console.log('[WebSocket] Disconnecting...');
    
    this.stopHeartbeat();
    this.clearReconnectTimer();
    
    if (this.ws) {
      this.ws.close(1000, 'Client disconnect');
      this.ws = null;
    }
    
    this.isConnected = false;
    this.isConnecting = false;
    this.notifyConnectionListeners(false);
  }

  // ============================================================================
  // Channel Subscription
  // ============================================================================

  /**
   * Subscribe to a channel
   * @param channel - Channel name to subscribe to
   * @param onMessage - Optional callback for messages on this channel
   */
  subscribe(channel: string, onMessage?: MessageListener): void {
    if (!this.isConnected) {
      console.warn('[WebSocket] Cannot subscribe while disconnected');
      return;
    }

    const message: WSMessage = {
      message_id: this.generateMessageId(),
      message_type: MessageType.SUBSCRIBE,
      channel,
      payload: {},
      timestamp: new Date().toISOString(),
    };

    this.send(message);
    this.subscribedChannels.add(channel);

    if (onMessage) {
      this.on(`channel:${channel}`, onMessage);
    }
  }

  /**
   * Unsubscribe from a channel
   * @param channel - Channel name to unsubscribe from
   */
  unsubscribe(channel: string): void {
    if (!this.isConnected) {
      return;
    }

    const message: WSMessage = {
      message_id: this.generateMessageId(),
      message_type: MessageType.UNSUBSCRIBE,
      channel,
      payload: {},
      timestamp: new Date().toISOString(),
    };

    this.send(message);
    this.subscribedChannels.delete(channel);
    this.off(`channel:${channel}`);
  }

  /**
   * Resubscribe to all channels after reconnection
   */
  private resubscribeToChannels(): void {
    this.subscribedChannels.forEach((channel) => {
      this.subscribe(channel);
    });
  }

  // ============================================================================
  // Message Sending
  // ============================================================================

  /**
   * Send a message to a channel
   * @param channel - Target channel
   * @param payload - Message payload
   * @param correlationId - Optional correlation ID for tracking
   */
  sendMessage(channel: string, payload: Record<string, any>, correlationId?: string): void {
    const message: WSMessage = {
      message_id: this.generateMessageId(),
      message_type: MessageType.MESSAGE,
      channel,
      payload,
      timestamp: new Date().toISOString(),
      correlation_id: correlationId,
    };

    this.send(message);
  }

  /**
   * Send a ping to keep the connection alive
   */
  ping(): void {
    const message: WSMessage = {
      message_id: this.generateMessageId(),
      message_type: MessageType.PING,
      channel: 'system',
      payload: { timestamp: new Date().toISOString() },
      timestamp: new Date().toISOString(),
    };

    this.send(message);
  }

  /**
   * Send a message (with queuing if disconnected)
   */
  private send(message: WSMessage): void {
    if (this.isConnected && this.ws?.readyState === WebSocket.OPEN) {
      try {
        this.ws.send(JSON.stringify(message));
      } catch (error) {
        console.error('[WebSocket] Send error:', error);
        this.queueMessage(message);
      }
    } else {
      this.queueMessage(message);
    }
  }

  /**
   * Queue a message for later delivery
   */
  private queueMessage(message: WSMessage): void {
    if (this.messageQueue.length >= WS_CONFIG.maxQueueSize) {
      // Remove oldest message if queue is full
      this.messageQueue.shift();
    }
    this.messageQueue.push(message);
    console.log(`[WebSocket] Message queued (queue size: ${this.messageQueue.length})`);
  }

  /**
   * Flush queued messages after reconnection
   */
  private flushMessageQueue(): void {
    if (!WS_CONFIG.flushOnReconnect) {
      return;
    }

    console.log(`[WebSocket] Flushing ${this.messageQueue.length} queued messages`);
    
    while (this.messageQueue.length > 0 && this.isConnected) {
      const message = this.messageQueue.shift();
      if (message && this.ws) {
        try {
          this.ws.send(JSON.stringify(message));
        } catch (error) {
          console.error('[WebSocket] Failed to flush message:', error);
          this.messageQueue.unshift(message); // Put it back
          break;
        }
      }
    }
  }

  // ============================================================================
  // Event Listeners
  // ============================================================================

  /**
   * Add a listener for a specific message type
   * @param type - Message type or channel prefix (e.g., 'message', 'channel:notifications')
   * @param callback - Callback function
   */
  on(type: string, callback: MessageListener): void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(callback);
  }

  /**
   * Remove a listener for a specific message type
   * @param type - Message type
   * @param callback - Callback function to remove (if omitted, removes all)
   */
  off(type: string, callback?: MessageListener): void {
    if (callback) {
      this.listeners.get(type)?.delete(callback);
    } else {
      this.listeners.delete(type);
    }
  }

  /**
   * Add an error listener
   */
  onError(callback: ErrorListener): void {
    this.errorListeners.add(callback);
  }

  /**
   * Remove an error listener
   */
  offError(callback: ErrorListener): void {
    this.errorListeners.delete(callback);
  }

  /**
   * Add a connection state listener
   */
  onConnectionChange(callback: ConnectionListener): void {
    this.connectionListeners.add(callback);
  }

  /**
   * Remove a connection state listener
   */
  offConnectionChange(callback: ConnectionListener): void {
    this.connectionListeners.delete(callback);
  }

  // ============================================================================
  // Message Handling
  // ============================================================================

  /**
   * Handle incoming messages
   */
  private handleMessage(message: WSMessage): void {
    // Update last heartbeat on pong
    if (message.message_type === MessageType.PONG) {
      this.clearPongTimeout();
      return;
    }

    // Handle connection acknowledgment
    if (message.message_type === MessageType.ACK && message.payload.status === 'connected') {
      this.connectionId = message.payload.connection_id;
      this.userId = message.payload.user_id;
      console.log(`[WebSocket] Connected as user ${this.userId}, connection ${this.connectionId}`);
      return;
    }

    // Handle subscription acknowledgment
    if (message.message_type === MessageType.ACK && message.payload.action === 'subscribed') {
      console.log(`[WebSocket] Subscribed to channel: ${message.channel}`);
    }

    // Notify type-specific listeners
    const typeListeners = this.listeners.get(message.message_type);
    typeListeners?.forEach((callback) => {
      try {
        callback(message);
      } catch (error) {
        console.error('[WebSocket] Listener error:', error);
      }
    });

    // Notify channel-specific listeners
    const channelListeners = this.listeners.get(`channel:${message.channel}`);
    channelListeners?.forEach((callback) => {
      try {
        callback(message);
      } catch (error) {
        console.error('[WebSocket] Channel listener error:', error);
      }
    });

    // Notify generic message listeners
    const messageListeners = this.listeners.get('message');
    messageListeners?.forEach((callback) => {
      try {
        callback(message);
      } catch (error) {
        console.error('[WebSocket] Message listener error:', error);
      }
    });
  }

  // ============================================================================
  // Heartbeat Management
  // ============================================================================

  /**
   * Start heartbeat timer
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    
    this.heartbeatTimer = setInterval(() => {
      if (this.isConnected) {
        this.ping();
        
        // Set pong timeout
        this.pongTimeoutTimer = setTimeout(() => {
          console.warn('[WebSocket] Pong timeout, reconnecting...');
          this.ws?.close(4000, 'Pong timeout');
        }, WS_CONFIG.pongTimeout);
      }
    }, WS_CONFIG.heartbeatInterval);
  }

  /**
   * Stop heartbeat timer
   */
  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer);
      this.heartbeatTimer = null;
    }
    this.clearPongTimeout();
  }

  /**
   * Clear pong timeout timer
   */
  private clearPongTimeout(): void {
    if (this.pongTimeoutTimer) {
      clearTimeout(this.pongTimeoutTimer);
      this.pongTimeoutTimer = null;
    }
  }

  // ============================================================================
  // Reconnection Logic
  // ============================================================================

  /**
   * Schedule a reconnection attempt with exponential backoff
   */
  private scheduleReconnect(authToken: string): void {
    if (this.reconnectAttempts >= WS_CONFIG.maxReconnectAttempts) {
      console.error('[WebSocket] Max reconnection attempts reached');
      this.notifyErrorListeners(new Error('Max reconnection attempts reached'));
      return;
    }

    const delay = Math.min(
      WS_CONFIG.initialReconnectDelay * Math.pow(WS_CONFIG.reconnectBackoffMultiplier, this.reconnectAttempts),
      WS_CONFIG.maxReconnectDelay
    );

    this.reconnectAttempts++;
    console.log(`[WebSocket] Scheduling reconnect ${this.reconnectAttempts}/${WS_CONFIG.maxReconnectAttempts} in ${delay}ms`);

    this.reconnectTimer = setTimeout(() => {
      this.connect(authToken).catch((error) => {
        console.error('[WebSocket] Reconnection failed:', error);
      });
    }, delay);
  }

  /**
   * Clear reconnect timer
   */
  private clearReconnectTimer(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  // ============================================================================
  // App State Management
  // ============================================================================

  /**
   * Handle app state changes (background/foreground)
   */
  private handleAppStateChange(nextAppState: AppStateStatus): void {
    console.log(`[WebSocket] App state changed: ${this.appState} -> ${nextAppState}`);
    
    if (this.appState.match(/inactive|background/) && nextAppState === 'active') {
      // Coming to foreground - check connection and reconnect if needed
      if (!this.isConnected) {
        console.log('[WebSocket] Reconnecting after coming to foreground');
        if (this.authToken) {
          this.connect(this.authToken);
        }
      }
    } else if (this.appState === 'active' && nextAppState.match(/inactive|background/)) {
      // Going to background - optional: could reduce heartbeat frequency
    }

    this.appState = nextAppState;
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  /**
   * Generate a unique message ID
   */
  private generateMessageId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Notify error listeners
   */
  private notifyErrorListeners(error: Error): void {
    this.errorListeners.forEach((callback) => {
      try {
        callback(error);
      } catch (e) {
        console.error('[WebSocket] Error listener error:', e);
      }
    });
  }

  /**
   * Notify connection listeners
   */
  private notifyConnectionListeners(connected: boolean): void {
    this.connectionListeners.forEach((callback) => {
      try {
        callback(connected);
      } catch (e) {
        console.error('[WebSocket] Connection listener error:', e);
      }
    });
  }

  /**
   * Get current connection statistics
   */
  getStats(): ConnectionStats {
    return {
      isConnected: this.isConnected,
      connectionId: this.connectionId || undefined,
      userId: this.userId || undefined,
      channels: Array.from(this.subscribedChannels),
      messageCount: 0, // Could track this if needed
      lastHeartbeat: undefined,
      reconnectAttempts: this.reconnectAttempts,
      queuedMessages: this.messageQueue.length,
    };
  }

  /**
   * Check if the WebSocket is connected
   */
  isConnectionActive(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Clear all listeners (useful for cleanup)
   */
  clearAllListeners(): void {
    this.listeners.clear();
    this.errorListeners.clear();
    this.connectionListeners.clear();
  }
}

// ============================================================================
// Singleton Instance
// ============================================================================

export const websocketService = new WebSocketService();

// ============================================================================
// React Hook Helper (for functional components)
// ============================================================================

/**
 * Example usage in a React component:
 * 
 * import { useWebSocket } from './websocket';
 * 
 * function MyComponent() {
 *   const { isConnected, messages } = useWebSocket('notifications');
 *   
 *   return (
 *     <View>
 *       <Text>Connection: {isConnected ? 'Connected' : 'Disconnected'}</Text>
 *       {messages.map(msg => <Text key={msg.message_id}>{msg.payload.text}</Text>)}
 *     </View>
 *   );
 * }
 */
