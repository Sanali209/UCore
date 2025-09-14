"""
UCore Framework - Event Bus
Core event publish/subscribe system for in-process component communication.
"""

import asyncio
import inspect
import logging
from collections import defaultdict
from typing import Any, Callable, Dict, List, Type, Union, Tuple, Optional
from .events import Event


class EventHandlerInfo:
    """Internal class to track handler information"""

    def __init__(self,
                 handler: Callable,
                 handler_id: str,
                 priority: int = 0,
                 filters: Optional[List] = None):
        self.handler = handler
        self.handler_id = handler_id
        self.priority = priority
        self.filters = filters or []

    def matches_event(self, event: Event) -> bool:
        """Check if this handler matches the given event"""
        if not self.filters:
            return True

        # Apply all filters
        for filter_obj in self.filters:
            if hasattr(filter_obj, 'matches'):
                if not filter_obj.matches(event):
                    return False
            else:
                # Assume it's a callable filter
                try:
                    if not filter_obj(event):
                        return False
                except Exception:
                    return False

        return True


class EventBus:
    """
    Central event bus for publish/subscribe pattern.

    Features:
    - Type-safe event handling
    - Synchronous and asynchronous event publishing
    - Middleware pipeline for event processing
    - Error isolation per handler
    - Handler prioritization
    - Event filtering

    Usage:
        bus = EventBus()

        # Subscribe to events
        @bus.subscribe(ComponentStartedEvent)
        def handle_component_start(event: ComponentStartedEvent):
            print(f"Component {event.component_name} started")

        # Publish events
        event = ComponentStartedEvent(component_name="MyComponent", component_type=str)
        bus.publish(event)
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        self._handlers: Dict[Type[Event], List[EventHandlerInfo]] = defaultdict(list)
        self._middlewares: List[Callable[[Event, Callable], Any]] = []
        self._logger = logger or logging.getLogger(__name__)
        self._next_handler_id = 0
        self._running = True

    def subscribe(self,
                  event_type: Type[Event],
                  priority: int = 0,
                  filters: Optional[List] = None) -> Callable:
        """
        Decorator to subscribe a function to an event type.

        Args:
            event_type: The Event class to listen for
            priority: Handler priority (higher = called earlier)
            filters: List of filter objects/callables to apply

        Returns:
            Decorator function

        Usage:
            @event_bus.subscribe(ComponentStartedEvent)
            def handle_event(event: ComponentStartedEvent):
                pass
        """
        def decorator(handler: Callable) -> Callable:
            self._add_handler(event_type, handler, priority, filters)
            return handler
        return decorator

    def add_handler(self,
                    event_type: Type[Event],
                    handler: Callable,
                    priority: int = 0,
                    filters: Optional[List] = None) -> str:
        """
        Add an event handler programmatically.

        Args:
            event_type: The Event class to listen for
            handler: The handler function
            priority: Handler priority (higher = called earlier)
            filters: List of filter objects/callables to apply

        Returns:
            Handler ID for later removal
        """
        return self._add_handler(event_type, handler, priority, filters)

    def remove_handler(self, event_type: Type[Event], handler_id: str) -> bool:
        """
        Remove a specific handler by its ID.

        Args:
            event_type: The Event class
            handler_id: Handler ID returned from add_handler

        Returns:
            True if handler was removed, False if not found
        """
        if event_type not in self._handlers:
            return False

        handlers = self._handlers[event_type]
        for i, handler_info in enumerate(handlers):
            if handler_info.handler_id == handler_id:
                handlers.pop(i)
                self._logger.debug(f"Removed handler {handler_id} for {event_type.__name__}")
                return True

        return False

    def publish(self, event: Event) -> None:
        """
        Publish an event synchronously.

        Args:
            event: The event to publish

        Note:
            This method blocks until all handlers complete.
            For async contexts, use publish_async() instead.
        """
        if not self._running:
            self._logger.warning("Event bus is shutting down, skipping event publishing")
            return

        self._logger.debug(f"Publishing event: {event.__class__.__name__} from {event.source}")

        # Apply middleware pipeline
        processed_event = self._apply_middlewares(event)

        # Get and sort handlers by priority
        handlers = self._get_handlers(event, processed_event)

        # Execute handlers synchronously
        for handler_info in handlers:
            try:
                self._execute_handler_sync(handler_info, processed_event)
            except Exception as e:
                self._logger.error(f"Error in event handler {handler_info.handler_id}: {e}", exc_info=True)

    async def publish_async(self, event: Event) -> None:
        """
        Publish an event asynchronously.

        Args:
            event: The event to publish
        """
        if not self._running:
            self._logger.warning("Event bus is shutting down, skipping event publishing")
            return

        self._logger.debug(f"Async publishing event: {event.__class__.__name__} from {event.source}")

        # Apply middleware pipeline (potentially async)
        processed_event = await self._apply_middlewares_async(event)

        # Get and sort handlers by priority
        handlers = self._get_handlers(event, processed_event)

        # Execute handlers asynchronously
        tasks = []
        for handler_info in handlers:
            task = asyncio.create_task(
                self._execute_handler_async(handler_info, processed_event)
            )
            tasks.append(task)

        # Wait for all handlers to complete or gather errors
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    def add_middleware(self, middleware: Callable) -> None:
        """
        Add a middleware function to the event processing pipeline.

        Middleware format:
            def my_middleware(event):
                # Pre-processing
                processed_event = modify_event(event)
                return processed_event  # Return modified event or None to keep original

        Args:
            middleware: A callable that takes (event) and optionally returns a modified event
        """
        self._middlewares.append(middleware)
        self._logger.debug(f"Added middleware: {middleware}")

    def get_handler_count(self, event_type: Optional[Type[Event]] = None) -> int:
        """
        Get the number of handlers for a specific event type or total.

        Args:
            event_type: Specific event type, or None for all handlers

        Returns:
            Number of handlers
        """
        if event_type is None:
            return sum(len(handlers) for handlers in self._handlers.values())
        else:
            return len(self._handlers[event_type])

    def get_event_types(self) -> List[Type[Event]]:
        """
        Get list of all event types that have handlers.

        Returns:
            List of Event classes
        """
        return list(self._handlers.keys())

    def clear_handlers(self, event_type: Optional[Type[Event]] = None) -> int:
        """
        Clear all handlers for a specific event type or all handlers.

        Args:
            event_type: Specific event type, or None for all

        Returns:
            Number of handlers removed
        """
        if event_type is None:
            total = self.get_handler_count()
            self._handlers.clear()
            self._logger.info(f"Cleared all {total} handlers")
            return total
        else:
            count = len(self._handlers[event_type])
            self._handlers[event_type].clear()
            self._logger.info(f"Cleared {count} handlers for {event_type.__name__}")
            return count

    def shutdown(self) -> None:
        """Shut down the event bus gracefully"""
        self._running = False
        self.clear_handlers()
        self._middlewares.clear()
        self._logger.info("Event bus shut down")

    def _add_handler(self,
                     event_type: Type[Event],
                     handler: Callable,
                     priority: int = 0,
                     filters: Optional[List] = None) -> str:
        """Internal method to add a handler"""
        if not callable(handler):
            raise ValueError("Handler must be callable")

        handler_id = f"{event_type.__name__}_{self._next_handler_id}"
        self._next_handler_id += 1

        handler_info = EventHandlerInfo(handler, handler_id, priority, filters)
        self._handlers[event_type].append(handler_info)

        # Sort handlers by priority (highest first)
        self._handlers[event_type].sort(key=lambda h: h.priority, reverse=True)

        self._logger.debug(f"Added handler {handler_id} for {event_type.__name__} with priority {priority}")
        return handler_id

    def _get_handlers(self, event: Event, processed_event: Event) -> List[EventHandlerInfo]:
        """Get handlers that match the event, sorted by priority"""
        if type(event) not in self._handlers:
            return []

        # Filter handlers that match the processed event
        matching_handlers = [
            handler_info for handler_info in self._handlers[type(event)]
            if handler_info.matches_event(processed_event)
        ]

        return matching_handlers

    def _apply_middlewares(self, event: Event) -> Event:
        """Apply middleware chain synchronously"""
        if not self._middlewares:
            return event

        processed_event = event
        for middleware in self._middlewares:
            # Each middleware gets the current processed event
            # Middlewares can modify the event and return a new event
            try:
                result = middleware(processed_event)
                if result is not None:
                    processed_event = result
            except Exception as e:
                self._logger.error(f"Middleware error: {e}", exc_info=True)

        return processed_event

    async def _apply_middlewares_async(self, event: Event) -> Event:
        """Apply middleware chain asynchronously"""
        if not self._middlewares:
            return event

        processed_event = event
        for middleware in self._middlewares:
            # Each middleware gets the current processed event
            # Middlewares can modify the event and return a new event
            try:
                # Handle both sync and async middlewares
                if inspect.iscoroutinefunction(middleware):
                    result = await middleware(processed_event)
                else:
                    result = middleware(processed_event)
                if result is not None:
                    processed_event = result
            except Exception as e:
                self._logger.error(f"Middleware error: {e}", exc_info=True)

        return processed_event

    def _execute_handler_sync(self, handler_info: EventHandlerInfo, event: Event) -> None:
        """Execute a handler synchronously"""
        try:
            handler_info.handler(event)
        except Exception as e:
            self._logger.error(f"Handler {handler_info.handler_id} failed: {e}", exc_info=True)

    async def _execute_handler_async(self, handler_info: EventHandlerInfo, event: Event) -> None:
        """Execute a handler asynchronously"""
        try:
            # Handle both sync and async handlers
            if inspect.iscoroutinefunction(handler_info.handler):
                await handler_info.handler(event)
            else:
                # Run sync handler in thread pool
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, handler_info.handler, event)
        except Exception as e:
            self._logger.error(f"Handler {handler_info.handler_id} failed: {e}", exc_info=True)
