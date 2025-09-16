"""
Resource Pooling Implementation
Connection pooling for efficient resource management
"""

import asyncio
from framework.monitoring.logging import Logging
import time
from typing import Any, Dict, List, Optional
from abc import ABC, abstractmethod

from .exceptions import ResourcePoolExhaustedError, ResourceError
from .events import ResourcePoolExhaustedEvent, ResourcePoolEvent


logger = Logging().get_logger(__name__)


class PoolEntry:
    """Pool entry for tracking connection metadata"""

    def __init__(self, connection, created_at: float, last_used: float):
        self.connection = connection
        self.created_at = created_at
        self.last_used = last_used
        self.use_count = 0


class ResourcePool(ABC):
    """
    Abstract base class for resource pooling

    Provides connection pooling with automatic lifecycle management,
    health checks, and resource optimization.
    """

    def __init__(
        self,
        resource_name: str,
        pool_size: int = 10,
        min_pool_size: int = 0,
        max_idle_time: float = 300.0,  # 5 minutes
        health_check_interval: float = 30.0,
        acquire_timeout: float = 10.0,
        event_bus=None
    ):
        self.resource_name = resource_name
        self.pool_size = pool_size
        self.min_pool_size = min_pool_size
        self.max_idle_time = max_idle_time
        self.health_check_interval = health_check_interval
        self.acquire_timeout = acquire_timeout
        self.event_bus = event_bus

        # Pool state
        self._pool: List[PoolEntry] = []
        self._available: List[PoolEntry] = []
        self._in_use: Dict[Any, PoolEntry] = {}
        self._waiters: List[asyncio.Future] = []

        # Statistics
        self._total_connections_created = 0
        self._total_connections_destroyed = 0
        self._total_acquires = 0
        self._total_releases = 0
        self._total_timeouts = 0

        # Maintenance task
        self._maintenance_task: Optional[asyncio.Task] = None
        self._is_shutdown = False

        logger.info(f"Resource pool {resource_name} created with size {pool_size}")

    @property
    def size(self) -> int:
        """Current pool size"""
        return len(self._pool)

    @property
    def available_count(self) -> int:
        """Number of available connections"""
        return len(self._available)

    @property
    def in_use_count(self) -> int:
        """Number of connections in use"""
        return len(self._in_use)

    @property
    def waiting_count(self) -> int:
        """Number of waiters for connections"""
        return len(self._waiters)

    async def start(self) -> None:
        """Start the pool and pre-populate if needed"""
        if self._is_shutdown:
            raise ResourceError("Pool is shutdown", self.resource_name)

        logger.info(f"Starting resource pool {self.resource_name}")

        # Initialize minimum connections
        for _ in range(self.min_pool_size):
            connection = await self._create_connection()
            entry = PoolEntry(connection, time.time(), time.time())
            self._pool.append(entry)
            self._available.append(entry)
            self._total_connections_created += 1

        # Start maintenance task
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())

        logger.info(f"Resource pool {self.resource_name} started with {len(self._pool)} connections")

    async def stop(self) -> None:
        """Shutdown the pool and cleanup all connections"""
        if self._is_shutdown:
            return

        logger.info(f"Stopping resource pool {self.resource_name}")
        self._is_shutdown = True

        # Cancel maintenance task
        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

        # Fail all waiters
        for waiter in self._waiters:
            if not waiter.done():
                waiter.set_exception(ResourceError("Pool shutting down", self.resource_name))
        self._waiters.clear()

        # Close all connections
        for entry in self._pool:
            await self._close_connection(entry.connection)
            self._total_connections_destroyed += 1

        self._pool.clear()
        self._available.clear()
        self._in_use.clear()

        logger.info(f"Resource pool {self.resource_name} stopped")

    async def acquire(self) -> Any:
        """
        Acquire a connection from the pool

        Returns:
            Connection object

        Raises:
            ResourcePoolExhaustedError: If pool is full and acquire_timeout expires
        """
        if self._is_shutdown:
            raise ResourceError("Pool is shutdown", self.resource_name)

        start_time = time.time()
        self._total_acquires += 1

        # Try to get connection immediately
        if self._available:
            entry = self._available.pop()
            entry.last_used = time.time()
            entry.use_count += 1
            self._in_use[entry.connection] = entry
            return entry.connection

        # Pool full, create new connection if possible
        if len(self._pool) < self.pool_size:
            connection = await self._create_connection()
            entry = PoolEntry(connection, time.time(), time.time())
            entry.use_count += 1
            self._pool.append(entry)
            self._in_use[connection] = entry
            self._total_connections_created += 1
            return connection

        # Pool exhausted, try to wait
        logger.debug(f"Pool {self.resource_name} exhausted, waiting for available connection")

        # Publish pool exhausted event
        await self._publish_event(ResourcePoolExhaustedEvent(
            resource_name=self.resource_name,
            resource_type="pool",
            timestamp=time.time(),
            pool_name=self.resource_name,
            pool_size=self.pool_size,
            available_count=self.available_count,
            waiters_count=self.waiting_count
        ))

        waiter = asyncio.get_event_loop().create_future()
        self._waiters.append(waiter)

        try:
            connection = await asyncio.wait_for(waiter, timeout=self.acquire_timeout)

            # Check if connection is still valid
            if not await self._is_connection_valid(connection):
                await self._close_connection(connection)
                await self._publish_pool_stats()
                raise ResourceError("Acquired connection is invalid", self.resource_name)

            return connection

        except asyncio.TimeoutError:
            self._total_timeouts += 1
            await self._publish_pool_stats()
            raise ResourcePoolExhaustedError(self.resource_name, self.pool_size)

    async def release(self, connection) -> None:
        """
        Release a connection back to the pool

        Args:
            connection: Connection to release
        """
        if self._is_shutdown:
            await self._close_connection(connection)
            return

        entry = self._in_use.pop(connection, None)
        if not entry:
            logger.warning(f"Releasing unknown connection for {self.resource_name}")
            await self._close_connection(connection)
            return

        self._total_releases += 1

        # Check if connection is still valid
        if not await self._is_connection_valid(connection):
            # Remove invalid connection
            self._pool.remove(entry)
            await self._close_connection(connection)
            self._total_connections_destroyed += 1

            # Publish pool stats
            await self._publish_pool_stats()

            # Notify first waiter
            if self._waiters:
                waiter = self._waiters.pop(0)
                if not waiter.done():
                    # Try to create new connection for waiter
                    try:
                        new_connection = await self._create_connection()
                        new_entry = PoolEntry(new_connection, time.time(), time.time())
                        new_entry.use_count += 1
                        self._pool.append(new_entry)
                        self._in_use[new_connection] = new_entry
                        self._total_connections_created += 1
                        waiter.set_result(new_connection)
                    except Exception as e:
                        waiter.set_exception(e)
        else:
            # Return to available pool
            self._available.append(entry)

            # Notify first waiter
            if self._waiters:
                waiter = self._waiters.pop(0)
                if not waiter.done():
                    waiter.set_result(connection)

    async def health_check(self) -> Dict[str, Any]:
        """Perform pool health check"""
        unhealthy_count = 0
        for entry in self._pool:
            if not await self._is_connection_valid(entry.connection):
                unhealthy_count += 1

        health_status = {
            "pool_size": self.size,
            "available": self.available_count,
            "in_use": self.in_use_count,
            "waiting": self.waiting_count,
            "unhealthy_connections": unhealthy_count,
            "total_created": self._total_connections_created,
            "total_destroyed": self._total_connections_destroyed,
            "total_acquires": self._total_acquires,
            "total_releases": self._total_releases,
            "total_timeouts": self._total_timeouts,
        }

        return health_status

    async def _maintenance_loop(self) -> None:
        """Background maintenance loop"""
        while not self._is_shutdown:
            try:
                await asyncio.sleep(self.health_check_interval)

                # Evict idle connections
                current_time = time.time()
                to_evict = []

                for entry in self._available[:]:  # Copy to avoid modification during iteration
                    if current_time - entry.last_used > self.max_idle_time:
                        to_evict.append(entry)

                for entry in to_evict:
                    self._available.remove(entry)
                    self._pool.remove(entry)
                    await self._close_connection(entry.connection)
                    self._total_connections_destroyed += 1
                    logger.debug(f"Evicted idle connection from pool {self.resource_name}")

                # Health check existing connections
                for entry in self._pool:
                    if not await self._is_connection_valid(entry.connection):
                        logger.warning(f"Found unhealthy connection in pool {self.resource_name}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in pool maintenance for {self.resource_name}: {e}")

    async def _publish_event(self, event) -> None:
        """Publish pool event"""
        if self.event_bus:
            await self.event_bus.publish(f"resource.pool.{event.__class__.__name__.lower()}", event)

    async def _publish_pool_stats(self) -> None:
        """Publish current pool statistics"""
        if self.event_bus:
            await self.event_bus.publish("resource.pool.stats", {
                "pool_name": self.resource_name,
                "pool_size": self.pool_size,
                "available_count": self.available_count,
                "in_use_count": self.in_use_count,
                "waiting_count": self.waiting_count,
                "total_created": self._total_connections_created,
                "total_destroyed": self._total_connections_destroyed,
                "total_acquires": self._total_acquires,
                "total_releases": self._total_releases,
                "total_timeouts": self._total_timeouts,
            })

    @abstractmethod
    async def _create_connection(self) -> Any:
        """Create a new connection"""
        pass

    @abstractmethod
    async def _close_connection(self, connection) -> None:
        """Close a connection"""
        pass

    @abstractmethod
    async def _is_connection_valid(self, connection) -> bool:
        """Check if connection is valid"""
        pass
