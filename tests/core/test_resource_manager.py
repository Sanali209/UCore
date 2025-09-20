import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from ucore_framework.core.resource.manager import ResourceManager
from ucore_framework.core.resource.resource import Resource

@pytest.mark.asyncio
async def test_register_and_get_resource():
    manager = ResourceManager()
    mock_resource = AsyncMock(spec=Resource)
    mock_resource.name = "mock"
    mock_resource.resource_type = "test"
    manager.register_resource(mock_resource)
    assert manager.get_resource("mock") is mock_resource

@pytest.mark.asyncio
async def test_start_all_resources():
    manager = ResourceManager()
    resource1 = AsyncMock(spec=Resource)
    resource1.name = "r1"
    resource1.resource_type = "test"
    resource2 = AsyncMock(spec=Resource)
    resource2.name = "r2"
    resource2.resource_type = "test"
    manager.register_resource(resource1)
    manager.register_resource(resource2)
    await manager.start_all_resources()
    resource1.initialize.assert_awaited_once()
    resource2.initialize.assert_awaited_once()

@pytest.mark.asyncio
async def test_stop_all_resources():
    manager = ResourceManager()
    mock_resource = AsyncMock(spec=Resource)
    mock_resource.name = "mock"
    mock_resource.resource_type = "test"
    mock_resource.is_ready = True
    manager.register_resource(mock_resource)
    manager._is_started = True
    await manager.stop_all_resources()
    mock_resource.cleanup.assert_awaited()

@pytest.mark.asyncio
async def test_resource_start_failure():
    manager = ResourceManager()
    failing_resource = AsyncMock(spec=Resource)
    failing_resource.name = "fail"
    failing_resource.resource_type = "test"
    failing_resource.initialize.side_effect = Exception("fail")
    manager.register_resource(failing_resource)
    with patch.object(manager, "_handle_resource_failure", new_callable=AsyncMock) as mock_handle_failure:
        await manager.start_all_resources()
        mock_handle_failure.assert_awaited_once()
