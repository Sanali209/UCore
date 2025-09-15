#!/usr/bin/env python3
"""
Redis EventBus Bridge Demo - UCore Framework

Demonstrates Redis EventBus integration with external Redis server configuration:
- 🔗 External Redis server connection setup
- 🔄 Bidirectional EventBus ↔ Redis bridging
- ⚙️ Custom Redis connection parameters (host, port, auth)
- 📊 Bridge statistics and monitoring
- ✅ Error handling for Redis connectivity

Configuration Options:
- REDIS_HOST: Redis server hostname/IP
- REDIS_PORT: Redis server port (default: 6379)
- REDIS_DB: Redis database number (default: 0)
- REDIS_PASSWORD: Redis authentication password
- REDIS_BRIDGE: EventBus bridge configuration
"""

import asyncio
import sys
import os
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import App
from framework.messaging.redis_adapter import RedisAdapter
from framework.messaging.events import UserEvent


def create_demo_app():
    """Create a demo UCore application with Redis EventBus bridge."""
    print("🔄 Creating Redis EventBus Bridge demo application...")

    app = App("RedisBridgeDemo")

    print("✅ Application initialized successfully")

    return app


async def simulate_app_lifecycle():
    """Demonstrate automatic EventBus → Redis forwarding."""
    print("🚀 Starting Redis EventBus Bridge Demo")
    print("=" * 50)

    app = create_demo_app()

    # Create and register Redis adapter with bridge
    redis_adapter = RedisAdapter(app)
    app.register_component(redis_adapter)

    print("\n📋 Bridge Configuration:")
    print(f"   Instance ID: {redis_adapter.bridge_settings['instance_id']}")
    print(f"   EventBus→Redis: {redis_adapter.bridge_settings['eventbus_to_redis_enabled']}")
    print(f"   Redis→EventBus: {redis_adapter.bridge_settings['redis_to_eventbus_enabled']}")
    print(f"   Forward App Events: {redis_adapter.bridge_settings['forward_app_events']}")
    print(f"   Forward Component Events: {redis_adapter.bridge_settings['forward_component_events']}")

    print("\n📺 Redis Channel Mappings:")
    for event_type, channel in redis_adapter.bridge_channels.items():
        print(f"   {event_type} → {channel}")

    # Try to connect to Redis (skip if not available)
    try:
        await redis_adapter.start()
        redis_connected = redis_adapter.redis is not None
    except:
        redis_connected = False

    if not redis_connected:
        print("\n⚠️  Redis not available - running in demo mode (no actual forwarding)")

        # Simulate bridge forwarding in demo mode
        print("\n📨 Simulating framework event forwarding:")

        simulated_events = [
            ("AppStartedEvent", {
                "app_name": "RedisBridgeDemo",
                "component_count": 2,
                "instance_id": redis_adapter.bridge_settings['instance_id']
            }),
            ("ComponentStartedEvent", {
                "component_name": "RedisAdapter",
                "component_type": "RedisAdapter",
                "instance_id": redis_adapter.bridge_settings['instance_id']
            })
        ]

        for event_type, event_data in simulated_events:
            # Show what would be forwarded
            message = {
                "event_type": event_type,
                "timestamp": "2025-09-14T22:17:00",
                "source": "ucore_framework",
                "event_bus_source": "ucore_framework",
                "instance_id": redis_adapter.bridge_settings['instance_id'],
                "data": event_data
            }

            channel = redis_adapter.bridge_channels[event_type.lower().replace("event", "").replace("appstarted", "app_started").replace("componentstarted", "component_started")]

            print(f"\n   📤 Forwarding {event_type}")
            print(f"      Channel: {channel}")
            print(f"      Message: {message}")
            print(f"      → WouldForwardToRedis")
    else:
        print("\n✅ Redis connected - live forwarding active!")

        # Configure bridge to listen to its own channels
        print("\n🔄 Configuring bidirectional bridge...")

        # Listen to Redis channels for bridge feedback
        @redis_adapter.subscribe('ucore.demo.app.started')
        async def handle_app_started(message):
            print(f"📥 Received from Redis channel 'ucore.demo.app.started': {message}")

        @redis_adapter.subscribe('ucore.demo.component.started')
        async def handle_component_started(message):
            print(f"📥 Received from Redis channel 'ucore.demo.component.started': {message}")

        # Note: No additional components needed for basic bridge demo

        print("\n⏳ Starting application lifecycle...")

        # Start app (this will trigger AppStartedEvent)
        await app.start()

        # Wait a moment for events to propagate
        await asyncio.sleep(1)

        # Show bridge statistics
        stats = redis_adapter.get_bridge_stats()
        print(f"\n📊 Bridge Statistics:")
        for key, value in stats.items():
            print(f"   {key}: {value}")

    print("\n🎯 Key Features Demonstrated:")
    print("   ✓ Automatic framework event forwarding")
    print("   ✓ Configurable Redis channel mapping")
    print("   ✓ Instance identification for distributed apps")
    print("   ✓ Bridge enable/disable controls")
    print("   ✓ Bidirectional event flow")
    print("   ✓ Error handling and statistics tracking")

    # Cleanup
    if redis_connected:
        await redis_adapter.stop()

    print("\n✨ Demo completed!")


async def demo_external_redis_configuration():
    """Demonstrate Redis adapter configuration for external Redis servers."""
    print("\n🔗 External Redis Server Configuration Demo")
    print("=" * 50)
    print("\n⚙️ UCore Redis Configuration Methods:")
    print("=" * 50)

    # Method 1: Environment Variables
    print("\n1. 🌍 Environment Variable Configuration:")
    print("   # Set before running your app")
    print("   export REDIS_HOST=redis.mycloud.com")
    print("   export REDIS_PORT=6380")
    print("   export REDIS_PASSWORD=mysecurepassword")
    print("   export REDIS_DB=1")
    print("   ")
    print("   # Then run your UCore application")
    print("   python examples/redis_eventbridge_demo.py")

    # Method 2: Config File
    print("\n2. 📄 JSON Configuration File (config.json):")
    print("   {")
    print('     "REDIS_HOST": "redis.mycloud.com",')
    print('     "REDIS_PORT": 6380,')
    print('     "REDIS_PASSWORD": "mysecurepassword",')
    print('     "REDIS_DB": 1,')
    print('     "REDIS_BRIDGE": {')
    print('       "eventbus_to_redis_enabled": true,')
    print('       "redis_to_eventbus_enabled": false,')
    print('       "instance_id": "production_app_01"')
    print('     }')
    print('   }')

    # Method 3: Manual Config (Programmatic)
    print("\n3. 🔧 Programmatic Configuration (In Code):")

    # Replicate RedisAdapter config fallback manually
    redis_config = {
        "REDIS_HOST": "redis.mycloud.com",        # External Redis hostname/IP
        "REDIS_PORT": 6380,                        # Non-standard port
        "REDIS_DB": 1,                              # Use database 1
        "REDIS_PASSWORD": "mysecurepassword",       # Authentication
        "REDIS_BRIDGE": {
            "eventbus_to_redis_enabled": True,
            "redis_to_eventbus_enabled": False,      # Only send to Redis
            "instance_id": "production_app_01"
        }
    }

    print("   redis_config = {")
    for key, value in redis_config.items():
        if key == "REDIS_BRIDGE":
            print(f"       '{key}': {{")
            for sub_key, sub_value in value.items():
                print(f"           '{sub_key}': {sub_value}")
            print("       }")
        else:
            print(f"       '{key}': '{value}',")
    print("   }")

    # Method 4: Docker Examples
    print("\n4. 🐳 Docker Deployment Examples:")
    print("   ")
    print("   # Redis Stack (with persistence, JSON, search)")
    print("   docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest")
    print("   ")
    print("   # Redis Cloud connection")
    print("   REDIS_HOST=redis-12345.mycloud.com")
    print("   REDIS_PORT=6380")
    print("   REDIS_PASSWORD=cloud-redis-password")

    # Method 5: Testing Configuration
    print("\n5. 🧪 Testing Redis Configuration:")

    app = create_demo_app()
    redis_adapter = RedisAdapter(app)

    # Manually set config to simulate external Redis
    external_redis_config = {
        "REDIS_HOST": "my.external.redis.server",
        "REDIS_PORT": 6379,
        "REDIS_DB": 0,
        "REDIS_PASSWORD": "secure_password_here"
    }

    # Override the config that RedisAdapter will use
    redis_adapter.config = external_redis_config

    print("   External Redis Configuration Example:")
    print(f"   • Host: {redis_adapter.config.get('REDIS_HOST')}")
    print(f"   • Port: {redis_adapter.config.get('REDIS_PORT')}")
    print(f"   • Database: {redis_adapter.config.get('REDIS_DB')}")
    print(f"   • Auth: {'Yes' if redis_adapter.config.get('REDIS_PASSWORD') else 'No'}")

    print("\n🎯 Configuration Success Factors:")
    print("   ✓ Network connectivity to Redis server")
    print("   ✓ Correct hostname/IP address")
    print("   ✓ Proper port number (6379 default)")
    print("   ✓ Authentication credentials (if required)")
    print("   ✓ Firewall rules allowing connection")
    print("   ✓ Redis server accepting connections")


async def demo_bridge_customization():
    """Demonstrate custom bridge configuration."""
    print("\n🔧 Custom Bridge Configuration Demo")
    print("=" * 50)

    app = create_demo_app()

    # Create RedisAdapter
    redis_adapter = RedisAdapter(app)
    app.register_component(redis_adapter)

    print("Before customization:")
    print(f"   Forward app events: {redis_adapter.bridge_settings['forward_app_events']}")
    print(f"   Forward config events: {redis_adapter.bridge_settings['forward_config_events']}")

    # Customize bridge settings
    redis_adapter.bridge_settings.update({
        'forward_app_events': False,        # Don't forward app events
        'forward_config_events': True,      # Do forward config events
        'forward_user_events': True,        # Forward user-defined events
    })

    # Add custom event forwarding with UserEvent (already imported above)

    def forward_utilization_events(event):
        """Only forward high utilization events."""
        return event.payload.get('cpu_usage', 0) > 80

    redis_adapter.register_event_forwarder(
        event_type=UserEvent,
        redis_channel='ucore.monitoring.high_utilization',
        event_filter=forward_utilization_events
    )

    print("\nAfter customization:")
    print(f"   Forward app events: {redis_adapter.bridge_settings['forward_app_events']}")
    print(f"   Forward config events: {redis_adapter.bridge_settings['forward_config_events']}")
    print(f"   Forward user events: {redis_adapter.bridge_settings['forward_user_events']}")
    print(f"   Custom forwarders: {len(redis_adapter.event_forwarders)}")

    print("\n🎯 Customization Benefits:")
    print("   ✓ Selective event forwarding")
    print("   ✓ Custom filtering and routing")
    print("   ✓ Channel mapping customization")
    print("   ✓ Bridge runtime reconfiguration")


if __name__ == "__main__":
    try:
        # Run main demo
        asyncio.run(simulate_app_lifecycle())

        # Run external Redis configuration demo
        asyncio.run(demo_external_redis_configuration())

        # Run customization demo
        asyncio.run(demo_bridge_customization())

    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()
