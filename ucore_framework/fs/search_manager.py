"""Search management logic module (decomposed from resource.py)."""

from ucore_framework.fs.models import FileRecord
from typing import Any, Dict, List, Optional

class SearchManager:
    """
    Handles search operations for file records.
    """
    def __init__(self, adapter=None):
        self.adapter = adapter

    async def search_files(self, query: Dict[str, Any]) -> List[FileRecord]:
        """
        Search for file records matching a query.
        Args:
            query (dict): Mongo-style query.
        Returns:
            list[FileRecord]
        """
        if self.adapter:
            return await self.adapter.search_files(query)
        return await FileRecord.find(query)
