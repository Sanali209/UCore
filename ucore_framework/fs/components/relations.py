"""
Relation management for files_db.
Defines RelationRecord and hooks for managing relationships between records.
"""

from ucore_framework.data.mongo_orm import BaseMongoRecord, Field, ReferenceField

class RelationRecord(BaseMongoRecord):
    """
    Record representing a relation between two entities (e.g., files, tags, catalogs).
    """
    collection_name = "relations"
    from_id = Field(str)
    to_id = Field(str)
    type = Field(str)
    sub_type = Field(str, default=None)
    distance = Field(float, default=None)
    value = Field(str, default=None)

    @classmethod
    def delete_all_relations(cls, record_id):
        """
        Delete all relations for a given record.
        Args:
            record_id (str): The record's unique identifier.
        """
        # TODO: Implement deletion logic using ORM
        pass

# Example hook for onDelete (to be connected in resource or model logic)
def on_delete_record(record_id):
    """
    Hook to be called when a record is deleted.
    Deletes all relations for the record.
    """
    RelationRecord.delete_all_relations(record_id)
