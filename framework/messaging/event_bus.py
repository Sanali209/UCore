"""
UCore Framework - Event Bus
Core event publish/subscribe system for in-process component communication.
"""

import asyncio
import inspect
from framework.monitoring.logging import Logging
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

    def __init__(self, logger=None):
        self._handlers: Dict[Type[Event], List[EventHandlerInfo]] = defaultdict(list)
        self._middlewares: List[Callable[[Event, Callable], Any]] = []
        self._logger = logger or Logging().get_logger(__name__)
        self._next_handler_id = 0
        self._running = False

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
            del self._handlers[event_type]
            self._logger.info(f"Cleared {count} handlers for {event_type.__name__}")
            return count

    # ---- Enhanced Event Publishing Methods ----

    def publish_error_event(self,
                           component_name: str,
                           error: Exception,
                           context: Optional[Dict] = None) -> None:
        """
        Publish a standardized error event.

        Args:
            component_name: Name of the component where error occurred
            error: The exception object
            context: Optional additional context information
        """
        from .events import ComponentErrorEvent
        import traceback

        event_context = {
            'component_name': component_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
        }

        additional_context = {}
        if context:
            additional_context.update(context)

        error_event = ComponentErrorEvent(
            component_name=event_context['component_name'],
            error_type=event_context['error_type'],
            error_message=event_context['error_message'],
            traceback=event_context['traceback'],
            context=additional_context
        )
        self.publish(error_event)

        # Log error for immediate visibility
        self._logger.error(f"Component error in {component_name}: {error}", exc_info=True)

    def publish_performance_event(self,
                                 metric_name: str,
                                 value: float,
                                 component_type: str = "",
                                 tags: Optional[Dict[str, str]] = None) -> None:
        """
        Publish a standardized performance event.

        Args:
            metric_name: Name of the performance metric
            value: The metric value
            component_type: Type of component publishing the metric
            tags: Optional tags for metric categorization
        """
        from .events import UserEvent

        performance_event = UserEvent(
            event_type="performance_metric",
            data={
                'metric_name': metric_name,
                'value': value,
                'component_type': component_type,
                'tags': tags or {}
            }
        )
        self.publish(performance_event)

    def create_event_context(self, component_name: str) -> Dict:
        """
        Create a standardized event context dictionary.

        Args:
            component_name: Name of the component

        Returns:
            Dictionary with standardized context fields
        """
        return {
            'component_name': component_name,
            'timestamp': None,  # Will be set by Event.__post_init__
            'correlation_id': None,  # Can be set by caller
            'instance_id': None,  # Can be set by caller
        }

    def publish_component_event(self,
                               component_name: str,
                               event_type: str,
                               data: Optional[Dict] = None,
                               context: Optional[Dict] = None) -> None:
        """
        Publish a generic component event with standardized structure.

        Args:
            component_name: Name of the component
            event_type: Specific event type (e.g., 'started', 'stopped', 'error')
            data: Optional event-specific data
            context: Optional additional context
        """
        from .events import UserEvent

        event_data = {
            'component_name': component_name,
            'event_type': event_type,
            'data': data or {}
        }

        if context:
            event_data.update(context)

        component_event = UserEvent(**event_data)
        self.publish(component_event)

    def publish_lifecycle_event(self,
                               component_name: str,
                               lifecycle_type: str,
                               success: bool = True,
                               duration: Optional[float] = None,
                               error_details: Optional[Dict] = None) -> None:
        """
        Publish a standardized component lifecycle event.

        Args:
            component_name: Name of the component
            lifecycle_type: Type of lifecycle event ('starting', 'started', 'stopping', 'stopped', 'error')
            success: Whether the lifecycle operation was successful
            duration: Time taken for the lifecycle operation
            error_details: Details if operation failed
        """
        from .events import UserEvent

        lifecycle_event = UserEvent(
            event_type="component_lifecycle",
            data={
                'component_name': component_name,
                'lifecycle_type': lifecycle_type,
                'success': success,
                'duration': duration,
                'error_details': error_details
            }
        )
        self.publish(lifecycle_event)

    def start(self) -> None:
        """Start the event bus - enable event publishing"""
        self._running = True
        self._logger.info("Event bus started")

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
                await loop.run_in_executor(None, lambda: handler_info.handler(event))
        except Exception as e:
            self._logger.error(f"Handler {handler_info.handler_id} failed: {e}", exc_info=True)
