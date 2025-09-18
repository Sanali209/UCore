import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from UCoreFrameworck.core.component import Component
from UCoreFrameworck.core.app import App
from UCoreFrameworck.messaging.event_bus import EventBus
from UCoreFrameworck.messaging.events import Event, AppStartedEvent


class TestComponentInitialization:
    """Test Component initialization and basic setup."""

    def test_component_create_without_app(self):
        """Test component creation without app reference."""
        component = Component()

        assert component.app is None

    def test_component_create_with_app(self):
        """Test component creation with app reference."""
        mock_app = Mock()
        component = Component(mock_app)

        assert component.app == mock_app

    def test_component_basic_attributes(self):
        """Test component has expected basic attributes."""
        component = Component()

        # Should have event bus methods
        assert hasattr(component, 'get_event_bus')
        assert hasattr(component, 'subscribe')
        assert hasattr(component, 'publish')
        assert hasattr(component, 'publish_async')

        # Should have lifecycle methods
        assert hasattr(component, 'start')
        assert hasattr(component, 'stop')
        assert hasattr(component, 'on_config_update')


class TestComponentLifecycle:
    """Test component lifecycle management."""

    def test_component_start_default_implementation(self):
        """Test component start method default behavior."""
        component = Component()
        # Should not raise any exceptions
        component.start()

    def test_component_stop_default_implementation(self):
        """Test component stop method default behavior."""
        component = Component()
        # Should not raise any exceptions
        component.stop()

    @pytest.mark.asyncio
    async def test_component_start_async_implementation(self):
        """Test async component start method."""
        class AsyncComponent(Component):
            async def start(self):
                # Simulate async operation
                await asyncio.sleep(0.01)

        component = AsyncComponent()
        # Should handle async methods gracefully
        await component.start()

    def test_component_on_config_update_default(self):
        """Test config update handler default behavior."""
        component = Component()
        mock_config = Mock()

        # Should not raise any exceptions (legacy method)
        component.on_config_update(mock_config)


class TestEventBusIntegration:
    """Test component event bus integration."""

    def test_get_event_bus_without_app(self):
        """Test getting event bus without app configured."""
        component = Component()

        result = component.get_event_bus()
        assert result is None

    def test_get_event_bus_with_app(self):
        """Test getting event bus with app configured."""
        mock_app = Mock()
        mock_event_bus = Mock(spec=EventBus)
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)

        result = component.get_event_bus()
        assert result == mock_event_bus
        mock_container.get.assert_called_once_with(EventBus)

    def test_get_event_bus_container_error(self):
        """Test event bus retrieval when container fails - should not break."""
        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.side_effect = Exception("Container error")
        mock_app.container = mock_container

        component = Component(mock_app)

        # Component should handle container errors gracefully
        result = component.get_event_bus()
        # Container error should result in None, not crash the component
        assert result is None

    def test_get_event_bus_with_real_app(self):
        """Test event bus integration with real app instance."""
        app = App("TestApp")

        component = Component(app)

        event_bus = component.get_event_bus()
        assert event_bus is not None
        assert isinstance(event_bus, EventBus)


class TestEventSubscription:
    """Test component event subscription functionality."""

    def test_subscribe_as_decorator_without_app(self):
        """Test subscribe decorator without app - should raise error."""
        component = Component()

        with pytest.raises(RuntimeError, match="Cannot subscribe to events: no app configured"):
            @component.subscribe(AppStartedEvent)
            def handler(event):
                pass

    def test_subscribe_programmatic_without_app(self):
        """Test programmatic subscribe without app - should raise error."""
        component = Component()

        with pytest.raises(RuntimeError, match="Cannot subscribe to events: no app configured"):
            component.subscribe(AppStartedEvent, lambda x: None)

    def test_subscribe_as_decorator(self):
        """Test subscribe decorator functionality."""
        mock_event_bus = Mock()
        mock_event_bus.subscribe.return_value = "decorator_result"

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)

        # Use as decorator
        decorator = component.subscribe(AppStartedEvent)
        mock_event_bus.subscribe.assert_called_once_with(AppStartedEvent)

        assert decorator == "decorator_result"

    def test_subscribe_programmatic(self):
        """Test programmatic event subscription."""
        mock_event_bus = Mock()
        mock_event_bus.add_handler.return_value = "handler_id"

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)

        mock_handler = Mock()
        result = component.subscribe(AppStartedEvent, mock_handler)

        mock_event_bus.add_handler.assert_called_once_with(AppStartedEvent, mock_handler)
        assert result == "handler_id"

    def test_subscribe_programmatic_with_kwargs(self):
        """Test programmatic subscription with additional kwargs."""
        mock_event_bus = Mock()

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)

        mock_handler = Mock()
        component.subscribe(AppStartedEvent, mock_handler, priority=5, filters={"enabled": True})

        mock_event_bus.add_handler.assert_called_once_with(
            AppStartedEvent, mock_handler, priority=5, filters={"enabled": True}
        )


class TestEventPublishing:
    """Test component event publishing functionality."""

    def test_publish_without_app(self):
        """Test publish event without app - should raise error."""
        component = Component()
        event = AppStartedEvent("test_source")

        with pytest.raises(RuntimeError, match="Cannot publish event: no app configured"):
            component.publish(event)

    def test_publish_with_app(self):
        """Test publishing event with app configured."""
        mock_event_bus = Mock()

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)
        event = AppStartedEvent("test_source")

        component.publish(event)

        mock_event_bus.publish.assert_called_once_with(event)

    def test_publish_async_without_app(self):
        """Test publish async event without app - should raise error."""
        component = Component()
        event = AppStartedEvent("test_source")

        with pytest.raises(RuntimeError, match="Cannot publish event: no app configured"):
            component.publish_async(event)

    def test_publish_async_with_app(self):
        """Test publishing async event with app configured."""
        mock_event_bus = Mock()

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)
        event = AppStartedEvent("test_source")

        with patch('asyncio.create_task') as mock_create_task:
            component.publish_async(event)

            mock_create_task.assert_called_once()
            # Verify that event_bus.publish_async was called within the create_task
            args = mock_create_task.call_args[0][0]
            # The coroutine should be calling publish_async
            assert hasattr(args, 'cr_frame')

    def test_publish_event_bus_error_handling(self):
        """Test error handling when event bus fails."""
        mock_event_bus = Mock()
        mock_event_bus.publish.side_effect = Exception("Event bus error")

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)
        event = AppStartedEvent("test_source")

        # Should raise the event bus error
        with pytest.raises(Exception, match="Event bus error"):
            component.publish(event)


class TestComponentInheritance:
    """Test component inheritance patterns."""

    def test_custom_component_inheritance(self):
        """Test custom component inheriting from Component."""
        class CustomComponent(Component):
            def __init__(self, app=None, custom_value=None):
                super().__init__(app)
                self.custom_value = custom_value

            def start(self):
                super().start()
                self.custom_value = "started"

            def stop(self):
                super().stop()
                self.custom_value = "stopped"

        component = CustomComponent(custom_value="initialized")

        assert component.custom_value == "initialized"
        assert isinstance(component, Component)

        component.start()
        assert component.custom_value == "started"

        component.stop()
        assert component.custom_value == "stopped"


class TestComponentRealIntegration:
    """Test component with real app integration."""

    def test_component_with_real_app_integration(self):
        """Test component with real app instance and event publishing."""
        app = App("TestApp")

        class TestComponent(Component):
            def __init__(self, app=None):
                super().__init__(app)
                self.received_events = []

            def handle_app_started(self, event):
                self.received_events.append(event)
                return None

            def register_handlers(self):
                if self.app:  # Only if we have an app
                    self.subscribe(AppStartedEvent, self.handle_app_started)

        component = TestComponent(app)

        # Register component with app
        app.register_component(component)

        # Should have event bus available
        event_bus = component.get_event_bus()
        assert event_bus is not None
        assert isinstance(event_bus, EventBus)

        # Should be able to publish events
        event = AppStartedEvent("test_source")
        component.publish(event)

        # Event should be published (can't easily test receipt without starting the app)

    def test_component_multiple_apps(self):
        """Test component behavior with different app instances."""
        app1 = App("App1")
        app2 = App("App2")

        component1 = Component(app1)
        component2 = Component(app2)

        # Different apps should have different event buses
        event_bus1 = component1.get_event_bus()
        event_bus2 = component2.get_event_bus()

        assert event_bus1 is not None
        assert event_bus2 is not None
        assert event_bus1 is not event_bus2


class TestComponentErrorScenarios:
    """Test component error handling and edge cases."""

    def test_component_none_event_bus(self):
        """Test component behavior when event bus is None."""
        # This shouldn't happen in normal use, but test edge case
        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = None
        mock_app.container = mock_container

        component = Component(mock_app)

        result = component.get_event_bus()
        assert result is None

    def test_component_subscribe_invalid_event_type(self):
        """Test subscribing to invalid event type."""
        mock_event_bus = Mock()
        mock_event_bus.subscribe.side_effect = TypeError("Invalid event type")

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)

        with pytest.raises(TypeError, match="Invalid event type"):
            component.subscribe("invalid_event_class")

    def test_component_publish_none_event(self):
        """Test publishing None event."""
        mock_event_bus = Mock()

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)

        # Should handle None event gracefully (though typically not recommended)
        component.publish(None)

        mock_event_bus.publish.assert_called_once_with(None)


class TestComponentAsyncEventPublishing:
    """Test async event publishing with real asyncio."""

    @pytest.mark.asyncio
    async def test_async_event_publishing(self):
        """Test async event publishing with create_task."""
        mock_event_bus = Mock()
        mock_event_bus.publish_async = AsyncMock()

        mock_app = Mock()
        mock_container = Mock()
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)
        event = AppStartedEvent("test_source")

        with patch('asyncio.create_task') as mock_create_task:
            component.publish_async(event)

            # Verify create_task was called once
            mock_create_task.assert_called_once()

            # Get the coroutine that was passed to create_task
            task_coro = mock_create_task.call_args[0][0]

            # Execute the coroutine to verify it calls publish_async
            await task_coro

            mock_event_bus.publish_async.assert_called_once_with(event)


class TestComponentEventBusLazyLoading:
    """Test event bus lazy loading behavior."""

    def test_event_bus_lazy_initialization(self):
        """Test that event bus is initialized lazily."""
        mock_app = Mock()
        mock_container = Mock()

        # Initially return None to simulate event bus not ready yet
        mock_event_bus = Mock()
        call_results = [None, mock_event_bus]
        def get_event_bus_side_effect(*args, **kwargs):
            return call_results.pop(0)
        mock_container.get.side_effect = get_event_bus_side_effect
        mock_app.container = mock_container

        component = Component(mock_app)

        # First call should return None
        result1 = component.get_event_bus()
        assert result1 is None

        # Clear cache before next call to simulate fresh lookup
        component.clear_event_bus_cache()

        # Second call should return the event bus
        result2 = component.get_event_bus()
        assert result2 is mock_event_bus

    def test_event_bus_caching(self):
        """Test that event bus instance is cached after first access."""
        mock_app = Mock()
        mock_event_bus = Mock()
        mock_container = Mock()
        # Always return the same mock_event_bus for caching test
        mock_container.get.return_value = mock_event_bus
        mock_app.container = mock_container

        component = Component(mock_app)

        # First call - should cache the event bus
        result1 = component.get_event_bus()
        assert result1 is mock_event_bus

        # Change what container returns (should not affect cached result)
        mock_container.get.return_value = Mock()

        # Second call should still return cached instance
        result2 = component.get_event_bus()
        assert result2 is mock_event_bus  # Should be cached instance
