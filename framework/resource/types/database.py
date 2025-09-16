"""
Database Resource
Provides database connection management with lifecycle management
"""

import asyncio
from framework.monitoring.logging import Logging
from typing import Any, Dict, Optional, Union
from abc import ABC, abstractmethod

from ..resource import Resource, ResourceHealth, ResourceState
from ..exceptions import ResourceError, ResourceConnectionError, ResourceStateError


logger = Logging().get_logger(__name__)


class DatabaseResource(Resource, ABC):
    """
    Abstract database resource providing common database operations

    Provides connection management, health checks, and query execution
    for various database types (MongoDB, SQL, etc.)
    """

    def __init__(
        self,
        name: str,
        connection_string: str,
        config: Optional[Dict[str, Any]] = None,
        connection_timeout: float = 10.0,
        max_pool_size: int = 10,
        min_pool_size: int = 0,
        health_check_query: Optional[str] = None,
    ):
        super().__init__(name, "database", config, connection_timeout)

        self.connection_string = connection_string
        self.max_pool_size = max_pool_size
        self.min_pool_size = min_pool_size
        self.health_check_query = health_check_query or self._default_health_check_query()

        # Connection state
        self._connection = None
        self._is_connected = False

        logger.info(f"Database resource {name} configured for connection: {self._mask_connection_string(connection_string)}")

    @abstractmethod
    async def _create_connection(self) -> Any:
        """Create database connection"""
        pass

    @abstractmethod
    async def _close_connection(self, connection) -> None:
        """Close database connection"""
        pass

    @abstractmethod
    async def _test_connection(self, connection) -> bool:
        """Test if connection is alive"""
        pass

    @abstractmethod
    async def _execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute database query"""
        pass

    @abstractmethod
    def _default_health_check_query(self) -> str:
        """Return default health check query for this database type"""
        pass

    def _mask_connection_string(self, conn_string: str) -> str:
        """Mask sensitive information in connection string"""
        import re
        # Mask password patterns
        masked = re.sub(r'password=[^&\s]+', 'password=***', conn_string, flags=re.IGNORECASE)
        masked = re.sub(r'pwd=[^&\s]+', 'pwd=***', masked, flags=re.IGNORECASE)
        return masked

    async def _initialize(self) -> None:
        """Initialize database resource"""
        # Validate connection string format
        if not self.connection_string:
            raise ResourceError("Connection string is required", self.name)

        # Try to parse connection string to validate format
        try:
            self._validate_connection_string(self.connection_string)
        except Exception as e:
            raise ResourceError(f"Invalid connection string: {e}", self.name)

        logger.info(f"Database resource {self.name} initialized successfully")

    async def _connect(self) -> None:
        """Establish database connection"""
        try:
            self._connection = await self._create_connection()
            self._is_connected = True

            # Test connection immediately
            if not await self._test_connection(self._connection):
                await self._close_connection(self._connection)
                self._connection = None
                self._is_connected = False
                raise ResourceConnectionError(self.name, self.connection_string)

            logger.info(f"Database resource {self.name} connected successfully")

        except Exception as e:
            self._is_connected = False
            if self._connection:
                try:
                    await self._close_connection(self._connection)
                except Exception:
                    pass  # Ignore cleanup errors
                self._connection = None

            raise ResourceConnectionError(self.name, self.connection_string) from e

    async def _disconnect(self) -> None:
        """Close database connection"""
        if self._connection:
            try:
                await self._close_connection(self._connection)
                logger.info(f"Database resource {self.name} disconnected successfully")
            except Exception as e:
                logger.error(f"Error disconnecting database {self.name}: {e}")
            finally:
                self._connection = None
                self._is_connected = False

    async def _health_check(self) -> ResourceHealth:
        """Perform database health check"""
        if not self._is_connected or not self._connection:
            return ResourceHealth.UNHEALTHY

        try:
            # Test connection first
            if not await self._test_connection(self._connection):
                self._is_connected = False
                return ResourceHealth.UNHEALTHY

            # Execute health check query if configured
            if self.health_check_query:
                result = await self._execute_query(self.health_check_query)
                return ResourceHealth.HEALTHY if result is not None else ResourceHealth.DEGRADED

            return ResourceHealth.HEALTHY

        except Exception as e:
            logger.warning(f"Database health check failed for {self.name}: {e}")
            self._is_connected = False
            return ResourceHealth.UNHEALTHY

    async def _cleanup(self) -> None:
        """Cleanup database resource"""
        await self._disconnect()
        logger.info(f"Database resource {self.name} cleaned up")

    def _validate_connection_string(self, conn_string: str) -> None:
        """Validate connection string format"""
        # Basic validation - override in subclasses for specific formats
        if len(conn_string.strip()) == 0:
            raise ValueError("Connection string cannot be empty")

    @abstractmethod
    async def ping(self) -> bool:
        """Ping database to test connectivity"""
        pass

    @abstractmethod
    async def get_database_stats(self) -> Dict[str, Any]:
        """Get database-specific statistics"""
        pass

    # Common database operations (override in subclasses)
    async def execute(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute a database query

        Args:
            query: Query string
            params: Query parameters

        Returns:
            Query result

        Raises:
            ResourceStateError: If not connected
            ResourceError: If query execution fails
        """
        if not self.is_connected:
            raise ResourceStateError(self.name, self.state.value, ResourceState.CONNECTED.value)

        try:
            return await self._execute_query(query, params)
        except Exception as e:
            raise ResourceError(f"Query execution failed: {e}", self.name) from e

    def get_stats(self) -> Dict[str, Any]:
        """Enhanced database statistics"""
        stats = super().get_stats()
        stats.update({
            "connection_string": self._mask_connection_string(self.connection_string),
            "is_connected": self._is_connected,
            "max_pool_size": self.max_pool_size,
            "min_pool_size": self.min_pool_size,
            "has_health_check_query": self.health_check_query is not None,
        })

        # Add database-specific stats if connected
        if self.is_connected:
            # This should be implemented in subclasses - avoiding the method name conflict
            # by calling get_database_stats() instead
            try:
                db_stats = asyncio.run(self.get_database_stats())
                stats.update(db_stats)
            except Exception as e:
                logger.warning(f"Could not get database stats for {self.name}: {e}")

        return stats
