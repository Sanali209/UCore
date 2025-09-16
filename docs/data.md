# Data Domain Guide

## Purpose

The data domain provides persistence and caching for UCore, including SQLAlchemy integration, disk cache, and a MongoDB Object-Document Mapper (ODM).

---

## Main Classes & Components

- `SQLAlchemyAdapter`: Async database adapter for SQL databases.
- `DiskCacheAdapter`: High-performance disk-based cache.
- `MongoDBAdapter`: MongoDB integration and model registration.
- `BaseMongoRecord`, `Field`, `ReferenceField`: MongoDB ODM model base and fields.
- `MongoHierarchicalDataViewModel`: Hierarchical data view for MongoDB.

---

## Usage Example

```python
from framework.data.db import SQLAlchemyAdapter
from framework.data.disk_cache import DiskCacheAdapter

db_adapter = SQLAlchemyAdapter(app)
cache = DiskCacheAdapter(app)
```

---

## MongoDB ODM Example

```python
from framework.data.mongo_orm import BaseMongoRecord, Field

class User(BaseMongoRecord):
    collection_name = "users"
    name: str = Field()
    email: str = Field()
```

---

## Extensibility & OOP

- Subclass `BaseMongoRecord` for new MongoDB models.
- Use adapters for custom DB or cache backends.

---

## Integration Points

- Used by resource, processing, and web domains for persistence and caching.
- MongoDB ODM integrates with event system and DI.

---

## See Also

- [MongoDB ODM Guide](data/mongodb-odm-guide.md)
- [Project Structure Guide](project-structure-guide.md)
