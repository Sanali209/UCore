"""
Component Management for UCore Framework.

This module provides the ComponentManager class, which is responsible for
registering, starting, and stopping application components in a managed lifecycle.
It supports both synchronous and asynchronous components, event publishing for
lifecycle transitions, and flexible registration (class, instance, or factory).

Classes:
    ComponentManager: Manages registration and lifecycle of application components.
"""

import inspect
from typing import List
from loguru import logger
from .component import Component
from .event_bus import EventBus
from .event_types import ComponentStartedEvent, ComponentStoppedEvent

class ComponentManager:
    """
    Manages registration and lifecycle of application components.

    Responsibilities:
        - Register components (by class, instance, or factory)
        - Start and stop all components, handling async/sync methods
        - Publish lifecycle events (ComponentStartedEvent, ComponentStoppedEvent)
        - Provide access to all registered components

    Args:
        container: Dependency injection container for resolving dependencies.
        app_logger: Optional logger instance for logging component actions.

    Example:
        >>> manager = ComponentManager(container)
        >>> manager.register_component(MyComponent)
        >>> await manager.start()
        >>> await manager.stop()
    """
    def __init__(self, container, app_logger=None):
        self.container = container
        self._components: List[Component] = []
        self.logger = app_logger or logger

    def register_component(self, component) -> None:
        """
        Registers and instantiates a component, adding it to the lifecycle management.
        Accepts Component classes, instances, or factory functions (callables).
        """
        component_instance = None

        if inspect.isclass(component) and issubclass(component, Component):
            component_instance = component(self)
        elif isinstance(component, Component):
            component_instance = component
        elif callable(component):
            try:
                potential_instance = component()
                if isinstance(potential_instance, Component):
                    component_instance = potential_instance
                    if not hasattr(component_instance, 'app') or component_instance.app is None:
                        component_instance.app = self
                else:
                    self.logger.warning(f"Factory function returned a {type(potential_instance).__name__}, expected Component")
                    return
            except Exception as e:
                self.logger.warning(f"Factory function call failed: {e}")
                return
        else:
            self.logger.warning(f"Invalid component type: {type(component).__name__}. Must be Component class, instance, or factory function")
            return

        self._components.append(component_instance)
        self.logger.info(f"Registered component: {component_instance.__class__.__name__}")

    async def start(self) -> None:
        """
        Starts all registered components.
        """
        event_bus = self.container.get(EventBus)
        event_bus.start()

        self.logger.info("Starting components...")
        for component in self._components:
            await self._execute_lifecycle_method(component, 'start')

    async def stop(self) -> None:
        """
        Stops all registered components in reverse order.
        """
        self.logger.info("Stopping components...")
        for component in reversed(self._components):
            await self._execute_lifecycle_method(component, 'stop')

        event_bus = self.container.get(EventBus)
        event_bus.shutdown()

    async def _execute_lifecycle_method(self, component: Component, method_name: str) -> None:
        """
        Executes a lifecycle method (start/stop) on a component,
        handling both sync and async methods.
        """
        method = getattr(component, method_name)
        try:
            if inspect.iscoroutinefunction(method):
                await method()
            else:
                method()
            self.logger.info(f"{method_name.capitalize()}d component: {component.__class__.__name__}")

            event_bus = self.container.get(EventBus)
            if method_name == 'start':
                event = ComponentStartedEvent(
                    component_name=component.__class__.__name__,
                    component_type=component.__class__.__name__
                )
            elif method_name == 'stop':
                event = ComponentStoppedEvent(
                    component_name=component.__class__.__name__,
                    component_type=component.__class__.__name__
                )
            event_bus.publish(event)

        except Exception as e:
            self.logger.error(f"Error {method_name}ing component {component.__class__.__name__}: {e}", exc_info=True)

    def get_all_components(self):
        """Returns all registered components."""
        return self._components
