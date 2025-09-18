# Test Failures and Error Analysis Report

## Group 1: NotImplementedError — Missing `collection_name` Attribute

### Description
Several MongoDB record classes do not define the required `collection_name` class attribute. This attribute is necessary for the `BaseMongoRecord`/`CollectionRecord` ORM to map models to MongoDB collections. Its absence causes all CRUD operations on these models to fail with `NotImplementedError`.

### Affected Classes and Files
- **CatalogRecord** (`framework/fs/models.py`)
- **FileRecord** (`framework/fs/models.py`)
- **TagRecord** (`framework/fs/models.py`)
- **RelationRecord** (`framework/fs/components/relations.py`)
- **WebLinkRecord** (`framework/fs/components/web_link.py`)

### Affected Tests
- `tests/fs/test_catalog_manager.py`
- `tests/fs/test_files_db.py`
- `tests/fs/test_tag_manager.py`
- `tests/fs/test_relation_record.py`
- `tests/fs/test_web_link_record.py`
- `tests/fs/test_files_db_resource.py`

### Example Error
```
NotImplementedError: CatalogRecord must define a 'collection_name' attribute.
```

### Root Cause
All affected classes inherit from `BaseMongoRecord` (directly or via `CollectionRecord`). The base class expects a `collection_name` attribute to be defined at the class level. Without it, any database operation raises `NotImplementedError`.

### Recommendation
Add a `collection_name` class attribute to each affected model, e.g.:
```python
class CatalogRecord(CollectionRecord):
    collection_name = "catalogs"
    ...
```
Repeat for each model with an appropriate collection name.

---

## Group 2: TypeError — ResourceEvent Unexpected Keyword Argument

### Description
A test involving resource initialization fails due to a `TypeError`:
```
TypeError: ResourceEvent.__init__() got an unexpected keyword argument 'metadata'
```
This occurs in:
- `framework/resource/resource.py` (when calling `ResourceEvent`)
- Affects: `tests/fs/test_files_db.py::test_files_db_resource_lifecycle`

### Root Cause
The `ResourceEvent` class does not accept a `metadata` keyword argument, but the code attempts to pass it.

### Recommendation
Update the `ResourceEvent` class to accept a `metadata` argument, or remove the argument from the call in `resource.py`.

---

## Group 3: RuntimeWarnings — Coroutine Was Never Awaited

### Description
Multiple warnings about coroutines not being awaited, e.g.:
```
RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
```
These are found in:
- `tests/desktop/test_flet_adapter.py`
- `tests/messaging/test_redis_adapter.py`
- `tests/messaging/test_redis_event_bridge.py`
- `tests/monitoring/test_http_metrics.py`
- `tests/processing/test_task_system.py`
- `tests/resource/test_resource_manager.py`
- `tests/web/test_http_server.py`
- ...and others

### Root Cause
Async functions or mocks are called without `await`. This can cause tests to pass incorrectly or miss async errors.

### Recommendation
Ensure all async functions and mocks are awaited in tests and implementation.

---

## Group 4: Pytest Deprecation Warnings

### Description
Warnings about deprecated or soon-to-be-unsupported pytest features, especially around async fixtures.

### Recommendation
Update test fixtures to use `@pytest_asyncio.fixture` or compatible async fixture patterns.

---

## Summary Table

| File/Test                                 | Error Type                  | Root Cause/Recommendation                  |
|--------------------------------------------|-----------------------------|--------------------------------------------|
| test_catalog_manager.py, test_files_db.py, test_tag_manager.py, test_relation_record.py, test_web_link_record.py, test_files_db_resource.py | NotImplementedError          | Add `collection_name` to models            |
| test_files_db.py::test_files_db_resource_lifecycle | TypeError                   | Fix `ResourceEvent` constructor            |
| Many tests                                | RuntimeWarning              | Await all async functions/mocks            |
| Many tests                                | PytestDeprecationWarning    | Update async fixture usage                 |
