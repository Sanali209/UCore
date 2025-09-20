"""Event publishing logic module (decomposed from resource.py)."""

from ucore_framework.core.resource.events import Event
from ucore_framework.fs.models import FileRecord

class FileAddedEvent(Event):
    """
    Event published when a file is added to the resource.
    """
    record: FileRecord

    def __init__(self, record: FileRecord) -> None:
        super().__init__()
        self.record = record

class EventPublisher:
    """
    Publishes events related to file operations.
    """
    def __init__(self, event_bus):
        self.event_bus = event_bus

    async def publish_file_added(self, record: FileRecord):
        event = FileAddedEvent(record)
        result = self.event_bus.publish(event)
        if result is not None and hasattr(result, "__await__"):
            await result
