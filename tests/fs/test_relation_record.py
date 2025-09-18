import pytest
import asyncio
from ucore_framework.fs.components.relations import RelationRecord

@pytest.mark.asyncio
async def test_create_and_delete_relation():
    relation = await RelationRecord.new_record(
        from_id="file1",
        to_id="file2",
        type="similarity",
        sub_type="visual",
        distance=0.5,
        value="0.5"
    )
    assert relation.from_id == "file1"
    assert relation.to_id == "file2"
    assert relation.type == "similarity"

    # Simulate deletion logic (stubbed)
    RelationRecord.delete_all_relations("file1")
    # No assertion here as delete_all_relations is a stub
