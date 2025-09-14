# examples/redis_messaging/main.py
"""
Redis Message Bus Example - Publisher-Subscriber Pattern

This example demonstrates:
- HTTP endpoint publishers sending messages via Redis
- Background subscribers consuming messages from Redis
- Stream processing for event-driven architectures
- Error handling and retry mechanisms

Usage:
1. Start Redis server
2. Run: python main.py (publisher application)
3. In another terminal: python examples/redis_messaging/subscriber.py (subscriber application)
4. Test endpoints:
   - POST /publish with {"channel": "notifications", "message": "Hello World"}
   - POST /stream with {"user_id": "123", "action": "login", "timestamp": "2024-01-01"}
   - GET /status - Check system status
"""

import sys
import asyncio
import time
from typing import Any
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.http import HttpServer
from framework.redis_adapter import RedisAdapter
from framework.di import Depends
import aiohttp
from aiohttp import web


def get_redis_adapter(redis_adapter: RedisAdapter):
    """Dependency provider for RedisAdapter"""
    return redis_adapter


def create_publisher_app():
    """
    Create an HTTP application that publishes messages to Redis.
    """
    app = App(name="RedisPublisher")

    # Create components
    http_server = HttpServer(app)
    redis_adapter = RedisAdapter(app)

    # Register components
    app.register_component(lambda: http_server)
    app.register_component(lambda: redis_adapter)

    # ---- Publisher Endpoints ----

    @http_server.route("/publish", "POST")
    async def publish_message_endpoint(request: web.Request, redis_adapter=Depends(get_redis_adapter)):
        """
        POST /publish
        JSON: {"channel": "notifications", "message": "Hello World"}

        Publishes a message to a Redis Pub/Sub channel.
        """
        try:
            data = await request.json()
            channel = data.get('channel', 'notifications')
            message = data.get('message', 'Default message')

            # Publish to Redis channel
            success = await redis_adapter.publish(channel, message)

            if success:
                return web.json_response({
                    "status": "success",
                    "channel": channel,
                    "message": message,
                    "message": f"Message published to channel '{channel}'"
                }, status=200)
            else:
                return web.json_response({
                    "status": "error",
                    "message": "Failed to publish message"
                }, status=500)

        except Exception as e:
            return web.json_response({
                "status": "error",
                "message": f"Server error: {str(e)}"
            }, status=500)

    @http_server.route("/stream", "POST")
    async def publish_to_stream_endpoint(request: web.Request, redis_adapter=Depends(get_redis_adapter)):
        """
        POST /stream
        JSON: {"user_id": "123", "action": "login", "timestamp": "2024-01-01"}

        Adds an event to a Redis Stream.
        """
        try:
            data = await request.json()

            # Generate unique event data
            event_data = {
                "event_id": f"evt_{int(time.time() * 1000)}",  # Unique ID based on time
                "user_id": data.get('user_id', 'anonymous'),
                "action": data.get('action', 'unknown'),
                "timestamp": data.get('timestamp', int(time.time())),
                "metadata": data.get('metadata', {}),
                "source": "publisher_app"
            }

            # Publish to stream
            message_id = await redis_adapter.publish_to_stream(
                "user_events",  # Stream name
                event_data,      # Event data
                max_length=1000  # Keep max 1000 events in stream
            )

            return web.json_response({
                "status": "success",
                "stream": "user_events",
                "message_id": message_id,
                "event_data": event_data,
                "message": f"Event added to stream with ID {message_id}"
            }, status=200)

        except Exception as e:
            return web.json_response({
                "status": "error",
                "message": f"Server error: {str(e)}"
            }, status=500)

    @http_server.route("/batch", "POST")
    async def batch_publish_endpoint(request: web.Request, redis_adapter=Depends(get_redis_adapter)):
        """
        POST /batch
        JSON: {"messages": [{"channel": "ch1", "message": "msg1"}, {"channel": "ch2", "message": "msg2"}]}

        Publishes multiple messages in batch.
        """
        try:
            data = await request.json()
            messages = data.get('messages', [])

            if not isinstance(messages, list):
                return web.json_response({
                    "status": "error",
                    "message": "Messages must be provided as an array"
                }, status=400)

            results = []
            for i, msg_data in enumerate(messages):
                try:
                    channel = msg_data.get('channel', f'channel_{i}')
                    message = msg_data.get('message', f'Message {i}')

                    success = await redis_adapter.publish(channel, message)
                    results.append({
                        "index": i,
                        "channel": channel,
                        "success": success,
                        "message": message if success else "Failed to publish"
                    })
                except Exception as e:
                    results.append({
                        "index": i,
                        "success": False,
                        "message": f"Error: {str(e)}"
                    })

            success_count = sum(1 for r in results if r['success'])

            return web.json_response({
                "status": "success",
                "total_messages": len(messages),
                "successful": success_count,
                "failed": len(messages) - success_count,
                "results": results,
                "message": f"Batch completed: {success_count}/{len(messages)} successful"
            }, status=200)

        except Exception as e:
            return web.json_response({
                "status": "error",
                "message": f"Server error: {str(e)}"
            }, status=500)

    @http_server.route("/cache", "POST")
    async def set_cache_endpoint(request: web.Request, redis_adapter=Depends(get_redis_adapter)):
        """
        POST /cache
        JSON: {"key": "my_key", "value": {"name": "test"}, "ttl": 60}

        Sets a value in Redis cache with optional TTL.
        """
        try:
            data = await request.json()
            key = data.get('key')
            value = data.get('value')
            ttl = data.get('ttl')  # Optional TTL in seconds

            if not key:
                return web.json_response({
                    "status": "error",
                    "message": "Key is required"
                }, status=400)

            success = await redis_adapter.set(key, value, ttl)

            if success:
                cache_info = f"Cache set for key '{key}'"
                if ttl:
                    cache_info += f" with TTL {ttl}s"
                return web.json_response({
                    "status": "success",
                    "key": key,
                    "ttl": ttl,
                    "message": cache_info
                }, status=200)
            else:
                return web.json_response({
                    "status": "error",
                    "message": "Failed to set cache value"
                }, status=500)

        except Exception as e:
            return web.json_response({
                "status": "error",
                "message": f"Server error: {str(e)}"
            }, status=500)

    @http_server.route("/cache/{key}", "GET")
    async def get_cache_endpoint(request: web.Request, redis_adapter=Depends(get_redis_adapter)):
        """
        GET /cache/{key}

        Retrieves a cached value from Redis.
        """
        try:
            key = request.match_info['key']
            value = await redis_adapter.get(key)

            if value is not None:
                return web.json_response({
                    "status": "success",
                    "key": key,
                    "value": value
                }, status=200)
            else:
                return web.json_response({
                    "status": "not_found",
                    "key": key,
                    "message": f"Cache key '{key}' not found"
                }, status=404)

        except Exception as e:
            return web.json_response({
                "status": "error",
                "message": f"Server error: {str(e)}"
            }, status=500)

    # ---- Status and Info Endpoints ----

    @http_server.route("/status", "GET")
    async def status_endpoint(request: web.Request, redis_adapter=Depends(get_redis_adapter)):
        """
        GET /status

        Returns system status including Redis connectivity.
        """
        redis_status = "unknown"
        try:
            # Test Redis connection
            await redis_adapter.redis.ping()
            redis_status = "connected"
        except Exception as e:
            redis_status = f"error: {str(e)}"

        return web.json_response({
            "status": "healthy" if redis_status == "connected" else "unhealthy",
            "redis_connection": redis_status,
            "app_name": "RedisPublisher",
            "components": ["HttpServer", "RedisAdapter"],
            "version": "v1.0",
            "endpoints": {
                "POST /publish": "Publish message to Redis channel",
                "POST /stream": "Add event to Redis Stream",
                "POST /batch": "Publish multiple messages",
                "POST /cache": "Set cache value",
                "GET /cache/{key}": "Get cache value",
                "GET /status": "System status"
            }
        }, status=200)

    @http_server.route("/", "GET")
    async def root_endpoint():
        """
        GET /

        Returns API documentation and usage information.
        """
        return web.json_response({
            "message": "UCore Redis Message Bus Publisher Example",
            "version": "v1.0",
            "role": "Publisher - Publishes messages to Redis",
            "setup_instructions": [
                "1. Start Redis server (redis-server)",
                "2. Run this publisher app: python main.py",
                "3. In another terminal, start subscriber: python subscriber.py"
            ],
            "test_commands": [
                "curl -X POST http://localhost:8080/publish -H 'Content-Type: application/json' -d '{\"channel\": \"notifications\", \"message\": \"Hello World\"}'",
                "curl -X POST http://localhost:8080/stream -H 'Content-Type: application/json' -d '{\"user_id\": \"123\", \"action\": \"login\"}'",
                "curl -X POST http://localhost:8080/cache -H 'Content-Type: application/json' -d '{\"key\": \"test_key\", \"value\": {\"name\": \"John\"}, \"ttl\": 60}'",
                "curl http://localhost:8080/cache/test_key"
            ],
            "redis_features": [
                "Pub/Sub messaging",
                "Stream processing",
                "Caching with TTL",
                "Batch operations",
                "Connection pooling",
                "Error handling"
            ]
        }, status=200)

    return app


def main():
    """
    Main entry point for the Redis publisher example.
    """
    print("🚀 UCore Redis Message Publisher Example")
    print("=" * 60)
    print()
    print("This application PUBLISHES messages and events to Redis.")
    print("Start a separate subscriber to see the messages being consumed.")
    print()
    print("Prerequisites:")
    print("  ✅ Redis server running (redis://localhost:6379/0)")
    print("  ❌ Start subscriber in separate terminal")
    print()
    print("API Endpoints:")
    print("  POST /publish  - Publish message to Redis channel")
    print("  POST /stream   - Add event to Redis Stream")
    print("  POST /batch    - Publish multiple messages")
    print("  POST /cache    - Set cache value with TTL")
    print("  GET  /cache/key - Retrieve cached value")
    print("  GET  /status   - System health check")
    print()

    # Create and run the application
    publisher_app = create_publisher_app()
    publisher_app.run()


if __name__ == "__main__":
    main()
