"""
MongoDB Database Resource
Concrete implementation of DatabaseResource for MongoDB
"""

import logging
from typing import Any, Dict, Optional, Union, List
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import ServerSelectionTimeoutError, OperationFailure

from .database import DatabaseResource
from ..exceptions import ResourceError, ResourceConnectionError


logger = logging.getLogger(__name__)


class MongoDBResource(DatabaseResource):
    """
    MongoDB-specific database resource implementation

    Integrates with the existing UCore MongoDB infrastructure and provides
    connection management, health checks, and query execution for MongoDB.
    """

    def __init__(
        self,
        name: str,
        connection_string: str,
        database_name: str = "ucore_db",
        config: Optional[Dict[str, Any]] = None,
        connection_timeout: float = 10.0,
        max_pool_size: int = 10,
        min_pool_size: int = 0,
        max_idle_time: float = 300.0,  # 5 minutes
        health_check_collection: str = "health_check",
    ):
        super().__init__(
            name=name,
            connection_string=connection_string,
            config=config,
            connection_timeout=connection_timeout,
            max_pool_size=max_pool_size,
            min_pool_size=min_pool_size,
            health_check_query=health_check_collection,
        )

        self.database_name = database_name
        self.max_idle_time = max_idle_time
        self.health_check_collection = health_check_collection

        # MongoDB-specific state
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._server_info: Optional[Dict[str, Any]] = None

    def _default_health_check_query(self) -> str:
        """Return default health check collection name"""
        return "health_check"

    def _validate_connection_string(self, conn_string: str) -> None:
        """Validate MongoDB connection string format"""
        super()._validate_connection_string(conn_string)

        # Basic MongoDB connection string validation
        if not conn_string.startswith("mongodb://") and not conn_string.startswith("mongodb+srv://"):
            raise ValueError("Invalid MongoDB connection string - must start with mongodb:// or mongodb+srv://")

        if len(self.database_name.strip()) == 0:
            raise ValueError("Database name cannot be empty")

    async def _create_connection(self) -> AsyncIOMotorClient:
        """Create MongoDB client connection"""
        try:
            # Configure client options
            client_kwargs = {
                'maxPoolSize': self.max_pool_size,
                'minPoolSize': self.min_pool_size,
                'maxIdleTimeMS': int(self.max_idle_time * 1000),
                'serverSelectionTimeoutMS': int(self.timeout * 1000),
                'connectTimeoutMS': int(self.timeout * 1000),
            }

            # Add SSL options if configured
            if self.config:
                if self.config.get('ssl', False):
                    client_kwargs['ssl'] = True
                if self.config.get('ssl_cert_reqs'):
                    client_kwargs['ssl_cert_reqs'] = self.config['ssl_cert_reqs']
                if self.config.get('ssl_ca_certs'):
                    client_kwargs['ssl_ca_certs'] = self.config['ssl_ca_certs']

            # Create client
            client = AsyncIOMotorClient(self.connection_string, **client_kwargs)

            # Test connection
            await client.admin.command('ping')

            # Get server info
            self._server_info = await client.server_info()

            # Get database reference
            self._database = client[self.database_name]

            logger.info(f"MongoDB client created - connected to {self._server_info.get('version', 'unknown version')}")
            return client

        except Exception as e:
            raise ResourceConnectionError(
                self.name,
                f"Failed to create MongoDB connection: {e}"
            ) from e

    async def _close_connection(self, connection: AsyncIOMotorClient) -> None:
        """Close MongoDB client connection"""
        if connection:
            connection.close()
            self._client = None
            self._database = None
            self._server_info = None
            logger.info("MongoDB client connection closed")

    async def _test_connection(self, connection: AsyncIOMotorClient) -> bool:
        """Test MongoDB connection health"""
        try:
            # Use admin command to test connection
            result = await connection.admin.command('ping')
            return result.get('ok', 0) == 1.0
        except Exception as e:
            logger.warning(f"MongoDB connection test failed: {e}")
            return False

    async def _execute_query(self, query: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """Execute MongoDB query"""
        if not self._database:
            raise ResourceError("Database not available", self.name)

        try:
            # For MongoDB, we expect query to be a collection name
            # and params to contain the query/filter
            collection = self._database[query]
            filter_dict = params or {}

            # Execute find_one as default query operation
            result = await collection.find_one(filter_dict)
            return result

        except Exception as e:
            raise ResourceError(f"MongoDB query failed: {e}", self.name) from e

    async def ping(self) -> bool:
        """Ping MongoDB to test connectivity"""
        return await self._test_connection(self._client) if self._client else False

    async def get_database_stats(self) -> Dict[str, Any]:
        """Get MongoDB-specific database statistics"""
        if not self._database:
            return {}

        try:
            # Get database stats
            db_stats = await self._database.command('dbStats')

            # Get server stats if available
            server_stats = {}
            if self._client:
                server_stats = await self._client.server_info()

            stats = {
                "mongodb_version": server_stats.get('version', 'unknown'),
                "database_name": self.database_name,
                "collections_count": db_stats.get('collections', 0),
                "documents_count": db_stats.get('objects', 0),
                "data_size_mb": round(db_stats.get('dataSize', 0) / (1024 * 1024), 2),
                "storage_size_mb": round(db_stats.get('storageSize', 0) / (1024 * 1024), 2),
                "indexes_count": db_stats.get('indexes', 0),
                "index_size_mb": round(db_stats.get('indexSize', 0) / (1024 * 1024), 2),
                "connections": {
                    "active": server_stats.get('connections', {}).get('current', 0),
                    "available": server_stats.get('connections', {}).get('available', 0),
                    "total_created": server_stats.get('connections', {}).get('totalCreated', 0),
                },
                "uptime_seconds": server_stats.get('uptime', 0),
            }

            return stats

        except Exception as e:
            logger.warning(f"Error getting MongoDB stats: {e}")
            return {}

    # MongoDB-specific operations
    async def list_collections(self) -> List[str]:
        """List all collections in the database"""
        if not self.is_connected or not self._database:
            raise ResourceError("Database not connected", self.name)

        try:
            collections = await self._database.list_collection_names()
            return collections
        except Exception as e:
            raise ResourceError(f"Failed to list collections: {e}", self.name) from e

    async def get_collection_stats(self, collection_name: str) -> Dict[str, Any]:
        """Get statistics for a specific collection"""
        if not self.is_connected or not self._database:
            raise ResourceError("Database not connected", self.name)

        try:
            collection = self._database[collection_name]
            stats = await self._database.command('collStats', collection_name)

            return {
                "name": collection_name,
                "document_count": stats.get('count', 0),
                "size_mb": round(stats.get('size', 0) / (1024 * 1024), 2),
                "storage_size_mb": round(stats.get('storageSize', 0) / (1024 * 1024), 2),
                "index_count": stats.get('nindexes', 0),
                "index_size_mb": round(stats.get('totalIndexSize', 0) / (1024 * 1024), 2),
            }
        except Exception as e:
            raise ResourceError(f"Failed to get collection stats: {e}", self.name) from e

    async def create_collection(self, name: str, **options) -> None:
        """Create a new collection"""
        if not self.is_connected or not self._database:
            raise ResourceError("Database not connected", self.name)

        try:
            await self._database.create_collection(name, **options)
            logger.info(f"Created MongoDB collection: {name}")
        except Exception as e:
            raise ResourceError(f"Failed to create collection {name}: {e}", self.name) from e

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        """Get a collection by name"""
        if not self.is_connected or not self._database:
            raise ResourceError("Database not connected", self.name)

        return self._database[name]

    async def health_check_detailed(self) -> Dict[str, Any]:
        """Perform detailed MongoDB health check"""
        health = {
            "connection_healthy": False,
            "database_accessible": False,
            "collections_accessible": False,
            "write_accessible": False,
            "latency_ms": None,
            "server_info": {},
            "collections_count": 0,
            "error": None,
        }

        try:
            if not self.is_connected or not self._client:
                health["error"] = "Not connected"
                return health

            # Test basic ping
            import time
            start_time = time.time()
            ping_result = await self._client.admin.command('ping')
            health["connection_healthy"] = ping_result.get('ok', 0) == 1.0
            end_time = time.time()
            health["latency_ms"] = round((end_time - start_time) * 1000, 2)

            if not self._database:
                health["error"] = "Database not available"
                return health

            # Test database access
            await self._database.command('dbStats')
            health["database_accessible"] = True

            # Test collections access
            collections = await self._database.list_collection_names()
            health["collections_count"] = len(collections)
            health["collections_accessible"] = True

            # Test write access (create test collection if needed)
            test_collection_name = "_resource_health_test"
            if test_collection_name not in collections:
                await self._database.create_collection(test_collection_name)

            collection = self._database[test_collection_name]
            test_doc = {"_id": "health_check", "timestamp": time.time(), "resource": self.name}
            await collection.replace_one({"_id": "health_check"}, test_doc, upsert=True)
            health["write_accessible"] = True

            # Cleanup test document
            await collection.delete_one({"_id": "health_check"})

            # Get server info
            health["server_info"] = {
                "version": self._server_info.get("version", "unknown") if self._server_info else "unknown",
                "host": self._server_info.get("host", "unknown") if self._server_info else "unknown",
                "uptime": self._server_info.get("uptime", 0) if self._server_info else 0,
            }

        except Exception as e:
            health["error"] = str(e)
            logger.warning(f"MongoDB detailed health check failed: {e}")

        return health
