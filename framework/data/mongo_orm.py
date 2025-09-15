# framework/data/mongo_orm.py
"""
This module provides the BaseMongoRecord class and related utilities,
forming the core of the UCore MongoDB ODM.
"""
import threading
import weakref
from collections import OrderedDict
from typing import Type
from bson import ObjectId

# Import for event handling (will be available when integrated)
try:
    from framework.messaging.events import (
        BaseEvent, DocumentDeletedEvent,
        DocumentCreatedEvent, DocumentUpdatedEvent
    )
    # Define events if they don't exist yet
    if 'DocumentDeletedEvent' not in globals():
        class DocumentDeletedEvent:
            def __init__(self, collection_name, document_id):
                self.collection_name = collection_name
                self.document_id = document_id

    if 'DocumentCreatedEvent' not in globals():
        class DocumentCreatedEvent:
            def __init__(self, collection_name, document_id):
                self.collection_name = collection_name
                self.document_id = document_id

    if 'DocumentUpdatedEvent' not in globals():
        class DocumentUpdatedEvent:
            def __init__(self, collection_name, document_id):
                self.collection_name = collection_name
                self.document_id = document_id
except ImportError:
    # Define placeholders if UCore event system isn't available
    class DocumentDeletedEvent:
        def __init__(self, collection_name, document_id):
            self.collection_name = collection_name
            self.document_id = document_id

    class DocumentCreatedEvent:
        def __init__(self, collection_name, document_id):
            self.collection_name = collection_name
            self.document_id = document_id

    class DocumentUpdatedEvent:
        def __init__(self, collection_name, document_id):
            self.collection_name = collection_name
            self.document_id = document_id

# Forward reference for type hints
BaseMongoRecord = None


# Reference Field Implementation
class ReferenceField:
    """A field that references another document in a different collection."""

    # Class-level LRU cache for LazyReference objects (prevent garbage collection)
    _global_ref_cache = {}  # Use regular dict to prevent GC

    def __init__(self, referenced_model: Type[BaseMongoRecord]):
        self.referenced_model = referenced_model

    def __get__(self, instance, owner):
        if instance is None:
            return self

        reference_id = instance.get_field_val(f"{self.referenced_model.__name__.lower()}_id")

        # Return None if no reference ID is set
        if not reference_id:
            return None

        cache_key = (reference_id, self.referenced_model)

        if cache_key not in ReferenceField._global_ref_cache:
            ReferenceField._global_ref_cache[cache_key] = LazyReference(reference_id, self.referenced_model)

        return ReferenceField._global_ref_cache[cache_key]

    def __set__(self, instance, value):
        if value is None:
            instance.set_field_val(f"{self.referenced_model.__name__.lower()}_id", None)
        elif hasattr(value, '_id') and value._id:
            instance.set_field_val(f"{self.referenced_model.__name__.lower()}_id", value._id)
        else:
            # Assume it's an ObjectId
            instance.set_field_val(f"{self.referenced_model.__name__.lower()}_id", ObjectId(value))


class LazyReference:
    """A lazy-loading proxy for referenced documents."""
    def __init__(self, reference_id: ObjectId, referenced_model: Type[BaseMongoRecord]):
        self.reference_id = reference_id
        self.referenced_model = referenced_model
        self._loaded_document = None

    async def fetch(self):
        """Fetch the referenced document from the database."""
        if self._loaded_document is None:
            self._loaded_document = await self.referenced_model.get_by_id(self.reference_id)
        return self._loaded_document

    @property
    def id(self):
        """Get the referenced document ID."""
        return self.reference_id


class ReferenceListField:
    """A field that references multiple documents in a different collection."""
    def __init__(self, referenced_model: Type[BaseMongoRecord]):
        self.referenced_model = referenced_model

    def __get__(self, instance, owner):
        if instance is None:
            return self
        reference_ids = instance.get_field_val(f"{self.referenced_model.__name__.lower()}_ids") or []
        return [LazyReference(rid, self.referenced_model) for rid in reference_ids]

    def __set__(self, instance, values):
        if values is None:
            ids = []
        else:
            ids = []
            for value in values:
                if hasattr(value, '_id') and value._id:
                    ids.append(value._id)
                elif isinstance(value, ObjectId):
                    ids.append(value)
                else:
                    try:
                        ids.append(ObjectId(value))
                    except:
                        continue
        instance.set_field_val(f"{self.referenced_model.__name__.lower()}_ids", ids)


# DEV-2.1: Field descriptor for model properties
class Field:
    """
    A descriptor for defining fields on a BaseMongoRecord model.
    It handles default values and supports type conversion/validation.
    """
    def __init__(self, field_type=None, default=None, converter=None, validator=None):
        self.name = None  # Set by the metaclass
        self.field_type = field_type
        self.default = default
        self.converter = converter  # Function to convert value
        self.validator = validator  # Function to validate value

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return instance.get_field_val(self.name, self.default)

    def __set__(self, instance, value):
        # Apply converter if available
        if self.converter and value is not None:
            value = self.converter(value)

        # Apply validator if available
        if self.validator and value is not None:
            if not self.validator(value):
                raise ValueError(f"Validation failed for field {self.name}: {value}")

        instance.set_field_val(self.name, value)


# DEV-1.5: Refactor caching mechanisms without global dependencies
class LRUCache:
    """A simple LRU cache implementation using OrderedDict."""
    def __init__(self, max_size=250):
        self.max_size = max_size
        self.cache = OrderedDict()

    def get(self, key):
        if key in self.cache:
            self.cache.move_to_end(key, last=False)
            return self.cache[key]
        return None

    def set(self, key, value):
        self.cache[key] = value
        self.cache.move_to_end(key, last=False)
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=True)

# DEV-1.5: Refactor metaclass to remove global state
class DbRecordMeta(type):
    """
    Metaclass for BaseMongoRecord that implements the Identity Map pattern
    using a combination of a WeakValueDictionary and an LRU cache.
    """
    def __new__(cls, name, bases, namespace, **kwargs):
        new_class = super().__new__(cls, name, bases, namespace)
        # Initialize instance-specific caches on the class itself
        new_class._cache = weakref.WeakValueDictionary()  # type: ignore
        new_class._lru_cache = LRUCache(max_size=250)  # type: ignore
        new_class._lock = threading.RLock()  # type: ignore
        # DEV-3.1: Placeholder for declarative indexes
        new_class.indexes = namespace.get('indexes', [])  # type: ignore

        # DEV-2.1: Set the name for each Field descriptor
        for key, value in namespace.items():
            if isinstance(value, Field):
                value.name = key

        return new_class

    def __call__(cls, record_id=None):
        with cls._lock:
            # Ensure record_id is a string for consistent caching
            record_id_str = str(record_id)

            if record_id is None:
                # Handle creation of a new, unsaved instance
                instance = super().__call__(None)
                # Don't cache unsaved instances by their None ID
                return instance

            # Check weakref cache first (active instances)
            if record_id_str in cls._cache:
                return cls._cache[record_id_str]

            # Check LRU cache next (recently used instances)
            instance = cls._lru_cache.get(record_id_str)
            if instance:
                cls._cache[record_id_str] = instance
                return instance

            # If not in any cache, create a new instance
            instance = super().__call__(record_id)
            cls._cache[record_id_str] = instance
            cls._lru_cache.set(record_id_str, instance)
            return instance

# DEV-1.4: Refactor MongoRecordWrapper into BaseMongoRecord
class BaseMongoRecord(metaclass=DbRecordMeta):
    """
    Base class for all MongoDB models in a UCore application.
    Implements the core ODM features and relies on the MongoDBAdapter
    for database connection injection.
    """
    _db = None
    _bulk_cache = None
    collection_name = None  # Must be overridden in subclasses

    def __init__(self, oid=None):
        if self._db is None:
            raise RuntimeError(
                f"Database not injected into {self.__class__.__name__}. "
                "Ensure the model is registered with the MongoDBAdapter."
            )
        self._id = ObjectId(oid) if oid else ObjectId()
        # Initialize props_cache by fetching data if an ID is provided
        self.props_cache = {}
        if oid:
            # In a real async scenario, this would be an async method,
            # but __init__ cannot be async. Data fetching is deferred.
            pass

    # DEV-1.6: Implement the DB client injection method
    @classmethod
    def inject_db_client(cls, db, bulk_cache):
        """
        Injects the database client and bulk cache from the MongoDBAdapter.
        This method is for internal framework use.
        """
        cls._db = db
        cls._bulk_cache = bulk_cache

    @classmethod
    def collection(cls):
        """
        Returns the raw motor collection object for this model.
        Raises NotImplementedError if collection_name is not set.
        """
        if not cls.collection_name:
            raise NotImplementedError(
                f"{cls.__name__} must define a 'collection_name' attribute."
            )
        return cls._db[cls.collection_name]

    # --- Data and Field Helpers ---

    def get_field_val(self, field_name: str, default=None):
        """Gets a value from the local property cache."""
        return self.props_cache.get(field_name, default)

    def set_field_val(self, field_name: str, value):
        """Sets a value in the local property cache. Does not save to DB."""
        self.props_cache[field_name] = value
        # In a more advanced implementation, this could mark the object as "dirty".

    async def _fetch_data(self):
        """Fetches the document from MongoDB and populates the local cache."""
        if not self._id:
            return
        data = await self.collection().find_one({'_id': self._id})
        if data:
            self.props_cache = data
        else:
            # Or raise a DocumentNotFound error
            self.props_cache = {}

    # --- Core Async CRUD Methods ---

    @classmethod
    async def get_by_id(cls, record_id):
        """
        Get record by id, utilizing the instance cache.
        :param record_id: id of record
        :return: BaseMongoRecord instance or None if not found
        """
        instance = cls(record_id)  # This uses the metaclass cache
        await instance._fetch_data()
        if not instance.props_cache:
            return None
        return instance

    @classmethod
    async def find_one(cls, query):
        """Finds a single document matching the query."""
        res = await cls.collection().find_one(query)
        if res is None:
            return None
        instance = cls(res["_id"])  # Use metaclass cache
        instance.props_cache = res  # Pre-populate the cache
        return instance

    @classmethod
    async def find(cls, query, sort_query=None):
        """Finds multiple documents matching the query."""
        if sort_query is None:
            cursor = cls.collection().find(query)
        else:
            cursor = cls.collection().find(query).sort(sort_query)
        
        results = []
        async for item in cursor:
            instance = cls(item["_id"])
            instance.props_cache = item
            results.append(instance)
        return results

    @classmethod
    async def new_record(cls, **kwargs):
        """
        Creates a new record in the database.
        :param kwargs: Field names and values for the new record.
        :return: A new instance of the class.
        """
        record_data = {}
        for key, value in cls.__dict__.items():
            if isinstance(value, Field):
                val = kwargs.get(key, value.default)
                record_data[value.name] = val
            elif isinstance(value, (ReferenceField, ReferenceListField)):
                # Handle references separately since they need special processing
                if key in kwargs:
                    val = kwargs[key]
                    if isinstance(value, ReferenceField):
                        # Store reference as ObjectId
                        if hasattr(val, '_id'):
                            record_data[value.referenced_model.__name__.lower() + "_id"] = val._id
                        # Remove the object from kwargs since we handled it
                        kwargs.pop(key)

        # Add any remaining kwargs that are not defined as fields
        record_data.update(kwargs)

        ins_res = await cls.collection().insert_one(record_data)
        return cls(ins_res.inserted_id)

    async def save(self):
        """Saves the current state of the object to the database (update/upsert)."""
        await self.collection().update_one(
            {'_id': self._id},
            {'$set': self.props_cache},
            upsert=True
        )

    async def delete(self):
        """Deletes the record from the database."""
        await self.collection().delete_one({"_id": self._id})
        # Here we would also fire an event on the UCore event bus (DEV-2.4)


    @classmethod
    async def bulk_update(cls, records: list, upsert=True):
        """
        Bulk update multiple records efficiently.
        :param records: List of documents to update
        :param upsert: Whether to upsert if record doesn't exist
        :return: Result of the bulk operation
        """
        if not records:
            return

        from pymongo import ReplaceOne
        bulk_op = []
        for record in records:
            if record is None:
                continue
            query = {'_id': record.get('_id')}
            # For update operations, we need to separate the _id from the data
            record_data = {k: v for k, v in record.items() if k != '_id'}
            bulk_op.append(ReplaceOne(query, record_data, upsert=upsert))

        if bulk_op:
            await cls.collection().bulk_write(bulk_op)


    def add_delete_many_bulk(self, query: dict):
        """
        Adds a bulk delete operation to be executed later via the adapter.
        :param query: Delete query criteria
        """
        # This would be enhanced in the MongoDBAdapter
        if self.__class__._bulk_cache is None:
            raise RuntimeError("Bulk operations cache not initialized")
        key = f"DeleteMany_{self.__class__.collection_name}"
        ops_list = self.__class__._bulk_cache.get(key, [])
        ops_list.append(query)
        self.__class__._bulk_cache[key] = ops_list

    @property
    def id(self):
        """Returns the ObjectId of this record."""
        return self._id


    # --- Placeholder for future development ---

    @classmethod
    async def _create_indexes(cls):
        """
        (DEV-3.2) Creates database indexes defined in the model's 'indexes' list.
        Called automatically by the MongoDBAdapter on startup.
        """
        if not cls.indexes:
            return
        # motor's create_indexes is idempotent and safe to run multiple times
        await cls.collection().create_indexes(cls.indexes)
