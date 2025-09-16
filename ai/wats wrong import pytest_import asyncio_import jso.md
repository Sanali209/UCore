<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# wats wrong import pytest

import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch, MagicMock, call
from redis.exceptions import ConnectionError, TimeoutError

import sys

# Patch Redis for all tests using a function-scoped autouse fixture

@pytest.fixture(autouse=True)
def patch_redis(monkeypatch):
    from unittest.mock import MagicMock
    monkeypatch.setattr("framework.messaging.redis_adapter.Redis", MagicMock())
    monkeypatch.setattr("redis.asyncio.Redis", MagicMock())

from framework.messaging.redis_event_bridge import EventBusRedisBridge, EventBusToRedisBridge, RedisToEventBusBridge

class TestRedisAdapterInitialization:
    """Test RedisAdapter initialization and configuration."""

def test_init_default_config(self):
        """Test initialization with default configuration fallback."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()

\# Mock config registration to fail
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
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        mock_config = Mock()
        mock_config.get.side_effect = lambda key, default=None: {
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
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

\# Should have default bridge settings
        assert adapter.bridge_settings['eventbus_to_redis_enabled'] is True
        assert adapter.bridge_settings['redis_to_eventbus_enabled'] is True
        assert adapter.bridge_settings['max_retries'] == 3
        assert 'instance_id' in adapter.bridge_settings

def test_component_inheritance(self):
        """Test that RedisAdapter properly inherits from required classes."""
        from framework.core.component import Component
        from framework.messaging.redis_adapter import RedisAdapter

app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

assert isinstance(adapter, Component)
        assert isinstance(adapter, EventBusRedisBridge)
        assert isinstance(adapter, EventBusToRedisBridge)
        assert isinstance(adapter, RedisToEventBusBridge)

class TestRedisAdapterLifecycle:
    """Test RedisAdapter start/stop lifecycle."""

@pytest.mark.asyncio
    @patch('framework.messaging.redis_adapter.Redis')
    async def test_start_success_with_config(self, mock_redis_class):
        """Test successful Redis connection with custom configuration."""
        from framework.messaging.redis_adapter import RedisAdapter
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

@pytest.mark.asyncio
    @patch('redis.asyncio.Redis')
    async def test_start_with_connection_failure(self, mock_redis_class):
        """Test start with Redis connection failure."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        logger = Mock()
        app.logger = logger

app.container.get.side_effect = Exception("Config not found")
        mock_redis_class.return_value = None  \# Simulate connection failure

adapter = RedisAdapter(app)

await adapter.start()

logger.error.assert_called()
        assert adapter.redis is None  \# Should be None on failure

@pytest.mark.asyncio
    async def test_stop_success(self):
        """Test successful shutdown."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        logger = Mock()
        app.logger = logger

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.close = AsyncMock()

\# Mock some tasks
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
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

@adapter.subscribe('test_channel')
        def test_handler(message):
            pass

assert 'test_channel' in adapter.subscribers
        assert adapter.subscribers['test_channel'] == test_handler

@pytest.mark.asyncio
    async def test_publish_success(self):
        """Test successful message publishing."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.publish = AsyncMock()

result = await adapter.publish('test_channel', {'message': 'test'})

assert result is True
        adapter.redis.publish.assert_called_once_with('test_channel', '{"message": "test"}')

@pytest.mark.asyncio
    async def test_publish_failure(self):
        """Test publish failure."""
        from framework.messaging.redis_adapter import RedisAdapter
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

@pytest.mark.asyncio
    async def test_publish_without_redis_connection(self):
        """Test publish without Redis connection."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = None  \# No connection

with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.publish('test_channel', 'message')

@pytest.mark.asyncio
    async def test_subscribe_channel_processing(self):
        """Test channel subscription and message processing."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        logger = Mock()
        app.logger = logger
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()

\# Mock pubsub
        mock_pubsub = AsyncMock()
        adapter.redis.pubsub.return_value = mock_pubsub

async def mock_callback(message_data):
            pass

\# Simulate message processing
        mock_message = {
            'type': 'message',
            'data': '{"test": "value"}'
        }

async def async_listen():
            yield mock_message

mock_pubsub.listen = async_listen
        mock_pubsub.subscribe = AsyncMock()

\# Call the subscription method directly
        with patch('asyncio.create_task'):
            await adapter._subscribe_channel('test_channel', mock_callback)
            mock_pubsub.subscribe.assert_called_with('test_channel')

@pytest.mark.asyncio
    async def test_subscribe_channel_json_error_handling(self):
        """Test channel subscription with JSON parsing error."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        logger = Mock()
        app.logger = logger
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()

\# Mock pubsub
        mock_pubsub = AsyncMock()
        adapter.redis.pubsub.return_value = mock_pubsub

async def mock_callback(message_data):
            pass

\# Simulate message with invalid JSON
        mock_message = {
            'type': 'message',
            'data': '{invalid json}'
        }

mock_pubsub.listen = Mock()
        mock_pubsub.listen.__aiter__ = Mock()
        mock_pubsub.listen.__anext__ = AsyncMock(side_effect=[mock_message, StopAsyncIteration])

await adapter._subscribe_channel('test_channel', mock_callback)

\# Should handle JSON error gracefully

class TestRedisAdapterStreamOperations:
    """Test RedisAdapter stream operations."""

def test_subscribe_stream_decorator(self):
        """Test stream subscription decorator."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

@adapter.subscribe('stream:test_stream')
        def stream_handler(message_id, message_data):
            pass

assert 'stream:test_stream' in adapter.subscribers
        assert adapter.subscribers['stream:test_stream'] == stream_handler

@pytest.mark.asyncio
    async def test_publish_to_stream_success(self):
        """Test successful publishing to stream."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.xadd = AsyncMock(return_value='123456789-0')

result = await adapter.publish_to_stream('test_stream', {'field': 'value'})

assert result == '123456789-0'
        adapter.redis.xadd.assert_called_once_with('test_stream', {'field': 'value'})

@pytest.mark.asyncio
    async def test_publish_to_stream_with_max_length(self):
        """Test publishing to stream with max length."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.xadd = AsyncMock(return_value='123456789-1')

result = await adapter.publish_to_stream('test_stream', {'field': 'value'}, max_length=100)

assert result == '123456789-1'
        adapter.redis.xadd.assert_called_once_with('test_stream', {'field': 'value'}, maxlen=100)

@pytest.mark.asyncio
    async def test_publish_to_stream_without_redis(self):
        """Test publishing to stream without Redis connection."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = None

with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.publish_to_stream('test_stream', {'field': 'value'})

class TestRedisAdapterUtilityOperations:
    """Test RedisAdapter utility operations (get, set, delete)."""

@pytest.mark.asyncio
    async def test_get_success(self):
        """Test successful get operation."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.get = AsyncMock(return_value='{"key": "value"}')

result = await adapter.get('test_key')

assert result == {"key": "value"}
        adapter.redis.get.assert_called_with('test_key')

@pytest.mark.asyncio
    async def test_get_string_value(self):
        """Test get operation with plain string value."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.get = AsyncMock(return_value='plain_string_value')

result = await adapter.get('test_key')

assert result == 'plain_string_value'

@pytest.mark.asyncio
    async def test_get_nonexistent_key(self):
        """Test get operation for non-existent key."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.get = AsyncMock(return_value=None)

result = await adapter.get('nonexistent_key', 'default_value')

assert result == 'default_value'

@pytest.mark.asyncio
    async def test_set_success(self):
        """Test successful set operation."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.set = AsyncMock(return_value=True)

result = await adapter.set('test_key', {'data': 'value'})

assert result is True
        adapter.redis.set.assert_called_with('test_key', '{"data": "value"}')

@pytest.mark.asyncio
    async def test_set_with_ttl(self):
        """Test set operation with TTL (time-to-live)."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.setex = AsyncMock(return_value=True)

result = await adapter.set('test_key', 'test_value', ttl=300)

assert result is True
        adapter.redis.setex.assert_called_with('test_key', 300, 'test_value')

@pytest.mark.asyncio
    async def test_set_failure(self):
        """Test set operation failure."""
        from framework.messaging.redis_adapter import RedisAdapter
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

@pytest.mark.asyncio
    async def test_set_without_redis_connection(self):
        """Test set without Redis connection."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = None  \# No connection

with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.set('test_key', 'value')

@pytest.mark.asyncio
    async def test_delete_success(self):
        """Test successful delete operation."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = AsyncMock()
        adapter.redis.delete = AsyncMock(return_value=2)  \# 2 keys deleted

result = await adapter.delete('key1', 'key2', 'key3')

assert result == 2
        adapter.redis.delete.assert_called_with('key1', 'key2', 'key3')

@pytest.mark.asyncio
    async def test_delete_without_redis_connection(self):
        """Test delete without Redis connection."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = None  \# No connection

with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.delete('key1', 'key2')

@pytest.mark.asyncio
    async def test_get_without_redis_connection(self):
        """Test get without Redis connection."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)
        adapter.redis = None  \# No connection

with pytest.raises(RuntimeError, match="Redis connection not established"):
            await adapter.get('test_key')

class TestRedisAdapterClientIPExtraction:
    """Test client IP extraction functionality."""

def test_get_client_ip_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

mock_request = Mock()
        mock_request.headers = {'X-Forwarded-For': '192.168.1.100, 10.0.0.1'}

result = adapter.get_client_ip(mock_request)

assert result == '192.168.1.100'

def test_get_client_ip_x_real_ip(self):
        """Test IP extraction from X-Real-IP header."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

mock_request = Mock()
        mock_request.headers = {'X-Real-IP': '192.168.1.200'}

result = adapter.get_client_ip(mock_request)

assert result == '192.168.1.200'

def test_get_client_ip_cf_connecting_ip(self):
        """Test IP extraction from Cloudflare header."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

mock_request = Mock()
        mock_request.headers = {'CF-Connecting-IP': '192.168.2.100'}

result = adapter.get_client_ip(mock_request)

assert result == '192.168.2.100'

def test_get_client_ip_multiple_headers(self):
        """Test IP extraction when multiple headers are present."""
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

mock_request = Mock()
        mock_request.headers = {
            'X-Forwarded-For': '192.168.1.100, 10.0.0.1',
            'X-Real-IP': '192.168.1.200',
            'CF-Connecting-IP': '192.168.2.100'
        }

\# Should use X-Forwarded-For as it appears first in the order
        result = adapter.get_client_ip(mock_request)

assert result == '192.168.1.100'

def test_get_client_ip_fallback_to_remote(self):
        """Test IP fallback to remote address."""
        from framework.messaging.redis_adapter import RedisAdapter
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
        from framework.messaging.redis_adapter import RedisAdapter
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
        from framework.messaging.redis_adapter import RedisAdapter
        app = Mock()
        app.container.get.side_effect = Exception("Config not found")

adapter = RedisAdapter(app)

mock_request = Mock()
        mock_request.headers = {'X-Forwarded-For': ''}
        mock_request.remote = ''
        \# Ensure remote is not a Mock
        type(mock_request).remote = ''

result = adapter.get_client_ip(mock_request)

assert result == 'unknown'
def assert_called_once_with(self, /, *args, **kwargs):
"""assert that the mock was called exactly once and that that call was
with the specified arguments."""
if not self.call_count == 1:
msg = ("Expected '%s' to be called once. Called %s times.%s"
% (self._mock_name or 'mock',
self.call_count,
self._calls_repr()))
>           raise AssertionError(msg)
E           AssertionError: Expected 'Redis' to be called once. Called 0 times.
C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\unittest\mock.py:950: AssertionError
During handling of the above exception, another exception occurred:
self = <test_redis_adapter.TestRedisAdapterLifecycle object at 0x000001B755A4F3D0>, mock_redis_class = <MagicMock name='Redis' id='1886927318416'>
@pytest.mark.asyncio
@patch('framework.messaging.redis_adapter.Redis')
async def test_start_success_with_config(self, mock_redis_class):
"""Test successful Redis connection with custom configuration."""
from framework.messaging.redis_adapter import RedisAdapter
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
>       mock_redis_class.assert_called_once_with(
host='test.redis.com',
port=6380,
db=1,
password='secret',
decode_responses=True
)
E       AssertionError: Expected 'Redis' to be called once. Called 0 times.
tests\messaging\test_redis_adapter.py:122: AssertionError
___________________________________________________________ TestRedisAdapterPubSubOperations.test_subscribe_channel_processing ___________________________________________________________
self = <AsyncMock name='mock.pubsub().subscribe' id='1886928581456'>, args = ('test_channel',), kwargs = {}, expected = "subscribe('test_channel')", actual = 'not called.'
error_message = "expected call not found.\nExpected: subscribe('test_channel')\n  Actual: not called."
def assert_called_with(self, /, *args, **kwargs):
"""assert that the last call was made with the specified arguments.
Raises an AssertionError if the args and keyword args passed in are
different to the last call to the mock."""
if self.call_args is None:
expected = self._format_mock_call_signature(args, kwargs)
actual = 'not called.'
error_message = ('expected call not found.\nExpected: %s\n  Actual: %s'
% (expected, actual))
>           raise AssertionError(error_message)
E           AssertionError: expected call not found.
E           Expected: subscribe('test_channel')
E             Actual: not called.
C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\unittest\mock.py:930: AssertionError
During handling of the above exception, another exception occurred:
self = <test_redis_adapter.TestRedisAdapterPubSubOperations object at 0x000001B755A4DD90>
@pytest.mark.asyncio
async def test_subscribe_channel_processing(self):
"""Test channel subscription and message processing."""
from framework.messaging.redis_adapter import RedisAdapter
app = Mock()
logger = Mock()
app.logger = logger
app.container.get.side_effect = Exception("Config not found")
adapter = RedisAdapter(app)
adapter.redis = AsyncMock()
\# Mock pubsub
mock_pubsub = AsyncMock()
adapter.redis.pubsub.return_value = mock_pubsub
async def mock_callback(message_data):
pass
\# Simulate message processing
mock_message = {
'type': 'message',
'data': '{"test": "value"}'
}
async def async_listen():
yield mock_message
mock_pubsub.listen = async_listen
mock_pubsub.subscribe = AsyncMock()
\# Call the subscription method directly
with patch('asyncio.create_task'):
await adapter._subscribe_channel('test_channel', mock_callback)
>           mock_pubsub.subscribe.assert_called_with('test_channel')
E           AssertionError: expected call not found.
E           Expected: subscribe('test_channel')
E             Actual: not called.
tests\messaging\test_redis_adapter.py:274: AssertionError
==================================================================================== warnings summary ====================================================================================
tests/messaging/test_redis_adapter.py::TestRedisAdapterPubSubOperations::test_subscribe_channel_processing
D:\UCore\tests\messaging\test_redis_adapter.py:273: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
await adapter._subscribe_channel('test_channel', mock_callback)
Enable tracemalloc to get traceback where the object was allocated.
See [https://docs.pytest.org/en/stable/how-to/capture-warnings.html\#resource-warnings](https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings) for more info.
tests/messaging/test_redis_adapter.py::TestRedisAdapterPubSubOperations::test_subscribe_channel_json_error_handling
D:\UCore\tests\messaging\test_redis_adapter.py:305: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
await adapter._subscribe_channel('test_channel', mock_callback)
Enable tracemalloc to get traceback where the object was allocated.
See [https://docs.pytest.org/en/stable/how-to/capture-warnings.html\#resource-warnings](https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings) for more info.
-- Docs: [https://docs.pytest.org/en/stable/how-to/capture-warnings.html](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
================================================================================ short test summary info =================================================================================
FAILED tests/messaging/test_redis_adapter.py::TestRedisAdapterLifecycle::test_start_success_with_config - AssertionError: Expected 'Redis' to be called once. Called 0 times.
FAILED tests/messaging/test_redis_adapter.py::TestRedisAdapterPubSubOperations::test_subscribe_channel_processing - AssertionError: expected call not found.
======================================================================== 2 failed, 32 passed, 2 warnings in 1.06s ========================================================================
PS D:\UCore> pytest tests/messaging/test_redis_adapter.py
================================================================================== test session starts ===================================================================================
platform win32 -- Python 3.11.9, pytest-8.4.2, pluggy-1.6.0
rootdir: D:\UCore
plugins: anyio-4.10.0, asyncio-1.2.0, mock-3.15.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 34 items
tests\messaging\test_redis_adapter.py ....F......F......................                                                                                                            [100%]
======================================================================================== FAILURES ========================================================================================
________________________________________________________________ TestRedisAdapterLifecycle.test_start_success_with_config ________________________________________________________________
self = <MagicMock name='Redis' id='2778812631952'>, args = (), kwargs = {'db': 1, 'decode_responses': True, 'host': 'test.redis.com', 'password': 'secret', ...}
msg = "Expected 'Redis' to be called once. Called 0 times."
def assert_called_once_with(self, /, *args, **kwargs):
"""assert that the mock was called exactly once and that that call was
with the specified arguments."""
if not self.call_count == 1:
msg = ("Expected '%s' to be called once. Called %s times.%s"
% (self._mock_name or 'mock',
self.call_count,
self._calls_repr()))
>           raise AssertionError(msg)
E           AssertionError: Expected 'Redis' to be called once. Called 0 times.
C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\unittest\mock.py:950: AssertionError
During handling of the above exception, another exception occurred:
self = <test_redis_adapter.TestRedisAdapterLifecycle object at 0x00000286FE21B7D0>, mock_redis_class = <MagicMock name='Redis' id='2778812631952'>
@pytest.mark.asyncio
@patch('framework.messaging.redis_adapter.Redis')
async def test_start_success_with_config(self, mock_redis_class):
"""Test successful Redis connection with custom configuration."""
from framework.messaging.redis_adapter import RedisAdapter
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
>       mock_redis_class.assert_called_once_with(
host='test.redis.com',
port=6380,
db=1,
password='secret',
decode_responses=True
)
E       AssertionError: Expected 'Redis' to be called once. Called 0 times.
tests\messaging\test_redis_adapter.py:124: AssertionError
___________________________________________________________ TestRedisAdapterPubSubOperations.test_subscribe_channel_processing ___________________________________________________________
self = <AsyncMock name='mock.pubsub().subscribe' id='2778810335120'>, args = ('test_channel',), kwargs = {}, expected = "subscribe('test_channel')", actual = 'not called.'
error_message = "expected call not found.\nExpected: subscribe('test_channel')\n  Actual: not called."
def assert_called_with(self, /, *args, **kwargs):
"""assert that the last call was made with the specified arguments.
Raises an AssertionError if the args and keyword args passed in are
different to the last call to the mock."""
if self.call_args is None:
expected = self._format_mock_call_signature(args, kwargs)
actual = 'not called.'
error_message = ('expected call not found.\nExpected: %s\n  Actual: %s'
% (expected, actual))
>           raise AssertionError(error_message)
E           AssertionError: expected call not found.
E           Expected: subscribe('test_channel')
E             Actual: not called.
C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\unittest\mock.py:930: AssertionError
During handling of the above exception, another exception occurred:
self = <test_redis_adapter.TestRedisAdapterPubSubOperations object at 0x00000286FE219F50>
@pytest.mark.asyncio
async def test_subscribe_channel_processing(self):
"""Test channel subscription and message processing."""
from framework.messaging.redis_adapter import RedisAdapter
app = Mock()
logger = Mock()
app.logger = logger
app.container.get.side_effect = Exception("Config not found")
adapter = RedisAdapter(app)
adapter.redis = AsyncMock()
\# Mock pubsub
mock_pubsub = AsyncMock()
adapter.redis.pubsub.return_value = mock_pubsub
async def mock_callback(message_data):
pass
\# Simulate message processing
mock_message = {
'type': 'message',
'data': '{"test": "value"}'
}
async def async_listen():
yield mock_message
mock_pubsub.listen = async_listen
mock_pubsub.subscribe = AsyncMock()
\# Call the subscription method directly
with patch('asyncio.create_task'):
await adapter._subscribe_channel('test_channel', mock_callback)
>           mock_pubsub.subscribe.assert_called_with('test_channel')
E           AssertionError: expected call not found.
E           Expected: subscribe('test_channel')
E             Actual: not called.
tests\messaging\test_redis_adapter.py:276: AssertionError
==================================================================================== warnings summary ====================================================================================
tests/messaging/test_redis_adapter.py::TestRedisAdapterPubSubOperations::test_subscribe_channel_processing
D:\UCore\tests\messaging\test_redis_adapter.py:275: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
await adapter._subscribe_channel('test_channel', mock_callback)
Enable tracemalloc to get traceback where the object was allocated.
See [https://docs.pytest.org/en/stable/how-to/capture-warnings.html\#resource-warnings](https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings) for more info.
tests/messaging/test_redis_adapter.py::TestRedisAdapterPubSubOperations::test_subscribe_channel_json_error_handling
D:\UCore\tests\messaging\test_redis_adapter.py:307: RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited
await adapter._subscribe_channel('test_channel', mock_callback)
Enable tracemalloc to get traceback where the object was allocated.
See [https://docs.pytest.org/en/stable/how-to/capture-warnings.html\#resource-warnings](https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings) for more info.
-- Docs: [https://docs.pytest.org/en/stable/how-to/capture-warnings.html](https://docs.pytest.org/en/stable/how-to/capture-warnings.html)
================================================================================ short test summary info =================================================================================
FAILED tests/messaging/test_redis_adapter.py::TestRedisAdapterLifecycle::test_start_success_with_config - AssertionError: Expected 'Redis' to be called once. Called 0 times.
FAILED tests/messaging/test_redis_adapter.py::TestRedisAdapterPubSubOperations::test_subscribe_channel_processing - AssertionError: expected call not found.

The main issue in these test failures is a conflict between your global Redis patching fixture and per-test patch decorators, resulting in **Redis not being called** or the mocks not behaving as intended during test execution.

***

### Why Are Tests Failing?

#### 1. Redis Not Called in `test_start_success_with_config`

- Your fixture `patch_redis` (autouse, function-scoped) runs for every test and globally monkeypatches both `"framework.messaging.redis_adapter.Redis"` and `"redis.asyncio.Redis"` with `MagicMock()`.
- But the test also uses `@patch('framework.messaging.redis_adapter.Redis')` — this decorator applies after the autouse fixture, replacing the already-mocked attribute with its own mock.
- The double monkeypatch means that the constructor for `RedisAdapter` uses a mock, but not the same mock as referenced in the assertion (`mock_redis_class`).
- Thus, when you call `adapter.start()` and check `mock_redis_class.assert_called_once_with(...)`, the call happened on a different MagicMock instance, resulting in “Expected 'Redis' to be called once. Called 0 times.”.


#### 2. Pubsub `subscribe` Not Called in `test_subscribe_channel_processing`

- Similar issue: global autouse fixture monkeypatches `redis.asyncio.Redis`, interfering with your AsyncMock setup inside the test.
- When `adapter.redis.pubsub.return_value.subscribe` is set as `AsyncMock()`, the Redis mock used by the adapter might not be the same as the test's mock, or the subscribe call is never properly awaited (see "coroutine ... was never awaited" warning). This happens if a coroutine-mock is set but called directly rather than awaited, or an inherited mock chain causes calls not to land where expected.


#### 3. RuntimeWarnings: Coroutines Not Awaited

- Some mocks are set as `AsyncMock`, but their coroutines are never actually awaited due to this patching confusion. It's a symptom of misconfigured mocking and test setup.

***

### How to Fix

#### **A. Remove or Re-scope the Global `patch_redis` Fixture**

- Instead of monkeypatching Redis for all tests, rely on decorators for fine-grained control:
    - Remove the autouse fixture, or set it to be module-scope and only patch base imports, not test-specific ones.
- If you _must_ patch globally, use consistent mocks and ensure per-test patch decorators do not conflict.


#### **B. Use Only One Mocking Mechanism Per Test**

- Where you use `@patch('...Redis')`, do **not** patch again via monkeypatch in the fixture.
- Prefer per-test decorators for isolated mocking/control.

```python
@pytest.fixture
def patch_redis(monkeypatch):
    # Only patch when not using test decorators
```


#### **C. Ensure AsyncMock Coroutines are Awaited**

- When assigning an `AsyncMock` to a coroutine, always await them in your code.
- Example:

```python
mock_pubsub.subscribe = AsyncMock()
await mock_pubsub.subscribe('test_channel')
```


#### **D. Verify That Calls Hit the Correct Mock**

- Assert on the correct instance (the one used by your adapter's code): use decorators' mocks, not hidden fixture mocks.

***

### Example: Fixing the First Test

**Remove the autouse fixture for Redis mocking.**

- Rely only on `@patch('framework.messaging.redis_adapter.Redis')` for mocking Redis in this test.

**Check Adapter Instantiation/Mock Usage:**

- After patching, any instantiation of `Redis` inside `RedisAdapter` will use the `mock_redis_class`, so your assertion will work.

**For Async Pubsub:**

- Assign coroutine methods as `AsyncMock()` and make sure they're awaited.

***

### Summary Table: Symptoms vs. Root Cause

| Symptom | Root Cause | Fix |
| :-- | :-- | :-- |
| Redis "not called" assertion error | Conflicting global/per-test mocks | Remove global patch or decorator clash |
| Pubsub subscribe "not called" assertion | Same as above + not awaited | Use one mock type, await AsyncMock |
| RuntimeWarning: coroutine not awaited | AsyncMock not used properly | Await AsyncMock coroutines |


***

### Reference

- [pytest monkeypatch vs unittest.mock.patch](https://docs.pytest.org/en/stable/how-to/monkeypatch.html)
- [unittest.mock behavior and gotchas](https://docs.python.org/3/library/unittest.mock.html)

***

**In short:**
The double-patching of Redis in both a global fixture and in per-test decorators makes the tests assert against an unused mock, causing assertion errors. Remove the autouse fixture and rely solely on per-test decorators, then verify that AsyncMocks are properly awaited. This will resolve both failed assertions and runtime warnings in your test suite.

