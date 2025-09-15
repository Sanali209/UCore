"""
Messaging and Event System Components

This package contains event-driven communication components:
- EventBus: Central event management and routing
- Event types and event handling
- RedisAdapter: Redis-based messaging adapter
- RedisEventBridge: Distributed event communication between instances
- Pub/sub patterns and message passing
"""

from .event_bus import EventBus
from .events import (
    Event,
    ComponentStartedEvent,
    ComponentStoppedEvent,
    AppStartedEvent,
    AppStoppedEvent,
    ConfigUpdatedEvent,
    UserEvent,
    EventFilter
)
from .redis_adapter import RedisAdapter
from .redis_event_bridge import EventBusRedisBridge, EventBusToRedisBridge, RedisToEventBusBridge

__all__ = [
    'EventBus', 'Event',
    'ComponentStartedEvent', 'ComponentStoppedEvent',
    'AppStartedEvent', 'AppStoppedEvent',
    'ConfigUpdatedEvent', 'UserEvent', 'EventFilter',
    'RedisAdapter', 'EventBusRedisBridge', 'EventBusToRedisBridge', 'RedisToEventBusBridge'
]
