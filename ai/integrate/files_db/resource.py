from framework.resource.resource import ObservableResource
from framework.messaging.event_bus import EventBus
from ai.integrate.files_db.models import FileRecord, FolderRecord, TagRecord, CatalogRecord, Detection, AnnotationRecord
from framework.messaging.events import Event
from framework.resource.resource import ResourceHealth

class FilesDBResource(ObservableResource):
    def __init__(self, config, event_bus: EventBus):
        super().__init__(name="files_db", resource_type="files_db")
        self.config = config
        self.event_bus = event_bus

    async def initialize(self):
        # Initialize adapters, models, etc.
        await super().initialize()

    async def connect(self):
        # Connect to storage backend
        await super().connect()

    async def disconnect(self):
        # Disconnect from storage backend
        await super().disconnect()

    async def health_check(self):
        # Implement health check logic
        return ResourceHealth(status="healthy", details={})

    async def add_file(self, file_data):
        record = await FileRecord.new_record(**file_data)
        # Proper event publishing (replace with actual FileAddedEvent if defined)
        if hasattr(self.event_bus, "publish"):
            self.event_bus.publish(FileAddedEvent(record))
        return record

class FileAddedEvent(Event):
    def __init__(self, record):
        super().__init__()
        self.record = record

    # Add methods for update, delete, search, tags, catalogs, detection, annotation, etc.
