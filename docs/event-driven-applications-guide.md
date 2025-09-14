# Guide to Building Event-Driven Applications with UCore Framework
## Event-Driven Architecture Tutorial Using Redis and Framework Patterns

---

## 📋 Overview

Event-driven architecture (EDA) is a powerful pattern for building scalable, loosely-coupled systems that react to changes in real-time. This comprehensive guide will teach you how to build event-driven applications using UCore Framework with Redis as the event transport layer.

---

## 🚀 Quick Start: Basic Event Publisher

Let's start with a simple event publishing example:

```python
from framework.app import App
from framework.redis_adapter import RedisAdapter
import asyncio

class EventPublisher(App):
    def __init__(self):
        super().__init__("EventPublisher")
        self.redis = None

    async def astart(self):
        await super().astart()

        # Initialize Redis connection
        self.redis = RedisAdapter("redis://localhost:6379/0")
        await self.redis.connect()

        # Publish some events
        await self.publish_sample_events()

    async def publish_sample_events(self):
        events = [
            {
                "event_type": "user_registration",
                "user_id": 12345,
                "email": "user@example.com",
                "timestamp": "2025-09-12T10:30:00Z"
            },
            {
                "event_type": "order_created",
                "order_id": 789,
                "user_id": 12345,
                "total_price": 99.99,
                "timestamp": "2025-09-12T10:35:00Z"
            },
            {
                "event_type": "payment_processed",
                "order_id": 789,
                "amount": 99.99,
                "payment_method": "credit_card",
                "timestamp": "2025-09-12T10:36:00Z"
            }
        ]

        for event in events:
            await self.redis.publish_json("ecommerce_events", event)
            print(f"📤 Published event: {event['event_type']}")

            # Add delay between events
            await asyncio.sleep(1)

async def main():
    publisher = EventPublisher()
    await publisher.astart()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 Event-Driven Architecture Concepts

### What is Event-Driven Architecture?

EDA is a software architecture pattern where:
- **Components communicate asynchronously** through events
- **Producers generate events** without knowing the consumers
- **Consumers react to events** independently
- **Systems remain loosely coupled** and scalable

### Key Benefits

1. **🔹 Loose Coupling**: Components don't need direct knowledge of each other
2. **🔹 Scalability**: Easy to add new consumers without affecting producers
3. **🔹 Real-time**: Immediate reaction to system state changes
4. **🔹 Auditability**: Complete chronological event history
5. **🔹 Resilience**: System continues operating if consumers fail

---

## 🏗️ Core Event-Driven Patterns

### 1. Publisher/Subscriber Pattern

**When to use**: When you need broadcast communication and multiple consumers should react to the same event.

**UCore Implementation**:
```python
# Publisher
await redis.publish_json("orders", {"order_id": 123, "status": "paid"})

# Multiple Subscribers
await redis.subscribe("orders", order_processing_handler)
await redis.subscribe("orders", audit_handler)
await redis.subscribe("orders", notification_handler)
```

### 2. Event Sourcing Pattern

**When to use**: When you need complete audit trails and the ability to rebuild system state.

**UCore Implementation**:
```python
class EventStore:
    async def save_event(self, event):
        event['timestamp'] = datetime.utcnow().isoformat()
        await self.redis.publish_json("event_store", event)
        # Also save to persistent storage

    async def get_entity_events(self, entity_id):
        # Query all events for a specific entity
        return await self.redis.get_all_events(f"entity:{entity_id}")
```

### 3. CQRS Pattern

**When to use**: When you have different requirements for read and write operations, separated concerns.

**UCore Implementation**:
```python
# Command (write) side
class OrderCommandHandler:
    async def create_order(self, data):
        event = {"type": "order_created", "data": data}
        await self.event_store.save(event)

# Query (read) side
class OrderQueryHandler:
    async def get_order_read_model(self, order_id):
        # Read from optimized denormalized read model
        return await self.read_db.get_order(order_id)
```

---

## 🔴 Redis Integration in UCore Framework

### RedisAdapter Features

UCore's RedisAdapter provides:

- **JSON serialization**: Seamless JSON message handling
- **Connection management**: Automatic reconnection and pooling
- **Error handling**: Built-in retry logic and timeouts
- **Pub/Sub operations**: Reliable publish/subscribe functionality
- **Data operations**: Simple key-value operations

### Basic Configuration

```python
# Redis configuration examples
redis = RedisAdapter("redis://localhost:6379/0")          # Single instance
redis = RedisAdapter("redis://host:port,password=password")  # Authenticated
redis = RedisAdapter("redis://host:port,db=1")           # Specific database
```

---

## 🎯 Hands-on Tutorial: Building an E-commerce Event System

Let's build a complete e-commerce system using event-driven patterns.

### Step 1: Define Your Event Schema

```python
# events.schema.py
class Event:
    event_id: str
    event_type: str
    timestamp: str
    user_id: Optional[int]
    data: Dict[str, Any]

# User events
USER_REGISTERED = "user_registered"
USER_PROFILE_UPDATED = "user_profile_updated"
USER_LOGIN = "user_login"

# Order events
ORDER_CREATED = "order_created"
ORDER_PAID = "order_paid"
ORDER_SHIPPED = "order_shipped"
ORDER_DELIVERED = "order_delivered"
ORDER_CANCELLED = "order_cancelled"

# Inventory events
INVENTORY_LOW = "inventory_low"
INVENTORY_RESTOCKED = "inventory_restocked"

# Payment events
PAYMENT_PROCESSED = "payment_processed"
PAYMENT_FAILED = "payment_failed"
PAYMENT_REFUNDED = "payment_refunded"
```

### Step 2: Create Event Publishers

```python
# services/order_service.py
from framework.app import App
from framework.redis_adapter import RedisAdapter

class OrderService(App):
    def __init__(self):
        super().__init__("OrderService")
        self.redis = RedisAdapter("redis://localhost:6379/0")

    async def astart(self):
        await super().astart()
        await self.redis.connect()
        self.logger.info("🚀 OrderService started")

    async def create_order(self, order_data):
        """Create a new order and publish events."""
        order_id = await self.save_order_to_database(order_data)

        # Publish order creation event
        event = {
            "event_id": f"order_{order_id}",
            "event_type": "order_created",
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": order_data['user_id'],
            "data": {
                "order_id": order_id,
                "items": order_data['items'],
                "total_price": order_data['total_price']
            }
        }

        await self.redis.publish_json("ecommerce_events", event)
        self.logger.info(f"📦 Order {order_id} created and event published")

        return order_id
```

### Step 3: Create Event Consumers

```python
# services/notification_service.py
class NotificationService(App):
    def __init__(self):
        super().__init__("NotificationService")
        self.redis = RedisAdapter("redis://localhost:6379/0")

    async def astart(self):
        await super().astart()
        await self.redis.connect()

        # Subscribe to order events
        await self.redis.subscribe("ecommerce_events", self.handle_order_events)
        self.logger.info("📬 NotificationService listening for events")

    async def handle_order_events(self, event):
        """Handle incoming order events and send notifications."""
        if event['event_type'] == 'order_created':
            await self.send_order_confirmation(event)
        elif event['event_type'] == 'order_shipped':
            await self.send_shipping_notification(event)
        elif event['event_type'] == 'payment_failed':
            await self.send_payment_failure_notification(event)

    async def send_order_confirmation(self, event):
        """Send order confirmation email."""
        order_data = event['data']
        user_email = await self.get_user_email(event['user_id'])

        # Simulate email sending
        self.logger.info(f"📧 Sent order confirmation to {user_email}")
        self.logger.info(f"   Order #{order_data['order_id']} - ${order_data['total_price']}")
```

### Step 4: Real-time Dashboard Consumer

```python
# services/realtime_dashboard.py
import json

class RealtimeDashboard(App):
    def __init__(self):
        super().__init__("RealtimeDashboard")
        self.redis = RedisAdapter("redis://localhost:6379/0")
        self.metrics = {
            "total_orders": 0,
            "total_revenue": 0.0,
            "active_users": set(),
            "orders_by_status": {}
        }

    async def astart(self):
        await super().astart()
        await self.redis.connect()

        await self.redis.subscribe("ecommerce_events", self.update_metrics)
        await self.redis.subscribe("user_events", self.update_user_metrics)
        self.logger.info("📊 RealtimeDashboard updating metrics...")

    async def update_metrics(self, event):
        """Update dashboard metrics in real-time."""
        if event['event_type'] == 'order_created':
            self.metrics['total_orders'] += 1
            self.metrics['total_revenue'] += event['data']['total_price']

            status = 'pending'
            if status not in self.metrics['orders_by_status']:
                self.metrics['orders_by_status'][status] = 0
            self.metrics['orders_by_status'][status] += 1

            await self.broadcast_metrics_update()

        elif event['event_type'] in ['order_paid', 'order_shipped', 'order_delivered']:
            # Update order status counts
            old_status = 'pending'
            new_status = event['event_type'].replace('order_', '')

            self.metrics['orders_by_status'][old_status] -= 1
            if new_status not in self.metrics['orders_by_status']:
                self.metrics['orders_by_status'][new_status] = 0
            self.metrics['orders_by_status'][new_status] += 1

            await self.broadcast_metrics_update()

    async def broadcast_metrics_update(self):
        """Broadcast updated metrics to dashboard clients."""
        # In a real implementation, this would use WebSockets
        # or Server-Sent Events to push updates to dashboard UI
        self.logger.info("📈 Metrics updated:")
        self.logger.info(f"   Orders: {self.metrics['total_orders']}")
        self.logger.info(f"   Revenue: ${self.metrics['total_revenue']:.2f}")
        self.logger.info(f"   Status distribution: {self.metrics['orders_by_status']}")
```

### Step 5: Handle Event Processing Errors

```python
# utils/event_error_handler.py
class EventErrorHandler:
    @staticmethod
    def should_retry(event, error, attempt=0):
        """Determine if an event should be retried."""
        max_retries = 3

        if attempt >= max_retries:
            return False

        # Retry certain types of errors
        retryable_errors = [
            ConnectionError,
            TimeoutError,
            redis.exceptions.ConnectionError
        ]

        return any(isinstance(error, err_type) for err_type in retryable_errors)

    @staticmethod
    def get_backoff_delay(attempt):
        """Calculate exponential backoff delay."""
        base_delay = 1  # seconds
        return base_delay * (2 ** attempt) + random.uniform(0, 1)

class ReliableEventConsumer(App):
    def __init__(self, event_type):
        super().__init__(f"EventConsumer_{event_type}")
        self.redis = RedisAdapter("redis://localhost:6379/0")
        self.event_type = event_type
        self.error_handler = EventErrorHandler()

    async def process_event_with_retry(self, event):
        """Process event with retry logic."""
        attempt = 0
        max_attempts = 3

        while attempt < max_attempts:
            try:
                await self.process_event(event)
                return True
            except Exception as e:
                attempt += 1
                should_retry = self.error_handler.should_retry(event, e, attempt - 1)

                if should_retry and attempt < max_attempts:
                    delay = self.error_handler.get_backoff_delay(attempt - 1)
                    self.logger.warning(f"❌ Event processing failed, retrying in {delay}s: {e}")
                    await asyncio.sleep(delay)
                else:
                    self.logger.error(f"❌ Event processing failed permanently: {e}")
                    await self.handle_failed_event(event, e)
                    return False

        return False
```

---

## 🎯 Advanced Patterns and Best Practices

### 1. Event Versioning and Schema Evolution

```python
# schemas/event_schemas.py
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class BaseEvent(BaseModel):
    event_id: str = Field(..., description="Unique event identifier")
    event_type: str = Field(..., description="Type of event")
    timestamp: str = Field(..., description="ISO 8601 timestamp")
    version: str = Field(default="1.0", description="Event schema version")
    metadata: Dict[str, Any] = Field(default_factory=dict)

class OrderCreatedEvent(BaseEvent):
    event_type: str = "order_created"
    user_id: int
    order_data: Dict[str, Any]
    total_amount: float

class OrderUpdatedEvent(BaseEvent):
    event_type: str = "order_updated"
    order_id: int
    previous_status: str
    new_status: str
    updated_by: str

# Event version evolution handler
class EventVersionAdapter:
    @staticmethod
    def migrate_order_event(event_data, from_version, to_version):
        """Migrate event data between versions."""
        if from_version == "1.0" and to_version == "1.1":
            # Added new field in v1.1
            if 'tax_amount' not in event_data:
                event_data['tax_amount'] = event_data['total_amount'] * 0.1
        return event_data
```

### 2. Event Store Pattern

```python
# patterns/event_store.py
class EventStore:
    def __init__(self, redis_url):
        self.redis = RedisAdapter(redis_url)
        self.stream_key = "event_store"

    async def save_event(self, event: Dict[str, Any]):
        """Save event to Redis stream for persistence."""
        event_id = event['event_id']
        serialized = json.dumps(event)

        # Use Redis streams for persistence
        await self.redis.xadd(self.stream_key, {'event': serialized})

        # Publish to real-time consumers
        await self.redis.publish_json("events", event)

    async def get_events_for_entity(self, entity_id: str):
        """Get all events for a specific entity."""
        # In a real implementation, you'd index events by entity
        all_events = await self.redis.xrange(self.stream_key)
        return [
            json.loads(event_data['event'])
            for event_id, event_data in all_events
            if json.loads(event_data['event']).get('entity_id') == entity_id
        ]

    async def replay_events(self, consumer_group: str, callback):
        """Replay all events for a consumer group."""
        await self.redis.xread_group(
            consumer_group,
            self.stream_key,
            callback
        )
```

### 3. Saga Pattern for Distributed Transactions

```python
# patterns/saga_pattern.py
class Saga:
    def __init__(self, saga_id):
        self.saga_id = saga_id
        self.redis = RedisAdapter("redis://localhost:6379/0")
        self.steps = []
        self.compensation_actions = []

    def add_step(self, step_name, action_func, compensation_func):
        """Add a step to the saga."""
        self.steps.append({
            'name': step_name,
            'action': action_func,
            'compensation': compensation_func,
            'status': 'pending'
        })

    async def execute(self):
        """Execute the saga."""
        for i, step in enumerate(self.steps):
            try:
                await step['action']()
                step['status'] = 'completed'
                await self.save_checkpoint(step, i)

                # Publish success event
                await self.redis.publish_json("saga_events", {
                    "saga_id": self.saga_id,
                    "step": step['name'],
                    "status": "step_completed",
                    "timestamp": datetime.utcnow().isoformat()
                })

            except Exception as e:
                step['status'] = 'failed'
                await self.compensate_failed_saga(i, e)
                return False

        return True

    async def compensate_failed_saga(self, failed_step_index, error):
        """Execute compensation actions in reverse order."""
        self.logger.error(f"❌ Saga failed at step {failed_step_index}: {error}")

        for i in range(failed_step_index, -1, -1):
            step = self.steps[i]
            if step['status'] == 'completed':
                try:
                    await step['compensation']()
                    step['status'] = 'compensated'
                    self.logger.info(f"🔄 Compensated step: {step['name']}")
                except Exception as comp_error:
                    self.logger.error(f"❌ Compensation failed for {step['name']}: {comp_error}")
```

---

## 🧪 Testing Event-Driven Applications

### Unit Testing Event Publishers

```python
# tests/test_event_publishing.py
import pytest
from unittest.mock import AsyncMock, Mock
from your_event_publisher import EventPublisher

@pytest.mark.asyncio
class TestEventPublisher:
    async def test_publish_user_created_event(self):
        """Test publishing user creation events."""
        redis_mock = AsyncMock()
        publisher = EventPublisher()
        publisher.redis = redis_mock

        user_data = {
            'user_id': 123,
            'email': 'test@example.com',
            'username': 'testuser'
        }

        await publisher.publish_user_created(user_data)

        # Verify event was published
        redis_mock.publish_json.assert_called_once_with(
            'user_events',
            {
                'event_type': 'user_created',
                'user_id': 123,
                'email': 'test@example.com',
                'username': 'testuser',
                'timestamp': Mock  # You'd use a specific timestamp mock
            }
        )
```

### Integration Testing Event Flows

```python
# tests/test_event_flows.py
import pytest
from framework.test_utils import RedisTestClient

@pytest.mark.asyncio
class TestOrderEventFlow:
    async def test_order_creation_flow(self, redis_client: RedisTestClient):
        """Test complete order creation event flow."""
        # Start order service
        order_service = OrderService()
        await order_service.astart()

        # Mock notification service
        notification_service = NotificationService()
        await notification_service.astart()

        # Create an order
        order_data = {
            'user_id': 123,
            'items': [{'product_id': 456, 'quantity': 2}],
            'total_price': 59.98
        }

        order_id = await order_service.create_order(order_data)

        # Verify events were published
        events = await redis_client.get_published_events("ecommerce_events")
        order_events = [e for e in events if e['data'].get('order_id') == order_id]

        assert len(order_events) > 0
        assert order_events[0]['event_type'] == 'order_created'
        assert order_events[0]['user_id'] == 123

        # Verify notification service received the event
        # (This would require additional async event checking)
```

---

## 🔧 Operational Best Practices

### 1. Event Monitoring and Observability

```python
# monitoring/event_monitor.py
class EventMonitor(App):
    def __init__(self):
        super().__init__("EventMonitor")
        self.redis = RedisAdapter("redis://localhost:6379/0")
        self.monitoring_port = 9091

    async def astart(self):
        await super().astart()
        await self.redis.connect()

        # Monitor all event channels
        await self.redis.psubscribe("*", self.handle_event)
        await self.start_monitoring_endpoint()

    async def handle_event(self, event, channel):
        """Monitor and log all events."""
        self.logger.info(f"📊 Event: {channel} -> {event.get('event_type')}")

        # Track event volumes
        event_key = f"event_counts:{channel}:{event.get('event_type')}"
        await self.redis.incr(event_key)

        # Check for abnormal patterns
        count = await self.redis.get(event_key)
        if int(count) > 1000:  # High volume alert
            await self.send_alert("High event volume", channel, event.get('event_type'))

    async def get_event_statistics(self):
        """Get comprehensive event statistics."""
        pattern = "event_counts:*"
        keys = await self.redis.keys(pattern)

        stats = {}
        for key in keys:
            parts = key.split(":")
            channel, event_type = parts[1], parts[2]
            count = await self.redis.get(key)

            if channel not in stats:
                stats[channel] = {}

            stats[channel][event_type] = int(count or 0)

        return stats
```

### 2. Event Replay and Recovery

```python
# recovery/event_replay.py
class EventReplayService(App):
    def __init__(self):
        super().__init__("EventReplayService")
        self.redis = RedisAdapter("redis://localhost:6379/0")
        self.event_store = EventStore("redis://localhost:6379/1")

    async def replay_events_for_entity(self, entity_id, from_timestamp=None):
        """Replay events for a specific entity."""
        events = await self.event_store.get_events_for_entity(entity_id)

        if from_timestamp:
            events = [e for e in events if e['timestamp'] >= from_timestamp]

        replayed_count = 0
        for event in events:
            try:
                # Re-publish the event
                await self.redis.publish_json("ecommerce_events", event)
                replayed_count += 1
                self.logger.info(f"🔄 Replayed event: {event['event_type']} for entity {entity_id}")
            except Exception as e:
                self.logger.error(f"❌ Failed to replay event: {e}")

        return replayed_count

    async def replay_all_events(self, event_types=None, start_date=None):
        """Replay all events matching criteria."""
        all_events = await self.event_store.get_all_events()

        if event_types:
            all_events = [e for e in all_events if e['event_type'] in event_types]

        if start_date:
            all_events = [e for e in all_events if e['timestamp'] >= start_date]

        # Sort events by timestamp
        all_events.sort(key=lambda e: e['timestamp'])

        for event in all_events:
            await self.redis.publish_json("ecommerce_events", event)

        return len(all_events)
```

### 3. Event Deduplication

```python
# utils/event_deduplicator.py
class EventDeduplicator:
    def __init__(self, redis_url, ttl_seconds=3600):
        self.redis = RedisAdapter(redis_url)
        self.ttl = ttl_seconds

    async def deduplication_required(self, event) -> bool:
        """Check if an event is a duplicate."""
        event_fingerprint = self.generate_fingerprint(event)
        key = f"event_idempotent:{event_fingerprint}"

        # Use SETNX to check if key exists
        exists = await self.redis.exists(key)

        if not exists:
            # Set the key with TTL if it's not a duplicate
            await self.redis.setex(key, self.ttl, "1")
            return False

        return True

    @staticmethod
    def generate_fingerprint(event):
        """Generate a unique fingerprint for the event."""
        import hashlib

        # Create a consistent hash based on event content
        event_str = json.dumps({
            'event_type': event.get('event_type'),
            'user_id': event.get('user_id'),
            'entity_id': event.get('entity_id'),
            'data': event.get('data', {}),
        }, sort_keys=True)

        return hashlib.sha256(event_str.encode()).hexdigest()[:32]
```

---

## 🚀 Advanced Topics and Future Directions

### 1. Event Streaming with Kafka Integration

For high-throughput scenarios, you might want to integrate with Apache Kafka:

```python
# TODO: Kafka integration example
class KafkaEventPublisher:
    def __init__(self):
        # Configure Kafka producer
        pass

    async def publish_event(self, event):
        # Publish to Kafka topic
        pass
```

### 2. Event Sourcing with CQRS

Implement full CQRS with separate read and write models:

```python
# TODO: Complete CQRS implementation
class CQRSArchitecture:
    def __init__(self):
        self.command_bus = CommandBus()
        self.query_bus = QueryBus()
        self.event_store = EventStore()
```

### 3. Event-Driven Microservices

Building on the comprehensive microservice example:

```python
# TODO: Microservice mesh with service discovery
class ServiceDiscovery:
    def __init__(self):
        # Register services for event routing
        pass

    async def discover_service_for_event(self, event_type):
        # Find which services should receive the event
        pass
```

---

## 📚 Reference: Event-Driven Patterns Catalog

| Pattern | Description | Use Case |
|---------|-------------|----------|
| **Publisher/Subscriber** | One-to-many event delivery | Notifications, logging |
| **Event Sourcing** | Complete event history | Audit trails, rebuilding state |
| **CQRS** | Separation of reads/writes | Complex domain models |
| **Saga** | Distributed transaction management | Multi-step workflows |
| **Event Replay** | Rebuilding system state | Recovery, testing |
| **Event Streams** | Continuous event processing | Real-time analytics |

---

## 🎯 Summary

This guide has provided you with:

1. **🔹 Comprehensive understanding** of event-driven architecture concepts
2. **🔹 Practical implementation** using UCore Framework and Redis
3. **🔹 Working code examples** for common patterns
4. **🔹 Best practices** for production deployments
5. **🔹 Testing strategies** for event-driven systems
6. **🔹 Monitoring and observability** techniques
7. **🔹 Error handling and recovery** patterns

The UCore Framework's Redis integration makes building event-driven applications straightforward while providing the flexibility to implement advanced patterns as your system grows.

Remember: **Start simple with pub/sub, then evolve to more complex patterns** (CQRS, Sagas) as your system requirements grow. Always prioritize **observability and monitoring** from day one.

For more detailed examples, check the `examples/` directory for working implementations of these concepts! 🚀
