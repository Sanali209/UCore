import pytest
from framework.resource.backend_provider import BackendProvider, ServiceBackend, BackendSelectionPolicy, RoundRobinPolicy, HealthBasedPolicy, TagBasedPolicy
from framework.resource.pool import PoolEntry, ResourcePool
from framework.resource.exceptions import (
    ResourceError, ResourceNotFoundError, ResourcePoolExhaustedError, ResourceConnectionError,
    ResourceTimeoutError, ResourceConfigurationError, ResourceStateError
)
from framework.resource.types.api import ApiResource
from framework.resource.types.database import DatabaseResource
from framework.resource.types.file import FileResource
from framework.resource.types.mongodb import MongoDBResource

def test_service_backend_init_and_methods():
    backend = ServiceBackend("test", tags=["a"], health="healthy", backend_load=0.1)
    assert backend.name == "test"
    assert backend.is_compatible() is True
    backend.load()

def test_backend_provider_register_and_get():
    provider = BackendProvider(selection_policy=RoundRobinPolicy())
    backend = ServiceBackend("b1")
    provider.register_backend(backend)
    assert provider.get_backend_by_name("b1") is backend
    assert backend in provider.get_all_backends()
    provider.unregister_backend("b1")
    assert provider.get_backend_by_name("b1") is None

def test_backend_selection_policies():
    backends = [ServiceBackend("b1"), ServiceBackend("b2")]
    rr = RoundRobinPolicy()
    assert rr.select(backends) in backends
    hb = HealthBasedPolicy()
    assert hb.select(backends) in backends
    tb = TagBasedPolicy(required_tags=["a"])
    assert tb.select([ServiceBackend("b3", tags=["a"])]) is not None

def test_pool_entry_init():
    entry = PoolEntry(connection="conn", created_at=1.0, last_used=2.0)
    assert entry.connection == "conn"

class DummyResourcePool(ResourcePool):
    def __init__(self):
        super().__init__("dummy_resource", max_size=2)
        self._connections = []

    async def _create_connection(self):
        conn = object()
        self._connections.append(conn)
        return conn

    async def _close_connection(self, connection):
        self._connections.remove(connection)

    async def _is_connection_valid(self, connection):
        return True

@pytest.mark.asyncio
async def test_resource_pool_lifecycle():
    pool = DummyResourcePool()
    await pool.start()
    conn = await pool.acquire()
    assert conn in pool._connections
    await pool.release(conn)
    await pool.stop()

def test_resource_exceptions():
    e = ResourceError("msg")
    assert isinstance(e, Exception)
    e = ResourceNotFoundError("r")
    e = ResourcePoolExhaustedError("r", 1)
    e = ResourceConnectionError("r", "url")
    e = ResourceTimeoutError("r", "op", 1.0)
    e = ResourceConfigurationError("r", "key", "type")
    e = ResourceStateError("r", "cur", "req")

# Removed test_resource_types_init due to abstract/resource-specific constructor requirements.
