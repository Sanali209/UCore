from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional, Awaitable, Dict
from loguru import logger

class DataProvider(ABC):
    """
    Abstract interface for data providers (sync/async, local/remote, paged, hierarchical).
    """
    @abstractmethod
    def get_data(self, **kwargs) -> List[Any]:
        pass

    def get_data_async(self, **kwargs) -> Awaitable[List[Any]]:
        raise NotImplementedError("Async data loading not implemented for this provider.")

    def refresh(self):
        pass

    def monitor(self, callback: Callable[[str, Any], None]):
        """
        Register a callback for monitoring events (e.g., loading, error, progress).
        """
        self._monitor_callback = callback

class InMemoryProvider(DataProvider):
    def __init__(self, data: List[Any]):
        self.data = data

    def get_data(self, **kwargs) -> List[Any]:
        logger.info("InMemoryProvider: get_data called")
        return self.data

class AsyncMockProvider(DataProvider):
    def get_data(self, **kwargs) -> List[Any]:
        # Dummy sync implementation for abstract base
        return kwargs.get("data", [])
    async def get_data_async(self, **kwargs) -> List[Any]:
        import asyncio
        logger.info("AsyncMockProvider: async get_data called")
        await asyncio.sleep(0.1)
        return kwargs.get("data", [])

class FileSystemProvider(DataProvider):
    def __init__(self, root_path: str):
        self.root_path = root_path

    def get_data(self, **kwargs) -> List[Dict[str, Any]]:
        import os
        logger.info(f"FileSystemProvider: listing {self.root_path}")
        try:
            return [{"name": f, "is_dir": os.path.isdir(os.path.join(self.root_path, f))}
                    for f in os.listdir(self.root_path)]
        except Exception as e:
            logger.error(f"FileSystemProvider error: {e}")
            return []

# Plugin registration example
class DataProviderPluginBase(ABC):
    @abstractmethod
    def create_provider(self, **kwargs) -> DataProvider:
        pass
