import pytest
from ucore_framework.data.mongo_orm import BaseMongoRecord

class SampleRecord(BaseMongoRecord):
    collection_name = "test_integration"

@pytest.fixture
def mongodb_fixture(mongodb):
    # mongodb is assumed to be a pytest-mongodb fixture providing a clean db
    db_client = mongodb
    SampleRecord.inject_db_client(db_client, None)
    yield db_client

@pytest.mark.asyncio
async def test_create_and_retrieve(mongodb_fixture):
    new_record = await SampleRecord.new_record(name="test_doc", value=42)
    retrieved = await SampleRecord.get_by_id(new_record.id)
    assert retrieved is not None
    assert retrieved.get_field_val("name") == "test_doc"

@pytest.mark.asyncio
async def test_find_by_query(mongodb_fixture):
    # Insert two docs directly
    await mongodb_fixture[SampleRecord.collection_name].insert_many([
        {"category": "A", "foo": 1},
        {"category": "B", "foo": 2}
    ])
    found = await SampleRecord.find({"category": "A"})
    assert len(found) == 1
    assert found[0].get_field_val("category") == "A"
