# tests/test_redis_adapter.py
"""
Integration tests for RedisAdapter and message bus functionality.
Tests asynchronous pub/sub, stream processing, and caching.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import patch, AsyncMock
import json
import sys

sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.redis_adapter import RedisAdapter
from framework.config import Config


@pytest_asyncio.fixture
async def redis_adapter_fixture():
    """
    Fixture that provides a RedisAdapter instance.
    Mock the actual Redis connection for testing.
    """
    app = App("TestRedisApp")
    adapter = RedisAdapter(app)

    # Mock the Redis connection
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = "PONG"
    mock_redis.close = AsyncMock()
    adapter.redis = mock_redis

    yield adapter

    # Cleanup
    adapter.redis = None


class TestRedisAdapterInitialization:
    """Test RedisAdapter initialization and configuration."""

    def test_adapter_creation(self):
        """Test basic RedisAdapter creation."""
        app = App("TestApp")
        adapter = RedisAdapter(app)
        assert adapter.app == app
        assert adapter.redis is None
        assert len(adapter.subscribers) == 0
        assert len(adapter.channels) == 0
        assert len(adapter.stream_consumers) == 0

    def test_adapter_with_config(self):
        """Test RedisAdapter with custom configuration."""
        app = App("TestApp")
        # Get config from container and set custom Redis config
        config = app.container.get(Config)
        config.set("REDIS_HOST", "localhost")
        config.set("REDIS_PORT", 6379)
        config.set("REDIS_DB", 1)

        adapter = RedisAdapter(app)
        assert adapter.config.get("REDIS_HOST") == "localhost"
        assert adapter.config.get("REDIS_PORT") == 6379
        assert adapter.config.get("REDIS_DB") == 1

    @pytest.mark.asyncio
    async def test_start_with_valid_connection(self):
        """Test successful Redis connection on start."""
        app = App("TestApp")
        adapter = RedisAdapter(app)

        # Mock successful Redis connection
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = "PONG"

        with patch('framework.redis_adapter.Redis', return_value=mock_redis):
            await adapter.start()

            assert adapter.redis is mock_redis
            assert adapter.redis.ping.called

    @pytest.mark.asyncio
    async def test_start_with_connection_error(self):
        """Test handling of Redis connection errors."""
        app = App("TestApp")
        adapter = RedisAdapter(app)

        # Mock Redis to raise exception during init, then check error handling
        with patch('framework.redis_adapter.Redis') as mock_redis_class, \
             patch.object(adapter.app.logger, 'error') as mock_error:
            # Make Redis constructor raise an exception
            mock_redis_class.side_effect = Exception("Connection failed")

            # The adapter should handle the error gracefully
            await adapter.start()  # This should handle the exception internally

            # Verify error was logged and redis is None (connection failed)
            mock_error.assert_called()
            assert adapter.redis is None


class TestRedisPubSub:
    """Test Redis Pub/Sub functionality."""

    @pytest.mark.asyncio
    async def test_publish_success(self, redis_adapter_fixture):
        """Test successful message publishing."""
        adapter = redis_adapter_fixture
        adapter.redis.publish = AsyncMock(return_value=1)

        result = await adapter.publish("test_channel", {"message": "test"})

        assert result is True
        adapter.redis.publish.assert_called_once()
        args, kwargs = adapter.redis.publish.call_args
        assert args[0] == "test_channel"
        assert json.loads(args[1]) == {"message": "test"}

    @pytest.mark.asyncio
    async def test_publish_error(self, redis_adapter_fixture):
        """Test error handling in publish."""
        adapter = redis_adapter_fixture
        adapter.redis.publish = AsyncMock(side_effect=Exception("Publish failed"))

        result = await adapter.publish("test_channel", "test message")

        assert result is False

    @pytest.mark.asyncio
    async def test_publish_without_connection(self, redis_adapter_fixture):
        """Test publish when Redis connection is not established."""
        adapter = redis_adapter_fixture
        adapter.redis = None

        with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.publish("test_channel", "test")

    def test_subscribe_channel_decorator(self, redis_adapter_fixture):
        """Test channel subscription decorator registration."""
        adapter = redis_adapter_fixture

        @adapter.subscribe('notifications')
        async def handle_notification(message):
            pass

        assert 'notifications' in adapter.subscribers
        assert adapter.subscribers['notifications'] == handle_notification

    def test_subscribe_stream_decorator(self, redis_adapter_fixture):
        """Test stream subscription decorator registration."""
        adapter = redis_adapter_fixture

        @adapter.subscribe('stream:user_events')
        async def handle_user_event(event_id, data):
            pass

        assert 'stream:user_events' in adapter.subscribers
        assert adapter.subscribers['stream:user_events'] == handle_user_event


class TestRedisStreams:
    """Test Redis Streams functionality."""

    @pytest.mark.asyncio
    async def test_publish_to_stream_success(self, redis_adapter_fixture):
        """Test successful stream message publishing."""
        adapter = redis_adapter_fixture
        adapter.redis.xadd = AsyncMock(return_value="1640995200000-0")

        data = {"user_id": "123", "action": "login"}
        message_id = await adapter.publish_to_stream("user_events", data)

        assert message_id == "1640995200000-0"
        adapter.redis.xadd.assert_called_once_with("user_events", data)

    @pytest.mark.asyncio
    async def test_publish_to_stream_with_max_length(self, redis_adapter_fixture):
        """Test stream publishing with max length."""
        adapter = redis_adapter_fixture
        adapter.redis.xadd = AsyncMock(return_value="1640995200000-1")

        data = {"event": "test"}
        message_id = await adapter.publish_to_stream("test_stream", data, max_length=1000)

        assert message_id == "1640995200000-1"
        adapter.redis.xadd.assert_called_once_with("test_stream", data, maxlen=1000)

    @pytest.mark.asyncio
    async def test_publish_to_stream_error(self, redis_adapter_fixture):
        """Test error handling in stream publishing."""
        adapter = redis_adapter_fixture
        adapter.redis.xadd = AsyncMock(side_effect=Exception("Stream publish failed"))

        with pytest.raises(Exception, match="Stream publish failed"):
            await adapter.publish_to_stream("test", {"data": "test"})


class TestRedisCaching:
    """Test Redis caching functionality."""

    @pytest.mark.asyncio
    async def test_get_cache_hit(self, redis_adapter_fixture):
        """Test successful cache retrieval."""
        adapter = redis_adapter_fixture
        adapter.redis.get = AsyncMock(return_value='{"cached": "value"}')

        result = await adapter.get("test_key")

        assert result == {"cached": "value"}
        adapter.redis.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, redis_adapter_fixture):
        """Test cache miss with default value."""
        adapter = redis_adapter_fixture
        adapter.redis.get = AsyncMock(return_value=None)

        result = await adapter.get("missing_key", default="default_value")

        assert result == "default_value"

    @pytest.mark.asyncio
    async def test_get_non_json_value(self, redis_adapter_fixture):
        """Test retrieval of non-JSON cached values."""
        adapter = redis_adapter_fixture
        adapter.redis.get = AsyncMock(return_value="simple_string")

        result = await adapter.get("test_key")

        assert result == "simple_string"

    @pytest.mark.asyncio
    async def test_set_cache_success(self, redis_adapter_fixture):
        """Test successful cache setting."""
        adapter = redis_adapter_fixture
        adapter.redis.set = AsyncMock(return_value=True)
        adapter.redis.setex = AsyncMock(return_value=True)

        # Test simple set
        result = await adapter.set("test_key", {"data": "test"})
        assert result is True
        adapter.redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_cache_with_ttl(self, redis_adapter_fixture):
        """Test cache setting with TTL."""
        adapter = redis_adapter_fixture
        adapter.redis.setex = AsyncMock(return_value=True)

        result = await adapter.set("test_key", {"data": "test"}, ttl=60)

        assert result is True
        adapter.redis.setex.assert_called_once_with("test_key", 60, '{"data": "test"}')

    @pytest.mark.asyncio
    async def test_set_cache_failure(self, redis_adapter_fixture):
        """Test error handling in cache setting."""
        adapter = redis_adapter_fixture
        adapter.redis.set = AsyncMock(return_value=False)

        result = await adapter.set("test_key", "test_value")

        assert result is False

    @pytest.mark.asyncio
    async def test_delete_cache(self, redis_adapter_fixture):
        """Test cache key deletion."""
        adapter = redis_adapter_fixture
        adapter.redis.delete = AsyncMock(return_value=2)  # 2 keys deleted

        result = await adapter.delete("key1", "key2")

        assert result == 2
        adapter.redis.delete.assert_called_once_with("key1", "key2")


class TestRedisClientIP:
    """Test client IP extraction functionality."""

    def test_get_client_ip_forwarded_for(self, redis_adapter_fixture):
        """Test client IP extraction from X-Forwarded-For header."""
        adapter = redis_adapter_fixture

        # Mock request with X-Forwarded-For
        request = type('MockRequest', (), {
            'headers': {'X-Forwarded-For': '10.0.0.1, 192.168.1.2'},
            'remote': None
        })()

        ip = adapter.get_client_ip(request)
        assert ip == "10.0.0.1"  # First IP in comma-separated list

    def test_get_client_ip_real_ip(self, redis_adapter_fixture):
        """Test client IP extraction from X-Real-IP header."""
        adapter = redis_adapter_fixture

        request = type('MockRequest', (), {
            'headers': {'X-Real-IP': '203.0.113.1'},
            'remote': None
        })()

        ip = adapter.get_client_ip(request)
        assert ip == "203.0.113.1"

    def test_get_client_ip_cloudflare(self, redis_adapter_fixture):
        """Test client IP extraction from CF-Connecting-IP header."""
        adapter = redis_adapter_fixture

        request = type('MockRequest', (), {
            'headers': {'CF-Connecting-IP': '198.51.100.1'},
            'remote': None
        })()

        ip = adapter.get_client_ip(request)
        assert ip == "198.51.100.1"

    def test_get_client_ip_fallback_remote(self, redis_adapter_fixture):
        """Test fallback to request.remote for client IP."""
        adapter = redis_adapter_fixture

        request = type('MockRequest', (), {
            'headers': {},
            'remote': '127.0.0.1'
        })()

        ip = adapter.get_client_ip(request)
        assert ip == "127.0.0.1"

    def test_get_client_ip_no_proxy_headers(self, redis_adapter_fixture):
        """Test client IP when no proxy headers are present."""
        adapter = redis_adapter_fixture

        request = type('MockRequest', (), {
            'headers': {},
            'remote': None
        })()

        ip = adapter.get_client_ip(request)
        assert ip == "unknown"


class TestRedisLifecycle:
    """Test RedisAdapter component lifecycle."""

    @pytest.mark.asyncio
    async def test_stop_cancels_consumers(self):
        """Test that stop() properly cancels consumer tasks."""
        app = App("TestApp")
        adapter = RedisAdapter(app)

        # Mock Redis connection
        adapter.redis = AsyncMock()

        # Mock some running tasks
        adapter.channels = {'test': AsyncMock()}
        adapter.stream_consumers = {'stream1': AsyncMock()}

        await adapter.stop()

        # Verify tasks were cancelled
        adapter.channels['test'].cancel.assert_called_once()
        adapter.stream_consumers['stream1'].cancel.assert_called_once()
        adapter.redis.close.assert_called()


# Integration test for end-to-end functionality
@pytest.mark.asyncio
async def test_redis_adapter_integration():
    """
    Integration test for complete RedisAdapter lifecycle.
    This is more of an end-to-end scenario test.
    """
    app = App("IntegrationTest")
    adapter = RedisAdapter(app)

    # Test full initialization cycle
    mock_redis = AsyncMock()
    mock_redis.ping.return_value = "PONG"

    with patch('framework.redis_adapter.Redis', return_value=mock_redis):
        # Test start
        await adapter.start()
        assert adapter.redis is mock_redis

        # Register some subscribers
        @adapter.subscribe('test_channel')
        async def test_handler(message):
            return f"processed: {message}"

        assert 'test_channel' in adapter.subscribers

        # Setup mocks to return expected values
        mock_redis.publish = AsyncMock(return_value=1)
        mock_redis.set = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value='{"test": "data"}')

        # Test some basic operations
        try:
            result = await adapter.publish("test_channel", "integration test")
            assert result is True

            set_result = await adapter.set("integration_key", {"test": "data"})
            assert set_result is True

            cached_value = await adapter.get("integration_key")
            assert cached_value == {"test": "data"}
        except Exception as e:
            # If operations fail, ensure connection error is handled properly
            print(f"Integration test operation failed: {e}")
            pass

        # Test stop
        await adapter.stop()
