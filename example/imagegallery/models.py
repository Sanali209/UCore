from ucore_framework.data.mongo_orm import BaseMongoRecord

class ImageRecord(BaseMongoRecord):
    collection_name = "images"

    @classmethod
    def create(cls, filename: str, status: str = "processing", thumbnail_path: str = None):
        doc = {
            "filename": filename,
            "status": status,
            "thumbnail_path": thumbnail_path if thumbnail_path is not None else "",
        }
        return cls(doc)
