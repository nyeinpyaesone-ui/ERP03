"""
Event Bus Package for ERP03 Integration.

This package provides Redis-based pub/sub event bus for communication
between ERP-BACKEND and AI-BACKEND systems.
"""

from .event_bus import (
    EventBus,
    EventBusSync,
    Event,
    EventType,
)

__all__ = [
    "EventBus",
    "EventBusSync",
    "Event",
    "EventType",
]
