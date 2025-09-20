"""
Redis adapter and message bus utilities for UCore Framework.

This module provides:
- RedisAdapter: Pub/sub messaging and stream processing for event-driven architectures
- Integration with UCore's component lifecycle and event bus
- Circuit breaker protection for Redis operations
- Automatic forwarding of framework events to Redis channels

Classes:
    RedisAdapter: Redis pub/sub and stream adapter for UCore.

Usage:
    from ucore_framework.core.redis_adapter import RedisAdapter

    redis_adapter = RedisAdapter(app)
    await redis_adapter.start()
    await redis_adapter.publish("notifications", {"msg": "hello"})
    await redis_adapter.stop()
"""

import redis.asyncio
from redis.exceptions import ConnectionError, TimeoutError
import json
import asyncio
from typing import Dict, Callable, Any, Optional
from ..core.component import Component
from .redis_event_bridge import EventBusRedisBridge
from typing import Dict, Optional
import uuid
from ucore_framework.core.circuit_breaker import CircuitBreakerManager, BreakerError


class RedisAdapter(Component, EventBusRedisBridge):
    """
    Redis pub/sub and stream adapter for UCore.

    Responsibilities:
        - Provide async pub/sub messaging and stream processing using Redis
        - Integrate with UCore's component lifecycle for resource management
        - Forward framework events to Redis channels for distributed eventing
        - Use circuit breaker for resilient Redis operations
        - Support decorator-based channel and stream subscription

    Example:
        redis_adapter = RedisAdapter(app)
        await redis_adapter.start()
        await redis_adapter.publish("notifications", {"msg": "hello"})
        await redis_adapter.stop()
    """

    def __init__(self, app):
        self.app = app

        # Initialize mixins explicitly
        Component.__init__(self, app)
        EventBusRedisBridge.__init__(self)

        self.redis_breaker = CircuitBreakerManager.get_breaker("redis_main")

        # Get configuration
        try:
            from ..core.config import ConfigManager
            self.config = app.container.get(ConfigManager)
        except:
            # Fallback configuration
            self.config = {
                "REDIS_HOST": "localhost",
                "REDIS_PORT": 6379,
                "REDIS_DB": 0,
                "REDIS_PASSWORD": None
            }

        self.redis = None
        self.subscribers: Dict[str, Callable] = {}
        self.channels: Dict[str, asyncio.Task] = {}
        self.stream_consumers: Dict[str, asyncio.Task] = {}

        # Bridge configuration and state
        # Default Redis channels for EventBus events
        self.bridge_channels: Dict[str, str] = {
            'app_started': 'ucore.events.app.started',
            'app_stopped': 'ucore.events.app.stopped',
            'component_started': 'ucore.events.component.started',
            'component_stopped': 'ucore.events.component.stopped',
            'config_updated': 'ucore.events.config.updated',
            'user_events': 'ucore.events.user',
        }

        # Bridge configuration options
        self.bridge_settings: Dict[str, Any] = {
            'eventbus_to_redis_enabled': True,
            'redis_to_eventbus_enabled': True,
            'forward_app_events': True,
            'forward_component_events': True,
            'forward_config_events': True,
            'forward_user_events': True,
            'instance_id': str(uuid.uuid4())[:8],  # Unique identifier for this instance
            'max_retries': 3,
            'retry_delay': 1.0,
        }

        # Load bridge settings from config
        self._load_bridge_settings()

        # Bridge handlers storage
        self.bridge_handlers: Dict[str, Callable] = {}
        self.redis_listeners: Dict[str, Callable] = {}

    def _load_bridge_settings(self) -> None:
        """
        Load bridge configuration from app config.
        """
        if isinstance(self.config, dict):
            # Load from config dict
            bridge_config = self.config.get("REDIS_BRIDGE", {})
            self.bridge_settings.update(bridge_config)

            # Load channel mapping overrides
            bridge_channels = bridge_config.get("channels", {})
            self.bridge_channels.update(bridge_channels)

        # Log bridge configuration
        if hasattr(self.app, 'logger'):
            self.app.logger.info(f"Redis EventBus Bridge enabled: "
                               f"E2R={self.bridge_settings['eventbus_to_redis_enabled']}, "
                               f"R2E={self.bridge_settings['redis_to_eventbus_enabled']}, "
                               f"Instance ID: {self.bridge_settings['instance_id']}")

        # Register default framework event forwarders
        self._register_framework_event_forwarders()

    def _register_framework_event_forwarders(self):
        """
        Register forwarders for standard UCore framework events.
        This enables automatic forwarding of framework events to Redis channels.
        """
        from .event_types import AppStartedEvent, ComponentStartedEvent, ComponentStoppedEvent, ConfigurationChangedEvent

        # Forward AppStartedEvent to Redis
        if self.bridge_settings['forward_app_events']:
            self.register_event_forwarder(
                event_type=AppStartedEvent,
                redis_channel=self.bridge_channels['app_started']
            )

        # Forward Component events to Redis
        if self.bridge_settings['forward_component_events']:
            self.register_event_forwarder(
                event_type=ComponentStartedEvent,
                redis_channel=self.bridge_channels['component_started']
            )

            # Note: ComponentStoppedEvent needs to be handled differently
            # since it doesn't have app_started equivalent in the lifecycle

        # Forward ConfigurationChangedEvent to Redis  
        if self.bridge_settings['forward_config_events']:
            self.register_event_forwarder(
                event_type=ConfigurationChangedEvent,
                redis_channel=self.bridge_channels['config_updated']
            )

        if hasattr(self.app, 'logger'):
            self.app.logger.info("Redis EventBus Bridge: Framework event forwarders registered")

    async def start(self):
        """
        Initialize Redis connection and start subscribers.
        """
        print(f"[DEBUG] RedisAdapter.start() called in module: {__name__}, file: {__file__}")
        try:
            # Create Redis connection
            host = self.config.get("REDIS_HOST", "localhost")
            port = self.config.get("REDIS_PORT", 6379)
            db = self.config.get("REDIS_DB", 0)
            password = self.config.get("REDIS_PASSWORD")

            self.redis = redis.asyncio.Redis(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True
            )

            # Test connection
            await self.redis.ping()
            self.app.logger.info(f"Redis connected successfully: {host}:{port}/{db}")

            # Start any registered subscribers
            for channel, callback in self.subscribers.items():
                if channel.startswith('stream:'):
                    # Stream consumer
                    stream_name = channel[7:]  # Remove 'stream:' prefix
                    task = asyncio.create_task(self._consume_stream(stream_name, callback))
                    self.stream_consumers[stream_name] = task
                else:
                    # Pub/sub channel
                    task = asyncio.create_task(self._subscribe_channel(channel, callback))
                    self.channels[channel] = task

        except Exception as e:
            self.app.logger.error(f"Failed to connect to Redis: {e}")
            # Don't crash application startup - Redis operations will fail gracefully
            self.redis = None

    async def stop(self):
        """
        Clean up Redis connections and stop subscribers.
        """
        # Cancel all consumer tasks
        for task in self.channels.values():
            task.cancel()
        for task in self.stream_consumers.values():
            task.cancel()

        # Close Redis connection
        if self.redis:
            await self.redis.close()
            self.app.logger.info("Redis connection closed")

    # ---- Pub/Sub Methods ----

    def subscribe(self, channel: str):
        """
        Decorator to register a function as a channel subscriber.

        Example:
            @redis_adapter.subscribe('notifications')
            async def handle_notification(message):
                print(f"Received: {message}")

            @redis_adapter.subscribe('stream:events')
            async def handle_stream_event(event_id, event_data):
                print(f"Stream event: {event_id} -> {event_data}")
        """
        def decorator(func: Callable):
            self.subscribers[channel] = func
            return func
        return decorator

    async def publish(self, channel: str, message: Any) -> bool:
        """
        Publish a message to a Redis channel.

        :param channel: Channel name
        :param message: Message to publish (will be JSON-serialized)
        :return: Success status
        """
        if not self.redis:
            raise RuntimeError("Redis connection not established")

        try:
            # Serialize message to JSON if it's not already a string
            if not isinstance(message, str):
                message = json.dumps(message)

            await self.redis.publish(channel, message)
            return True
        except Exception as e:
            self.app.logger.error(f"Failed to publish message: {e}")
            return False

    async def _subscribe_channel(self, channel: str, callback: Callable):
        """
        Subscribe to a channel and process messages.
        """
        try:
            pubsub = self.redis.pubsub()
            await pubsub.subscribe(channel)

            async for message in pubsub.listen():
                if message['type'] == 'message':
                    try:
                        # Try to parse as JSON
                        try:
                            data = json.loads(message['data'])
                        except (json.JSONDecodeError, TypeError):
                            data = message['data']

                        await callback(data)
                    except Exception as e:
                        self.app.logger.error(f"Error processing message on {channel}: {e}")

        except Exception as e:
            self.app.logger.error(f"Error subscribing to channel {channel}: {e}")

    # ---- Stream Methods ----

    async def publish_to_stream(self, stream: str, data: Dict[str, Any], max_length: int = None) -> str:
        """
        Publish a message to a Redis Stream.

        :param stream: Stream name
        :param data: Dictionary of field->value mappings
        :param max_length: Maximum stream length (optional)
        :return: Message ID
        """
        if not self.redis:
            raise RuntimeError("Redis connection not established")

        try:
            if max_length:
                message_id = await self.redis.xadd(stream, data, maxlen=max_length)
            else:
                message_id = await self.redis.xadd(stream, data)

            return message_id
        except Exception as e:
            self.app.logger.error(f"Failed to publish to stream {stream}: {e}")
            raise

    async def _consume_stream(self, stream: str, callback: Callable):
        """
        Consume messages from a Redis Stream.
        """
        try:
            last_id = '0'  # Start from beginning
            consumer_group = f"{stream}_group"
            consumer_name = f"{stream}_consumer"

            # Create consumer group if it doesn't exist
            try:
                await self.redis.xgroup_create(stream, consumer_group, '$', mkstream=True)
            except Exception:
                # Group might already exist
                pass

            while True:
                try:
                    # Read from stream
                    results = await self.redis.xreadgroup(
                        groupname=consumer_group,
                        consumername=consumer_name,
                        streams={stream: last_id},
                        count=1,
                        block=1000  # 1 second timeout
                    )

                    if results:
                        for stream_result in results:
                            stream_name, messages = stream_result
                            for message_id, message_data in messages:
                                try:
                                    # Call callback with message ID and data
                                    await callback(message_id, message_data)
                                    # Acknowledge message
                                    await self.redis.xack(stream, consumer_group, message_id)
                                    last_id = message_id
                                except Exception as e:
                                    self.app.logger.error(f"Error processing stream message {message_id}: {e}")

                    await asyncio.sleep(0.1)  # Small delay to prevent tight loop

                except Exception as e:
                    self.app.logger.error(f"Error consuming from stream {stream}: {e}")
                    await asyncio.sleep(1)  # Longer delay on error

        except Exception as e:
            self.app.logger.error(f"Fatal error consuming stream {stream}: {e}")

    # ---- Utility Methods ----

    async def get(self, key: str, default=None):
        """
        Get a key's value from Redis.
        """
        if not self.redis:
            raise RuntimeError("Redis connection not established")

        try:
            value = await self.redis_breaker.async_call(self.redis.get, key)
        except BreakerError:
            self.app.logger.error("Redis circuit breaker is open. Failing fast on get.")
            return default

        if value is None:
            return default

        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """
        Set a key's value in Redis.

        :param key: Key name
        :param value: Value (will be JSON-serialized if not string)
        :param ttl: Time-to-live in seconds (optional)
        :return: Success status
        """
        if not self.redis:
            raise RuntimeError("Redis connection not established")

        try:
            if not isinstance(value, str):
                value = json.dumps(value)

            if ttl:
                return await self.redis_breaker.async_call(self.redis.setex, key, ttl, value)
            else:
                return await self.redis_breaker.async_call(self.redis.set, key, value)
        except BreakerError:
            self.app.logger.error("Redis circuit breaker is open. Failing fast on set.")
            return False
        except Exception as e:
            self.app.logger.error(f"Failed to set Redis key {key}: {e}")
            return False

    async def delete(self, *keys) -> int:
        """
        Delete one or more keys from Redis.
        """
        if not self.redis:
            raise RuntimeError("Redis connection not established")

        return await self.redis.delete(*keys)

    def get_client_ip(self, request) -> str:
        """
        Extract client IP address from request headers.
        Handles proxy headers like X-Forwarded-For, etc.

        Note: This method is primarily used by metrics framework,
        but provided here for message content enrichment if needed.
        """
        # Check for forwarded headers (common in proxy/load balancer setups)
        for header in ['X-Forwarded-For', 'X-Real-IP']:
            forwarded = request.headers.get(header)
            if forwarded:
                # Take first IP if multiple are present
                return forwarded.split(',')[0].strip()

        # Check for Cloudflare header
        cf_ip = request.headers.get('CF-Connecting-IP')
        if cf_ip:
            return cf_ip

        # Fallback to aiohttp's remote address
        if hasattr(request, 'remote'):
            return request.remote or 'unknown'

        return 'unknown'
