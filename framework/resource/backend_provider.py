"""
BackendProvider with Policy-Driven Backend Selection and UnifiedResourceRegistry integration.

Provides registration, discovery, and policy-based selection of backends.
"""

from typing import Any, Dict, List, Optional, Callable
from .unified_registry import IResourceRegistry

class ServiceBackend:
    def __init__(self, name: str, tags: Optional[List[str]] = None, health: str = "healthy", backend_load: float = 0.0):
        self.name = name
        self.tags = tags or []
        self.health = health
        self.backend_load = backend_load
        self.lazy_loaded = False

    def is_compatible(self, context: Optional[dict] = None) -> bool:
        return True

    def load(self):
        self.lazy_loaded = True

class BackendSelectionPolicy:
    def select(self, backends: List[ServiceBackend], context: Optional[dict] = None) -> Optional[ServiceBackend]:
        raise NotImplementedError

class RoundRobinPolicy(BackendSelectionPolicy):
    def __init__(self):
        self._index = 0

    def select(self, backends: List[ServiceBackend], context: Optional[dict] = None) -> Optional[ServiceBackend]:
        if not backends:
            return None
        backend = backends[self._index % len(backends)]
        self._index += 1
        return backend

class HealthBasedPolicy(BackendSelectionPolicy):
    def select(self, backends: List[ServiceBackend], context: Optional[dict] = None) -> Optional[ServiceBackend]:
        healthy = [b for b in backends if b.health == "healthy"]
        return healthy[0] if healthy else (backends[0] if backends else None)

class TagBasedPolicy(BackendSelectionPolicy):
    def __init__(self, required_tags: List[str]):
        self.required_tags = required_tags

    def select(self, backends: List[ServiceBackend], context: Optional[dict] = None) -> Optional[ServiceBackend]:
        for backend in backends:
            if all(tag in backend.tags for tag in self.required_tags):
                return backend
        return backends[0] if backends else None

class BackendProvider:
    def __init__(self, selection_policy: Optional[BackendSelectionPolicy] = None, registry: Optional[IResourceRegistry] = None):
        self.backends: Dict[str, ServiceBackend] = {}
        self.selection_policy = selection_policy or RoundRobinPolicy()
        self.registry = registry

    def register_backend(self, backend: ServiceBackend):
        self.backends[backend.name] = backend

    def unregister_backend(self, name: str):
        if name in self.backends:
            del self.backends[name]

    def get_backend(self, context: Optional[dict] = None) -> Optional[ServiceBackend]:
        # Discover backends from registry if available
        if self.registry:
            discovered = self.registry.find(type_=ServiceBackend)
            for backend in discovered:
                if backend.name not in self.backends:
                    self.backends[backend.name] = backend
        return self.selection_policy.select(list(self.backends.values()), context)

    def get_backend_by_name(self, name: str) -> Optional[ServiceBackend]:
        return self.backends.get(name)

    def set_policy(self, policy: BackendSelectionPolicy):
        self.selection_policy = policy

    def get_all_backends(self) -> List[ServiceBackend]:
        # Optionally include registry-discovered backends
        if self.registry:
            discovered = self.registry.find(type_=ServiceBackend)
            for backend in discovered:
                if backend.name not in self.backends:
                    self.backends[backend.name] = backend
        return list(self.backends.values())

    def get_all_by_tag(self, tag: str) -> List[ServiceBackend]:
        return [b for b in self.get_all_backends() if tag in b.tags]
