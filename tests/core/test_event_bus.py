import pytest
import asyncio
import weakref
import gc
from unittest.mock import Mock, AsyncMock, call
from ucore_framework.core.event_bus import EventBus
from ucore_framework.core.event_types import AppStartedEvent

@pytest.fixture
def event_bus():
    bus = EventBus()
    bus.start()
    yield bus
    bus.shutdown()

def test_sync_publish_subscribe(event_bus):
    handler = Mock()
    event = AppStartedEvent(app_name="TestApp", version="1.0.0")
    event_bus.add_handler(AppStartedEvent, handler)
    event_bus.publish(event)
    handler.assert_called_once_with(event)

@pytest.mark.asyncio
async def test_async_publish_subscribe(event_bus):
    handler = AsyncMock()
    event = AppStartedEvent(app_name="TestApp", version="1.0.0")
    event_bus.add_handler(AppStartedEvent, handler)
    await event_bus.publish_async(event)
    handler.assert_awaited_once_with(event)

def test_handler_priority(event_bus):
    manager = Mock()
    handler_low = Mock(side_effect=lambda e: manager.low(e))
    handler_high = Mock(side_effect=lambda e: manager.high(e))
    event = AppStartedEvent(app_name="TestApp", version="1.0.0")
    event_bus.add_handler(AppStartedEvent, handler_low, priority=0)
    event_bus.add_handler(AppStartedEvent, handler_high, priority=10)
    event_bus.publish(event)
    # High priority handler should be called before low
    calls = [call.high(event), call.low(event)]
    manager.assert_has_calls(calls)

def test_weak_reference_memory_leak(event_bus):
    class HandlerClass:
        def handle_event(self, event):
            self.called = True

    obj = HandlerClass()
    obj.called = False
    ref = weakref.ref(obj)
    event = AppStartedEvent(app_name="TestApp", version="1.0.0")
    event_bus.add_handler(AppStartedEvent, obj.handle_event)
    del obj
    gc.collect()
    assert ref() is None
    # After GC, handler should not be called and should be cleaned up
    event_bus.publish(event)
    assert event_bus.get_handler_count(AppStartedEvent) == 0
