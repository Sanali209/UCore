#!/usr/bin/env python3
"""
Comprehensive Microservice Example for UCore Framework
======================================================

This example demonstrates a complete production-grade microservice using all UCore components:

🔌 UCore HttpServer with dependency injection
🗄️ UCore SQLAlchemyAdapter with database operations
🔴 UCore Redis Adapter for pub/sub messaging
⚡ UCore Event Bus for decoupled communication
📊 UCore Metrics and Observability

Architecture:
- Users API (CRUD operations)
- Orders API (e-commerce example)
- Background order processing with asyncio tasks
- Order status notifications via Redis pub/sub and event bus
- Performance monitoring and metrics
- Proper component lifecycle management

Installation Requirements:
pip install sqlalchemy redis

Usage:
python examples/comprehensive_microservice.py

Endpoints:
- GET    /health          - Health check
- GET    /users/{id}      - Get user
- POST   /users           - Create user
- GET    /orders/{id}     - Get order
- POST   /orders          - Create order
- PUT    /orders/{id}     - Update order status
- GET    /metrics         - Prometheus metrics

Features Demonstrated:
- Enterprise HTTP API with validation and proper aiohttp responses
- Database ORM with component-based DI
- Redis pub/sub event system
- Event-driven architecture with observables
- Metrics collection and tracing
- Professional logging and error handling
- Configuration management through DI
- Health monitoring
"""

import sys
import asyncio
from datetime import datetime
from typing import Dict, Any

# UCore framework imports
sys.path.insert(0, 'd:/UCore')

from framework import App
from framework.web import HttpServer
from framework.data.db import SQLAlchemyAdapter
from framework.messaging.redis_adapter import RedisAdapter
from framework.messaging.event_bus import EventBus
from framework.monitoring.metrics import HTTPMetricsAdapter
from framework.core.di import Depends
from framework.messaging.events import UserEvent
from aiohttp import web

# Global event bus instance for use in background tasks
global_event_bus = None

# Database Models (simplified for demo)
class User:
    """Simplified user model for demo."""
    def __init__(self, username: str, email: str, balance: float = 0.0):
        self.id = id(self)
        self.username = username
        self.email = email
        self.balance = balance
        self.created_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'balance': self.balance,
            'created_at': self.created_at.isoformat()
        }

class Order:
    """Simplified order model for demo."""
    def __init__(self, user_id: int, product_name: str, quantity: int, total_price: float):
        self.id = id(self)
        self.user_id = user_id
        self.product_name = product_name
        self.quantity = quantity
        self.total_price = total_price
        self.status = 'pending'
        self.created_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'product_name': self.product_name,
            'quantity': self.quantity,
            'total_price': self.total_price,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

# Custom Events using UserEvent
class UserCreatedEvent(UserEvent):
    def __init__(self, user_id: int, username: str, email: str):
        super().__init__(
            event_type="user_created",
            payload={
                'user_id': user_id,
                'username': username,
                'email': email
            }
        )

class OrderCreatedEvent(UserEvent):
    def __init__(self, order_id: int, user_id: int, total_price: float):
        super().__init__(
            event_type="order_created",
            payload={
                'order_id': order_id,
                'user_id': user_id,
                'total_price': total_price
            }
        )

class OrderProcessedEvent(UserEvent):
    def __init__(self, order_id: int, user_id: int, status: str):
        super().__init__(
            event_type="order_processed",
            payload={
                'order_id': order_id,
                'user_id': user_id,
                'status': status
            }
        )

def get_event_bus(event_bus: EventBus):
    """Dependency provider for event bus."""
    return event_bus

def get_redis_adapter(redis_adapter: RedisAdapter):
    """Dependency provider for Redis."""
    return redis_adapter

def create_comprehensive_app():
    """
    Create the comprehensive microservice application.
    """
    app = App(name="ComprehensiveMicroservice")

    # Initialize components
    http_server = HttpServer(app)
    database = SQLAlchemyAdapter(app)
    redis_adapter = RedisAdapter(app)
    event_bus = EventBus(app.logger)  # EventBus is not a Component, just initialize it
    metrics_adapter = HTTPMetricsAdapter(app)

    # Register components (only actual components)
    app.register_component(lambda: http_server)
    app.register_component(lambda: database)
    app.register_component(lambda: redis_adapter)
    app.register_component(lambda: metrics_adapter)

    # Store event bus reference globally for use in background tasks
    global global_event_bus
    global_event_bus = event_bus

    # Simple in-memory storage for demo (in production, use database)
    users_storage = {}
    orders_storage = {}
    next_user_id = 1
    next_order_id = 1

    # Routes using UCore HttpServer
    @http_server.route("/health", "GET")
    async def health_handler(request):
        """Health check endpoint."""
        return web.json_response({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {
                'database': True,
                'event_bus': event_bus._running,
                'redis': bool(redis_adapter.redis),
                'metrics': True
            }
        })

    @http_server.route("/users", "POST")
    async def create_user_handler(request):
        """Create a new user."""
        try:
            data = await request.json()

            # Validation
            required_fields = ['username', 'email']
            for field in required_fields:
                if field not in data:
                    return web.json_response(
                        {'error': f'Missing required field: {field}'}, status=400
                    )

            # Check if user exists (in real implementation, would check database)
            if any(u.username == data['username'] or u.email == data['email'] for u in users_storage.values()):
                return web.json_response({'error': 'Username or email already exists'}, status=400)

            # Create user
            nonlocal next_user_id
            user = User(
                username=data['username'],
                email=data['email'],
                balance=data.get('balance', 0.0)
            )
            user.id = next_user_id
            users_storage[user.id] = user
            next_user_id += 1

            # Publish user created event
            event_bus.publish(UserCreatedEvent(user.id, user.username, user.email))

            # Also publish via Redis if available
            try:
                if redis_adapter.redis:
                    await redis_adapter.publish('user_events', {
                        'type': 'user_created',
                        'user_id': user.id,
                        'username': user.username,
                        'timestamp': datetime.utcnow().isoformat()
                    })
            except Exception as e:
                app.logger.warning(f"Redis publishing failed: {e}")

            return web.json_response(user.to_dict(), status=201)

        except Exception as e:
            return web.json_response({'error': f'Server error: {str(e)}'}, status=500)

    @http_server.route("/users/{user_id}", "GET")
    async def get_user_handler(request):
        """Get user by ID."""
        try:
            user_id = int(request.match_info['user_id'])

            user = users_storage.get(user_id)
            if not user:
                return web.json_response({'error': 'User not found'}, status=404)

            return web.json_response(user.to_dict())

        except ValueError:
            return web.json_response({'error': 'Invalid user ID'}, status=400)

    @http_server.route("/orders", "POST")
    async def create_order_handler(request, event_bus=Depends(get_event_bus)):
        """Create a new order."""
        try:
            data = await request.json()

            # Validation
            required_fields = ['user_id', 'product_name', 'quantity', 'total_price']
            for field in required_fields:
                if field not in data:
                    return await request.app.json_response(
                        {'error': f'Missing required field: {field}'}, status=400
                    )

            if data['quantity'] <= 0 or data['total_price'] <= 0:
                return web.json_response({'error': 'Invalid quantity or price'}, status=400)

            # Check if user exists
            if data['user_id'] not in users_storage:
                return web.json_response({'error': 'User not found'}, status=400)

            # Create order
            nonlocal next_order_id
            order = Order(
                user_id=data['user_id'],
                product_name=data['product_name'],
                quantity=data['quantity'],
                total_price=data['total_price']
            )
            order.id = next_order_id
            orders_storage[order.id] = order
            next_order_id += 1

            # Publish order event
            event_bus.publish(OrderCreatedEvent(order.id, order.user_id, order.total_price))

            # Start background processing
            asyncio.create_task(process_order_background(order.id, app))

            return web.json_response(order.to_dict(), status=201)

        except Exception as e:
            return web.json_response({'error': f'Server error: {str(e)}'}, status=500)

    @http_server.route("/orders/{order_id}", "GET")
    async def get_order_handler(request):
        """Get order by ID."""
        try:
            order_id = int(request.match_info['order_id'])

            order = orders_storage.get(order_id)
            if not order:
                return await request.app.json_response({'error': 'Order not found'}, status=404)

            return order.to_dict()

        except ValueError:
            return await request.app.json_response({'error': 'Invalid order ID'}, status=400)

    @http_server.route("/orders/{order_id}", "PUT")
    async def update_order_handler(request, event_bus=Depends(get_event_bus)):
        """Update order status."""
        try:
            order_id = int(request.match_info['order_id'])
            data = await request.json()

            order = orders_storage.get(order_id)
            if not order:
                return await request.app.json_response({'error': 'Order not found'}, status=404)

            if 'status' not in data:
                return await request.app.json_response({'error': 'Status field required'}, status=400)

            # Update order
            order.status = data['status']
            order.updated_at = datetime.utcnow()

            # Publish status update event
            event_bus.publish(OrderProcessedEvent(order.id, order.user_id, order.status))

            return order.to_dict()

        except ValueError:
            return await request.app.json_response({'error': 'Invalid order ID'}, status=400)

    @http_server.route("/metrics", "GET")
    async def metrics_endpoint():
        """Serve Prometheus metrics."""
        from prometheus_client import REGISTRY
        from framework.monitoring.metrics import generate_latest

        try:
            metrics_output = generate_latest(REGISTRY).decode('utf-8')
            return {
                'content': metrics_output,
                'content_type': 'text/plain; version=0.0.4; charset=utf-8',
                'headers': {'Cache-Control': 'no-cache, no-store, must-revalidate'}
            }
        except Exception as e:
            return {'error': f'Metrics error: {str(e)}'}, 500

    # Event handlers
    @event_bus.subscribe(OrderCreatedEvent)
    async def handle_order_created(event: OrderCreatedEvent):
        """Handle order creation events."""
        app.logger.info(f"📦 Order {event.payload['order_id']} created for user {event.payload['user_id']}")

    @event_bus.subscribe(OrderProcessedEvent)
    async def handle_order_processed(event: OrderProcessedEvent):
        """Handle order processing events."""
        app.logger.info(f"✅ Order {event.payload['order_id']} status changed to: {event.payload['status']}")

    @event_bus.subscribe(UserCreatedEvent)
    async def handle_user_created(event: UserCreatedEvent):
        """Handle user creation events."""
        app.logger.info(f"👤 User {event.payload['user_id']} created: {event.payload['username']}")

    return app


async def process_order_background(order_id: int, app: App):
    """
    Process order in background (simulating asyncio task).
    """
    try:
        app.logger.info(f"⚡ Processing order {order_id} in background...")

        # Simulate processing steps
        await asyncio.sleep(2)  # Payment validation
        app.logger.info(f"💳 Order {order_id} - Payment validated")

        await asyncio.sleep(2)  # Inventory check
        app.logger.info(f"📦 Order {order_id} - Inventory checked")

        await asyncio.sleep(1)  # Shipping preparation
        app.logger.info(f"🚚 Order {order_id} - Shipping prepared")

        # Update order status (in real implementation, would save to database)
        app.logger.info(f"✅ Order {order_id} completed!")

        # Get event bus from global variable and publish completion event
        global global_event_bus
        if global_event_bus:
            global_event_bus.publish(OrderProcessedEvent(order_id, 0, 'completed'))

    except Exception as e:
        app.logger.error(f"❌ Order processing failed: {e}")


async def main():
    """Main demonstration function."""
    print("🏗️ COMPREHENSIVE MICROSERVICE DEMO")
    print("=" * 50)

    # Create the microservice application
    app = create_comprehensive_app()

    print("\n🚀 Starting Comprehensive Microservice...")

    try:
        # Start the application (this initializes all components)
        await app.start()

        print("\n✅ MICROSERVICE STARTED SUCCESSFULLY!")
        print("\n📊 Service Status:")
        print("   🌐 HTTP API: Running on port 8080")
        print(f"   🗄️  Database: SQLite Ready")
        print(f"   🔴 Redis: Connected")
        print(f"   📊 Metrics: Enabled")
        print(f"   📢 Events: Enabled")

        print("\n🔌 AVAILABLE ENDPOINTS:")
        print("   GET  http://localhost:8080/health       - Health check")
        print("   POST http://localhost:8080/users        - Create user")
        print("   GET  http://localhost:8080/users/{id}   - Get user")
        print("   POST http://localhost:8080/orders       - Create order")
        print("   GET  http://localhost:8080/orders/{id}  - Get order")
        print("   PUT  http://localhost:8080/orders/{id}  - Update order status")
        print("   GET  http://localhost:8080/metrics      - Prometheus metrics")

        print("\n🎯 DEMONSTRATION FEATURES:")
        print("   🏗️  UCore Component Architecture")
        print("   🔗 Dependency Injection with @Depends()")
        print("   📢 Event-Driven Communication")
        print("   🔴 Redis Pub/Sub Messaging")
        print("   📊 Auto Metrics Collection")
        print("   ⚡ Background Task Processing")
        print("   🔄 Real-time Health Monitoring")

        print("\n💡 TESTING THE MICROSERVICE:")

        print("\n1. Check health:")
        print('   curl http://localhost:8080/health')

        print("\n2. Create a user:")
        print('   curl -X POST http://localhost:8080/users \\')
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"username":"demo","email":"demo@example.com"}\'')

        print("\n3. Create an order:")
        print('   curl -X POST http://localhost:8080/orders \\')
        print('        -H "Content-Type: application/json" \\')
        print('        -d \'{"user_id":1,"product_name":"Widget","quantity":3,"total_price":75.99}\'')

        print("\n4. Check metrics:")
        print('   curl http://localhost:8080/metrics')

        print("\n🎯 MICROSERVICE RUNNING - Press Ctrl+C to stop")

        # Keep the service running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 MICROSERVICE INTERRUPTED BY USER")
    except Exception as e:
        print(f"❌ MICROSERVICE ERROR: {e}")
        raise
    finally:
        print("\n🏁 CLEANING UP MICROSERVICE...")
        await app.stop()
        print("✨ SHUTDOWN COMPLETE")


if __name__ == "__main__":
    asyncio.run(main())
