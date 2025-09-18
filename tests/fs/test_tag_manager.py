import pytest
import asyncio
from UCoreFrameworck.fs.components.tags import TagManager
from UCoreFrameworck.fs.models import TagRecord

@pytest.mark.asyncio
async def test_create_and_find_tag():
    tag = await TagManager.create_tag("test_tag")
    assert tag.fullName == "test_tag"
    found = await TagManager.find_tag_by_name("test_tag")
    assert found is not None
    assert found.fullName == "test_tag"

@pytest.mark.asyncio
async def test_tag_hierarchy():
    parent = await TagManager.create_tag("parent_tag")
    child = await TagManager.create_tag("child_tag", parent_tag=parent)
    children = await TagManager.get_child_tags(parent)
    assert any(t.fullName == "child_tag" for t in children)

@pytest.mark.asyncio
async def test_update_tag():
    tag = await TagManager.create_tag("update_tag")
    updated = await TagManager.update_tag(tag._id, {"fullName": "updated_tag"})
    assert updated.fullName == "updated_tag"

@pytest.mark.asyncio
async def test_delete_tag():
    tag = await TagManager.create_tag("delete_tag")
    deleted = await TagManager.delete_tag(tag._id)
    assert deleted
    found = await TagManager.find_tag_by_name("delete_tag")
    assert found is None
