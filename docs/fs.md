# File System Resource Management

This section documents the file system resource management layer of UCore, including file/folder/tag/catalog models, adapters, and integration with the event bus and resource manager.

---

## Overview

UCore provides a unified interface for managing files, folders, tags, catalogs, detections, and annotations.  
It supports:
- CRUD operations for file records
- Integration with storage adapters (e.g., MongoDB, local FS)
- Event-driven updates via the event bus
- Extensible resource manager for registration and pooling

---

## Key Components

- **FilesDBResource:**  
  Main resource class for managing files and related entities.

- **FileRecord, FolderRecord, TagRecord, CatalogRecord, Detection, AnnotationRecord:**  
  Data models for file system entities.

- **Adapters:**  
  Pluggable backends for storage (MongoFilesDBAdapter, etc.).

---

## Usage Example

```python
from ucore_framework.fs.resource import FilesDBResource

files_db = FilesDBResource(config, event_bus)

# Add a file
record = await files_db.add_file({"name": "report.pdf", "tags": ["finance"]})

# Get a file by ID
file = await files_db.get_file(record.id)

# Update a file
await files_db.update_file(file.id, {"tags": ["finance", "2025"]})

# Delete a file
await files_db.delete_file(file.id)

# Search files
results = await files_db.search_files({"tags": "finance"})
```

---

## Event Integration

File operations can publish events to the event bus for real-time updates and automation.

```python
from ucore_framework.fs.resource import FileAddedEvent

@event_bus.subscribe(FileAddedEvent)
async def on_file_added(event):
    print("File added:", event.record)
```

---

## Extending File System Resources

- Implement new adapters by subclassing the resource or adapter base classes.
- Add new entity types (e.g., custom tags, metadata) by extending the models.
- Integrate with monitoring for file system health and metrics.

---

See also:  
- [Core Framework](core.md)  
- [Data Layer & MongoDB ORM](data.md)
