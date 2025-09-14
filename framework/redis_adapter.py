# framework/redis_adapter.py
"""
Redis Message Bus for UCore Framework.
Provides pub/sub messaging and stream processing for event-driven architectures.
"""

from redis import asyncio as aioredis
from redis.asyncio import Redis
from redis.exceptions import ConnectionError, TimeoutError
import json
import asyncio
from typing import Dict, Callable, Any, Optional
from .component import Component


class RedisAdapter(Component):
    """
    Redis adapter for pub/sub messaging and stream processing.
    Integrates with UCore's component lifecycle for proper resource management.
    """

    def __init__(self, app):
        self.app = app

        # Get configuration
        try:
            from .config import Config
            self.config = app.container.get(Config)
        except:
            # Fallback configuration
            self.config = {
                "REDIS_HOST": "localhost",
                "REDIS_PORT": 6379,
                "REDIS_DB": 0,
                "REDIS_PASSWORD": None
            }

        self.redis: Optional[Redis] = None
        self.subscribers: Dict[str, Callable] = {}
        self.channels: Dict[str, asyncio.Task] = {}
        self.stream_consumers: Dict[str, asyncio.Task] = {}

    async def start(self):
        """
        Initialize Redis connection and start subscribers.
        """
        try:
            # Create Redis connection
            host = self.config.get("REDIS_HOST", "localhost")
            port = self.config.get("REDIS_PORT", 6379)
            db = self.config.get("REDIS_DB", 0)
            password = self.config.get("REDIS_PASSWORD")

            self.redis = Redis(
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

        value = await self.redis.get(key)
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
                return await self.redis.setex(key, ttl, value)
            else:
                return await self.redis.set(key, value)
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
