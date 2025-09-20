"""Core file database logic module (decomposed from resource.py)."""

from ucore_framework.core.resource.resource import ObservableResource
from ucore_framework.fs.models import FileRecord
from typing import Any, Optional, Dict, List

class FilesDBCore(ObservableResource):
    """
    Core logic for managing files, folders, and related records.
    Handles connection, CRUD, and adapter integration.
    """
    config: Dict[str, Any]
    pool: Optional[Any]
    adapter: Optional[Any]

    def __init__(
        self,
        config: Dict[str, Any],
        pool: Optional[Any] = None,
        adapter: Optional[Any] = None
    ) -> None:
        super().__init__(name="files_db", resource_type="files_db")
        self.config = config
        self.pool = pool
        self.adapter = adapter

    async def _create_connection(self) -> Optional[Any]:
        return None

    async def _close_connection(self, connection: Optional[Any]) -> None:
        pass

    async def _is_connection_valid(self, connection: Optional[Any]) -> bool:
        return True

    async def _observable_initialize(self) -> None:
        pass

    async def _observable_connect(self) -> None:
        pass

    async def _observable_disconnect(self) -> None:
        pass

    async def _observable_health_check(self) -> Any:
        from ucore_framework.core.resource.resource import ResourceHealth
        return ResourceHealth(status="healthy", details={})

    async def _observable_cleanup(self) -> None:
        pass

    async def initialize(self):
        await super().initialize()

    async def connect(self):
        await super().connect()

    async def disconnect(self):
        await super().disconnect()

    async def health_check(self):
        from ucore_framework.core.resource.resource import ResourceHealth
        pool_status: Any = "ok" if self.pool else "not_configured"
        details: Dict[str, Any] = {"pool": pool_status}
        return ResourceHealth(status="healthy", details=details)

    async def add_file(self, file_data: Dict[str, Any]) -> FileRecord:
        if self.adapter:
            record: FileRecord = await self.adapter.add_file(file_data)
        else:
            record: FileRecord = await FileRecord.new_record(**file_data)
        return record

    async def get_file(self, file_id: Any) -> Optional[FileRecord]:
        if self.adapter:
            return await self.adapter.get_file(file_id)
        return await FileRecord.find_one({'_id': file_id})

    async def update_file(self, file_id: Any, update_data: Dict[str, Any]) -> Optional[FileRecord]:
        if self.adapter:
            return await self.adapter.update_file(file_id, update_data)
        record: Optional[FileRecord] = await FileRecord.find_one({'_id': file_id})
        if record:
            for k, v in update_data.items():
                setattr(record, k, v)
            await record.save()
        return record

    async def delete_file(self, file_id: Any) -> Optional[FileRecord]:
        if self.adapter:
            return await self.adapter.delete_file(file_id)
        record: Optional[FileRecord] = await FileRecord.find_one({'_id': file_id})
        if record:
            await record.delete()
        return record
