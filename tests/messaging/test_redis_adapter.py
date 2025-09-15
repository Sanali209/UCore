import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from redis.exceptions import ConnectionError, TimeoutError

from framework.messaging.redis_adapter import RedisAdapter
from framework.messaging.redis_event_bridge import EventBusRedisBridge, EventBusToRedisBridge, RedisToEventBusBridge


class TestRedisAdapterInitialization:
    """Test RedisAdapter initialization and configuration."""

    def test_init_default_config(self):
        """Test initialization with default configuration fallback."""
        app = Mock()

        # Mock config registration to fail
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        assert adapter.app == app
        assert adapter.redis is None
        assert adapter.subscribers == {}
        assert adapter.channels == {}
        assert adapter.stream_consumers == {}
        assert adapter.bridge_handlers == {}
        assert adapter.redis_listeners == {}
        assert 'REDIS_HOST' in adapter.config
        assert adapter.config['REDIS_HOST'] == 'localhost'

    def test_init_with_config(self):
        """Test initialization with configuration service."""
        app = Mock()
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: {
            'REDIS_HOST': 'redis.example.com',
            'REDIS_PORT': 6380,
            'REDIS_DB': 1,
            'REDIS_PASSWORD': 'secret'
        }.get(key, default)

        app.container.get.return_value = mock_config

        adapter = RedisAdapter(app)

        assert adapter.config.get('REDIS_HOST') == 'redis.example.com'
        assert adapter.config.get('REDIS_PORT') == 6380
        assert adapter.bridge_channels['app_started'] == 'ucore.events.app.started'

    def test_bridge_settings_loading(self):
        """Test loading bridge settings from configuration."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        # Should have default bridge settings
        assert adapter.bridge_settings['eventbus_to_redis_enabled'] is True
        assert adapter.bridge_settings['redis_to_eventbus_enabled'] is True
        assert adapter.bridge_settings['max_retries'] == 3
        assert 'instance_id' in adapter.bridge_settings

    def test_component_inheritance(self):
        """Test that RedisAdapter properly inherits from required classes."""
        from framework.core.component import Component

        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        assert isinstance(adapter, Component)
        assert isinstance(adapter, EventBusRedisBridge)
        assert isinstance(adapter, EventBusToRedisBridge)
        assert isinstance(adapter, RedisToEventBusBridge)


class TestRedisAdapterLifecycle:
    """Test RedisAdapter start/stop lifecycle."""

    @patch('framework.messaging.redis_adapter.aioredis.Redis')
    async def test_start_success_with_config(self, mock_redis_class):
        """Test successful Redis connection with custom configuration."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default: {
            'REDIS_HOST': 'test.redis.com',
            'REDIS_PORT': 6380,
            'REDIS_DB': 1,
            'REDIS_PASSWORD': 'secret'
        }.get(key, default)

        mock_redis_instance = AsyncMock()
        mock_redis_instance.ping = AsyncMock()
        mock_redis_class.return_value = mock_redis_instance

        app.container.get.return_value = mock_config

        adapter = RedisAdapter(app)

        with patch('asyncio.create_task'):
            await adapter.start()

            mock_redis_class.assert_called_once_with(
                host='test.redis.com',
                port=6380,
                db=1,
                password='secret',
                decode_responses=True
            )
            mock_redis_instance.ping.assert_called_once()
            logger.info.assert_any_call("Redis EventBus Bridge enabled: E2R=True, R2E=True, Instance ID: *")

    @patch('framework.messaging.redis_adapter.aioredis.Redis')
    async def test_start_with_connection_failure(self, mock_redis_class):
        """Test start with Redis connection failure."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        app.container.get.side_effect = Exception("Config not found")
        mock_redis_class.return_value = None  # Simulate connection failure

        adapter = RedisAdapter(app)

        await adapter.start()

        logger.error.assert_called()
        assert adapter.redis is None  # Should be None on failure

    async def test_stop_success(self):
        """Test successful shutdown."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.close = AsyncMock()

        # Mock some tasks
        adapter.channels['channel1'] = Mock()
        adapter.channels['channel1'].cancel = Mock()
        adapter.stream_consumers['stream1'] = Mock()
        adapter.stream_consumers['stream1'].cancel = Mock()

        await adapter.stop()

        adapter.redis.close.assert_called_once()
        logger.info.assert_called_with("Redis connection closed")


class TestRedisAdapterPubSubOperations:
    """Test RedisAdapter pub/sub functionality."""

    def test_subscribe_decorator(self):
        """Test subscribe decorator registration."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        @adapter.subscribe('test_channel')
        def test_handler(message):
            pass

        assert 'test_channel' in adapter.subscribers
        assert adapter.subscribers['test_channel'] == test_handler

    async def test_publish_success(self):
        """Test successful message publishing."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.publish = AsyncMock()

        result = await adapter.publish('test_channel', {'message': 'test'})

        assert result is True
        adapter.redis.publish.assert_called_once_with('test_channel', '{"message": "test"}')

    async def test_publish_failure(self):
        """Test publish failure."""
        app = Mock()
        logger = Mock()
        app.logger = logger
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.publish.side_effect = Exception("Publish failed")

        result = await adapter.publish('test_channel', 'test message')

        assert result is False
        logger.error.assert_called()

    async def test_publish_without_redis_connection(self):
        """Test publish without Redis connection."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = None  # No connection

        with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.publish('test_channel', 'message')

    async def test_subscribe_channel_processing(self):
        """Test channel subscription and message processing."""
        app = Mock()
        logger = Mock()
        app.logger = logger
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()

        # Mock pubsub
        mock_pubsub = AsyncMock()
        adapter.redis.pubsub.return_value = mock_pubsub

        async def mock_callback(message_data):
            pass

        # Simulate message processing
        mock_message = {
            'type': 'message',
            'data': '{"test": "value"}'
        }

        mock_pubsub.listen = Mock()
        mock_pubsub.listen.__aiter__ = Mock()
        mock_pubsub.listen.__anext__ = AsyncMock(side_effect=[mock_message, StopAsyncIteration])

        # Call the subscription method directly
        with patch('asyncio.create_task') as mock_create_task:
            await adapter._subscribe_channel('test_channel', mock_callback)
            mock_pubsub.subscribe.assert_called_with('test_channel')

    async def test_subscribe_channel_json_error_handling(self):
        """Test channel subscription with JSON parsing error."""
        app = Mock()
        logger = Mock()
        app.logger = logger
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()

        # Mock pubsub
        mock_pubsub = AsyncMock()
        adapter.redis.pubsub.return_value = mock_pubsub

        async def mock_callback(message_data):
            pass

        # Simulate message with invalid JSON
        mock_message = {
            'type': 'message',
            'data': '{invalid json}'
        }

        mock_pubsub.listen = Mock()
        mock_pubsub.listen.__aiter__ = Mock()
        mock_pubsub.listen.__anext__ = AsyncMock(side_effect=[mock_message, StopAsyncIteration])

        await adapter._subscribe_channel('test_channel', mock_callback)

        # Should handle JSON error gracefully


class TestRedisAdapterStreamOperations:
    """Test RedisAdapter stream operations."""

    def test_subscribe_stream_decorator(self):
        """Test stream subscription decorator."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        @adapter.subscribe('stream:test_stream')
        def stream_handler(message_id, message_data):
            pass

        assert 'stream:test_stream' in adapter.subscribers
        assert adapter.subscribers['stream:test_stream'] == stream_handler

    async def test_publish_to_stream_success(self):
        """Test successful publishing to stream."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.xadd = AsyncMock(return_value='123456789-0')

        result = await adapter.publish_to_stream('test_stream', {'field': 'value'})

        assert result == '123456789-0'
        adapter.redis.xadd.assert_called_once_with('test_stream', {'field': 'value'})

    async def test_publish_to_stream_with_max_length(self):
        """Test publishing to stream with max length."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.xadd = AsyncMock(return_value='123456789-1')

        result = await adapter.publish_to_stream('test_stream', {'field': 'value'}, max_length=100)

        assert result == '123456789-1'
        adapter.redis.xadd.assert_called_once_with('test_stream', {'field': 'value'}, maxlen=100)

    async def test_publish_to_stream_without_redis(self):
        """Test publishing to stream without Redis connection."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = None

        with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.publish_to_stream('test_stream', {'field': 'value'})


class TestRedisAdapterUtilityOperations:
    """Test RedisAdapter utility operations (get, set, delete)."""

    async def test_get_success(self):
        """Test successful get operation."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.get = AsyncMock(return_value='{"key": "value"}')

        result = await adapter.get('test_key')

        assert result == {"key": "value"}
        adapter.redis.get.assert_called_with('test_key')

    async def test_get_string_value(self):
        """Test get operation with plain string value."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.get = AsyncMock(return_value='plain_string_value')

        result = await adapter.get('test_key')

        assert result == 'plain_string_value'

    async def test_get_nonexistent_key(self):
        """Test get operation for non-existent key."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.get = AsyncMock(return_value=None)

        result = await adapter.get('nonexistent_key', 'default_value')

        assert result == 'default_value'

    async def test_set_success(self):
        """Test successful set operation."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.set = AsyncMock(return_value=True)

        result = await adapter.set('test_key', {'data': 'value'})

        assert result is True
        adapter.redis.set.assert_called_with('test_key', '{"data": "value"}')

    async def test_set_with_ttl(self):
        """Test set operation with TTL (time-to-live)."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.setex = AsyncMock(return_value=True)

        result = await adapter.set('test_key', 'test_value', ttl=300)

        assert result is True
        adapter.redis.setex.assert_called_with('test_key', 300, 'test_value')

    async def test_set_failure(self):
        """Test set operation failure."""
        app = Mock()
        logger = Mock()
        app.logger = logger
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.set.side_effect = Exception("Set failed")

        result = await adapter.set('test_key', 'test_value')

        assert result is False
        logger.error.assert_called()

    async def test_set_without_redis_connection(self):
        """Test set without Redis connection."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = None  # No connection

        with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.set('test_key', 'value')

    async def test_delete_success(self):
        """Test successful delete operation."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.delete = AsyncMock(return_value=2)  # 2 keys deleted

        result = await adapter.delete('key1', 'key2', 'key3')

        assert result == 2
        adapter.redis.delete.assert_called_with('key1', 'key2', 'key3')

    async def test_delete_without_redis_connection(self):
        """Test delete without Redis connection."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = None  # No connection

        with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.delete('key1', 'key2')

    async def test_get_without_redis_connection(self):
        """Test get without Redis connection."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)
        adapter.redis = None  # No connection

        with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.get('test_key')


class TestRedisAdapterClientIPExtraction:
    """Test client IP extraction functionality."""

    def test_get_client_ip_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        mock_request = Mock()
        mock_request.headers = {'X-Forwarded-For': '192.168.1.100, 10.0.0.1'}

        result = adapter.get_client_ip(mock_request)

        assert result == '192.168.1.100'

    def test_get_client_ip_x_real_ip(self):
        """Test IP extraction from X-Real-IP header."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        mock_request = Mock()
        mock_request.headers = {'X-Real-IP': '192.168.1.200'}

        result = adapter.get_client_ip(mock_request)

        assert result == '192.168.1.200'

    def test_get_client_ip_cf_connecting_ip(self):
        """Test IP extraction from Cloudflare header."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        mock_request = Mock()
        mock_request.headers = {'CF-Connecting-IP': '192.168.2.100'}

        result = adapter.get_client_ip(mock_request)

        assert result == '192.168.2.100'

    def test_get_client_ip_multiple_headers(self):
        """Test IP extraction when multiple headers are present."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        mock_request = Mock()
        mock_request.headers = {
            'X-Forwarded-For': '192.168.1.100, 10.0.0.1',
            'X-Real-IP': '192.168.1.200',
            'CF-Connecting-IP': '192.168.2.100'
        }

        # Should use X-Forwarded-For as it appears first in the order
        result = adapter.get_client_ip(mock_request)

        assert result == '192.168.1.100'

    def test_get_client_ip_fallback_to_remote(self):
        """Test IP fallback to remote address."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        mock_request = Mock()
        mock_request.headers = {}
        mock_request.remote = '10.0.0.5'

        result = adapter.get_client_ip(mock_request)

        assert result == '10.0.0.5'

    def test_get_client_ip_no_headers_no_remote(self):
        """Test IP extraction when no headers and no remote address."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        mock_request = Mock()
        mock_request.headers = {}
        mock_request.remote = None

        result = adapter.get_client_ip(mock_request)

        assert result == 'unknown'

    def test_get_client_ip_empty_x_forwarded_for(self):
        """Test IP extraction from empty X-Forwarded-For header."""
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

        adapter = RedisAdapter(app)

        mock_request = Mock()
        mock_request.headers = {'X-Forwarded-For': ''}

        result = adapter.get_client_ip(mock_request)

        assert result == ''
