"""
Web link management for files_db.
Defines WebLinkRecord and related logic for web link entities.
"""

from framework.fs.models import CollectionRecord
from framework.data.mongo_orm import Field

class WebLinkRecord(CollectionRecord):
    """
    Record representing a web link as a specialized collection item.
    Inherits all fields from CollectionRecord and adds web link-specific fields.
    """
    collection_name = "web_links"
    url = Field(str)
    title = Field(str, default=None)
    description = Field(str, default=None)
    related_id = Field(str, default=None)

# Additional web link logic and extension points can be added here.
