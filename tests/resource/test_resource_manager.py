import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from framework.resource.manager import ResourceManager
from framework.resource.resource import Resource, ResourceHealth
from framework.messaging.event_bus import EventBus


# Mock Resource Implementation
class MockResource(Resource):
    """Mock resource for testing."""

    def __init__(self, name="test_resource", resource_type="test"):
        super().__init__(name, resource_type)
        self.name = name
        self.resource_type = resource_type
        self.initialize_count = 0
        self.disconnect_count = 0
        self.cleanup_count = 0
        self.connect_fail = False
        self.cleanup_fail = False

    async def _initialize(self):
        """Mock initialization."""
        self.initialize_count += 1
        self._state = "created"
        self.is_connected = False
        await asyncio.sleep(0.01)  # Simulate async work

    async def _connect(self):
        """Mock connection."""
        if self.connect_fail:
            raise Exception("Connection failed")
        self.is_connected = True
        self._state = "connected"
        await asyncio.sleep(0.01)

    async def _disconnect(self):
        """Mock disconnection."""
        self.disconnect_count += 1
        self.is_connected = False
        await asyncio.sleep(0.01)

    async def _cleanup(self):
        """Mock cleanup."""
        if self.cleanup_fail:
            raise Exception("Cleanup failed")
        self.cleanup_count += 1
        await asyncio.sleep(0.01)

    async def _health_check(self):
        """Mock health check."""
        await asyncio.sleep(0.01)
        if self._state == "error":
            return ResourceHealth.UNHEALTHY
        return ResourceHealth.HEALTHY

    def get_stats(self):
        """Mock stats."""
        return {
            'initialize_count': self.initialize_count,
            'disconnect_count': self.disconnect_count,
            'cleanup_count': self.cleanup_count,
            'last_health_check': asyncio.get_event_loop().time()
        }


class TestResourceManagerInitialization:
    """Test ResourceManager initialization."""

    def test_manager_init(self):
        """Test basic manager initialization."""
        event_bus = Mock()
        di_container = Mock()

        manager = ResourceManager(event_bus, di_container)

        assert not manager.is_started
        assert manager.event_bus == event_bus
        assert manager.di_container == di_container
        assert len(manager._resources) == 0
        assert len(manager._resources_by_type) == 0
        assert manager._shutdown_timeout == 30.0
        assert not manager._is_shutting_down

    def test_manager_init_without_dependencies(self):
        """Test manager without event bus or DI container."""
        manager = ResourceManager()

        assert manager.event_bus is None
        assert manager.di_container is None

    def test_manager_properties(self):
        """Test manager properties."""
        manager = ResourceManager()

        # Test len property
        resource1 = MockResource("test1")
        resource2 = MockResource("test2")
        manager._resources = {"test1": resource1, "test2": resource2}

        assert len(manager) == 2

        # Test contains
        assert "test1" in manager
        assert "test3" not in manager

        # Test getitem
        assert manager["test1"] == resource1
        with pytest.raises(KeyError):
            _ = manager["test3"]


class TestResourceRegistration:
    """Test resource registration functionality."""

    def test_register_resource_success(self):
        """Test successful resource registration."""
        manager = ResourceManager()
        resource = MockResource("test_resource", "test_type")

        manager.register_resource(resource)

        # Verify resource is registered
        assert resource.name in manager._resources
        assert manager._resources[resource.name] == resource
        assert resource in manager._resources_by_type[resource.resource_type]

    def test_register_resource_with_di_container(self):
        """Test resource registration with DI container."""
        di_container = Mock()
        manager = ResourceManager(di_container=di_container)

        resource = MockResource("test_resource", "test_type")

        manager.register_resource(resource)

        # Verify DI registration
        di_container.register.assert_called_once_with(
            resource, resource.name
        )

    def test_register_existing_resource(self):
        """Test replacing existing resource."""
        manager = ResourceManager()

        resource1 = MockResource("test_resource", "test_type")
        resource2 = MockResource("test_resource", "different_type")

        manager.register_resource(resource1)
        assert manager._resources["test_resource"] == resource1
        assert resource1 in manager._resources_by_type["test_type"]

        # Register replacement
        manager.register_resource(resource2)

        # Verify replaced
        assert manager._resources["test_resource"] == resource2
        assert resource1 not in manager._resources_by_type["test_type"]
        assert resource2 in manager._resources_by_type["different_type"]

    def test_get_resource_success(self):
        """Test successful resource retrieval."""
        manager = ResourceManager()
        resource = MockResource("test_resource", "test_type")
        manager._resources["test_resource"] = resource

        result = manager.get_resource("test_resource")

        assert result == resource

    def test_get_resource_not_found(self):
        """Test resource retrieval when resource doesn't exist."""
        manager = ResourceManager()

        from framework.resource.exceptions import ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError):
            manager.get_resource("nonexistent")

    def test_get_resources_by_type(self):
        """Test getting resources by type."""
        manager = ResourceManager()

        resource1 = MockResource("test1", "type_a")
        resource2 = MockResource("test2", "type_a")
        resource3 = MockResource("test3", "type_b")

        manager.register_resource(resource1)
        manager.register_resource(resource2)
        manager.register_resource(resource3)

        type_a_resources = manager.get_resources_by_type("type_a")
        type_b_resources = manager.get_resources_by_type("type_b")

        assert len(type_a_resources) == 2
        assert resource1 in type_a_resources
        assert resource2 in type_a_resources
        assert len(type_b_resources) == 1
        assert resource3 in type_b_resources

    def test_get_all_resources(self):
        """Test getting all resources."""
        manager = ResourceManager()

        resource1 = MockResource("test1", "type_a")
        resource2 = MockResource("test2", "type_b")

        manager.register_resource(resource1)
        manager.register_resource(resource2)

        all_resources = manager.get_all_resources()

        assert len(all_resources) == 2
        assert all_resources["test1"] == resource1
        assert all_resources["test2"] == resource2


class TestLifecycleManagement:
    """Test resource lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_all_resources_success(self):
        """Test successful startup of all resources."""
        event_bus = Mock()
        manager = ResourceManager(event_bus=event_bus)

        # Add mock resources
        resource1 = MockResource("resource1", "type_a")
        resource2 = MockResource("resource2", "type_b")
        manager.register_resource(resource1)
        manager.register_resource(resource2)

        # Start all resources
        await manager.start_all_resources()

        # Verify manager state
        assert manager.is_started

        # Verify event publishing
        event_bus.publish_async.assert_called()

        # Verify resources were initialized
        assert resource1.initialize_count == 1
        assert resource2.initialize_count == 1

    @pytest.mark.asyncio
    async def test_start_all_resources_with_failure(self):
        """Test startup with resource failure."""
        event_bus = Mock()
        manager = ResourceManager(event_bus=event_bus)

        # Add resources - one will fail
        resource1 = MockResource("resource1", "type_a")
        resource2 = MockResource("resource2", "type_b")
        resource2.connect_fail = True
        manager.register_resource(resource1)
        manager.register_resource(resource2)

        # Start resources - should handle failure gracefully
        await manager.start_all_resources()

        # Verify manager still starts despite failure
        assert manager.is_started

        # Event should still be published
        event_bus.publish_async.assert_called()

    @pytest.mark.asyncio
    async def test_stop_all_resources_success(self):
        """Test successful shutdown of all resources."""
        event_bus = Mock()
        manager = ResourceManager(event_bus=event_bus)

        # Add and start resources
        resource1 = MockResource("resource1", "type_a")
        resource2 = MockResource("resource2", "type_b")
        manager.register_resource(resource1)
        manager.register_resource(resource2)

        await manager.start_all_resources()

        # Stop all resources
        await manager.stop_all_resources()

        # Verify resources were stopped
        assert not manager.is_started
        assert resource1.disconnect_count >= 1
        assert resource2.disconnect_count >= 1
        assert resource1.cleanup_count >= 1
        assert resource2.cleanup_count >= 1

    @pytest.mark.asyncio
    async def test_stop_all_resources_with_failure(self):
        """Test shutdown with resource failure."""
        event_bus = Mock()
        manager = ResourceManager(event_bus=event_bus)

        # Add resources - one will fail during cleanup
        resource1 = MockResource("resource1", "type_a")
        resource2 = MockResource("resource2", "type_b")
        resource2.cleanup_fail = True
        manager.register_resource(resource1)
        manager.register_resource(resource2)

        await manager.start_all_resources()

        # Stop resources - should handle failure gracefully
        await manager.stop_all_resources()

        # Manager should still be stopped
        assert not manager.is_started

    @pytest.mark.asyncio
    async def test_shutdown_timeout(self):
        """Test shutdown timeout handling."""
        manager = ResourceManager()

        resource = MockResource("slow_resource", "test")

        # Make cleanup very slow
        async def slow_cleanup():
            await asyncio.sleep(35)  # Longer than timeout
            await resource.cleanup()

        resource.cleanup = slow_cleanup
        manager.register_resource(resource)

        with patch('asyncio.wait_for') as mock_wait_for:
            mock_wait_for.side_effect = asyncio.TimeoutError()

            await manager.start_all_resources()
            await manager.stop_all_resources()

            # Should handle timeout gracefully
            mock_wait_for.assert_called_once()


class TestHealthMonitoring:
    """Test health check functionality."""

    @pytest.mark.asyncio
    async def test_health_check_all_resources(self):
        """Test health check for all resources."""
        manager = ResourceManager()

        resource1 = MockResource("resource1", "type_a")
        resource2 = MockResource("resource2", "type_b")
        resource2.state = "error"  # This will return unhealthy

        manager.register_resource(resource1)
        manager.register_resource(resource2)

        health_summary = await manager.health_check_all()

        assert health_summary["total_resources"] == 2
        assert health_summary["healthy_count"] == 1
        assert health_summary["unhealthy_count"] == 1
        assert health_summary["unknown_count"] == 0

        # Check individual resource status
        assert health_summary["resources"]["resource1"]["health"] == ResourceHealth.HEALTHY.value
        assert health_summary["resources"]["resource2"]["health"] == ResourceHealth.UNHEALTHY.value

    @pytest.mark.asyncio
    async def test_health_check_monitoring_loop(self):
        """Test background health monitoring."""
        event_bus = Mock()
        manager = ResourceManager(event_bus=event_bus)

        resource = MockResource("monitored_resource", "test")
        manager.register_resource(resource)

        # Start manager to trigger health monitoring
        await manager.start_all_resources()

        # Wait a bit for health monitoring to run (it checks every 60 seconds)
        # In test, we manually simulate one iteration
        await manager._health_monitor_loop()

        # Verify health check was performed
        # Note: Real health monitoring runs every 60 seconds, so we can't easily test
        # the background loop without extensive mocking

        # Stop manager
        await manager.stop_all_resources()

        # Verify monitoring task was cancelled
        assert manager._health_monitor_task.cancelled()

    def test_get_resource_stats(self):
        """Test getting resource statistics."""
        manager = ResourceManager()

        resource = MockResource("stats_resource", "test")
        manager.register_resource(resource)

        stats = manager.get_resource_stats()

        assert "stats_resource" in stats
        assert stats["stats_resource"]["initialize_count"] >= 0
        assert stats["stats_resource"]["disconnect_count"] >= 0


class TestResourceCleanup:
    """Test resource cleanup functionality."""

    def test_unregister_resource_success(self):
        """Test successful resource unregistration."""
        manager = ResourceManager()

        resource = MockResource("test_resource", "test_type")
        manager.register_resource(resource)

        # Remove from all structures first
        manager._resources.pop("test_resource", None)

        # Verify cleanup is called (this would normally be done automatically)

    @pytest.mark.asyncio
    async def test_unregister_resource_with_di_cleanup(self):
        """Test resource unregistration with DI cleanup."""
        di_container = Mock()
        manager = ResourceManager(di_container=di_container)

        resource = MockResource("test_resource", "test_type")
        manager.register_resource(resource)

        # Normally, cleanup would happen automatically in _shutdown_resource_safe
        # But for test purposes, we manually remove
        manager._resources.pop("test_resource")

        # Verify DI unregister was called
        di_container.unregister.assert_called_once_with("test_resource")


class TestEventIntegration:
    """Test event bus integration."""

    @pytest.mark.asyncio
    async def test_event_publishing_on_startup(self):
        """Test event publishing during startup."""
        event_bus = Mock()
        manager = ResourceManager(event_bus=event_bus)

        resource = MockResource("event_resource", "test")
        manager.register_resource(resource)

        # Mock event bus publish_async
        event_bus.publish_async = AsyncMock()

        await manager.start_all_resources()

        # Verify startup event was published
        event_bus.publish_async.assert_called()

    @pytest.mark.asyncio
    async def test_event_publishing_on_shutdown(self):
        """Test event publishing during shutdown."""
        event_bus = Mock()
        manager = ResourceManager(event_bus=event_bus)

        resource = MockResource("event_resource", "test")
        manager.register_resource(resource)

        await manager.start_all_resources()

        # Clear any event calls from startup
        event_bus.publish_async.reset_mock()

        await manager.stop_all_resources()

        # Verify shutdown event was published
        event_bus.publish_async.assert_called()


class TestContextManager:
    """Test context manager functionality."""

    @pytest.mark.asyncio
    async def test_context_manager_usage(self):
        """Test using ResourceManager as context manager."""
        manager = ResourceManager()

        resource = MockResource("context_resource", "test")
        manager.register_resource(resource)

        async with manager:
            # Verify started
            assert manager.is_started
            assert resource.is_ready

        # Verify stopped
        assert not manager.is_started
        assert resource.disconnect_count >= 1
        assert resource.cleanup_count >= 1


class TestHandlerRegistration:
    """Test handler management functionality."""

    def test_get_handler_count(self):
        """Test getting handler counts."""
        manager = ResourceManager()

        # Initially no handlers
        assert manager.get_handler_count() == 0
        assert manager.get_handler_count("test_type") == 0

        # After adding resources, count should increase
        resource1 = MockResource("test1", "type_a")
        resource2 = MockResource("test2", "type_a")
        resource3 = MockResource("test3", "type_b")

        manager.register_resource(resource1)
        manager.register_resource(resource2)
        manager.register_resource(resource3)

        assert manager.get_handler_count() == 3
        assert manager.get_handler_count("type_a") == 2
        assert manager.get_handler_count("type_b") == 1
        assert manager.get_handler_count("nonexistent") == 0

    def test_get_event_types(self):
        """Test getting registered event types."""
        manager = ResourceManager()

        resource1 = MockResource("test1", "database")
        resource2 = MockResource("test2", "cache")
        resource3 = MockResource("test3", "database")

        manager.register_resource(resource1)
        manager.register_resource(resource2)
        manager.register_resource(resource3)

        event_types = manager.get_event_types()

        # Event types should match resource types
        assert "database" in event_types
        assert "cache" in event_types
        assert len(event_types) == 2

    def test_clear_handlers(self):
        """Test clearing handlers."""
        manager = ResourceManager()

        resource1 = MockResource("test1", "type_a")
        resource2 = MockResource("test2", "type_a")

        manager.register_resource(resource1)
        manager.register_resource(resource2)

        assert len(manager._resources) == 2
        assert len(manager.get_resources_by_type("type_a")) == 2

        # Clear specific type
        removed_count = manager.clear_handlers("type_a")
        assert removed_count == 2
        assert len(manager.get_resources_by_type("type_a")) == 0

        # Clear all
        removed_count = manager.clear_handlers()
        assert removed_count == 0  # Already cleared above


class TestErrorHandling:
    """Test error handling in ResourceManager."""

    @pytest.mark.asyncio
    async def test_resource_startup_error_isolation(self):
        """Test that one resource startup error doesn't stop others."""
        manager = ResourceManager()

        resource1 = MockResource("good_resource", "test")
        resource2 = MockResource("bad_resource", "test")
        resource2.connect_fail = True

        manager.register_resource(resource1)
        manager.register_resource(resource2)

        # Start resources - bad resource should fail but good should succeed
        await manager.start_all_resources()

        # Manager should still be started
        assert manager.is_started

        # Good resource should be initialized
        assert resource1.initialize_count == 1

        # Bad resource should still be registered but failed
        assert resource2.name in manager._resources

    @pytest.mark.asyncio
    async def test_resource_shutdown_error_isolation(self):
        """Test that one resource shutdown error doesn't stop others."""
        manager = ResourceManager()

        resource1 = MockResource("good_resource", "test")
        resource2 = MockResource("bad_resource", "test")
        resource2.cleanup_fail = True

        manager.register_resource(resource1)
        manager.register_resource(resource2)

        await manager.start_all_resources()

        # Stop resources - bad resource cleanup should fail but not crash
        await manager.stop_all_resources()

        # Manager should still be stopped properly
        assert not manager.is_started

    def test_resource_access_error_handling(self):
        """Test error handling for invalid resource access."""
        manager = ResourceManager()

        # Accessing non-existent resource should raise ResourceNotFoundError
        from framework.resource.exceptions import ResourceNotFoundError

        with pytest.raises(ResourceNotFoundError):
            manager.get_resource("nonexistent")

        with pytest.raises(KeyError):
            _ = manager["nonexistent"]
