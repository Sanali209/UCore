import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from bson import ObjectId
import threading

from framework.data.mongo_orm import (
    ReferenceField, LazyReference, ReferenceListField,
    Field, LRUCache, DbRecordMeta, BaseMongoRecord,
    DocumentCreatedEvent, DocumentDeletedEvent, DocumentUpdatedEvent
)


from loguru import logger

class TestReferenceField:
    """Test ReferenceField descriptor functionality."""

    def test_init(self):
        """Test ReferenceField initialization."""
        mock_model = Mock()
        field = ReferenceField(mock_model)

        assert field.referenced_model == mock_model

    def test_get_with_no_instance(self):
        """Test __get__ returns self when called on class."""
        mock_model = Mock()
        field = ReferenceField(mock_model)

        result = field.__get__(None, Mock)
        assert result is field
        logger.debug("test_get_with_no_instance: PASSED")

    def test_get_with_reference_id(self):
        """Test __get__ returns LazyReference when reference ID exists."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceField(mock_model)
        instance = Mock()
        instance.get_field_val.return_value = ObjectId()

        result = field.__get__(instance, Mock)

        assert isinstance(result, LazyReference)
        assert result.referenced_model == mock_model
        assert result.reference_id == instance.get_field_val.return_value
        logger.debug("test_get_with_reference_id: PASSED")

    def test_get_with_no_reference_id(self):
        """Test __get__ returns None when no reference ID."""
        mock_model = Mock()
        field = ReferenceField(mock_model)
        instance = Mock()
        instance.get_field_val.return_value = None

        result = field.__get__(instance, Mock)

        assert result is None
        logger.debug("test_get_with_no_reference_id: PASSED")

    def test_set_with_none(self):
        """Test __set__ with None value."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceField(mock_model)
        instance = Mock()

        field.__set__(instance, None)

        instance.set_field_val.assert_called_with("testmodel_id", None)
        logger.debug("test_set_with_none: PASSED")

    def test_set_with_object_id(self):
        """Test __set__ with object that has _id."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceField(mock_model)
        instance = Mock()

        mock_value = Mock()
        mock_value._id = ObjectId()

        field.__set__(instance, mock_value)

        instance.set_field_val.assert_called_with("testmodel_id", mock_value._id)
        logger.debug("test_set_with_object_id: PASSED")

    def test_set_with_string_id(self):
        """Test __set__ with string ID."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceField(mock_model)
        instance = Mock()

        field.__set__(instance, "507f1f77bcf86cd799439011")

        # Should convert to ObjectId
        instance.set_field_val.assert_called_with("testmodel_id", ObjectId("507f1f77bcf86cd799439011"))
        logger.debug("test_set_with_string_id: PASSED")

    def test_global_cache(self):
        """Test that global cache reuses LazyReference objects."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceField(mock_model)
        instance1 = Mock()
        instance2 = Mock()
        ref_id = ObjectId()

        instance1.get_field_val.return_value = ref_id
        instance2.get_field_val.return_value = ref_id

        result1 = field.__get__(instance1, Mock)
        result2 = field.__get__(instance2, Mock)

        assert result1 is result2  # Same object from cache
        logger.debug("test_global_cache: PASSED")


class TestLazyReference:
    """Test LazyReference functionality."""

    def test_init(self):
        """Test LazyReference initialization."""
        ref_id = ObjectId()
        mock_model = Mock()

        lazy_ref = LazyReference(ref_id, mock_model)

        assert lazy_ref.reference_id == ref_id
        assert lazy_ref.referenced_model == mock_model
        assert lazy_ref._loaded_document is None

    def test_id_property(self):
        """Test id property."""
        ref_id = ObjectId()
        lazy_ref = LazyReference(ref_id, Mock)

        assert lazy_ref.id == ref_id

    @pytest.mark.asyncio
    async def test_fetch_success(self):
        """Test fetch method success."""
        ref_id = ObjectId()
        mock_model = Mock()
        mock_document = Mock()

        mock_model.get_by_id = AsyncMock(return_value=mock_document)
        lazy_ref = LazyReference(ref_id, mock_model)

        result = await lazy_ref.fetch()

        assert result == mock_document
        assert lazy_ref._loaded_document == mock_document
        mock_model.get_by_id.assert_called_once_with(ref_id)

    @pytest.mark.asyncio
    async def test_fetch_cached(self):
        """Test fetch method returns cached document."""
        ref_id = ObjectId()
        mock_model = Mock()
        mock_document = Mock()

        lazy_ref = LazyReference(ref_id, mock_model)
        lazy_ref._loaded_document = mock_document

        result = await lazy_ref.fetch()

        assert result == mock_document
        mock_model.get_by_id.assert_not_called()


class TestReferenceListField:
    """Test ReferenceListField descriptor functionality."""

    def test_init(self):
        """Test ReferenceListField initialization."""
        mock_model = Mock()
        field = ReferenceListField(mock_model)

        assert field.referenced_model == mock_model

    def test_get_with_no_instance(self):
        """Test __get__ returns self when called on class."""
        mock_model = Mock()
        field = ReferenceListField(mock_model)

        result = field.__get__(None, Mock)
        assert result is field

    def test_get_with_empty_list(self):
        """Test __get__ with empty list of reference IDs."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceListField(mock_model)
        instance = Mock()
        instance.get_field_val.return_value = []

        result = field.__get__(instance, Mock)

        assert result == []

    def test_get_with_reference_ids(self):
        """Test __get__ with list of reference IDs."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceListField(mock_model)
        instance = Mock()
        ref_ids = [ObjectId(), ObjectId()]
        instance.get_field_val.return_value = ref_ids

        result = field.__get__(instance, Mock)

        assert len(result) == 2
        for item in result:
            assert isinstance(item, LazyReference)
            assert item.referenced_model == mock_model
        assert result[0].reference_id == ref_ids[0]
        assert result[1].reference_id == ref_ids[1]

    def test_get_with_none_value(self):
        """Test __get__ when get_field_val returns None."""
        mock_model = Mock()
        field = ReferenceListField(mock_model)
        instance = Mock()
        instance.get_field_val.return_value = None

        result = field.__get__(instance, Mock)

        assert result == []

    def test_set_with_none(self):
        """Test __set__ with None value."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceListField(mock_model)
        instance = Mock()

        field.__set__(instance, None)

        instance.set_field_val.assert_called_with("testmodel_ids", [])

    def test_set_with_valid_objects(self):
        """Test __set__ with objects that have _id."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceListField(mock_model)
        instance = Mock()

        mock_obj1 = Mock()
        mock_obj1._id = ObjectId("507f1f77bcf86cd799439011")
        mock_obj2 = Mock()
        mock_obj2._id = ObjectId("507f1f77bcf86cd799439012")

        field.__set__(instance, [mock_obj1, mock_obj2])

        expected_ids = [ObjectId("507f1f77bcf86cd799439011"), ObjectId("507f1f77bcf86cd799439012")]
        instance.set_field_val.assert_called_with("testmodel_ids", expected_ids)

    def test_set_with_mixed_values(self):
        """Test __set__ with mixed types of IDs."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceListField(mock_model)
        instance = Mock()

        obj_id = ObjectId("507f1f77bcf86cd799439011")
        str_id = "507f1f77bcf86cd799439012"
        values = [obj_id, str_id]

        field.__set__(instance, values)

        expected_ids = [obj_id, ObjectId(str_id)]
        instance.set_field_val.assert_called_with("testmodel_ids", expected_ids)

    def test_set_with_invalid_value(self):
        """Test __set__ with invalid value that can't be converted."""
        mock_model = Mock()
        mock_model.__name__ = "TestModel"

        field = ReferenceListField(mock_model)
        instance = Mock()

        # Invalid object without _id and not ObjectId/string
        field.__set__(instance, [123, ObjectId("507f1f77bcf86cd799439011"), "invalid"])

        # Should only include valid IDs
        expected_ids = [ObjectId("507f1f77bcf86cd799439011")]
        instance.set_field_val.assert_called_with("testmodel_ids", expected_ids)


class TestField:
    """Test Field descriptor functionality."""

    def test_init(self):
        """Test Field initialization."""
        field = Field(field_type=str, default="test", converter=str.upper)

        assert field.field_type == str
        assert field.default == "test"
        assert field.converter == str.upper
        assert field.validator is None

    def test_get_with_no_instance(self):
        """Test __get__ returns self when called on class."""
        field = Field()
        result = field.__get__(None, Mock)
        assert result is field

    def test_get_with_value(self):
        """Test __get__ with stored value."""
        field = Field()
        field.name = "test_field"
        instance = Mock()
        instance.get_field_val.return_value = "stored_value"

        result = field.__get__(instance, Mock)

        assert result == "stored_value"
        instance.get_field_val.assert_called_with("test_field", field.default)

    def test_get_with_default(self):
        """Test __get__ returns default when no value stored."""
        field = Field(default="default_value")
        field.name = "test_field"
        instance = Mock()
        instance.get_field_val.return_value = None

        result = field.__get__(instance, Mock)

        assert result == "default_value"

    def test_set_without_converter_validator(self):
        """Test __set__ without converter or validator."""
        field = Field()
        field.name = "test_field"
        instance = Mock()

        field.__set__(instance, "test_value")

        instance.set_field_val.assert_called_with("test_field", "test_value")

    def test_set_with_converter(self):
        """Test __set__ with converter function."""
        field = Field(converter=str.upper)
        field.name = "test_field"
        instance = Mock()

        field.__set__(instance, "test_value")

        instance.set_field_val.assert_called_with("test_field", "TEST_VALUE")

    def test_set_with_validator_success(self):
        """Test __set__ with validator that passes."""
        field = Field(validator=lambda x: len(x) > 3)
        field.name = "test_field"
        instance = Mock()

        field.__set__(instance, "test")

        instance.set_field_val.assert_called_with("test_field", "test")

    def test_set_with_validator_failure(self):
        """Test __set__ with validator that fails."""
        field = Field(validator=lambda x: len(x) > 5)
        field.name = "test_field"
        instance = Mock()

        with pytest.raises(ValueError, match="Validation failed for field test_field"):
            field.__set__(instance, "test")

    def test_set_with_converter_and_validator(self):
        """Test __set__ with both converter and validator."""
        field = Field(
            converter=str.upper,
            validator=lambda x: len(x) == 4
        )
        field.name = "test_field"
        instance = Mock()

        field.__set__(instance, "test")  # Should become "TEST", length 4

        instance.set_field_val.assert_called_with("test_field", "TEST")

    def test_set_none_with_converter(self):
        """Test __set__ with None value and converter present."""
        field = Field(converter=str.upper)
        field.name = "test_field"
        instance = Mock()

        field.__set__(instance, None)

        # Converter should not be applied to None
        instance.set_field_val.assert_called_with("test_field", None)


class TestLRUCache:
    """Test LRUCache functionality."""

    def test_init(self):
        """Test LRUCache initialization."""
        cache = LRUCache(max_size=100)

        assert cache.max_size == 100
        assert isinstance(cache.cache, dict)

    def test_init_default_size(self):
        """Test LRUCache with default max_size."""
        cache = LRUCache()

        assert cache.max_size == 250

    def test_get_nonexistent_key(self):
        """Test get with key that doesn't exist."""
        cache = LRUCache()

        result = cache.get("nonexistent")

        assert result is None

    def test_set_and_get(self):
        """Test set and get operations."""
        cache = LRUCache()

        cache.set("key1", "value1")
        result = cache.get("key1")

        assert result == "value1"

    def test_get_promotes_to_recent(self):
        """Test that get moves accessed item to most recent."""
        cache = LRUCache()

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key1, should move to front
        cache.get("key1")

        # key1 should now be the most recent (last in OrderedDict)
        assert list(cache.cache.keys())[-1] == "key1"

    def test_max_size_enforcement(self):
        """Test that cache evicts oldest item when max_size exceeded."""
        cache = LRUCache(max_size=2)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")  # Should evict key1

        assert len(cache.cache) == 2
        assert "key1" not in cache.cache
        assert "key2" in cache.cache
        assert "key3" in cache.cache

    def test_lru_ordering(self):
        """Test that LRU maintains proper ordering."""
        cache = LRUCache(max_size=3)

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        cache.set("key3", "value3")

        # Access key2 and key1 to change order
        cache.get("key2")
        cache.get("key1")

        # After accessing key2 and key1, order should be: key3, key2, key1 (key1 most recent)
        keys = list(cache.cache.keys())
        assert keys == ["key3", "key2", "key1"]

        cache.set("key4", "value4")  # Should evict key3

        keys = list(cache.cache.keys())
        assert keys == ["key2", "key1", "key4"]
        assert "key3" not in cache.cache


class TestDbRecordMeta:
    """Test DbRecordMeta metaclass functionality."""

    def test_metaclass_creation(self):
        """Test metaclass creates class with proper caches."""

        class TestRecord(metaclass=DbRecordMeta):
            pass

        assert hasattr(TestRecord, '_cache')
        assert hasattr(TestRecord, '_lru_cache')
        assert hasattr(TestRecord, '_lock')
        assert isinstance(TestRecord._lock, TestRecord._lock_type)
        assert TestRecord.indexes == []

    def test_metaclass_with_indexes(self):
        """Test metaclass handles indexes attribute."""

        class TestRecordWithIndexes(metaclass=DbRecordMeta):
            indexes = ["test_index"]

        assert TestRecordWithIndexes.indexes == ["test_index"]

    def test_metaclass_sets_field_names(self):
        """Test metaclass sets names on Field descriptors."""

        class TestRecord(metaclass=DbRecordMeta):
            name = Field()
            age = Field()

        assert TestRecord.name.name == "name"
        assert TestRecord.age.name == "age"

    def test_metaclass_call_with_none_id(self):
        """Test metaclass call with None ID creates new instance."""
        mock_db = Mock()

        class TestRecord(metaclass=DbRecordMeta):
            _db = mock_db

        instance = TestRecord(None)

        assert isinstance(instance, TestRecord)
        assert instance._id is None

    def test_metaclass_call_caching(self):
        """Test metaclass call implements caching."""
        mock_db = Mock()

        class TestRecord(metaclass=DbRecordMeta):
            _db = mock_db

        # Create instance with same ID twice
        instance1 = TestRecord("507f1f77bcf86cd799439011")
        instance2 = TestRecord("507f1f77bcf86cd799439011")

        assert instance1 is instance2  # Same object from cache

    def test_metaclass_call_different_ids(self):
        """Test metaclass call creates different instances for different IDs."""
        mock_db = Mock()

        class TestRecord(metaclass=DbRecordMeta):
            _db = mock_db

        instance1 = TestRecord("507f1f77bcf86cd799439011")
        instance2 = TestRecord("507f1f77bcf86cd799439012")

        assert instance1 is not instance2


class TestBaseMongoRecord:
    """Test BaseMongoRecord functionality. This requires complex mocking of database operations."""

    def setup_method(self):
        """Setup method for tests."""
        # Mock the database and bulk cache for the entire class
        mock_db = AsyncMock()
        mock_bulk_cache = Mock()

        BaseMongoRecord._db = mock_db
        BaseMongoRecord._bulk_cache = mock_bulk_cache

        # Create a test subclass for testing
        class TestModel(BaseMongoRecord):
            collection_name = "test_models"
            name = Field()
            age = Field(default=25)

        self.TestModel = TestModel

    def test_inject_db_client(self):
        """Test inject_db_client method."""
        mock_db = Mock()
        mock_bulk_cache = Mock()

        BaseMongoRecord.inject_db_client(mock_db, mock_bulk_cache)

        assert BaseMongoRecord._db == mock_db
        assert BaseMongoRecord._bulk_cache == mock_bulk_cache

    def test_collection_method(self):
        """Test collection method returns database collection."""
        mock_db = BaseMongoRecord._db
        mock_collection = Mock()
        mock_db.__getitem__.return_value = mock_collection

        result = self.TestModel.collection()

        assert result == mock_collection
        mock_db.__getitem__.assert_called_with("test_models")

    def test_collection_method_no_collection_name(self):
        """Test collection method fails without collection_name."""

        class ModelWithoutCollection(BaseMongoRecord):
            pass

        with pytest.raises(NotImplementedError, match="must define a 'collection_name' attribute"):
            ModelWithoutCollection.collection()

    def test_get_field_val(self):
        """Test get_field_val method."""
        instance = self.TestModel()
        instance.props_cache = {"name": "John", "age": 30}

        result = instance.get_field_val("name")
        assert result == "John"

        result = instance.get_field_val("nonexistent", "default")
        assert result == "default"

    def test_set_field_val(self):
        """Test set_field_val method."""
        instance = self.TestModel()
        instance.props_cache = {}

        instance.set_field_val("name", "Jane")

        assert instance.props_cache["name"] == "Jane"

    @pytest.mark.asyncio
    async def test_fetch_data_success(self):
        """Test _fetch_data method with found document."""
        instance = self.TestModel("507f1f77bcf86cd799439011")

        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "John"}

        with patch.object(self.TestModel, 'collection', return_value=mock_collection):
            await instance._fetch_data()

            assert instance.props_cache == {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "John"}
            mock_collection.find_one.assert_called_with({'_id': instance._id})

    @pytest.mark.asyncio
    async def test_fetch_data_not_found(self):
        """Test _fetch_data method with document not found."""
        instance = self.TestModel("507f1f77bcf86cd799439011")

        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = None

        with patch.object(self.TestModel, 'collection', return_value=mock_collection):
            await instance._fetch_data()

            assert instance.props_cache == {}

    @patch('framework.data.mongo_orm.BaseMongoRecord.collection')
    @pytest.mark.asyncio
    async def test_get_by_id_success(self, mock_collection_method):
        """Test get_by_id method success."""
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "John"}
        mock_collection_method.return_value = mock_collection

        result = await self.TestModel.get_by_id("507f1f77bcf86cd799439011")

        assert result is not None
        assert result.props_cache["name"] == "John"

    @patch('framework.data.mongo_orm.BaseMongoRecord.collection')
    @pytest.mark.asyncio
    async def test_get_by_id_not_found(self, mock_collection_method):
        """Test get_by_id method with document not found."""
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = None
        mock_collection_method.return_value = mock_collection

        result = await self.TestModel.get_by_id("507f1f77bcf86cd799439011")

        assert result is None

    @patch('framework.data.mongo_orm.BaseMongoRecord.collection')
    @pytest.mark.asyncio
    async def test_find_one_success(self, mock_collection_method):
        """Test find_one method success."""
        mock_collection = AsyncMock()
        mock_collection.find_one.return_value = {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "John"}
        mock_collection_method.return_value = mock_collection

        result = await self.TestModel.find_one({"name": "John"})

        assert result is not None
        assert result.props_cache["name"] == "John"
        mock_collection.find_one.assert_called_with({"name": "John"})



    @patch('framework.data.mongo_orm.BaseMongoRecord.collection')
    @pytest.mark.asyncio
    async def test_new_record_success(self, mock_collection_method):
        """Test new_record method creates new document."""
        mock_collection = AsyncMock()
        mock_collection.insert_one.return_value = Mock(inserted_id=ObjectId("507f1f77bcf86cd799439011"))
        mock_collection_method.return_value = mock_collection

        result = await self.TestModel.new_record(name="Tom", age=35, extra_field="extra")

        assert isinstance(result, self.TestModel)
        assert result._id == ObjectId("507f1f77bcf86cd799439011")

        # Verify insert_one was called with correct data
        expected_data = {
            "name": "Tom",
            "age": 35,
            "extra_field": "extra"
        }
        mock_collection.insert_one.assert_called_with(expected_data)

    @patch('framework.data.mongo_orm.BaseMongoRecord.collection')
    @pytest.mark.asyncio
    async def test_save_success(self, mock_collection_method):
        """Test save method updates document."""
        mock_collection = AsyncMock()
        mock_collection_method.return_value = mock_collection

        instance = self.TestModel("507f1f77bcf86cd799439011")
        instance.props_cache = {"name": "Updated", "age": 40}

        await instance.save()

        mock_collection.update_one.assert_called_with(
            {'_id': instance._id},
            {'$set': instance.props_cache},
            upsert=True
        )

    @patch('framework.data.mongo_orm.BaseMongoRecord.collection')
    @pytest.mark.asyncio
    async def test_delete_success(self, mock_collection_method):
        """Test delete method removes document."""
        mock_collection = AsyncMock()
        mock_collection_method.return_value = mock_collection

        instance = self.TestModel("507f1f77bcf86cd799439011")

        await instance.delete()

        mock_collection.delete_one.assert_called_with({"_id": instance._id})

    @patch('framework.data.mongo_orm.BaseMongoRecord.collection')
    @pytest.mark.asyncio
    async def test_bulk_update_success(self, mock_collection_method):
        """Test bulk_update method."""
        mock_collection = AsyncMock()
        mock_collection_method.return_value = mock_collection

        records = [
            {"_id": ObjectId("507f1f77bcf86cd799439011"), "name": "John"},
            {"_id": ObjectId("507f1f77bcf86cd799439012"), "name": "Jane"}
        ]

        await self.TestModel.bulk_update(records)

        mock_collection.bulk_write.assert_called_once()

    def test_bulk_update_empty_list(self):
        """Test bulk_update with empty list does nothing."""
        # Mock collection method to ensure it's not called
        with patch.object(self.TestModel, 'collection', side_effect=Exception("Should not call")):
            # Should not raise exception
            result = asyncio.run(self.TestModel.bulk_update([]))
            assert result is None

    def test_add_delete_many_bulk_success(self):
        """Test add_delete_many_bulk method."""
        instance = self.TestModel()

        query = {"status": "inactive"}

        # Patch: Use a real dict for bulk_cache to avoid Mock iterable bug
        orig_bulk_cache = self.TestModel._bulk_cache
        self.TestModel._bulk_cache = {}

        instance.add_delete_many_bulk(query)

        # Verify the query was added to bulk cache
        expected_key = "DeleteMany_test_models"
        assert expected_key in self.TestModel._bulk_cache
        assert query in self.TestModel._bulk_cache[expected_key]

        # Restore original bulk_cache
        self.TestModel._bulk_cache = orig_bulk_cache

    def test_add_delete_many_bulk_no_cache(self):
        """Test add_delete_many_bulk with no bulk cache initialized."""
        # Reset bulk cache
        original_cache = self.TestModel._bulk_cache
        self.TestModel._bulk_cache = None

        try:
            instance = self.TestModel()

            query = {"status": "inactive"}

            with pytest.raises(RuntimeError, match="Bulk operations cache not initialized"):
                instance.add_delete_many_bulk(query)
        finally:
            self.TestModel._bulk_cache = original_cache

    def test_id_property(self):
        """Test id property returns ObjectId."""
        instance = self.TestModel("507f1f77bcf86cd799439011")

        assert instance.id == instance._id


class TestEventPlaceholders:
    """Test placeholder event classes."""

    def test_document_created_event(self):
        """Test DocumentCreatedEvent placeholder."""
        event = DocumentCreatedEvent("test_collection", ObjectId())

        assert event.collection_name == "test_collection"
        assert isinstance(event.document_id, ObjectId)

    def test_document_deleted_event(self):
        """Test DocumentDeletedEvent placeholder."""
        event = DocumentDeletedEvent("test_collection", ObjectId())

        assert event.collection_name == "test_collection"
        assert isinstance(event.document_id, ObjectId)

    def test_document_updated_event(self):
        """Test DocumentUpdatedEvent placeholder."""
        event = DocumentUpdatedEvent("test_collection", ObjectId())

        assert event.collection_name == "test_collection"
        assert isinstance(event.document_id, ObjectId)
