import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import os
import asyncio
from ucore_framework.resource.manager import ResourceManager, Resource
from ucore_framework.resource.ucore_registry import UCoreResourceRegistry
from ucore_framework.resource.unified_registry import UnifiedResourceRegistry
from ucore_framework.resource.backend_provider import BackendProvider, ServiceBackend, RoundRobinPolicy
from ucore_framework.resource.secrets import EnvVarSecretsManager

class DummyResource(Resource):
    async def _initialize(self): pass
    async def _connect(self): pass
    async def _disconnect(self): pass
    async def _cleanup(self): pass
    async def _health_check(self): return self.health
    async def health_check(self): return self.health

@pytest.mark.asyncio
async def test_resource_lifecycle_and_registry_integration():
    resource_manager = ResourceManager()
    ucore_registry = UCoreResourceRegistry(resource_manager)
    unified_registry = UnifiedResourceRegistry(ucore_registry, ucore_registry)

    # Register and start resource
    my_resource = DummyResource(name="integration_db", resource_type="database")
    unified_registry.register(my_resource)
    await resource_manager.start_all_resources()
    assert "integration_db" in resource_manager.get_all_resources()

    # Stop all resources
    await resource_manager.stop_all_resources()
    assert resource_manager.is_started is False

def test_backend_provider_with_registry():
    resource_manager = ResourceManager()
    ucore_registry = UCoreResourceRegistry(resource_manager)
    unified_registry = UnifiedResourceRegistry(ucore_registry, ucore_registry)
    provider = BackendProvider(selection_policy=RoundRobinPolicy(), registry=unified_registry)

    # Register backend and resource
    backend = ServiceBackend(name="integration_db", tags=["database"])
    provider.register_backend(backend)
    my_resource = DummyResource(name="integration_db", resource_type="database")
    unified_registry.register(my_resource)

    # Should select backend by name
    selected = provider.get_backend()
    assert selected and selected.name == "integration_db"

def test_secrets_manager_integration(monkeypatch):
    secrets = EnvVarSecretsManager()
    key = "INTEGRATION_SECRET"
    value = "integration_secret_value"
    secrets.set_secret(key, value)
    assert secrets.get_secret(key) == value
    secrets.rotate_secret(key, "rotated_value")
    audit = secrets.audit(key)
    assert any(e["event"] == "rotate" for e in audit["events"])
    del os.environ[key]
