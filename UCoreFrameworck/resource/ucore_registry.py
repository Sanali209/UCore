"""
UCoreResourceRegistry adapter for UnifiedResourceRegistry

Wraps the UCore ResourceManager to provide the IResourceRegistry interface.
"""

from typing import Any, List, Optional, Callable
from .unified_registry import IResourceRegistry
from .manager import ResourceManager, Resource

class UCoreResourceRegistry(IResourceRegistry):
    def __init__(self, resource_manager: ResourceManager):
        self.resource_manager = resource_manager
        self._callbacks: List[Callable] = []

    def register(self, resource: Resource) -> None:
        self.resource_manager.register_resource(resource)
        self._notify('register', resource)

    def unregister(self, resource: Resource) -> None:
        self.resource_manager.unregister_resource(resource.name)
        self._notify('unregister', resource)

    def find(self, name: Optional[str] = None, type_: Optional[type] = None, tags: Optional[List[str]] = None) -> List[Resource]:
        results = []
        if name:
            try:
                res = self.resource_manager.get_resource(name)
                if res:
                    results.append(res)
            except Exception:
                pass
        elif type_:
            results.extend(self.resource_manager.get_resources_by_type(type_.__name__))
        else:
            results.extend(self.resource_manager.get_all_resources().values())
        if tags:
            results = [r for r in results if hasattr(r, "tags") and set(tags).issubset(set(r.tags))]
        return results

    def list_resources(self) -> List[Resource]:
        return list(self.resource_manager.get_all_resources().values())

    def monitor(self, callback) -> None:
        self._callbacks.append(callback)

    def _notify(self, event_type: str, resource: Resource) -> None:
        for cb in self._callbacks:
            cb(event_type, resource)
