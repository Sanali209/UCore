# framework/data/mongo_adapter.py
"""
This module contains the MongoDBAdapter, a UCore component for managing 
MongoDB connections and integrating models into the application lifecycle.
"""
from typing import Type
from motor.motor_asyncio import AsyncIOMotorClient
from diskcache import Index

from UCoreFrameworck.core.component import Component
from UCoreFrameworck.core.config import Config
from UCoreFrameworck.data.mongo_orm import BaseMongoRecord


class MongoDBAdapter(Component):
    """
    Manages the connection to MongoDB and handles the lifecycle of MongoDB-based
    data models within a UCore application.
    """
    def __init__(self, app):
        super().__init__(app)
        self.client = None
        self.db = None
        self.bulk_op_cache = None
        self._registered_models: list[Type[BaseMongoRecord]] = []

    def register_models(self, models: list[Type[BaseMongoRecord]]):
        """
        Registers model classes with the adapter. The adapter will inject the
        database client into these models upon application startup.

        :param models: A list of BaseMongoRecord subclasses to register.
        """
        self._registered_models.extend(models)

    async def start(self):
        """
        UCore lifecycle method. Connects to the database, initializes the bulk
        operation cache, and injects dependencies into the registered models.
        """
        # DEV-1.3: Read config and connect
        self.app.logger.info("MongoDBAdapter starting...")
        # Get the Config instance from the app's container
        config = self.app.container.get(Config)
        db_config = config.get('database.mongodb', {})
        db_url = db_config.get('url', 'mongodb://localhost:27017')
        db_name = db_config.get('database_name', 'ucore_db')

        self.client = AsyncIOMotorClient(db_url)
        self.db = self.client[db_name]
        self.app.logger.info(f"Connected to MongoDB at {db_url}/{db_name}.")

        # Placeholder for bulk op cache initialization
        cache_dir = db_config.get('cache_dir', './.cache/mongo_bulk_ops')
        self.bulk_op_cache = Index(cache_dir)
        
        # DEV-1.6: Inject DB client into models
        for model_cls in self._registered_models:
            try:
                model_cls.inject_db_client(self.db, self.bulk_op_cache)
                self.app.logger.debug(f"Injected DB client into model: {model_cls.__name__}")
                # DEV-3.3: Create indexes now that the client is injected
                await model_cls._create_indexes()
            except Exception as e:
                self.app.logger.error(f"Error injecting DB client into model {getattr(model_cls, '__name__', str(model_cls))}: {e}")

    async def stop(self):
        """
        UCore lifecycle method. Processes any outstanding bulk operations and
        gracefully closes the database connection.
        """
        self.app.logger.info("MongoDBAdapter stopping...")
        # DEV-4.3: Process bulk ops - now enabled
        await self.process_bulk_ops()
        if self.client:
            self.client.close()
            self.app.logger.info("MongoDB connection closed.")

    async def process_bulk_ops(self):
        """
        Processes all queued bulk operations from the disk cache.
        Adapted from the original code's attended_process_bulk_ops.
        """
        # DEV-4.3: Full implementation of deferred bulk operations
        self.app.logger.info("Processing outstanding bulk MongoDB operations...")

        if not self.bulk_op_cache:
            return

        # Get all keys from the bulk cache
        all_keys = list(self.bulk_op_cache.keys())

        for key in all_keys:
            if key.startswith("DeleteMany_"):
                collection_name = key.split("_", 1)[1]
                try:
                    collection = self.db[collection_name]
                    bulk_ops = self.bulk_op_cache[key]

                    if bulk_ops:
                        from pymongo import DeleteMany

                        # Convert to DeleteMany operations
                        delete_ops = [DeleteMany(query) for query in bulk_ops if query]

                        # Process in batches of 128
                        batch_size = 128
                        for i in range(0, len(delete_ops), batch_size):
                            batch = delete_ops[i:i+batch_size]
                            if batch:
                                collection.bulk_write(batch)

                        # Clear processed operations
                        del self.bulk_op_cache[key]

                except Exception as e:
                    self.app.logger.error(f"Error processing bulk ops for {collection_name}: {e}")
