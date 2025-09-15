# examples/observability_demo/main.py
"""
Observability Demo - UCore Framework Enterprise Observability Features

This example demonstrates comprehensive observability capabilities:
- HTTP metrics middleware (automatic request counting, duration, status codes)
- Custom metrics decorators (@metrics_counter, @metrics_histogram)
- OpenTelemetry distributed tracing (@trace_function)
- Advanced health checks with detailed service monitoring
- Readiness probes for Kubernetes deployments

Features demonstrated:
1. Automatic HTTP metrics collection for all endpoints
2. Custom business logic metrics with decorators
3. Distributed tracing with context propagation
4. Comprehensive health checks (HTTP, Database, Redis)
5. Prometheus-compatible metrics output
6. Readiness checks for deployment orchestration

Usage:
    python examples/observability_demo/main.py

Endpoints:
    GET /api/users          - List users (with tracing and metrics)
    GET /api/users/{id}     - Get specific user
    POST /api/users         - Create new user
    POST /api/users/{id}/process - Process user data (background task)
    GET /metrics            - Prometheus metrics
    GET /health             - Detailed health check
    GET /ready              - Readiness for Kubernetes

CLI Demo:
    # View system status
    curl http://localhost:8090/health
    curl http://localhost:8090/ready
    curl http://localhost:8090/metrics

    # Test API with metrics
    curl http://localhost:8090/api/users
    curl -X POST http://localhost:8090/api/users -H "Content-Type: application/json" -d '{"name":"John","email":"john@example.com"}'

    # Check metrics
    curl http://localhost:8090/metrics
"""

import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass

from aiohttp import web
import aiohttp

import sys
sys.path.insert(0, 'd:/UCore')

from framework import App
from framework.web import HttpServer
from framework.monitoring.observability import Observability, metrics_counter, metrics_histogram, trace_function
from framework.processing.background import TaskQueueAdapter
from framework.processing.tasks import task


@dataclass
class User:
    """Simple user model for demo."""
    id: int
    name: str
    email: str
    created_at: float


class UserService:
    """User service with observability decorators."""

    def __init__(self):
        self.users: Dict[int, User] = {}
        self.next_id = 1

    @metrics_counter(
        "user_service_get_calls_total",
        "Total number of get_user calls",
        ["result"]
    )
    @metrics_histogram(
        "user_service_get_duration_seconds",
        "Time spent getting users"
    )
    @trace_function("get_user")
    def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID with observability."""
        # Simulate some processing time for demo
        time.sleep(0.01)

        user = self.users.get(user_id)
        return user

    @metrics_counter(
        "user_service_list_calls_total",
        "Total number of list_users calls"
    )
    @trace_function("list_users")
    def list_users(self) -> List[User]:
        """List all users with observability."""
        time.sleep(0.005)  # Simulate processing
        return list(self.users.values())

    @metrics_counter(
        "user_service_create_calls_total",
        "Total number of create_user calls",
        ["success"]
    )
    @trace_function("create_user")
    def create_user(self, name: str, email: str) -> User:
        """Create new user with observability."""
        time.sleep(0.02)  # Simulate processing

        user = User(
            id=self.next_id,
            name=name,
            email=email,
            created_at=time.time()
        )

        self.users[self.next_id] = user
        self.next_id += 1

        return user

    @trace_function("process_user_data")
    @metrics_histogram("user_process_duration_seconds", "Time to process user data")
    def process_user_data(self, user_id: int) -> Dict[str, any]:
        """Process user data with observability."""
        time.sleep(0.1)  # Simulate heavy processing

        user = self.get_user(user_id)
        if not user:
            return {"error": f"User {user_id} not found"}

        # Simulate processing result
        result = {
            "user_id": user_id,
            "processed": True,
            "data": f"{user.name}'s data processed successfully",
            "timestamp": time.time()
        }

        return result


def create_observability_demo_app():
    """
    Create the observability demo application with comprehensive monitoring.

    This example shows:
    - HTTP metrics middleware (automatic collection)
    - Custom business metrics with decorators
    - Distributed tracing with decorators
    - Advanced health checks
    - Readiness probes
    - Background task integration
    """

    # Initialize the application
    app = App("ObservabilityDemo")
    user_service = UserService()

    # Register services in DI container
    from framework.core.di import Container
    if isinstance(app.container, Container):
        app.container.register_instance(user_service, UserService)

    # Initialize components
    http_server = HttpServer(app, port=8090)  # Use different port to avoid conflicts
    observability = Observability(app)
    task_adapter = TaskQueueAdapter(app)

    # Register all components
    app.register_component(lambda: http_server)
    app.register_component(lambda: observability)
    app.register_component(lambda: task_adapter)

    # API Routes with observability annotations
    @http_server.route("/api/users", "GET")
    @trace_function("list_users_endpoint")
    async def list_users_endpoint(request):
        """List all users with automatic metrics and tracing."""
        users_data = []
        for user in user_service.list_users():
            users_data.append({
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user.created_at))
            })

        return web.json_response({
            "users": users_data,
            "count": len(users_data),
            "timestamp": time.time()
        })

    @http_server.route("/api/users/{user_id}", "GET")
    @trace_function("get_user_endpoint")
    async def get_user_endpoint(request):
        """Get specific user with automatic metrics and tracing."""
        user_id = int(request.match_info['user_id'])

        try:
            user = user_service.get_user(user_id)
            if not user:
                return web.json_response(
                    {"error": f"User {user_id} not found"},
                    status=404
                )

            return web.json_response({
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "created_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(user.created_at))
                }
            })

        except ValueError:
            return web.json_response({"error": "Invalid user ID"}, status=400)

    @http_server.route("/api/users", "POST")
    @trace_function("create_user_endpoint")
    async def create_user_endpoint(request):
        """Create new user with automatic metrics and tracing."""
        try:
            data = await request.json()
            name = data.get('name')
            email = data.get('email')

            if not name or not email:
                return web.json_response(
                    {"error": "Name and email are required"},
                    status=400
                )

            user = user_service.create_user(name, email)

            return web.json_response({
                "message": "User created successfully",
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email
                }
            }, status=201)

        except Exception as e:
            return web.json_response({"error": str(e)}, status=400)

    @http_server.route("/api/users/{user_id}/process", "POST")
    @trace_function("process_user_endpoint")
    async def process_user_endpoint(request):
        """Process user data with background task."""
        user_id = int(request.match_info['user_id'])

        # Queue background task
        task_result = task_adapter.send_task(
            'examples.observability_demo.main.UserService.process_user_data',
            args=[user_id]
        )

        return web.json_response({
            "message": "Processing queued successfully",
            "user_id": user_id,
            "task_id": str(task_result.id) if task_result else "background_processing",
            "status": "processing"
        })

    # Demo endpoints with different response patterns
    @http_server.route("/api/delayed", "GET")
    async def delayed_endpoint(request):
        """Endpoint with artificial delay to demonstrate metrics."""
        delay = float(request.query.get('delay', '0.1'))
        await asyncio.sleep(delay)
        return web.json_response({"message": f"Delayed by {delay}s"})

    @http_server.route("/api/error", "GET")
    async def error_endpoint(request):
        """Endpoint that always returns 500 to demonstrate error metrics."""
        return web.json_response({"error": "This is a test error"}, status=500)

    # Demo endpoint to show trace context propagation
    @http_server.route("/api/chained", "GET")
    @trace_function("chained_operations")
    async def chained_endpoint(request):
        """Demonstrate chained operations with trace context."""
        user_ids = [1, 2, 3]  # Will result in errors for missing users

        results = []
        for user_id in user_ids:
            # This will create child spans
            user_result = await get_user_endpoint(request)
            results.append(user_result)

        return web.json_response({
            "message": "Chained operations completed",
            "results": results
        })

    return app


def show_observability_demo_help():
    """
    Display comprehensive help information for the observability demo.
    """

    print("🔍 UCore Framework - Observability Demo")
    print("=" * 60)
    print()
    print("This demo showcases enterprise-grade observability features:")
    print("• HTTP metrics middleware (automatic collection)")
    print("• Custom metrics decorators (@metrics_counter, @metrics_histogram)")
    print("• Distributed tracing (@trace_function)")
    print("• Advanced health checks (/health, /ready)")
    print("• Prometheus-compatible metrics (/metrics)")
    print("• Background task monitoring")
    print()
    print("🚀 Quick Start:")
    print()
    print("1️⃣ Start the server:")
    print("   python examples/observability_demo/main.py")
    print()
    print("2️⃣ Test API endpoints:")
    print("   curl http://localhost:8080/api/users")
    print("   curl http://localhost:8080/api/users -X POST \\")
    print("        -H \"Content-Type: application/json\" \\")
    print("        -d '{\"name\":\"Alice\",\"email\":\"alice@example.com\"}'")
    print()
    print("3️⃣ View metrics:")
    print("   curl http://localhost:8080/metrics")
    print()
    print("4️⃣ Check health:")
    print("   curl http://localhost:8080/health")
    print("   curl http://localhost:8080/ready")
    print()
    print("5️⃣ Generate traffic to see metrics:")
    print("   for i in {1..10}; do curl -s http://localhost:8080/api/users/$i; done")
    print("   curl http://localhost:8080/api/delayed?delay=0.2")
    print("   curl http://localhost:8080/api/error")
    print()
    print("6️⃣ Check updated metrics:")
    print("   curl http://localhost:8080/metrics | grep -E \"(requests_total|duration_seconds|response_status_total)\"")
    print()
    print("📊 Monitoring Endpoints:")
    print()
    print("Endpoint           Purpose                          Features")
    print("-" * 55)
    print("/metrics           Prometheus metrics               Requests, duration, status codes")
    print("/health            Detailed health checks          HTTP, Database, Redis status")
    print("/ready             Kubernetes readiness            Deployment orchestration")
    print("/api/users         User CRUD operations            Full observability stack")
    print("/api/delayed       Test delayed responses          Metrics timing demonstration")
    print("/api/error         Generate error responses        Error rate monitoring")
    print("/api/chained       Demonstrate trace context       Child spans and propagation")
    print()
    print("🎯 Metrics Collected:")
    print()
    print("• HTTP request count by method/endpoint/status")
    print("• Request duration histograms")
    print("• Error rate and response status tracking")
    print("• Custom business metrics (user operations)")
    print("• Function execution timing")
    print("• Service health and uptime")
    print("• Distributed tracing spans")
    print()
    print("🔗 Prometheus Integration:")
    print("   Add this to prometheus.yml:")
    print("   - job_name: 'ucore-demo'")
    print("     static_configs:")
    print("     - targets: ['localhost:8080']")
    print()
    print("=" * 60)


def main():
    """
    Main entry point for the observability demo.
    """
    if len(aiohttp.__dict__) == 0:
        print("aiohttp library not available in this context")
        return

    # Show help if no arguments provided
    if len(aiohttp.__dict__) > 0:  # Simulate checking for demo mode
        show_observability_demo_help()
        print("\n🌐 Starting UCore Observability Demo Server...")

        try:
            demo_app = create_observability_demo_app()
            demo_app.run()
        except Exception as e:
            print(f"❌ Error starting observability demo: {e}")
            print("Make sure all dependencies are installed:")
            print("   pip install aiohttp prometheus-client opentelemetry-api opentelemetry-sdk")


if __name__ == "__main__":
    main()
