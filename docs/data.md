# Data Layer & MongoDB ORM

This section documents the data management layer of UCore, including the async MongoDB ORM, test adapters, and extensibility patterns.

---

## Overview

UCore provides an extensible, asynchronous Object-Document Mapper (ODM) for MongoDB, supporting:
- Async CRUD operations
- Field descriptors and reference fields
- Batched queries for performance
- Test adapters for isolated unit testing
- Bulk operations and identity map pattern

---

## Key Components

- **BaseMongoRecord:**  
  The base class for all MongoDB models. Provides async CRUD, field management, and instance caching.

- **Field, ReferenceField, ReferenceListField:**  
  Descriptors for model fields and relationships.

- **DbRecordMeta:**  
  Metaclass implementing identity map and schema caching.

- **TestableMongoRecord:**  
  Test-specific subclass for mocking and patching in unit tests.

---

## Defining a Model

```python
from ucore_framework.data.mongo_orm import BaseMongoRecord, Field, ReferenceField

class User(BaseMongoRecord):
    collection_name = "users"
    name = Field(str)
    email = Field(str)

class Group(BaseMongoRecord):
    collection_name = "groups"
    name = Field(str)

User.group = ReferenceField(Group)
```

---

## CRUD Operations

```python
# Inject db client (see tests/utils/test_mongo.py for setup)
User.inject_db_client(db, bulk_cache=None)

# Create a new user
user = await User.new_record(name="Alice", email="alice@example.com")

# Fetch by id
user = await User.get_by_id(user_id)

# Find with query
users = await User.find({"name": "Alice"})

# Update and save
user.props_cache["email"] = "alice@new.com"
await user.save()

# Delete
await user.delete()
```

---

## Reference Fields

Reference fields allow you to define relationships between documents.

```python
class User(BaseMongoRecord):
    collection_name = "users"
    group = ReferenceField(Group)

# Access referenced group
group_ref = user.group  # LazyReference
group = await group_ref.fetch()
```

---

## Bulk Operations

Efficiently update or insert many records:

```python
await User.bulk_update([{"_id": id1, "name": "A"}, {"_id": id2, "name": "B"}])
```

---

## Testing with TestableMongoRecord

For unit tests, use the test adapter to patch and mock database operations.

```python
from ucore_framework.data.mongo_test_adapter import TestableMongoRecord

class TestUser(TestableMongoRecord):
    collection_name = "test_users"
```

---

## Extending the ORM

- Add custom field types by subclassing `Field`.
- Implement new adapters for other databases by following the BaseMongoRecord pattern.
- Use the identity map and LRU cache for efficient instance management.

---

See also:  
- [Core Framework](core.md)  
- [Testing](testing.md)
