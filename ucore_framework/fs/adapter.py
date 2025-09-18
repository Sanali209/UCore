from abc import ABC, abstractmethod
from typing import Any, Dict, List

class FileSystemAdapter(ABC):
    """
    Base interface for file system adapters (local, remote, cloud, archive).
    """
    @abstractmethod
    def list_dir(self, path: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def read_file(self, path: str) -> bytes:
        pass

    @abstractmethod
    def write_file(self, path: str, data: bytes):
        pass

    @abstractmethod
    def delete_file(self, path: str):
        pass

    @abstractmethod
    def move_file(self, src: str, dst: str):
        pass

    @abstractmethod
    def copy_file(self, src: str, dst: str):
        pass

# DEPRECATED: Use ucore_framework.resource.types.file.FileSystem and its providers for all file system operations.
# All adapter registration and lookup should go through the FileSystem service.
