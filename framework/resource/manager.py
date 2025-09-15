"""
Resource Manager
Central component for managing all resources in the framework
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Type
from collections import defaultdict

from .resource import Resource, ResourceHealth
from .exceptions import ResourceNotFoundError, ResourceError
from .events import ResourceEvent


logger = logging.getLogger(__name__)


class ResourceManager:
    """
    Central resource management component

    The ResourceManager is responsible for:
    - Registering and organizing resources by type
    - Managing resource lifecycle (start/stop/health checks)
    - Providing resource discovery and lookup
    - Coordinating resource cleanup on shutdown
    - Integrating with dependency injection
    """

    def __init__(self, event_bus=None, di_container=None):
        self.event_bus = event_bus
        self.di_container = di_container

        # Resource registry
        self._resources: Dict[str, Resource] = {}
        self._resources_by_type: Dict[str, List[Resource]] = defaultdict(list)

        # Manager state
        self._is_started = False
        self._is_shutting_down = False
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._shutdown_timeout = 30.0  # seconds

        logger.info("ResourceManager created")

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
        """Start all registered resources"""
        if self._is_started:
            logger.warning("ResourceManager already started")
            return

        logger.info("Starting all resources...")

        # Start resources in dependency order (basic approach - can be enhanced)
        started_resources = set()
        failed_resources = []

        for resource in self._resources.values():
            try:
                await resource.initialize()
                if hasattr(resource, 'start_management'):
                    await resource.start_management()  # type: ignore
                started_resources.add(resource.name)
                logger.info(f"Started resource {resource.name}")
            except Exception as e:
                logger.error(f"Failed to start resource {resource.name}: {e}")
                failed_resources.append((resource.name, str(e)))

        # Publish startup complete event
        await self._publish_event("resources_started", {
            "started_count": len(started_resources),
            "failed_count": len(failed_resources),
            "failed_resources": failed_resources
        })

        self._is_started = True

        # Start health monitoring
        self._health_monitor_task = asyncio.create_task(self._health_monitor_loop())

        if failed_resources:
            logger.warning(f"Some resources failed to start: {failed_resources}")

    async def stop_all_resources(self) -> None:
        """Stop all resources gracefully"""
        if not self._is_started:
            logger.warning("ResourceManager not started")
            return

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
        shutdown_tasks = []
        for resource in reversed(list(self._resources.values())):
            if resource.is_ready:
                task = asyncio.create_task(self._shutdown_resource_safe(resource))
                shutdown_tasks.append(task)

        # Wait for all shutdown tasks with timeout
        if shutdown_tasks:
            try:
                await asyncio.wait_for(
                    asyncio.gather(*shutdown_tasks, return_exceptions=True),
                    timeout=self._shutdown_timeout
                )
            except asyncio.TimeoutError:
                logger.error(f"Resource shutdown timed out after {self._shutdown_timeout}s")

        # Publish shutdown complete event
        await self._publish_event("resources_stopped", {
            "shutdown_count": len(self._resources)
        })

        self._is_started = False
        self._is_shutting_down = False
        logger.info("All resources stopped")

    async def _shutdown_resource_safe(self, resource: Resource) -> None:
        """Safely shutdown a single resource"""
        try:
            if resource.is_connected:
                await resource.disconnect()
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
                "state": resource.state.value,
                "is_connected": resource.is_connected,
                "last_check": resource.get_stats().get("last_health_check", 0)
            }

            if health == ResourceHealth.HEALTHY:
                health_summary["healthy_count"] += 1
            elif health == ResourceHealth.UNHEALTHY:
                health_summary["unhealthy_count"] += 1
            else:
                health_summary["unknown_count"] += 1

        return health_summary

    async def get_resource_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all resources

        Returns:
            Dictionary of resource names to statistics
        """
        stats = {}
        for name, resource in self._resources.items():
            stats[name] = resource.get_stats()
            stats[name]["health"] = resource.health.value
        return stats

    async def _health_monitor_loop(self) -> None:
        """Background health monitoring loop"""
        while self._is_started and not self._is_shutting_down:
            try:
                await asyncio.sleep(60)  # Health check every minute

                health_summary = await self.health_check_all()

                # Publish health update event
                await self._publish_event("health_update", health_summary)

                # Log unhealthy resources
                unhealthy = []
                for name, info in health_summary["resources"].items():
                    if info["health"] in ["unhealthy", "unknown"]:
                        unhealthy.append(f"{name}({info['health']})")

                if unhealthy:
                    logger.warning(f"Unhealthy resources: {', '.join(unhealthy)}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in health monitor loop: {e}")

    async def _publish_event(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish manager event"""
        if self.event_bus:
            event = ResourceEvent(
                resource_name="resource_manager",
                resource_type="manager",
                timestamp=asyncio.get_event_loop().time(),
                metadata=data
            )
            await self.event_bus.publish(f"resource.manager.{event_type}", event)

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
        return self.get_resource(name)
