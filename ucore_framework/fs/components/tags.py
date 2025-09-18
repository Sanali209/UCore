"""
Tag management for files_db.
Defines TagRecord and related logic for tag entities.
"""

from UCoreFrameworck.fs.models import TagRecord
from typing import List, Optional

class TagManager:
    """
    Manager for tag operations: create, find, update, delete, and hierarchy.
    """
    @staticmethod
    async def create_tag(name: str, parent_tag: Optional[TagRecord] = None, autotag: bool = False) -> TagRecord:
        tag = await TagRecord.new_record(fullName=name, parent_tag=parent_tag, autotag=autotag)
        return tag

    @staticmethod
    async def find_tag_by_name(name: str) -> Optional[TagRecord]:
        return await TagRecord.find_one({'fullName': name})

    @staticmethod
    async def get_child_tags(parent_tag: TagRecord) -> List[TagRecord]:
        return await TagRecord.find({'parent_tag': parent_tag})

    @staticmethod
    async def update_tag(tag_id: str, update_data: dict) -> Optional[TagRecord]:
        tag = await TagRecord.find_one({'_id': tag_id})
        if tag:
            for k, v in update_data.items():
                setattr(tag, k, v)
            await tag.save()
        return tag

    @staticmethod
    async def delete_tag(tag_id: str) -> bool:
        tag = await TagRecord.find_one({'_id': tag_id})
        if tag:
            await tag.delete()
            return True
        return False
