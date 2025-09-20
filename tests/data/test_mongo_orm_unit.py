import pytest
from unittest.mock import AsyncMock, MagicMock
from ucore_framework.data.mongo_orm import BaseMongoRecord

class SampleRecord(BaseMongoRecord):
    collection_name = "test_collection"

@pytest.fixture
def mock_db_and_cache(monkeypatch):
    # Mock the collection with async methods
    mock_collection = MagicMock()
    mock_collection.find_one = AsyncMock()
    mock_collection.update_one = AsyncMock()
    # Patch _db and _bulk_cache on SampleRecord
    monkeypatch.setattr(SampleRecord, "_db", {"test_collection": mock_collection})
    monkeypatch.setattr(SampleRecord, "_bulk_cache", MagicMock())
    return mock_collection

@pytest.mark.asyncio
async def test_find_one(mock_db_and_cache):
    from bson import ObjectId
    test_id = ObjectId()
    sample_doc = {"_id": test_id, "foo": "bar"}
    mock_db_and_cache.find_one.return_value = sample_doc
    query = {"foo": "bar"}
    result = await SampleRecord.find_one(query)
    mock_db_and_cache.find_one.assert_awaited_once_with(query)
    assert isinstance(result, SampleRecord)
    assert result.props_cache == sample_doc

@pytest.mark.asyncio
async def test_save(mock_db_and_cache):
    from bson import ObjectId
    test_id = ObjectId()
    record = SampleRecord(test_id)
    record.props_cache = {"_id": test_id, "foo": "bar"}
    await record.save()
    mock_db_and_cache.update_one.assert_awaited_once_with(
        {"_id": record._id},
        {"$set": record.props_cache},
        upsert=True
    )
