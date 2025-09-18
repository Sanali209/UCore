from typing import Callable, Dict, List, Any
from loguru import logger

class EventBus:
    """
    Simple event bus for decoupled messaging.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Any], None]]] = {}

    def subscribe(self, event_type: str, handler: Callable[[Any], None]):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)
        logger.info(f"Subscribed handler to event: {event_type}")

    def unsubscribe(self, event_type: str, handler: Callable[[Any], None]):
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(handler)
            logger.info(f"Unsubscribed handler from event: {event_type}")

    def publish(self, event_type: str, data: Any = None):
        handlers = self._subscribers.get(event_type, [])
        logger.info(f"Publishing event: {event_type} to {len(handlers)} handlers")
        for handler in handlers:
            handler(data)
