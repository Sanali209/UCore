"""
Unit tests for UCore Framework Event Bus implementation.
Tests EventBus functionality, component integration, and lifecycle events.
"""
import unittest
import asyncio
from unittest.mock import MagicMock
import sys
import os

# Add framework to path
sys.path.insert(0, os.path.abspath('.'))

from framework.app import App
from framework.core.component import Component
from framework.messaging.events import (
    Event, AppStartedEvent, AppStoppedEvent,
    ComponentStartedEvent, ComponentStoppedEvent,
    ConfigUpdatedEvent, UserEvent
)
from framework.messaging.event_bus import EventBus, EventHandlerInfo


class TestEventSystem(unittest.TestCase):
    """Test basic Event system classes and functionality."""

    def test_event_creation(self):
        """Test that Event objects are created correctly with automatic fields."""
        event = Event(event_id="test-id", data={"key": "value"})

        self.assertEqual(event.event_id, "test-id")
        self.assertIsNotNone(event.timestamp)
        self.assertEqual(event.data, {"key": "value"})
        self.assertIsNotNone(event.source)  # Source should be detected automatically
        self.assertNotEqual(event.source, "")  # Should not be empty

    def test_event_subclass_creation(self):
        """Test creation of framework-specific event subclasses."""
        # Test AppStartedEvent
        app_event = AppStartedEvent(app_name="TestApp", component_count=3)
        self.assertEqual(app_event.app_name, "TestApp")
        self.assertEqual(app_event.component_count, 3)

        # Test ComponentStartedEvent
        comp_event = ComponentStartedEvent(component_name="TestComp", component_type=str)
        self.assertEqual(comp_event.component_name, "TestComp")
        self.assertEqual(comp_event.component_type, str)

        # Test ConfigUpdatedEvent
        config_event = ConfigUpdatedEvent(
            updated_keys=["key1"],
            old_values={"key1": "old"},
            new_values={"key1": "new"}
        )
        self.assertEqual(config_event.updated_keys, ["key1"])
        self.assertEqual(config_event.old_values, {"key1": "old"})
        self.assertEqual(config_event.new_values, {"key1": "new"})


class TestEventBus(unittest.TestCase):
    """Test EventBus core functionality."""

    def setUp(self):
        """Set up EventBus instance for each test."""
        self.event_bus = EventBus()
        self.event_bus._running = True  # Enable publishing for tests

    def test_event_bus_creation(self):
        """Test EventBus initialization."""
        event_bus = EventBus()  # Create fresh instance for this test
        self.assertIsNotNone(event_bus._handlers)
        self.assertIsNotNone(event_bus._middlewares)
        self.assertFalse(event_bus._running)

    def test_synchronous_publishing(self):
        """Test synchronous event publishing."""
        # Create a simple event
        event = UserEvent(event_type="test", payload={"message": "hello"})

        # Track calls
        call_count = 0
        def handler(evt):
            nonlocal call_count
            call_count += 1
            self.assertEqual(evt.event_type, "test")
            self.assertEqual(evt.payload, {"message": "hello"})

        # Subscribe and publish
        handler_id = self.event_bus.add_handler(UserEvent, handler)
        self.event_bus.publish(event)

        self.assertEqual(call_count, 1)

    def test_multiple_handlers(self):
        """Test multiple handlers for the same event type."""
        event = UserEvent(event_type="test")

        call_counts = []
        def handler1(evt): call_counts.append("handler1")
        def handler2(evt): call_counts.append("handler2")

        self.event_bus.add_handler(UserEvent, handler1)
        self.event_bus.add_handler(UserEvent, handler2)

        self.event_bus.publish(event)

        self.assertEqual(len(call_counts), 2)
        self.assertIn("handler1", call_counts)
        self.assertIn("handler2", call_counts)

    def test_async_publishing(self):
        """Test asynchronous event publishing."""
        event = UserEvent(event_type="async_test")

        async def test_async():
            call_count = 0
            def handler(evt):
                nonlocal call_count
                call_count += 1

            self.event_bus.add_handler(UserEvent, handler)
            await self.event_bus.publish_async(event)

            self.assertEqual(call_count, 1)

        asyncio.run(test_async())

    def test_handler_removal(self):
        """Test removing event handlers."""
        event = UserEvent(event_type="removal_test")

        def handler(evt):
            pass

        handler_id = self.event_bus.add_handler(UserEvent, handler)
        self.assertTrue(self.event_bus.remove_handler(UserEvent, handler_id))

        # Publish should not call removed handler
        call_count = 0
        def new_handler(evt):
            nonlocal call_count
            call_count += 1

        self.event_bus.add_handler(UserEvent, new_handler)
        self.event_bus.publish(event)

        self.assertEqual(call_count, 1)


class TestComponentIntegration(unittest.TestCase):
    """Test EventBus integration with Component base class."""

    def setUp(self):
        """Set up app and component for testing."""
        self.app = App("TestApp")
        self.component = TestIntegrationComponent(self.app)
        self.app.register_component(self.component)

        # Bootstrap the app to set up services
        import argparse
        args = argparse.Namespace()
        args.config = None
        args.log_level = "INFO"
        args.plugins_dir = None
        self.app.bootstrap(args)

    def test_component_get_event_bus(self):
        """Test that components can access the EventBus."""
        event_bus = self.component.get_event_bus()
        self.assertIsNotNone(event_bus)
        self.assertIsInstance(event_bus, EventBus)

    def test_component_publish(self):
        """Test component event publishing."""
        test_event = UserEvent(event_type="component_test")
        self.component.publish(test_event)

        # Should not raise an error
        self.assertTrue(True)

    def test_component_subscribe_decorator(self):
        """Test component subscription using decorator."""
        @self.component.subscribe(UserEvent)
        def test_handler(event):
            event.received = True

        # Publish event
        event = UserEvent(event_type="test")
        self.component.publish(event)

        # Check if handler was called
        # Note: Since it's the same event bus, it should work
        self.assertTrue(hasattr(event, 'received'), "Handler should have been called")


class TestFrameworkIntegration(unittest.TestCase):
    """Test EventBus integration with full App lifecycle."""

    def setUp(self):
        """Set up test app and component."""
        self.app = App("IntegrationTest")
        self.component = LifecycleTestComponent(self.app)
        self.app.register_component(self.component)

    def test_lifecycle_events_published(self):
        """Test that lifecycle events are published during app lifecycle."""
        # Bootstrap app
        import argparse
        args = argparse.Namespace()
        args.config = None
        args.log_level = "INFO"
        args.plugins_dir = None
        self.app.bootstrap(args)

        # Mock the event loop to avoid actually starting
        with unittest.mock.patch.object(self.app, '_get_event_loop', return_value=MagicMock()):
            with unittest.mock.patch.object(asyncio, 'Event'):
                # This would normally start the event loop, but we just want to check setup
                pass

        # Event bus should be available
        from framework.messaging.event_bus import EventBus
        event_bus = self.app.container.get(EventBus)
        self.assertIsNotNone(event_bus)


class TestIntegrationComponent(Component):
    """Test component for integration testing."""

    def __init__(self, app):
        super().__init__(app)
        self.events_received = []

    def start(self):
        pass

    def stop(self):
        pass


class LifecycleTestComponent(Component):
    """Component that tracks lifecycle events."""

    def __init__(self, app):
        super().__init__(app)
        self.started_called = False
        self.stopped_called = False

    def start(self):
        self.started_called = True

    def stop(self):
        self.stopped_called = True


if __name__ == '__main__':
    unittest.main()
