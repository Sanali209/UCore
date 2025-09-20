"""
Unit tests for the UCore MongoDB ORM (BaseMongoRecord).

This module tests:
- Database client injection for test models
- Direct document insertion and retrieval
- The async find method and property cache

Classes:
    TestRecord: Minimal test model for MongoDB ORM.

Test Functions:
    test_insert_and_find_document: Insert and retrieve a document using the ORM.
"""

import pytest
from ucore_framework.data.mongo_orm import BaseMongoRecord
from tests.utils.test_mongo import mongo_db_session

class SampleRecord(BaseMongoRecord):
    """
    Minimal test model for MongoDB ORM.
    """
    collection_name = "test_records"

@pytest.mark.asyncio
async def test_insert_and_find_document(mongo_db_session):
    """
    Insert a document directly and retrieve it using the ORM's find method.
    """
    # Inject the test database into the ORM
    SampleRecord.inject_db_client(mongo_db_session, bulk_cache=None)

    # Insert a document directly using the collection
    await SampleRecord.collection().insert_one({"_id": "abc123", "name": "real_doc", "value": 123})

    # Use the ORM's find method
    results = await SampleRecord.find({"name": "real_doc"})
    assert len(results) == 1
    assert results[0].props_cache["value"] == 123
