"""
Integration Tests for Redis Adapter EventBus Bridge
Tests bidirectional communication between EventBus and Redis.
"""
import unittest
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock

# Add framework to path
sys.path.insert(0, os.path.abspath('.'))

from framework.app import App
from framework.messaging.events import AppStartedEvent, ComponentStartedEvent, UserEvent
from framework.messaging.redis_adapter import RedisAdapter


class TestRedisEventBusIntegration(unittest.TestCase):
    """Integration tests for Redis Adapter EventBus bridge functionality."""

    def setUp(self):
        """Set up test app with RedisAdapter."""
        self.app = App("BridgeTest")

        # Create RedisAdapter with bridge capabilities
        self.redis_adapter = RedisAdapter(self.app)
        self.app.register_component(self.redis_adapter)

        # Bootstrap app to set up dependencies
        import argparse
        args = argparse.Namespace()
        args.config = None
        args.log_level = "WARNING"  # Reduce log noise in tests
        args.plugins_dir = None
        self.app.bootstrap(args)

        # Disable actual Redis connections for unit tests
        self.redis_adapter.redis = MagicMock()

        # Track bridge events and messages
        self.bridge_events_received = []
        self.redis_messages_received = []

    def test_bridge_configuration(self):
        """Test that bridge configuration is properly loaded."""
        self.assertTrue(self.redis_adapter.bridge_settings)
        self.assertIn('eventbus_to_redis_enabled', self.redis_adapter.bridge_settings)
        self.assertIn('redis_to_eventbus_enabled', self.redis_adapter.bridge_settings)
        self.assertIn('instance_id', self.redis_adapter.bridge_settings)

        # Test instance ID is generated
        instance_id = self.redis_adapter.bridge_settings['instance_id']
        self.assertTrue(len(instance_id) > 0)
        self.assertEqual(len(instance_id), 8)  # Should be 8 characters

    def test_bridge_channels_configuration(self):
        """Test that bridge channels are properly configured."""
        self.assertIn('app_started', self.redis_adapter.bridge_channels)
        self.assertIn('component_started', self.redis_adapter.bridge_channels)
        self.assertIn('config_updated', self.redis_adapter.bridge_channels)

        # Verify channel naming convention
        for channel_type, channel_name in self.redis_adapter.bridge_channels.items():
            self.assertTrue(channel_name.startswith('ucore.events'))

    def test_message_format_creation(self):
        """Test standardized message format creation."""
        test_event = AppStartedEvent(app_name="TestApp", component_count=5)

        message = self.redis_adapter._create_bridge_message(test_event)

        self.assertEqual(message['event_type'], 'AppStartedEvent')
        self.assertEqual(message['event_bus_source'], 'ucore_framework')
        self.assertIn('instance_id', message)
        self.assertIn('timestamp', message)
        self.assertEqual(message['data']['app_name'], 'TestApp')
        self.assertEqual(message['data']['component_count'], 5)

    def test_bridge_enable_disable(self):
        """Test bridge enable/disable functionality."""
        # Initially enabled
        self.assertTrue(self.redis_adapter.bridge_settings['eventbus_to_redis_enabled'])
        self.assertTrue(self.redis_adapter.bridge_settings['redis_to_eventbus_enabled'])

        # Test disable
        self.redis_adapter.disable_bridge('both')
        self.assertFalse(self.redis_adapter.bridge_settings['eventbus_to_redis_enabled'])
        self.assertFalse(self.redis_adapter.bridge_settings['redis_to_eventbus_enabled'])

        # Test enable
        self.redis_adapter.enable_bridge('eventbus_to_redis')
        self.assertTrue(self.redis_adapter.bridge_settings['eventbus_to_redis_enabled'])
        self.assertFalse(self.redis_adapter.bridge_settings['redis_to_eventbus_enabled'])

    def test_bridge_statistics(self):
        """Test bridge statistics tracking."""
        stats = self.redis_adapter.get_bridge_stats()

        self.assertIn('events_forwarded_eventbus_to_redis', stats)
        self.assertIn('messages_forwarded_redis_to_eventbus', stats)
        self.assertIn('errors_eventbus_to_redis', stats)
        self.assertIn('errors_redis_to_eventbus', stats)

        # All should be 0 initially
        for key, value in stats.items():
            self.assertEqual(value, 0)

        # Test reset
        self.redis_adapter.reset_bridge_stats()
        stats_after = self.redis_adapter.get_bridge_stats()
        self.assertEqual(stats, stats_after)

    def test_event_forwarder_registration(self):
        """Test registration of event forwarders."""
        # Mock EventBus
        mock_event_bus = MagicMock()
        with patch.object(self.redis_adapter.app.container, 'get', return_value=mock_event_bus):
            # Register forwarder
            self.redis_adapter.register_event_forwarder(
                event_type=UserEvent,
                redis_channel='test.channel'
            )

            # Should be stored for future registration
            self.assertIn('user_event', self.redis_adapter.event_forwarders)

    def test_redis_listener_registration(self):
        """Test registration of Redis listeners."""
        # Register listener
        self.redis_adapter.register_redis_listener(
            redis_channel='external.events'
        )

        # Should be stored for Redis subscription
        self.assertIn('external.events', self.redis_adapter.redis_listeners)

    @patch('asyncio.create_task')
    def test_publish_bridge_message(self, mock_create_task):
        """Test publishing bridge message to Redis."""
        # Mock the publish method
        self.redis_adapter.publish = MagicMock(return_value=True)

        test_event = UserEvent(event_type="test", payload={"data": "value"})

        # Mock the bridge message creation
        with patch.object(self.redis_adapter, '_create_bridge_message') as mock_create:
            mock_create.return_value = {"event_type": "test", "data": {"key": "value"}}

            # Register and trigger forwarder (would normally happen in start())
            forwarder = self.redis_adapter.register_event_forwarder(
                event_type=UserEvent,
                redis_channel='test.channel'
            )

            # Simulate calling the forwarder
            self.redis_adapter.event_forwarders['user_event'](test_event)

            # Should have called publish if EventBus was available
            # Note: In actual usage, this would require proper EventBus registration

    def test_partial_bridge_setup(self):
        """Test that bridge can be partially configured."""
        # Test specific direction enabling
        self.redis_adapter.enable_bridge('eventbus_to_redis')
        self.assertTrue(self.redis_adapter.bridge_settings['eventbus_to_redis_enabled'])
        self.assertFalse(self.redis_adapter.bridge_settings['redis_to_eventbus_enabled'])

        # Test specific direction disabling
        self.redis_adapter.disable_bridge('eventbus_to_redis')
        self.assertFalse(self.redis_adapter.bridge_settings['eventbus_to_redis_enabled'])
        self.assertFalse(self.redis_adapter.bridge_settings['redis_to_eventbus_enabled'])

    def test_bridge_with_error_handling(self):
        """Test bridge handles errors gracefully."""
        # Test with failed publish (publish returns False)
        self.redis_adapter.publish = MagicMock(return_value=False)

        test_event = UserEvent(event_type="error_test")

        # Create message and try to publish (should not crash)
        message = self.redis_adapter._create_bridge_message(test_event)

        # Should return a valid message even with error
        self.assertIsInstance(message, dict)
        self.assertIn('event_type', message)

        # Should not raise exceptions when bridge methods are called on failed state
        self.redis_adapter.disable_bridge('both')
        self.redis_adapter.enable_bridge('both')

        # All should work without crashes
        self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()
