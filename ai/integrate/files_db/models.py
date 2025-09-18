from framework.data.mongo_orm import BaseMongoRecord, ReferenceField, Field
from typing import Dict
from datetime import datetime

class CollectionRecord(BaseMongoRecord):
    itemTypeMap: Dict[str, type] = {}
    itemType = Field(str, default="CollectionRecord")
    name = Field(str)
    favorite = Field(bool, default=False)
    hidden = Field(bool, default=False)
    rating = Field(int, default=0)
    document_content = Field(str, default="")
    full_text_search = Field(str, default="")
    title = Field(str, default="")
    description = Field(str, default="")
    notes = Field(str, default="")
    ai_expertise = Field(list, default=[])
    file_content_md5 = Field(str, default="")
    metadata_dirty = Field(bool, default=False)
    local_path = Field(str, default=None)
    url_source = Field(str, default=None)

    @classmethod
    def register_type(cls, type_name: str, type_cls: type):
        cls.itemTypeMap[type_name] = type_cls

    @classmethod
    def get_record_wrapper(cls, record_id):
        record_data = cls.find_one({'_id': record_id})
        wrapper_cls = cls.itemTypeMap.get(record_data.itemType, cls)
        return wrapper_cls(record_id)

class FileRecord(CollectionRecord):
    path = Field(str)
    size = Field(int)
    tags = Field(list, default=[])
    parent = ReferenceField('FolderRecord')

class FolderRecord(CollectionRecord):
    parent = ReferenceField('FolderRecord')

class TagRecord(CollectionRecord):
    fullName = Field(str)
    parent_tag = ReferenceField('TagRecord')
    autotag = Field(bool, default=False)
    remap_to_tags = Field(str, default=None)

class CatalogRecord(CollectionRecord):
    fullName = Field(str)
    parent_catalog = ReferenceField('CatalogRecord')

class DetectionObjectClass(CollectionRecord):
    pass

class Detection(CollectionRecord):
    obj_name = Field(str)
    object_class = ReferenceField('DetectionObjectClass')
    rect_region = Field(list)
    region_format = Field(str)
    backend = Field(str)
    parent_obj = ReferenceField('RecognizedObject')
    parent_file = ReferenceField('FileRecord')

class RecognizedObject(CollectionRecord):
    obj_class = ReferenceField('DetectionObjectClass')

class AnnotationRecord(CollectionRecord):
    file = ReferenceField(FileRecord)
    label = Field(str)
    rating = Field(float)
    user = Field(str)
    created_at = Field(datetime)
