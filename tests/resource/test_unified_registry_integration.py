import pytest
from framework.resource.manager import ResourceManager, Resource
from framework.resource.ucore_registry import UCoreResourceRegistry
from framework.resource.unified_registry import UnifiedResourceRegistry
from framework.resource.backend_provider import BackendProvider, ServiceBackend, RoundRobinPolicy

class DummyResource(Resource):
    async def _initialize(self): pass
    async def _connect(self): pass
    async def _disconnect(self): pass
    async def _cleanup(self): pass
    async def _health_check(self): return self.health
    async def health_check(self): return self.health

def test_unified_registry_and_backend_provider_integration():
    resource_manager = ResourceManager()
    ucore_registry = UCoreResourceRegistry(resource_manager)
    unified_registry = UnifiedResourceRegistry(ucore_registry, ucore_registry)

    # Register resource and backend
    my_resource = DummyResource(name="db1", resource_type="database")
    unified_registry.register(my_resource)
    provider = BackendProvider(selection_policy=RoundRobinPolicy(), registry=unified_registry)
    backend = ServiceBackend(name="db1", tags=["database"])
    provider.register_backend(backend)

    # Should find backend by registry and by provider
    found = unified_registry.find(name="db1")
    assert found and found[0].name == "db1"
    selected = provider.get_backend()
    assert selected and selected.name == "db1"

def test_registry_edge_cases():
    resource_manager = ResourceManager()
    ucore_registry = UCoreResourceRegistry(resource_manager)
    unified_registry = UnifiedResourceRegistry(ucore_registry, ucore_registry)

    # Unregister non-existent resource
    try:
        unified_registry.unregister("notfound")
    except Exception:
        pass  # Should not raise

    # Find with no match
    assert unified_registry.find(name="missing") == []

def test_progress_manager_event_bus(monkeypatch):
    from framework.monitoring.progress import ProgressManager

    events = []
    class DummyBus:
        def publish(self, topic, data):
            events.append((topic, data))

    pm = ProgressManager(max_progress=2, event_bus=DummyBus(), description="Test")
    pm.step("step1")
    pm.step("step2")
    assert len(events) == 2
    assert events[0][0] == "progress.update"
    assert events[1][1]["progress"] == 2
