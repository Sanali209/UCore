import pytest
import asyncio
from UCoreFrameworck.fs.resource import FilesDBResource
from UCoreFrameworck.fs.models import FileRecord
from UCoreFrameworck.fs.storage_adapter import MongoFilesDBAdapter

class DummyEventBus:
    async def publish(self, *args, **kwargs):
        self.last_event = args[1] if len(args) > 1 else args[0] if args else None

@pytest.mark.asyncio
async def test_files_db_resource_crud(monkeypatch):
    event_bus = DummyEventBus()
    resource = FilesDBResource(config={}, event_bus=event_bus, adapter=MongoFilesDBAdapter(app=None))

    # Add file
    file_data = {"path": "test.txt", "size": 123, "tags": ["unit"]}
    record = await resource.add_file(file_data)
    assert record.path == "test.txt"
    assert record.size == 123

    # Get file
    fetched = await resource.get_file(record._id)
    assert fetched is not None
    assert fetched.path == "test.txt"

    # Update file
    updated = await resource.update_file(record._id, {"size": 456})
    assert updated.size == 456

    # Search files
    results = await resource.search_files({"tags": ["unit"]})
    assert any(f.path == "test.txt" for f in results)

    # Delete file
    deleted = await resource.delete_file(record._id)
    assert deleted is not None
    assert deleted.path == "test.txt"
