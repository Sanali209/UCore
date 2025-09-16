# Messaging Domain Guide

## Purpose

The messaging domain provides event-driven communication within UCore, supporting both in-process and distributed messaging via EventBus and Redis.

---

## Main Classes & Components

- `EventBus`: Central event dispatcher for async/sync events.
- `Event`: Base class for all events.
- `RedisAdapter`: Redis-based event transport for distributed messaging.
- `RedisEventBridge`: Bridge for cross-process and cross-service event propagation.

---

## Usage Example

```python
from framework.messaging.event_bus import EventBus, Event

class MyEvent(Event):
    def __init__(self, data):
        self.data = data

def handle_event(event):
    print(f"Received: {event.data}")

bus = EventBus()
bus.subscribe(MyEvent, handle_event)
bus.publish(MyEvent("Hello"))
```

---

## Distributed Messaging Example

```python
from framework.messaging.redis_event_bridge import RedisEventBridge

bridge = RedisEventBridge(app, redis_url="redis://localhost:6379")
bridge.start()
```

---

## Extensibility & OOP

- Subclass `Event` for custom event types.
- Implement custom adapters for new transports.

---

## Integration Points

- Used by all domains for decoupled communication.
- Supports event filtering, async/sync handlers, and distributed events.

---

## See Also

- [Project Structure Guide](project-structure-guide.md)
- [UCore Framework Guide](ucore-framework-guide.md)
