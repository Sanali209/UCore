# framework/component.py
from typing import TYPE_CHECKING, Callable, Type, Any, Optional

if TYPE_CHECKING:
    from .app import App
    from .config import Config
    from ..messaging.event_bus import EventBus
    from ..messaging.events import Event

# Use a module-level variable for lazy import to avoid circular dependency
_event_bus_class = None

class Component:
    """
    Base class for components that have a lifecycle managed by the App.
    Components can be initialized with a reference to the main App instance.
    """
    def __init__(self, app: Optional["App"] = None, name: Optional[str] = None):
        self.app = app
        self.name = name

    def start(self) -> None:
        """
        Called when the application starts.
        This method can be a coroutine.
        """
        pass

    def stop(self) -> None:
        """
        Called when the application stops.
        This method can be a coroutine.
        """
        pass

    def on_config_update(self, config: "Config") -> None:
        """
        Called when the application configuration is updated at runtime.
        Components can implement this method to react to configuration changes.
        """
        pass

    # Event bus helpers

    def get_event_bus(self) -> Optional["EventBus"]:
        """
        Get the application's event bus instance.

        Returns:
            EventBus: The shared event bus instance
        """
        # Only cache a valid event bus, never cache None
        if not hasattr(self, "_cached_event_bus"):
            self._cached_event_bus = None

        if self._cached_event_bus is not None:
            return self._cached_event_bus

        if self.app:
            try:
                from ..messaging.event_bus import EventBus
                event_bus = self.app.container.get(EventBus)
                if event_bus is not None:
                    self._cached_event_bus = event_bus
                    return event_bus
                else:
                    return None
            except Exception:
                return None
        return None

    def clear_event_bus_cache(self):
        """
        Clear the cached event bus instance (for testing or reinitialization).
        """
        if hasattr(self, "_cached_event_bus"):
            del self._cached_event_bus

    def subscribe(self, event_type: Type["Event"], handler: Optional[Callable] = None, **kwargs) -> Any:
        """
        Subscribe to events of a specific type.

        Can be used as decorator:
            @component.subscribe(MyEvent)
            def handle_event(event: MyEvent):
                pass

        Or programmatically:
            component.subscribe(MyEvent, my_handler)

        Args:
            event_type: The Event class to listen for
            handler: The handler function (for programmatic use)
            **kwargs: Additional arguments for subscribe method

        Returns:
            Decorator or handler ID
        """
        event_bus = self.get_event_bus()
        if event_bus is None:
            raise RuntimeError("Cannot subscribe to events: no app configured")

        if handler is None:
            # Used as decorator
            return event_bus.subscribe(event_type)
        else:
            # Programmatic subscription
            return event_bus.add_handler(event_type, handler, **kwargs)

    def publish(self, event: "Event") -> None:
        """
        Publish an event to the application's event bus.

        Args:
            event: The event to publish
        """
        event_bus = self.get_event_bus()
        if event_bus is None:
            raise RuntimeError("Cannot publish event: no app configured")
        event_bus.publish(event)

    def publish_async(self, event: "Event") -> None:
        """
        Publish an event asynchronously to the application's event bus.

        Args:
            event: The event to publish
        """
        event_bus = self.get_event_bus()
        if event_bus is None:
            raise RuntimeError("Cannot publish event: no app configured")
        import asyncio
        asyncio.create_task(event_bus.publish_async(event))
