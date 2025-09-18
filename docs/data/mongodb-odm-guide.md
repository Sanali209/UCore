# MongoDB ODM Guide

This guide explains the MongoDB Object-Document Mapper (ODM) in UCore, including model definition, CRUD operations, and advanced features.

---

## Overview

- Async-first ODM for MongoDB, integrated with UCore's component system.
- Identity map caching for efficient object reuse.
- Declarative indexes and relationship management.

---

## Defining Models

```python
from ucore_framework.data.mongo_orm import BaseMongoRecord, Field, ReferenceField
from pymongo import IndexModel, ASCENDING

class Company(BaseMongoRecord):
    collection_name = "companies"
    name: str = Field()
    address: str = Field()

class User(BaseMongoRecord):
    collection_name = "users"
    indexes = [
        IndexModel([("email", ASCENDING)], unique=True),
    ]
    name: str = Field(default="Anonymous")
    email: str = Field()
    company = ReferenceField(Company)
```

---

## Registering Models

```python
from ucore_framework.data.mongo_adapter import MongoDBAdapter

mongo_adapter = MongoDBAdapter(app)
mongo_adapter.register_models([User, Company])
```

---

## CRUD Operations

```python
# Create
user = await User.new_record(name="Alice", email="alice@example.com")

# Read
user = await User.get_by_id(user.id)
user2 = await User.find_one({"email": "alice@example.com"})

# Update
user.name = "Alice Smith"
await user.save()

# Delete
await user.delete()
```

---

## Relationships

```python
company = await Company.new_record(name="Acme Inc.", address="123 Main St")
user = await User.new_record(name="Bob", email="bob@example.com", company=company)
fetched_company = await user.company.fetch()
```

---

## Indexes

- Define indexes using the `indexes` attribute on your model.
- Indexes are created automatically on startup.

---

## Advanced Features

- Identity map caching: repeated queries for the same object return the same instance.
- Bulk operations: `bulk_update`, `add_delete_many_bulk`.
- Async and sync API support.

---

## See Also

- [UCore Framework Guide](../ucore-ucore_framework-guide.md)
- [Project Structure Guide](../project-structure-guide.md)
