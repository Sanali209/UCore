import pytest
from ucore_framework.fs.components.tags import TagManager, TagRecord

@pytest.mark.asyncio
async def test_tag_manager_create_and_find(mongodb):
    TagRecord.inject_db_client(mongodb, None)
    created_tag = await TagManager.create_tag("test-tag")
    found_tag = await TagManager.find_tag_by_name("test-tag")
    assert found_tag is not None
    assert created_tag.id == found_tag.id

@pytest.mark.asyncio
async def test_hierarchical_tags(mongodb):
    TagRecord.inject_db_client(mongodb, None)
    parent_tag = await TagManager.create_tag("parent")
    child_tag = await TagManager.create_tag("child", parent_tag=parent_tag)
    children = await TagManager.get_child_tags(parent_tag)
    assert len(children) == 1
    assert children[0].id == child_tag.id
