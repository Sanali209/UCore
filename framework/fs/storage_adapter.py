from abc import ABC, abstractmethod
from framework.fs.models import FileRecord
from framework.data.mongo_adapter import MongoDBAdapter

from typing import Any

class FilesDBStorageAdapter(ABC):
    """
    Abstract base class for files_db storage adapters.
    Defines the CRUD and search interface for file records.
    """
    @abstractmethod
    async def start(self):
        """Start the adapter and initialize resources."""
        pass

    @abstractmethod
    async def stop(self):
        """Stop the adapter and release resources."""
        pass

    @abstractmethod
    async def add_file(self, file_data) -> Any:
        """
        Create a new file record.
        Args:
            file_data (dict): File metadata and attributes.
        Returns:
            FileRecord: The created file record.
        """
        pass

    @abstractmethod
    async def get_file(self, file_id) -> Any:
        """
        Retrieve a file record by its ID.
        Args:
            file_id: The file's unique identifier.
        Returns:
            FileRecord or None
        """
        pass

    @abstractmethod
    async def update_file(self, file_id, update_data) -> Any:
        """
        Update a file record by its ID.
        Args:
            file_id: The file's unique identifier.
            update_data (dict): Fields to update.
        Returns:
            FileRecord or None
        """
        pass

    @abstractmethod
    async def delete_file(self, file_id) -> Any:
        """
        Delete a file record by its ID.
        Args:
            file_id: The file's unique identifier.
        Returns:
            FileRecord or None
        """
        pass

    @abstractmethod
    async def search_files(self, query: dict) -> list[Any]:
        """
        Search for file records matching a query.
        Args:
            query (dict): Mongo-style query.
        Returns:
            list[FileRecord]
        """
        pass

class MongoFilesDBAdapter(FilesDBStorageAdapter):
    """
    MongoDB implementation of FilesDBStorageAdapter.
    Uses FileRecord and MongoDBAdapter for backend operations.
    """
    def __init__(self, app):
        """
        Args:
            app: The application instance for MongoDBAdapter.
        """
        self.app = app
        self.adapter = MongoDBAdapter(app)

    async def start(self):
        """Start the MongoDB adapter."""
        await self.adapter.start()

    async def stop(self):
        """Stop the MongoDB adapter."""
        await self.adapter.stop()

    async def add_file(self, file_data):
        """Create a new file record in MongoDB."""
        return await FileRecord.new_record(**file_data)

    async def get_file(self, file_id):
        """Retrieve a file record by its ID from MongoDB."""
        return await FileRecord.find_one({'_id': file_id})

    async def update_file(self, file_id, update_data):
        """Update a file record by its ID in MongoDB."""
        record = await FileRecord.find_one({'_id': file_id})
        if record:
            for k, v in update_data.items():
                setattr(record, k, v)
            await record.save()
        return record

    async def delete_file(self, file_id):
        """Delete a file record by its ID from MongoDB."""
        record = await FileRecord.find_one({'_id': file_id})
        if record:
            await record.delete()
        return record

    async def search_files(self, query: dict):
        """Search for file records in MongoDB matching a query."""
        return await FileRecord.find(query)
