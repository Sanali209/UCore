# examples/redis_messaging/subscriber.py
"""
Redis Message Bus Subscriber Example

This application SUBSCRIBES to and consumes messages from Redis.
It demonstrates:
- Channel subscription for pub/sub messaging
- Stream consumption with consumer groups
- Error handling and graceful shutdown
- Message processing with acknowledgments

Usage:
1. Start Redis server
2. Run publisher: python main.py
3. Run subscriber: python subscriber.py
4. Watch messages being received and processed
"""

import sys
import json
import asyncio
import signal
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.redis_adapter import RedisAdapter


def create_subscriber_app():
    """
    Create a Redis subscriber application that consumes messages.
    """
    app = App(name="RedisSubscriber")

    # Create and register Redis adapter
    redis_adapter = RedisAdapter(app)
    app.register_component(lambda: redis_adapter)

    # ---- Register Subscribers ----

    # 1. Channel subscriber for notifications
    @redis_adapter.subscribe('notifications')
    async def handle_notifications(message):
        """
        Handle notification messages from the 'notifications' channel.
        """
        print("🔔 [Channel] Received notification:", message)
        # Simulate processing time
        await asyncio.sleep(0.1)
        print("✅ [Channel] Notification processed successfully")
        # In real application, this would:
        # - Send email notifications
        # - Update UI dashboards
        # - Trigger alerts
        # - Log to monitoring systems

    # 2. Channel subscriber for alerts
    @redis_adapter.subscribe('alerts')
    async def handle_alerts(message):
        """
        Handle alert messages with higher priority processing.
        """
        print("🚨 [Channel] ALERT:", message)
        print("🔥 [Channel] High-priority alert processing...")

        # Simulate more complex processing
        await asyncio.sleep(0.2)
        print("✅ [Channel] Alert processed with priority handling")
        # High-priority alerts might:
        # - Send SMS notifications
        # - Page on-call engineers
        # - Trigger immediate actions

    # 3. Stream subscriber for user events
    @redis_adapter.subscribe('stream:user_events')
    async def handle_user_events(event_id, event_data):
        """
        Handle user events from the 'user_events' stream.
        Each event is acknowledged when processed successfully.
        """
        print(f"👤 [Stream] User event received:")
        print(f"   Event ID: {event_id}")
        print(f"   User ID: {event_data.get('user_id', 'N/A')}")
        print(f"   Action: {event_data.get('action', 'unknown')}")
        print(f"   Timestamp: {event_data.get('timestamp', 'N/A')}")
        print(f"   Source: {event_data.get('source', 'N/A')}")

        # Simulate user event processing
        await asyncio.sleep(0.15)

        print("✅ [Stream] User event processed successfully")
        # User event processing might include:
        # - Update user analytics
        # - Trigger recommendation engine
        # - Log user behavior
        # - Send personalized notifications

    # 4. Subscriber for system events (with error handling)
    @redis_adapter.subscribe('stream:system_events')
    async def handle_system_events(event_id, event_data):
        """
        Handle system monitoring events.
        """
        try:
            print("🔧 [Stream] System event:")
            print(f"   Event ID: {event_id}")
            print(f"   Component: {event_data.get('component', 'unknown')}")
            print(f"   Event type: {event_data.get('event_type', 'info')}")
            print(f"   Details: {event_data.get('details', {})}")

            # Simulate system monitoring
            await asyncio.sleep(0.05)

            # Check for critical system events
            event_type = event_data.get('event_type')
            if event_type == 'critical':
                print("🚨 [Stream] CRITICAL SYSTEM EVENT - ALERTING ENGINEERS")
            elif event_type == 'warning':
                print("⚠️  [Stream] Warning system event")

            print("✅ [Stream] System event processed")

        except Exception as e:
            print(f"❌ [Stream] Error processing system event {event_id}: {e}")
            # In production, log to error tracking system

    # 5. Generic channel subscriber for any unmatched messages
    @redis_adapter.subscribe('general')
    async def handle_general_messages(message):
        """
        Handle general-purpose messages.
        """
        print("📨 [Channel] General message:")
        if isinstance(message, dict) and 'type' in message:
            msg_type = message.get('type')
            if msg_type == 'metrics':
                print(f"📊 [Channel] Metrics data: {message.get('data', {})}")
            elif msg_type == 'health':
                print(f"🏥 [Channel] Health check: {message.get('status', 'unknown')}")
            else:
                print(f"❓ [Channel] Unknown message type: {msg_type}")
        else:
            print(f"📨 [Channel] Raw message: {message}")

        await asyncio.sleep(0.08)
        print("✅ [Channel] General message processed")
    return app


def demo_message_sending():
    """
    Demonstrate various types of messages that can be sent to test the subscribers.
    """
    messages = [
        # Channel messages
        {"type": "channel", "channel": "notifications", "message": "User logged in successfully"},
        {"type": "channel", "channel": "alerts", "message": "High CPU usage detected!"},
        {"type": "channel", "channel": "general", "message": {"type": "metrics", "data": {"cpu": 85, "memory": 70}}},

        # Stream events
        {"type": "stream",
         "stream": "user_events",
         "data": {"user_id": "user_123", "action": "purchase", "product_id": "12345"}},

        {"type": "stream",
         "stream": "system_events",
         "data": {"component": "database", "event_type": "critical", "details": {"error": "Connection timeout"}}},
    ]

    print("\n📝 TEST MESSAGE SAMPLES:")
    print("Copy these curl commands to test the subscriber:")
    print()

    for msg in messages:
        print(f"# {msg['type'].upper()} - {msg['channel'] if 'channel' in msg else msg['stream']}")
        if msg['type'] == 'channel':
            print(f'curl -X POST http://localhost:8080/publish \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{{"channel": "{msg["channel"]}", "message": "{msg["message"]}"}}\'')
        else:  # stream
            data_str = json.dumps(msg['data'])
            print(f'curl -X POST http://localhost:8080/stream \\')
            print(f'  -H "Content-Type: application/json" \\')
            print(f'  -d \'{data_str}\'')

        print()


def signal_handler(signum, frame):
    """
    Handle graceful shutdown on Ctrl+C.
    """
    print("\n🛑 [Subscriber] Shutdown signal received...")
    print("👋 [Subscriber] Subscriber will shutdown gracefully")
    # The asyncio event loop will handle cleanup properly


def main():
    """
    Main entry point for the Redis subscriber example.
    """
    print("🚀 UCore Redis Message Subscriber Example")
    print("=" * 60)
    print()
    print("This application SUBSCRIBES TO and consumes messages from Redis.")
    print("Start the publisher application to see live message processing.")
    print()
    print("Prerequisites:")
    print("  ✅ Publisher app running (python main.py)")
    print("  ❌ Redis server running (redis://localhost:6379/0)")
    print()

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Show test message examples
    demo_message_sending()

    print("🔄 SUBSCRIBED CHANNELS:")
    print("  • notifications - Notification messages")
    print("  • alerts - High-priority alerts")
    print("  • general - General-purpose messages")
    print()

    print("🔄 SUBSCRIBED STREAMS:")
    print("  • user_events - User action events")
    print("  • system_events - System monitoring events")
    print()

    print("🎯 MESSAGE PROCESSING:")
    print("  • Auto-acknowledgment of processed stream messages")
    print("  • Error handling and logging")
    print("  • Graceful shutdown on signal")
    print()

    print("💡 Test the subscriber:")
    print("1. Start this subscriber: python subscriber.py")
    print("2. In another terminal, start publisher: python main.py")
    print("3. Use curl commands above to send test messages")
    print("4. Watch this terminal for message processing logs")
    print()
    print("⚡ Ready to process Redis messages...")
    print("=" * 60)

    # Create and run the subscriber application
    subscriber_app = create_subscriber_app()
    subscriber_app.run()


if __name__ == "__main__":
    main()
