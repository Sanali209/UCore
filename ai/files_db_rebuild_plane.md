# files_db Rebuild Implementation Plan

## Overview

This plan describes how to rebuild the `files_db` module using current UCore framework capabilities, focusing on modularity, extensibility, and integration with the event-driven/resource architecture.

---

## 1. Core Entities and Models

- All file, folder, tag, catalog, detection, and annotation records are defined in `framework/fs/models.py` using Mongo ORM.
- Reference fields enable rich relationships (parent, tag, catalog, object, etc).
- Extendable via `itemTypeMap` for custom record types.

---

## 2. Resource Layer

- `FilesDBResource` in `framework/fs/resource.py` implements the ObservableResource pattern.
- Handles lifecycle: initialize, connect, disconnect, health_check.
- Integrates with `ResourceManager` and `EventBus` for registration and event publishing.
- Abstract method stubs allow for pooling and async resource management.

---

## 3. Storage Adapter

- `FilesDBStorageAdapter` interface and `MongoFilesDBAdapter` implementation in `framework/fs/storage_adapter.py`.
- Adapters encapsulate backend logic (MongoDB, future alternatives).
- Methods for start/stop, add_file, and future CRUD/search operations.

---

## 4. Indexers and File Type Strategies

- `framework/fs/indexers.py` provides:
  - Base `Indexer` class for pluggable file analysis.
  - Example indexers: DeepDanboru, FaceDetector.
  - `FileTypeStrategy` for extension-based processing pipelines.
  - Registry for dynamic strategy lookup and registration.

---

## 5. Annotation Tools

- `framework/fs/annotation.py` provides:
  - Base `AnnotationJob` class for annotation logic.
  - Example jobs: average rating, single label.
  - Registry for registering and retrieving annotation jobs.

---

## 6. Testing

- `tests/fs/test_files_db.py` scaffolds resource lifecycle and event publishing tests.
- Dummy managers and event buses allow isolated unit/integration testing.

---

## 7. Extensibility Recommendations

- **Add new indexers** by subclassing `Indexer` and registering with strategies.
- **Add new annotation jobs** by subclassing `AnnotationJob` and registering in the job registry.
- **Support new storage backends** by implementing `FilesDBStorageAdapter`.
- **Integrate with other UCore resources** via event bus and resource manager patterns.
- **Use Mongo ORM features** for advanced queries, relationships, and schema evolution.

---

## 8. Pseudocode for Integration

```python
# Register resource in app
resource = FilesDBResource(config, event_bus, resource_manager)
resource_manager.register(resource)

# Add a file and trigger indexers
record = await resource.add_file(file_data)
strategy = get_strategy_by_extension(record.path.split('.')[-1])
if strategy:
    await strategy.process(record, record.path)

# Run annotation job
job = get_annotation_job("avg_rating")
await job.run(record, annotation_data)
```

---

## 9. Best Practices

- Keep indexers and annotation jobs stateless and idempotent.
- Use event-driven patterns for extensibility and decoupling.
- Prefer async methods for all IO and resource operations.
- Write comprehensive tests for each extension point.

---

## 10. Next Steps

- Implement CRUD/search methods in resource and adapter.
- Expand test coverage for indexers and annotation jobs.
- Document extension APIs for plugin developers.

---

This plan ensures a robust, extensible, and maintainable files_db module leveraging the full power of the UCore framework.
