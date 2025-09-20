import pytest
from unittest.mock import AsyncMock, Mock
from ucore_framework.core.component_manager import ComponentManager
from ucore_framework.core.component import Component

@pytest.fixture
def component_manager():
    mock_container = Mock()
    mock_event_bus = Mock()
    mock_container.get.return_value = mock_event_bus
    manager = ComponentManager(container=mock_container)
    return manager

@pytest.mark.asyncio
async def test_register_component_types(component_manager):
    class MockComponent(Component):
        def __init__(self, manager=None):
            super().__init__(name="mock")
        def start(self): pass
        def stop(self): pass

    mock_instance = MockComponent()
    component_manager.register_component(MockComponent)
    component_manager.register_component(mock_instance)
    assert len(component_manager.get_all_components()) == 2

@pytest.mark.asyncio
async def test_start_and_stop_lifecycle(component_manager):
    class MockComponent(Component):
        def __init__(self):
            super().__init__(name="mock")
        def start(self): pass
        def stop(self): pass

    mock_component = MockComponent()
    mock_component.start = AsyncMock()
    mock_component.stop = AsyncMock()
    component_manager.register_component(mock_component)
    await component_manager.start()
    await component_manager.stop()
    mock_component.start.assert_awaited_once()
    mock_component.stop.assert_awaited_once()
