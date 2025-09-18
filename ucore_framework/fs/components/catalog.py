"""
Catalog management for files_db.
Defines CatalogRecord and related logic for catalog entities.
"""

from UCoreFrameworck.fs.models import CatalogRecord
from typing import List, Optional

class CatalogManager:
    """
    Manager for catalog operations: create, find, update, delete, and hierarchy.
    """
    @staticmethod
    async def create_catalog(name: str, parent_catalog: Optional[CatalogRecord] = None) -> CatalogRecord:
        catalog = await CatalogRecord.new_record(fullName=name, parent_catalog=parent_catalog)
        return catalog

    @staticmethod
    async def find_catalog_by_name(name: str) -> Optional[CatalogRecord]:
        return await CatalogRecord.find_one({'fullName': name})

    @staticmethod
    async def get_child_catalogs(parent_catalog: CatalogRecord) -> List[CatalogRecord]:
        return await CatalogRecord.find({'parent_catalog': parent_catalog})

    @staticmethod
    async def update_catalog(catalog_id: str, update_data: dict) -> Optional[CatalogRecord]:
        catalog = await CatalogRecord.find_one({'_id': catalog_id})
        if catalog:
            for k, v in update_data.items():
                setattr(catalog, k, v)
            await catalog.save()
        return catalog

    @staticmethod
    async def delete_catalog(catalog_id: str) -> bool:
        catalog = await CatalogRecord.find_one({'_id': catalog_id})
        if catalog:
            await catalog.delete()
            return True
        return False
