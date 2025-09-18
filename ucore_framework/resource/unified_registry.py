"""
Unified Resource Registry for UCore & SLM Integration

Defines IResourceRegistry interface and UnifiedResourceRegistry implementation.
Provides unified API for resource registration, discovery, monitoring, and orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class IResourceRegistry(ABC):
    @abstractmethod
    def register(self, resource: Any) -> None:
        pass

    @abstractmethod
    def unregister(self, resource: Any) -> None:
        pass

    @abstractmethod
    def find(self, name: Optional[str] = None, type_: Optional[type] = None, tags: Optional[List[str]] = None) -> List[Any]:
        pass

    @abstractmethod
    def list_resources(self) -> List[Any]:
        pass

    @abstractmethod
    def monitor(self, callback) -> None:
        """Subscribe to resource events (add/remove/update)."""
        pass

class UnifiedResourceRegistry(IResourceRegistry):
    def __init__(self, ucore_registry: IResourceRegistry, slm_registry: IResourceRegistry):
        self.ucore_registry = ucore_registry
        self.slm_registry = slm_registry
        self._callbacks = []

    def register(self, resource: Any) -> None:
        self.ucore_registry.register(resource)
        self.slm_registry.register(resource)
        self._notify('register', resource)

    def unregister(self, resource: Any) -> None:
        self.ucore_registry.unregister(resource)
        self.slm_registry.unregister(resource)
        self._notify('unregister', resource)

    def find(self, name: Optional[str] = None, type_: Optional[type] = None, tags: Optional[List[str]] = None) -> List[Any]:
        name = name if name is not None else ""
        tags = tags if tags is not None else []
        results = self.ucore_registry.find(name, type_, tags) + self.slm_registry.find(name, type_, tags)
        # Remove duplicates by id
        seen = set()
        unique = []
        for r in results:
            if id(r) not in seen:
                unique.append(r)
                seen.add(id(r))
        return unique

    def list_resources(self) -> List[Any]:
        return self.find()

    def monitor(self, callback) -> None:
        self._callbacks.append(callback)

    def _notify(self, event_type: str, resource: Any) -> None:
        for cb in self._callbacks:
            cb(event_type, resource)

    # Optionally: add methods for metadata, health, orchestration, etc.
