import pytest
import asyncio
from UCoreFrameworck.fs.resource import FilesDBResource, FileAddedEvent
from UCoreFrameworck.fs.models import FileRecord
from UCoreFrameworck.messaging.event_bus import EventBus

class DummyResourceManager:
    def __init__(self):
        self.registered = []
    def register(self, resource):
        self.registered.append(resource)

class DummyEventBus(EventBus):
    def __init__(self):
        self.events = []
    async def publish(self, *args, **kwargs):
        self.events.append(args[1] if len(args) > 1 else args[0] if args else None)

@pytest.mark.asyncio
async def test_files_db_resource_lifecycle():
    config = {}
    event_bus = DummyEventBus()
    resource_manager = DummyResourceManager()
    resource = FilesDBResource(config, event_bus, resource_manager=resource_manager)
    await resource.initialize()
    await resource.connect()
    await resource.disconnect()
    assert resource in resource_manager.registered

@pytest.mark.asyncio
async def test_files_db_add_file_event():
    config = {}
    event_bus = DummyEventBus()
    resource = FilesDBResource(config, event_bus)
    file_data = {"name": "test.txt", "path": "/tmp/test.txt", "size": 123}
    record = await resource.add_file(file_data)
    assert isinstance(record, FileRecord)
    assert any(isinstance(e, FileAddedEvent) for e in event_bus.events)
