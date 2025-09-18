from UCoreFrameworck.data.mongo_orm import BaseMongoRecord, ReferenceField, Field
from typing import Dict
from datetime import datetime

class CollectionRecord(BaseMongoRecord):
    """
    Base record for all collection entities (files, folders, tags, catalogs, detections, etc).
    Provides common fields and type registration for polymorphic access.
    """
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
        """
        Register a new record type for polymorphic access.
        Args:
            type_name (str): Name of the type.
            type_cls (type): Class to register.
        """
        cls.itemTypeMap[type_name] = type_cls

    @classmethod
    def get_record_wrapper(cls, record_id):
        """
        Get the wrapper class for a record by its type.
        Args:
            record_id: The record's unique identifier.
        Returns:
            Instance of the appropriate subclass.
        """
        record_data = cls.find_one({'_id': record_id})
        wrapper_cls = cls.itemTypeMap.get(record_data.itemType, cls)
        return wrapper_cls(record_id)

    @classmethod
    def create_index(cls, name: str, keys: dict):
        """
        Create an index on the collection.
        Args:
            name (str): Index name.
            keys (dict): Keys and directions for the index, e.g. {'field': 1}.
        """
        # TODO: Integrate with Mongo ORM or backend to create index
        pass

class FileRecord(CollectionRecord):
    """
    Record representing a file in the collection.
    """
    collection_name = "files"
    path = Field(str)
    size = Field(int)
    tags = Field(list, default=[])

class FolderRecord(CollectionRecord):
    """
    Record representing a folder in the collection.
    """
    pass

class TagRecord(CollectionRecord):
    """
    Record representing a tag in the collection.
    """
    collection_name = "tags"
    fullName = Field(str)
    autotag = Field(bool, default=False)
    remap_to_tags = Field(str, default=None)

class CatalogRecord(CollectionRecord):
    """
    Record representing a catalog in the collection.
    """
    collection_name = "catalogs"
    fullName = Field(str)

class DetectionObjectClass(CollectionRecord):
    """
    Record representing an object class for detection.
    """
    pass

class Detection(CollectionRecord):
    """
    Record representing a detection result.
    """
    obj_name = Field(str)
    rect_region = Field(list)
    region_format = Field(str)
    backend = Field(str)

class RecognizedObject(CollectionRecord):
    """
    Record representing a recognized object.
    """
    pass

class AnnotationRecord(CollectionRecord):
    """
    Record representing an annotation for a file.
    """
    label = Field(str)
    rating = Field(float)
    user = Field(str)
    created_at = Field(datetime)

# Assign ReferenceFields after all classes are defined
FileRecord.parent = ReferenceField(FolderRecord)  # Parent folder
FolderRecord.parent = ReferenceField(FolderRecord)  # Parent folder (for nesting)
TagRecord.parent_tag = ReferenceField(TagRecord)  # Parent tag (for hierarchy)
CatalogRecord.parent_catalog = ReferenceField(CatalogRecord)  # Parent catalog
Detection.object_class = ReferenceField(DetectionObjectClass)  # Object class reference
Detection.parent_obj = ReferenceField(RecognizedObject)  # Parent recognized object
Detection.parent_file = ReferenceField(FileRecord)  # File where detection occurred
RecognizedObject.obj_class = ReferenceField(DetectionObjectClass)  # Object class reference
AnnotationRecord.file = ReferenceField(FileRecord)  # Annotated file
