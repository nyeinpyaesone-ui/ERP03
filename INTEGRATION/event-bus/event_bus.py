"""
Event Bus Adapter for ERP03 Integration.

This module provides Redis-based pub/sub event bus for communication between
ERP-BACKEND and AI-BACKEND systems.
"""

import json
import asyncio
import logging
import redis.asyncio as redis
from typing import Optional, Dict, Any, List, Callable, Awaitable
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class EventType(str, Enum):
    """Standard event types in ERP03."""
    # CRM Events
    CUSTOMER_CREATED = "crm.customer.created"
    CUSTOMER_UPDATED = "crm.customer.updated"
    CUSTOMER_DELETED = "crm.customer.deleted"
    
    CONTACT_CREATED = "crm.contact.created"
    CONTACT_UPDATED = "crm.contact.updated"
    CONTACT_DELETED = "crm.contact.deleted"
    
    OPPORTUNITY_CREATED = "crm.opportunity.created"
    OPPORTUNITY_UPDATED = "crm.opportunity.updated"
    OPPORTUNITY_DELETED = "crm.opportunity.deleted"
    
    # Inventory Events
    PRODUCT_CREATED = "inventory.product.created"
    PRODUCT_UPDATED = "inventory.product.updated"
    PRODUCT_DELETED = "inventory.product.deleted"
    
    STOCK_ADJUSTED = "inventory.stock.adjusted"
    STOCK_MOVED = "inventory.stock.moved"
    STOCK_LOW = "inventory.stock.low"
    
    # Order Events
    ORDER_CREATED = "order.created"
    ORDER_UPDATED = "order.updated"
    ORDER_COMPLETED = "order.completed"
    ORDER_CANCELLED = "order.cancelled"
    
    # Finance Events
    INVOICE_CREATED = "finance.invoice.created"
    PAYMENT_RECEIVED = "finance.payment.received"
    PAYMENT_FAILED = "finance.payment.failed"
    
    # User Events
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_DELETED = "user.deleted"


@dataclass
class Event:
    """Event envelope structure."""
    event_id: str
    event_type: str
    event_version: str
    source: str
    correlation_id: Optional[str]
    timestamp: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    
    @classmethod
    def create(
        cls,
        event_type: str,
        data: Dict[str, Any],
        source: str = "erp-backend",
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> 'Event':
        """
        Create an event with generated identity, version, and UTC timestamp.
        
        Parameters:
            event_type (str): Event type identifier.
            data (Dict[str, Any]): Event payload.
            source (str): System that originated the event.
            correlation_id (Optional[str]): Identifier linking the event to a related operation.
            metadata (Optional[Dict[str, Any]]): Additional event metadata.
        
        Returns:
            Event: A newly initialized event with version ``v1``.
        """
        return cls(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            event_version="v1",
            source=source,
            correlation_id=correlation_id,
            timestamp=datetime.utcnow().isoformat(),
            data=data,
            metadata=metadata or {}
        )
    
    def to_json(self) -> str:
        """Serialize the event as a JSON string.
        
        Returns:
        	str: The JSON representation of the event.
        """
        return json.dumps(asdict(self))
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Event':
        """Deserialize an event from a JSON string.
        
        Parameters:
            json_str (str): JSON representation of the event.
        
        Returns:
            Event: The deserialized event.
        """
        data = json.loads(json_str)
        return cls(**data)


class EventBus:
    """
    Redis-based event bus for ERP03 integration.
    
    Features:
    - Publish/subscribe pattern
    - Event serialization/deserialization
    - Topic-based routing
    - Async support
    - Connection management
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "erp03.events"
    ):
        """Initialize an asynchronous event bus with Redis connection settings and empty subscription state.
        
        Parameters:
        	redis_url (str): Redis connection URL.
        	channel_prefix (str): Prefix used for event channels.
        """
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self._redis: Optional[redis.Redis] = None
        self._subscribers: Dict[str, List[Callable[[Event], Awaitable[None]]]] = {}
        self._pubsub: Optional[redis.client.PubSub] = None
        self._listen_task: Optional[asyncio.Task] = None
    
    async def connect(self):
        """Establish connection to Redis."""
        self._redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"EventBus connected to Redis: {self.redis_url}")
    
    async def disconnect(self):
        """Close the Redis connection and release associated event bus resources."""
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self._pubsub:
            await self._pubsub.close()
        
        if self._redis:
            await self._redis.close()
        
        logger.info("EventBus disconnected from Redis")
    
    def _get_channel_name(self, event_type: str) -> str:
        """Build the Redis channel name for an event type.
        
        Parameters:
        	event_type (str): Dot-separated event type used to derive the channel topic.
        
        Returns:
        	str: The channel prefix followed by the event topic."""
        # Convert event type to channel format (e.g., "crm.customer.created" -> "crm.customer.*")
        parts = event_type.split('.')
        if len(parts) >= 2:
            topic = f"{parts[0]}.{parts[1]}"
            return f"{self.channel_prefix}.{topic}"
        return f"{self.channel_prefix}.{event_type}"
    
    async def publish(self, event: Event):
        """
        Publish an event to the Redis event bus.
        
        Args:
            event: Event to publish.
        
        Raises:
            RuntimeError: If the event bus is not connected.
        """
        if not self._redis:
            raise RuntimeError("EventBus not connected. Call connect() first.")
        
        channel = self._get_channel_name(event.event_type)
        message = event.to_json()
        
        await self._redis.publish(channel, message)
        logger.debug(f"Published event {event.event_id} ({event.event_type}) to {channel}")
    
    async def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], Awaitable[None]]
    ):
        """
        Register an asynchronous handler for events matching the specified type.
        
        Parameters:
            event_type (str): Event type pattern to subscribe to, including supported wildcards.
            handler (Callable[[Event], Awaitable[None]]): Callback invoked for matching events.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to {event_type} with handler {handler.__name__}")
        
        # Start listener if not already running
        if not self._listen_task and self._redis:
            self._listen_task = asyncio.create_task(self._listen_loop())
    
    async def unsubscribe(
        self,
        event_type: str,
        handler: Optional[Callable[[Event], Awaitable[None]]] = None
    ):
        """
        Remove one handler or all handlers registered for an event type.
        
        Parameters:
        	event_type (str): Event type whose subscriptions should be removed.
        	handler (Optional[Callable[[Event], Awaitable[None]]]): Specific handler to remove; when omitted, remove all handlers for the event type.
        """
        if event_type in self._subscribers:
            if handler:
                self._subscribers[event_type].remove(handler)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
            else:
                del self._subscribers[event_type]
            
            logger.info(f"Unsubscribed from {event_type}")
    
    async def _listen_loop(self):
        """Listen for events and dispatch to handlers."""
        if not self._redis:
            return
        
        self._pubsub = self._redis.pubsub()
        
        # Subscribe to all channels
        channels = set()
        for event_type in self._subscribers.keys():
            channel = self._get_channel_name(event_type)
            channels.add(channel)
        
        if channels:
            await self._pubsub.subscribe(*channels)
            logger.info(f"Listening on channels: {channels}")
        
        try:
            async for message in self._pubsub.listen():
                if message['type'] == 'message':
                    await self._handle_message(message['channel'], message['data'])
        except asyncio.CancelledError:
            logger.info("EventBus listen loop cancelled")
        except Exception as e:
            logger.error(f"EventBus listen error: {e}")
            raise
    
    async def _handle_message(self, channel: str, data: str):
        """
        Dispatch an incoming event message to matching subscribers.
        
        Parameters:
        	channel (str): Redis channel that delivered the message.
        	data (str): JSON-encoded event message.
        """
        try:
            event = Event.from_json(data)
            logger.debug(f"Received event {event.event_id} ({event.event_type}) on {channel}")
            
            # Find matching handlers
            handlers = []
            for event_type, type_handlers in self._subscribers.items():
                if self._matches_event_type(event.event_type, event_type):
                    handlers.extend(type_handlers)
            
            # Execute handlers
            for handler in handlers:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler {handler.__name__} failed: {e}")
        
        except Exception as e:
            logger.error(f"Failed to handle message: {e}")
    
    def _matches_event_type(self, event_type: str, pattern: str) -> bool:
        """Determine whether an event type matches an exact pattern or trailing-prefix wildcard.
        
        Parameters:
        	event_type (str): The event type to evaluate.
        	pattern (str): The exact event type or trailing-prefix wildcard pattern.
        
        Returns:
        	bool: `true` if the event type matches the pattern, `false` otherwise.
        """
        if pattern.endswith('*'):
            prefix = pattern[:-1]
            return event_type.startswith(prefix)
        return event_type == pattern
    
    async def get_event_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Event]:
        """
        Get event history when persistence support is available.
        
        Currently returns an empty list because Redis Streams history is not implemented.
        
        Args:
            event_type: Optional event type filter.
            limit: Maximum number of events to retrieve.
        
        Returns:
            An empty list.
        """
        # This would require Redis Streams implementation
        # For now, return empty list
        logger.warning("Event history not implemented - requires Redis Streams")
        return []


# ============================================================================
# Synchronous version for non-async contexts
# ============================================================================

class EventBusSync:
    """Synchronous version of EventBus."""
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        channel_prefix: str = "erp03.events"
    ):
        """Initialize the synchronous event bus with Redis connection settings and no subscribers.
        
        Parameters:
        	redis_url (str): Redis server URL.
        	channel_prefix (str): Prefix used for event channel names.
        """
        self.redis_url = redis_url
        self.channel_prefix = channel_prefix
        self._redis: Optional[redis.Redis] = None
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
    
    def connect(self):
        """Establish connection to Redis."""
        self._redis = redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        logger.info(f"EventBusSync connected to Redis: {self.redis_url}")
    
    def disconnect(self):
        """Close Redis connection."""
        if self._redis:
            self._redis.close()
        logger.info("EventBusSync disconnected from Redis")
    
    def _get_channel_name(self, event_type: str) -> str:
        """Get full channel name for an event type."""
        parts = event_type.split('.')
        if len(parts) >= 2:
            topic = f"{parts[0]}.{parts[1]}"
            return f"{self.channel_prefix}.{topic}"
        return f"{self.channel_prefix}.{event_type}"
    
    def publish(self, event: Event):
        """
        Publish an event to the synchronous event bus.
        
        Parameters:
            event (Event): The event to publish.
        
        Raises:
            RuntimeError: If the event bus is not connected.
        """
        if not self._redis:
            raise RuntimeError("EventBusSync not connected. Call connect() first.")
        
        channel = self._get_channel_name(event.event_type)
        message = event.to_json()
        
        self._redis.publish(channel, message)
        logger.debug(f"Published event {event.event_id} ({event.event_type}) to {channel}")
    
    def subscribe(
        self,
        event_type: str,
        handler: Callable[[Event], None]
    ):
        """
        Subscribe a synchronous handler to events of a specified type.
        
        Parameters:
        	event_type (str): Event type to receive.
        	handler (Callable[[Event], None]): Function invoked for matching events.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed to {event_type} with handler {handler.__name__}")
    
    def unsubscribe(
        self,
        event_type: str,
        handler: Optional[Callable[[Event], None]] = None
    ):
        """
        Remove a synchronous event handler subscription.
        
        Parameters:
            event_type (str): Event type whose subscriptions are updated.
            handler (Optional[Callable[[Event], None]]): Handler to remove. When omitted, all handlers for the event type are removed.
        """
        if event_type in self._subscribers:
            if handler:
                self._subscribers[event_type].remove(handler)
                if not self._subscribers[event_type]:
                    del self._subscribers[event_type]
            else:
                del self._subscribers[event_type]
            logger.info(f"Unsubscribed from {event_type}")
