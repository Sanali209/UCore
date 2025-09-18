from abc import ABC, abstractmethod
from UCoreFrameworck.fs.models import FileRecord

class Indexer(ABC):
    """
    Abstract base class for file indexers.
    Indexers process files and extract metadata or features.
    """
    @abstractmethod
    async def process(self, file_record: FileRecord, file_path: str):
        """
        Process a file and update its record.
        Args:
            file_record (FileRecord): The file record to update.
            file_path (str): Path to the file.
        """
        pass

class DeepDanboruIndexer(Indexer):
    """
    Example indexer for deepdanboru-style feature extraction.
    """
    async def process(self, file_record: FileRecord, file_path: str):
        """
        Process the file using deepdanboru logic (placeholder).
        """
        pass

class FaceDetectorIndexer(Indexer):
    """
    Example indexer for face detection.
    """
    async def process(self, file_record: FileRecord, file_path: str):
        """
        Process the file for face detection (placeholder).
        """
        pass

class FileTypeStrategy:
    """
    Strategy for processing files of a specific type/extension.
    Holds a list of indexers to apply.
    """
    def __init__(self, name, indexers: list[Indexer]):
        """
        Args:
            name (str): Strategy name (usually file extension).
            indexers (list[Indexer]): List of indexers to apply.
        """
        self.name = name
        self.indexers = indexers

    async def process(self, file_record: FileRecord, file_path: str):
        """
        Run all indexers for this strategy on the file.
        Args:
            file_record (FileRecord): The file record to update.
            file_path (str): Path to the file.
        """
        for indexer in self.indexers:
            await indexer.process(file_record, file_path)

# Example registry for strategies
strategy_registry = {}

def register_strategy(extension: str, strategy: FileTypeStrategy):
    """
    Register a file type strategy for a given extension.
    Args:
        extension (str): File extension.
        strategy (FileTypeStrategy): Strategy instance.
    """
    strategy_registry[extension] = strategy

# Register example strategies
register_strategy("jpg", FileTypeStrategy("jpg", [DeepDanboruIndexer(), FaceDetectorIndexer()]))
register_strategy("png", FileTypeStrategy("png", [FaceDetectorIndexer()]))

from typing import Optional

def get_strategy_by_extension(extension: str) -> Optional[FileTypeStrategy]:
    """
    Get the strategy for a given file extension.
    Args:
        extension (str): File extension.
    Returns:
        FileTypeStrategy or None
    """
    return strategy_registry.get(extension)
