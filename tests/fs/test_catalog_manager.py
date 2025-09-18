import pytest
import asyncio
from UCoreFrameworck.fs.components.catalog import CatalogManager
from UCoreFrameworck.fs.models import CatalogRecord

@pytest.mark.asyncio
async def test_create_and_find_catalog():
    catalog = await CatalogManager.create_catalog("test_catalog")
    assert catalog.fullName == "test_catalog"
    found = await CatalogManager.find_catalog_by_name("test_catalog")
    assert found is not None
    assert found.fullName == "test_catalog"

@pytest.mark.asyncio
async def test_catalog_hierarchy():
    parent = await CatalogManager.create_catalog("parent_catalog")
    child = await CatalogManager.create_catalog("child_catalog", parent_catalog=parent)
    children = await CatalogManager.get_child_catalogs(parent)
    assert any(c.fullName == "child_catalog" for c in children)

@pytest.mark.asyncio
async def test_update_catalog():
    catalog = await CatalogManager.create_catalog("update_catalog")
    updated = await CatalogManager.update_catalog(str(catalog._id), {"fullName": "updated_catalog"})
    assert updated.fullName == "updated_catalog"

@pytest.mark.asyncio
async def test_delete_catalog():
    catalog = await CatalogManager.create_catalog("delete_catalog")
    deleted = await CatalogManager.delete_catalog(str(catalog._id))
    assert deleted
    found = await CatalogManager.find_catalog_by_name("delete_catalog")
    assert found is None
