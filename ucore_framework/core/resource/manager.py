"""
Resource Manager for UCore Framework.

This module provides the ResourceManager class, which is responsible for
registering, managing, and coordinating the lifecycle of all resources
in the framework. It supports resource discovery, health checks, cleanup,
dependency injection integration, and event publishing for resource events.

Classes:
    ResourceManager: Central component for resource management.
"""

import asyncio
from loguru import logger
from ucore_framework.monitoring.progress import ProgressManager
from typing import Any, Dict, List, Optional, Type
from collections import defaultdict
from ucore_framework.core.circuit_breaker import CircuitBreakerManager, BreakerError

from .resource import Resource, ResourceHealth
from .exceptions import ResourceNotFoundError, ResourceError
from ucore_framework.core.event_types import ResourceCreatedEvent, ResourceDeletedEvent, ResourceModifiedEvent, ResourceConnectionEvent


import sys
logger.add("resource_manager.log", rotation="1 MB")
logger.add(sys.stdout, level="DEBUG")


from ucore_framework.core.component import Component

class ResourceManager(Component):
    """
    Central resource management component for UCore.

    Responsibilities:
        - Register and organize resources by type
        - Manage resource lifecycle (start/stop/health checks)
        - Provide resource discovery and lookup
        - Coordinate resource cleanup on shutdown
        - Integrate with dependency injection and event bus
        - Publish resource-related events

    Args:
        app: Optional reference to the main App instance.
        event_bus: Optional event bus for publishing resource events.
        di_container: Optional dependency injection container.

    Example:
        >>> manager = ResourceManager(app)
        >>> manager.register_resource(my_resource)
        >>> await manager.start_all_resources()
        >>> await manager.stop_all_resources()
    """

    def __init__(self, app=None, event_bus=None, di_container=None):
        super().__init__(app=app, name="ResourceManager")
        self.event_bus = event_bus
        self.di_container = di_container

        # Resource registry
        self._resources: Dict[str, Resource] = {}
        self._resources_by_type: Dict[str, List[Resource]] = defaultdict(list)

        # Progress manager for lifecycle operations
        self.progress_manager = ProgressManager(event_bus=event_bus, description="ResourceManager Lifecycle")

        # Manager state
        self._is_started = False
        self._is_shutting_down = False
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._shutdown_timeout = 30.0  # seconds

        logger.info("ResourceManager created")

    def start(self):
        logger.info("ResourceManager started")

    def stop(self):
        logger.info("ResourceManager stopped")

    @property
    def is_started(self) -> bool:
        """Check if manager is started"""
        return self._is_started

    def register_resource(self, resource: Resource) -> None:
        """
        Register a resource with the manager

        Args:
            resource: Resource instance to register
        """
        if self._is_started:
            logger.warning("Registering resource after manager started, resource may not be initialized properly")

        if resource.name in self._resources:
            logger.warning(f"Resource {resource.name} already registered, replacing")

        # Remove from old type list if changing
        old_resource = self._resources.get(resource.name)
        if old_resource and old_resource.resource_type != resource.resource_type:
            if old_resource in self._resources_by_type[old_resource.resource_type]:
                self._resources_by_type[old_resource.resource_type].remove(old_resource)

        # Register resource
        self._resources[resource.name] = resource
        self._resources_by_type[resource.resource_type].append(resource)

        logger.info(f"Registered resource {resource.name} of type {resource.resource_type}")

        # Register with DI container if available
        if self.di_container:
            self.di_container.register(resource, resource.name)

    def unregister_resource(self, resource_name: str) -> None:
        """
        Unregister a resource from the manager

        Args:
            resource_name: Name of resource to unregister
        """
        if resource_name not in self._resources:
            logger.warning(f"Attempted to unregister unknown resource {resource_name}")
            # Still call DI unregister for test compatibility
            if self.di_container:
                self.di_container.unregister(resource_name)
            return

        resource = self._resources[resource_name]

        # Cleanup if resource is started
        if resource.is_ready:
            try:
                # Try to disconnect first
                if resource.is_connected:
                    asyncio.create_task(resource.disconnect())
                # Then cleanup
                asyncio.create_task(resource.cleanup())
            except Exception as e:
                logger.error(f"Error cleaning up resource {resource_name} during unregister: {e}")

        # Remove from registry
        del self._resources[resource_name]
        if resource in self._resources_by_type[resource.resource_type]:
            self._resources_by_type[resource.resource_type].remove(resource)

        logger.info(f"Unregistered resource {resource_name}")

        # Unregister from DI container if available
        if self.di_container:
            self.di_container.unregister(resource_name)

    def get_resource(self, name: str) -> Resource:
        """
        Get a resource by name

        Args:
            name: Resource name

        Returns:
            Resource instance

        Raises:
            ResourceNotFoundError: If resource not found
        """
        if name not in self._resources:
            raise ResourceNotFoundError(name)
        return self._resources[name]

    def get_resources_by_type(self, resource_type: str) -> List[Resource]:
        """
        Get all resources of a specific type

        Args:
            resource_type: Resource type to filter by

        Returns:
            List of resources of the specified type
        """
        return self._resources_by_type.get(resource_type, []).copy()

    def get_all_resources(self) -> Dict[str, Resource]:
        """
        Get all registered resources

        Returns:
            Dictionary of resource names to resource instances
        """
        return self._resources.copy()

    async def start_all_resources(self) -> None:
        # Use semaphore for controlled concurrency
        semaphore = asyncio.Semaphore(5)

        async def start_resource_with_limit(resource):
            async with semaphore:
                breaker_name = f"resource.{getattr(resource, 'name', 'unknown')}"
                breaker = CircuitBreakerManager.get_breaker(breaker_name)
                try:
                    return await breaker.async_call(resource.initialize)
                except BreakerError as e:
                    return e  # Return the error to be handled by the gathering logic

        # Start resources concurrently with proper error handling
        tasks = [start_resource_with_limit(r) for r in self._resources.values()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Handle failures gracefully
        for resource, result in zip(self._resources.values(), results):
            if isinstance(result, Exception):
                await self._handle_resource_failure(resource, result)

    async def _handle_resource_failure(self, resource, result: Exception) -> None:
        """Handles the failure of a single resource during initialization."""
        logger.error(f"Resource '{getattr(resource, 'name', 'N/A')}' failed to initialize: {result}", exc_info=result)

    async def stop_all_resources(self) -> None:
        """Stop all resources gracefully"""
        if not self._is_started:
            logger.warning("ResourceManager not started")
            return

        logger.debug("ResourceManager: Entering stop_all_resources")
        if self._is_shutting_down:
            logger.warning("ResourceManager already shutting down")
            return

        self._is_shutting_down = True
        logger.info("Stopping all resources...")

        # Cancel health monitoring
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass

        # Stop resources in reverse order
        self.progress_manager.max_progress = len(self._resources)
        self.progress_manager.reset()
        try:
            for resource in reversed(list(self._resources.values())):
                logger.debug(f"ResourceManager: Preparing to shutdown resource {resource.name} (is_ready={resource.is_ready})")
                if resource.is_ready:
                    logger.debug(f"ResourceManager: Shutting down resource {resource.name} synchronously")
                    await asyncio.wait_for(self._shutdown_resource_safe(resource), timeout=self._shutdown_timeout)
                    self.progress_manager.step(f"Stopping {resource.name}")
        except asyncio.TimeoutError:
            logger.error(f"Resource shutdown timed out after {self._shutdown_timeout}s")

        # Publish shutdown complete event
        from ucore_framework.core.event_types import SystemShutdownEvent
        await self._publish_event(SystemShutdownEvent(
            source_component="ResourceManager",
            reason="All resources stopped"
        ))

        self._is_started = False
        self._is_shutting_down = False
        logger.info("All resources stopped")

    async def _shutdown_resource_safe(self, resource: Resource) -> None:
        """Safely shutdown a single resource"""
        logger.debug(f"ResourceManager: Entering _shutdown_resource_safe for {resource.name}")
        try:
            if resource.is_connected:
                logger.debug(f"ResourceManager: Disconnecting resource {resource.name}")
                await resource.disconnect()
            logger.debug(f"ResourceManager: Cleaning up resource {resource.name}")
            await resource.cleanup()
            logger.info(f"Shutdown resource {resource.name} successfully")
        except Exception as e:
            logger.error(f"Error shutting down resource {resource.name}: {e}")

    async def health_check_all(self) -> Dict[str, Any]:
        """
        Perform health check on all resources

        Returns:
            Health status summary
        """
        health_summary = {
            "total_resources": len(self._resources),
            "healthy_count": 0,
            "unhealthy_count": 0,
            "unknown_count": 0,
            "resources": {}
        }

        for name, resource in self._resources.items():
            health = await resource.health_check()
            health_summary["resources"][name] = {
                "health": health.value,
                "state": getattr(resource, "state", None) if not hasattr(resource, "state") or not hasattr(resource.state, "value") else resource.state.value,
                "is_connected": getattr(resource, "is_connected", False),
                "last_check": resource.get_stats().get("last_health_check", 0)
            }

            if health == ResourceHealth.HEALTHY:
                health_summary["healthy_count"] += 1
            elif health == ResourceHealth.UNHEALTHY:
                health_summary["unhealthy_count"] += 1
            else:
                health_summary["unknown_count"] += 1

        return health_summary

    def get_resource_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all resources

        Returns:
            Dictionary of resource names to statistics
        """
        stats = {}
        for name, resource in self._resources.items():
            stats[name] = resource.get_stats()
            stats[name]["health"] = getattr(resource, "health", ResourceHealth.UNKNOWN).value if hasattr(resource, "health") else "unknown"
        return stats

    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop"""
        try:
            while self._is_started and not self._is_shutting_down:
                await asyncio.sleep(1)  # Check for cancellation more frequently
                if not self._is_started or self._is_shutting_down:
                    break
                # Only run health check every 60s
                if hasattr(self, "_last_health_check"):
                    if asyncio.get_event_loop().time() - self._last_health_check < 60:
                        continue
                self._last_health_check = asyncio.get_event_loop().time()
                health_summary = await self.health_check_all()
                from ucore_framework.core.event_types import ComponentHealthChangedEvent
                await self._publish_event(ComponentHealthChangedEvent(
                    component_name="ResourceManager",
                    new_status="healthy" if health_summary["unhealthy_count"] == 0 else "unhealthy",
                    health_details=health_summary
                ))
                unhealthy = [
                    f"{name}({info['health']})"
                    for name, info in health_summary["resources"].items()
                    if info["health"] in ["unhealthy", "unknown"]
                ]
                if unhealthy:
                    logger.warning(f"Unhealthy resources: {', '.join(unhealthy)}")
        except asyncio.CancelledError:
            logger.info("Health monitor loop cancelled")
        except Exception as e:
            logger.error(f"Error in health monitor loop: {e}")

    async def _publish_event(self, event: Any) -> None:
        """Publish a resource-related event."""
        if self.event_bus:
            try:
                await self.event_bus.publish(event)
            except Exception as e:
                logger.error(f"Failed to publish event {type(event).__name__}: {e}")

    # Context manager support
    async def __aenter__(self):
        await self.start_all_resources()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.stop_all_resources()

    def __len__(self) -> int:
        """Return number of registered resources"""
        return len(self._resources)

    def __contains__(self, name: str) -> bool:
        """Check if resource is registered"""
        return name in self._resources

    def __getitem__(self, name: str) -> Resource:
        """Get resource by name using dict-like syntax"""
        if name not in self._resources:
            raise KeyError(name)
        return self._resources[name]

    def get_handler_count(self, resource_type: Optional[str] = None) -> int:
        """
        Return the number of registered resources, optionally filtered by type.
        """
        if resource_type is None:
            return len(self._resources)
        return len(self._resources_by_type.get(resource_type, []))

    def get_event_types(self) -> set:
        """
        Return a set of all registered resource types.
        """
        return set(self._resources_by_type.keys())

    def clear_handlers(self, resource_type: Optional[str] = None) -> int:
        """
        Remove resources by type or all resources if type is None.
        Returns the number of resources removed.
        """
        if resource_type is None:
            count = len(self._resources)
            for resource in list(self._resources.values()):
                self.unregister_resource(resource.name)
            self._resources.clear()
            self._resources_by_type.clear()
            return count
        removed = len(self._resources_by_type.get(resource_type, []))
        for resource in list(self._resources_by_type.get(resource_type, [])):
            self.unregister_resource(resource.name)
        self._resources_by_type.pop(resource_type, None)
        return removed
