from ucore_framework.resource.resource import ObservableResource
from ucore_framework.messaging.event_bus import EventBus
from ucore_framework.fs.models import FileRecord, FolderRecord, TagRecord, CatalogRecord, Detection, AnnotationRecord

class FilesDBResource(ObservableResource):
    """
    Resource for managing files, folders, tags, catalogs, detections, and annotations.
    Integrates with storage adapters, event bus, and resource manager.
    Provides CRUD and search operations for file records.
    """
    def __init__(self, config, event_bus: EventBus, resource_manager=None, pool=None, adapter=None):
        """
        Initialize FilesDBResource.

        Args:
            config: Configuration dictionary.
            event_bus: EventBus instance for event publishing.
            resource_manager: Optional ResourceManager for registration.
            pool: Optional connection pool.
            adapter: Optional storage adapter (e.g., MongoFilesDBAdapter).
        """
        super().__init__(name="files_db", resource_type="files_db")
        self.config = config
        self.event_bus = event_bus
        self.resource_manager = resource_manager
        self.pool = pool  # Placeholder for connection pooling
        self.adapter = adapter  # Storage adapter (e.g., MongoFilesDBAdapter)

    async def _create_connection(self):
        """Create a new backend connection (stub for pooling)."""
        return None

    async def _close_connection(self, connection):
        """Close a backend connection (stub for pooling)."""
        pass

    async def _is_connection_valid(self, connection) -> bool:
        """Check if a backend connection is valid (stub for pooling)."""
        return True

    async def _observable_initialize(self) -> None:
        """Resource-specific observable initialization (stub)."""
        pass

    async def _observable_connect(self) -> None:
        """Resource-specific observable connection (stub)."""
        pass

    async def _observable_disconnect(self) -> None:
        """Resource-specific observable disconnection (stub)."""
        pass

    async def _observable_health_check(self):
        """Resource-specific observable health check (stub)."""
        from ucore_framework.resource.resource import ResourceHealth
        return ResourceHealth(status="healthy", details={})

    async def _observable_cleanup(self) -> None:
        """Resource-specific observable cleanup (stub)."""
        pass

    async def initialize(self):
        """
        Initialize the resource and register with ResourceManager if provided.
        """
        if self.resource_manager:
            self.resource_manager.register(self)
        await super().initialize()

    async def connect(self):
        """
        Connect to the storage backend.
        """
        await super().connect()

    async def disconnect(self):
        """
        Disconnect from the storage backend.
        """
        await super().disconnect()

    async def health_check(self):
        """
        Perform a health check on the resource and its pool.
        Returns:
            ResourceHealth: Health status and details.
        """
        from ucore_framework.resource.resource import ResourceHealth
        from typing import Any, Dict
        pool_status: Any = "ok" if self.pool else "not_configured"
        details: Dict[str, Any] = {"pool": pool_status}
        return ResourceHealth(status="healthy", details=details)

    async def add_file(self, file_data):
        """
        Create a new file record.
        Args:
            file_data (dict): File metadata and attributes.
        Returns:
            FileRecord: The created file record.
        """
        if hasattr(self, "adapter") and self.adapter:
            record = await self.adapter.add_file(file_data)
        else:
            from ucore_framework.messaging.events import Event
            record = await FileRecord.new_record(**file_data)
        if hasattr(self.event_bus, "publish"):
            result = self.event_bus.publish(FileAddedEvent(record))
            if result is not None and hasattr(result, "__await__"):
                await result
        return record

    async def get_file(self, file_id):
        """
        Retrieve a file record by its ID.
        Args:
            file_id: The file's unique identifier.
        Returns:
            FileRecord or None
        """
        if hasattr(self, "adapter") and self.adapter:
            return await self.adapter.get_file(file_id)
        return await FileRecord.find_one({'_id': file_id})

    async def update_file(self, file_id, update_data):
        """
        Update a file record by its ID.
        Args:
            file_id: The file's unique identifier.
            update_data (dict): Fields to update.
        Returns:
            FileRecord or None
        """
        if hasattr(self, "adapter") and self.adapter:
            return await self.adapter.update_file(file_id, update_data)
        record = await FileRecord.find_one({'_id': file_id})
        if record:
            for k, v in update_data.items():
                setattr(record, k, v)
            await record.save()
        return record

    async def delete_file(self, file_id):
        """
        Delete a file record by its ID.
        Args:
            file_id: The file's unique identifier.
        Returns:
            FileRecord or None
        """
        if hasattr(self, "adapter") and self.adapter:
            return await self.adapter.delete_file(file_id)
        record = await FileRecord.find_one({'_id': file_id})
        if record:
            await record.delete()
        return record

    async def search_files(self, query: dict):
        """
        Search for file records matching a query.
        Args:
            query (dict): Mongo-style query.
        Returns:
            list[FileRecord]
        """
        if hasattr(self, "adapter") and self.adapter:
            return await self.adapter.search_files(query)
        return await FileRecord.find(query)

from ucore_framework.messaging.events import Event
class FileAddedEvent(Event):
    """
    Event published when a file is added to the resource.
    """
    def __init__(self, record):
        """
        Args:
            record (FileRecord): The file record that was added.
        """
        super().__init__()
        self.record = record

# Example integration with ResourceManager and EventBus

def register_files_db_resource(app, config, event_bus, resource_manager):
    """
    Register the FilesDBResource with the resource manager.

    Args:
        app: The application instance.
        config: Configuration dictionary.
        event_bus: EventBus instance.
        resource_manager: ResourceManager instance.

    Returns:
        FilesDBResource: The registered resource.
    """
    resource = FilesDBResource(config, event_bus, resource_manager=resource_manager)
    resource_manager.register(resource)
    return resource

# Add methods for update, delete, search, tags, catalogs, detection, annotation, etc.
