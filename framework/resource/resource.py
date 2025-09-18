"""
Base Resource Classes
Core abstractions for resource management in UCore framework
"""

import asyncio
from loguru import logger
import time
from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional, Union
from contextlib import asynccontextmanager

from .exceptions import (
    ResourceError,
    ResourceConnectionError,
    ResourceStateError,
    ResourceTimeoutError
)
from .events import ResourceEvent


logger = logger.bind(logger_name=__name__)


class ResourceState(Enum):
    """Resource lifecycle states"""
    CREATED = "created"
    INITIALIZING = "initializing"
    READY = "ready"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CLEANUP = "cleanup"
    DESTROYED = "destroyed"


class ResourceHealth(Enum):
    """Resource health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class Resource(ABC):
    """
    Abstract base class for all resources

    Provides the core interface and lifecycle management for resources
    in the UCore framework.
    """

    def __init__(
        self,
        name: str,
        resource_type: str,
        config: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0
    ):
        self.name = name
        self.resource_type = resource_type
        self.config = config or {}
        self.timeout = timeout

        # State management
        self._state = ResourceState.CREATED
        self._health = ResourceHealth.UNKNOWN
        self._last_health_check = 0.0
        self._created_at = time.time()
        self._resource_id = f"{resource_type}_{name}_{int(self._created_at * 1000)}"

        # Performance tracking
        self._operation_count = 0
        self._error_count = 0
        self._last_operation_time = 0.0

        logger.info(f"Resource {name} created with type {resource_type}")

    @property
    def state(self) -> ResourceState:
        """Current resource state"""
        return self._state

    @property
    def health(self) -> ResourceHealth:
        """Current resource health"""
        return self._health

    @property
    def resource_id(self) -> str:
        """Unique resource identifier"""
        return self._resource_id

    @property
    def is_ready(self) -> bool:
        """Check if resource is ready for use"""
        return self._state in [ResourceState.READY, ResourceState.CONNECTED]

    @property
    def is_connected(self) -> bool:
        """Check if resource has active connections"""
        return self._state == ResourceState.CONNECTED

    async def initialize(self) -> None:
        """Initialize the resource"""
        if self._state != ResourceState.CREATED:
            raise ResourceStateError(
                self.name,
                self._state.value,
                ResourceState.CREATED.value
            )

        logger.info(f"Initializing resource {self.name}")
        self._state = ResourceState.INITIALIZING

        try:
            await self._initialize()
            self._state = ResourceState.READY
            logger.info(f"Resource {self.name} initialized successfully")
        except Exception as e:
            self._state = ResourceState.ERROR
            self._health = ResourceHealth.UNHEALTHY
            logger.error(f"Failed to initialize resource {self.name}: {e}")
            raise ResourceError(f"Initialization failed: {e}", self.name) from e

    @abstractmethod
    async def _initialize(self) -> None:
        """Resource-specific initialization logic"""
        pass

    async def connect(self) -> None:
        """Establish resource connections"""
        if self._state not in [ResourceState.READY, ResourceState.DISCONNECTED]:
            raise ResourceStateError(
                self.name,
                self._state.value,
                f"{ResourceState.READY.value} or {ResourceState.DISCONNECTED.value}"
            )

        logger.info(f"Connecting resource {self.name}")
        self._state = ResourceState.CONNECTING

        try:
            await asyncio.wait_for(self._connect(), timeout=self.timeout)
            self._state = ResourceState.CONNECTED
            self._health = ResourceHealth.HEALTHY
            logger.info(f"Resource {self.name} connected successfully")
        except asyncio.TimeoutError:
            self._state = ResourceState.ERROR
            self._health = ResourceHealth.UNHEALTHY
            raise ResourceTimeoutError(self.name, "connect", self.timeout)
        except Exception as e:
            self._state = ResourceState.ERROR
            self._health = ResourceHealth.UNHEALTHY
            logger.error(f"Failed to connect resource {self.name}: {e}")
            raise ResourceConnectionError(self.name) from e

    @abstractmethod
    async def _connect(self) -> None:
        """Resource-specific connection logic"""
        pass

    async def disconnect(self) -> None:
        """Close resource connections"""
        if self._state not in [ResourceState.CONNECTED, ResourceState.ERROR]:
            logger.warning(f"Resource {self.name} not connected, skipping disconnect")
            return

        logger.info(f"Disconnecting resource {self.name}")
        self._state = ResourceState.DISCONNECTING

        try:
            await self._disconnect()
            self._state = ResourceState.DISCONNECTED
            self._health = ResourceHealth.UNHEALTHY
            logger.info(f"Resource {self.name} disconnected successfully")
        except Exception as e:
            logger.error(f"Error during disconnect of {self.name}: {e}")
            self._state = ResourceState.ERROR
            raise ResourceError(f"Disconnect failed: {e}", self.name) from e

    @abstractmethod
    async def _disconnect(self) -> None:
        """Resource-specific disconnection logic"""
        pass

    async def health_check(self) -> ResourceHealth:
        """Perform health check"""
        try:
            current_time = time.time()
            self._last_health_check = current_time

            health = await asyncio.wait_for(self._health_check(), timeout=5.0)
            self._health = health

            logger.debug(f"Health check for {self.name}: {health.value}")
            return health
        except Exception as e:
            self._health = ResourceHealth.UNHEALTHY
            logger.warning(f"Health check failed for {self.name}: {e}")
            return ResourceHealth.UNHEALTHY

    @abstractmethod
    async def _health_check(self) -> ResourceHealth:
        """Resource-specific health check logic"""
        pass

    async def cleanup(self) -> None:
        """Clean up resource resources"""
        logger.info(f"Cleaning up resource {self.name}")
        self._state = ResourceState.CLEANUP

        try:
            await self._cleanup()
            self._state = ResourceState.DESTROYED
            logger.info(f"Resource {self.name} cleaned up successfully")
        except Exception as e:
            logger.error(f"Error during cleanup of {self.name}: {e}")
            self._state = ResourceState.ERROR
            raise ResourceError(f"Cleanup failed: {e}", self.name) from e

    @abstractmethod
    async def _cleanup(self) -> None:
        """Resource-specific cleanup logic"""
        pass

    def get_stats(self) -> Dict[str, Any]:
        """Get resource statistics"""
        return {
            "name": self.name,
            "type": self.resource_type,
            "id": self.resource_id,
            "state": self._state.value,
            "health": self._health.value,
            "created_at": self._created_at,
            "last_health_check": self._last_health_check,
            "operation_count": self._operation_count,
            "error_count": self._error_count,
            "last_operation": self._last_operation_time,
            "uptime": time.time() - self._created_at,
        }


class ManagedResource(Resource):
    """
    Resource with managed lifecycle and automatic health monitoring
    """

    def __init__(
        self,
        name: str,
        resource_type: str,
        config: Optional[Dict[str, Any]] = None,
        health_check_interval: float = 60.0,
        auto_reconnect: bool = True,
        max_reconnect_attempts: int = 3,
    ):
        super().__init__(name, resource_type, config)
        self.health_check_interval = health_check_interval
        self.auto_reconnect = auto_reconnect
        self.max_reconnect_attempts = max_reconnect_attempts

        # Auto-management
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._reconnect_attempts = 0

    async def start_management(self) -> None:
        """Start automatic resource management"""
        await self.initialize()
        await self.connect()

        # Start health monitoring
        self._health_monitor_task = asyncio.create_task(self._monitor_health())
        logger.info(f"Started management for resource {self.name}")

    async def stop_management(self) -> None:
        """Stop automatic resource management"""
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
            try:
                await self._health_monitor_task
            except asyncio.CancelledError:
                pass

        await self.disconnect()
        await self.cleanup()
        logger.info(f"Stopped management for resource {self.name}")

    async def _monitor_health(self) -> None:
        """Background health monitoring"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                health = await self.health_check()

                if health == ResourceHealth.UNHEALTHY and self.auto_reconnect:
                    await self._attempt_reconnect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitoring error for {self.name}: {e}")

    async def _attempt_reconnect(self) -> None:
        """Attempt to reconnect unhealthy resource"""
        if self._reconnect_attempts >= self.max_reconnect_attempts:
            logger.error(f"Max reconnection attempts reached for {self.name}")
            return

        self._reconnect_attempts += 1
        logger.info(f"Attempting reconnection for {self.name} (attempt {self._reconnect_attempts})")

        try:
            await self.disconnect()
            await asyncio.sleep(1)  # Brief pause before reconnect
            await self.connect()
            self._reconnect_attempts = 0
            logger.info(f"Successfully reconnected {self.name}")
        except Exception as e:
            logger.warning(f"Reconnection failed for {self.name}: {e}")


class PooledResource(Resource):
    """
    Resource with connection pooling capabilities
    """

    def __init__(
        self,
        name: str,
        resource_type: str,
        config: Optional[Dict[str, Any]] = None,
        pool_size: int = 10,
        min_pool_size: int = 0,
        max_idle_time: float = 300.0,  # 5 minutes
    ):
        super().__init__(name, resource_type, config)
        self.pool_size = pool_size
        self.min_pool_size = min_pool_size
        self.max_idle_time = max_idle_time

        # Pool management
        self._pool: list = []
        self._available: list = []
        self._waiters: list = []

    @asynccontextmanager
    async def get_connection(self):
        """Get a connection from the pool"""
        connection = await self._acquire_connection()

        try:
            yield connection
        finally:
            await self._release_connection(connection)

    async def _acquire_connection(self):
        """Acquire a connection from pool"""
        if self._available:
            connection = self._available.pop()
            # Check if connection is still valid
            if await self._is_connection_valid(connection):
                return connection
            else:
                # Remove invalid connection
                await self._close_connection(connection)

        # Create new connection if pool not full
        if len(self._pool) < self.pool_size:
            return await self._create_connection()

        # Wait for available connection or timeout
        # Implementation would continue with async waiting logic...

        raise ResourceError("Pool exhausted", self.name)

    async def _release_connection(self, connection) -> None:
        """Release connection back to pool"""
        if await self._is_connection_valid(connection):
            self._available.append(connection)
        else:
            await self._close_connection(connection)

    @abstractmethod
    async def _create_connection(self):
        """Create new connection for pool"""
        pass

    @abstractmethod
    async def _close_connection(self, connection) -> None:
        """Close a connection"""
        pass

    @abstractmethod
    async def _is_connection_valid(self, connection) -> bool:
        """Check if connection is still valid"""
        pass


class ObservableResource(ManagedResource, PooledResource):
    """
    Resource with full monitoring and observability features
    """

    def __init__(
        self,
        name: str,
        resource_type: str,
        config: Optional[Dict[str, Any]] = None,
        event_bus=None,
        metrics_collector=None,
    ):
        super().__init__(name, resource_type, config)
        self.event_bus = event_bus
        self.metrics_collector = metrics_collector

        # Monitoring
        self._performance_metrics = {}
        self._error_metrics = {}

    async def _publish_event(self, event_type: str, **kwargs) -> None:
        """Publish resource event if event bus available"""
        if self.event_bus:
            event = ResourceEvent(
                resource_name=self.name,
                resource_type=self.resource_type,
                timestamp=time.time()
            )
            await self.event_bus.publish(f"resource.{event_type}", event)

    async def _record_metric(self, metric_name: str, value: Union[int, float]) -> None:
        """Record metric if collector available"""
        if self.metrics_collector:
            await self.metrics_collector.record(
                f"resource_{metric_name}",
                value,
                labels={"resource": self.name, "type": self.resource_type}
            )

    async def _initialize(self) -> None:
        """Observable initialization"""
        start_time = time.time()
        try:
            await self._observable_initialize()
            duration = time.time() - start_time
            await self._record_metric("init_duration", duration)
            await self._publish_event("initialized")
        except Exception as e:
            await self._record_metric("init_error", 1)
            await self._publish_event("init_failed", error=str(e))
            raise

    async def _connect(self) -> None:
        """Observable connection"""
        start_time = time.time()
        try:
            await self._observable_connect()
            duration = time.time() - start_time
            await self._record_metric("connect_duration", duration)
            await self._publish_event("connected")
        except Exception as e:
            await self._record_metric("connect_error", 1)
            await self._publish_event("connect_failed", error=str(e))
            raise

    async def _disconnect(self) -> None:
        """Observable disconnection"""
        try:
            await self._observable_disconnect()
            await self._publish_event("disconnected")
        except Exception as e:
            await self._publish_event("disconnect_failed", error=str(e))
            raise

    async def _health_check(self) -> ResourceHealth:
        """Observable health check"""
        try:
            health = await self._observable_health_check()
            await self._record_metric(f"health_{health.value}", 1)
            if health != self.health:
                await self._publish_event("health_changed",
                                        old_health=self.health.value,
                                        new_health=health.value)
            return health
        except Exception as e:
            await self._record_metric("health_check_error", 1)
            return ResourceHealth.UNHEALTHY

    async def _cleanup(self) -> None:
        """Observable cleanup"""
        try:
            await self._observable_cleanup()
            await self._publish_event("destroyed")
        except Exception as e:
            await self._publish_event("cleanup_failed", error=str(e))
            raise

    @abstractmethod
    async def _observable_initialize(self) -> None:
        """Resource-specific observable initialization"""
        pass

    @abstractmethod
    async def _observable_connect(self) -> None:
        """Resource-specific observable connection"""
        pass

    @abstractmethod
    async def _observable_disconnect(self) -> None:
        """Resource-specific observable disconnection"""
        pass

    @abstractmethod
    async def _observable_health_check(self) -> ResourceHealth:
        """Resource-specific observable health check"""
        pass

    @abstractmethod
    async def _observable_cleanup(self) -> None:
        """Resource-specific observable cleanup"""
        pass
