"""
File database resource utilities for UCore Framework.

This module provides:
- FilesDBResource: Resource for managing files, folders, tags, catalogs, detections, and annotations
- Integration with storage adapters, event bus, and resource manager
- CRUD and search operations for file records
- FileAddedEvent: Event for file creation

Classes:
    FilesDBResource: File database resource for UCore.
    FileAddedEvent: Event published when a file is added.

Usage:
    from ucore_framework.fs.resource import FilesDBResource

    files_db = FilesDBResource(config, event_bus)
    await files_db.add_file({...})
    await files_db.get_file(file_id)
"""

from ucore_framework.core.resource.resource import ObservableResource
from ucore_framework.core.event_bus import EventBus
from ucore_framework.fs.models import FileRecord, FolderRecord, TagRecord, CatalogRecord, Detection, AnnotationRecord

from typing import Any, Optional, Dict, List

import asyncio

class FilesDBResource(ObservableResource):
    """
    File database resource for UCore.

    Responsibilities:
        - Manage files, folders, tags, catalogs, detections, and annotations
        - Integrate with storage adapters, event bus, and resource manager
        - Provide CRUD and search operations for file records

    Example:
        files_db = FilesDBResource(config, event_bus)
        await files_db.add_file({...})
        await files_db.get_file(file_id)
    """
    config: Dict[str, Any]
    event_bus: EventBus
    resource_manager: Optional[Any]
    pool: Optional[Any]
    adapter: Optional[Any]

    def __init__(
        self,
        config: Dict[str, Any],
        event_bus: EventBus,
        resource_manager: Optional[Any] = None,
        pool: Optional[Any] = None,
        adapter: Optional[Any] = None
    ) -> None:
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

    async def _create_connection(self) -> Optional[Any]:
        """Create a new backend connection (stub for pooling)."""
        return None

    async def _close_connection(self, connection: Optional[Any]) -> None:
        """Close a backend connection (stub for pooling)."""
        pass

    async def _is_connection_valid(self, connection: Optional[Any]) -> bool:
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

    async def _observable_health_check(self) -> Any:
        """Resource-specific observable health check (stub)."""
        from ucore_framework.core.resource.resource import ResourceHealth
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
        from ucore_framework.core.resource.resource import ResourceHealth
        from typing import Any, Dict
        pool_status: Any = "ok" if self.pool else "not_configured"
        details: Dict[str, Any] = {"pool": pool_status}
        return ResourceHealth(status="healthy", details=details)

    async def add_file(self, file_data: Dict[str, Any]) -> FileRecord:
        """
        Create a new file record.
        Args:
            file_data (dict): File metadata and attributes.
        Returns:
            FileRecord: The created file record.
        """
        if hasattr(self, "adapter") and self.adapter:
            record: FileRecord = await self.adapter.add_file(file_data)
        else:
            from ucore_framework.core.resource.events import Event
            record: FileRecord = await FileRecord.new_record(**file_data)
        if hasattr(self.event_bus, "publish"):
            result = self.event_bus.publish(FileAddedEvent(record))
            if result is not None and hasattr(result, "__await__"):
                await result
        return record

    async def get_file(self, file_id: Any) -> Optional[FileRecord]:
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

    async def update_file(self, file_id: Any, update_data: Dict[str, Any]) -> Optional[FileRecord]:
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
        record: Optional[FileRecord] = await FileRecord.find_one({'_id': file_id})
        if record:
            for k, v in update_data.items():
                setattr(record, k, v)
            await record.save()
        return record

    async def delete_file(self, file_id: Any) -> Optional[FileRecord]:
        """
        Delete a file record by its ID.
        Args:
            file_id: The file's unique identifier.
        Returns:
            FileRecord or None
        """
        if hasattr(self, "adapter") and self.adapter:
            return await self.adapter.delete_file(file_id)
        record: Optional[FileRecord] = await FileRecord.find_one({'_id': file_id})
        if record:
            await record.delete()
        return record

    async def search_files(self, query: Dict[str, Any]) -> List[FileRecord]:
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

    # Example: Non-blocking file read using asyncio.to_thread
    async def read_file_content(self, file_path: str) -> str:
        """
        Read file content in a non-blocking way using asyncio.to_thread.
        """
        def _read_file_sync(path):
            with open(path, "r", encoding="utf-8") as f:
                return f.read()
        return await asyncio.to_thread(_read_file_sync, file_path)

    # NOTE: If you add any sync file I/O in async methods, wrap it with asyncio.to_thread for non-blocking performance.

from ucore_framework.core.resource.events import Event
class FileAddedEvent(Event):
    """
    Event published when a file is added to the FilesDBResource.

    Attributes:
        record: The FileRecord that was added.

    Example:
        event = FileAddedEvent(record)
    """
    record: FileRecord

    def __init__(self, record: FileRecord) -> None:
        """
        Initialize a FileAddedEvent.

        Args:
            record (FileRecord): The file record that was added.
        """
        super().__init__()
        self.record = record

# Example integration with ResourceManager and EventBus

def register_files_db_resource(
    app: Any,
    config: Dict[str, Any],
    event_bus: EventBus,
    resource_manager: Any
) -> FilesDBResource:
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
