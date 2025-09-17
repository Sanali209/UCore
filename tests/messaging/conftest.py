import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock
from framework.messaging.event_bus import EventBus
from framework.messaging.events import Event, ComponentStartedEvent


@pytest.fixture
def event_bus():
    """Create EventBus instance for testing."""
    bus = EventBus()
    return bus


@pytest.fixture
def sample_event():
    """Create a sample event for testing."""
    return ComponentStartedEvent(
        component_name="TestComponent",
        component_type=str,
        source="test_source"
    )


@pytest.fixture
def mock_event_handler():
    """Create a mock event handler that tracks calls."""
    handler = Mock()
    handler.call_count = 0
    handler.last_event = None

    def tracking_handler(event):
        handler.call_count += 1
        handler.last_event = event

    handler.side_effect = tracking_handler
    return handler


@pytest.fixture
def async_event_handler():
    """Create an async event handler for testing."""
    handler = AsyncMock()
    handler.call_count = 0
    handler.last_event = None

    async def async_tracking_handler(event):
        handler.call_count += 1
        handler.last_event = event

    handler.side_effect = async_tracking_handler
    return handler


class TestEvent(Event):
    """Test event for EventBus testing."""
    def __init__(self, data: dict = None):
        super().__init__()
        self.data = data or {}


class ErrorEventHandler:
    """Handler that raises an exception."""
    def __init__(self):
        self.called = False

    def __call__(self, event):
        self.called = True
        raise ValueError("Test error in handler")


class FilterEventHandler:
    """Handler that implements filtering."""
    def __init__(self, filter_criteria):
        self.filter_criteria = filter_criteria
        self.handled_events = []

    def __call__(self, event):
        if hasattr(event, 'data') and event.data:
            if all(event.data.get(key) == value
                   for key, value in self.filter_criteria.items()):
                self.handled_events.append(event)


class MockMiddleware:
    """Mock middleware for testing."""
    def __init__(self):
        self.called = False
        self.last_event = None

    def __call__(self, event):
        self.called = True
        self.last_event = event
        # Return modified event
        event.processed = True
        return event
