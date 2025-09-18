# framework/metrics.py
"""
Prometheus metrics middleware for HTTP request monitoring.
Provides comprehensive observability for UCore applications.
"""

import sys
import types

# Patch for resource.getpagesize on Windows before prometheus_client import
try:
    import resource
except ImportError:
    resource = types.SimpleNamespace()
if not hasattr(resource, "getpagesize"):
    resource.getpagesize = lambda: 4096

import prometheus_client
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    generate_latest, CONTENT_TYPE_LATEST
)
from aiohttp import web
import time
from typing import Dict, Any, Optional
from ..core.component import Component
from ..core.config import Config


class HTTPMetricsAdapter(Component):
    """
    HTTP metrics adapter that provides comprehensive monitoring of HTTP requests.
    Integrates Prometheus metrics with the existing HTTP server.
    """

    def __init__(self, app, registry=None):
        self.app = app
        self.config = app.container.get(Config)
        self.registry = registry or prometheus_client.REGISTRY

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            'http_requests_total', 'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code', 'client_ip'],
            registry=self.registry
        )

        self.http_request_duration = Histogram(
            'http_request_duration_seconds', 'HTTP request duration in seconds',
            ['method', 'endpoint', 'status_code'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
            registry=self.registry
        )

        self.http_requests_in_progress = Gauge(
            'http_requests_in_progress', 'Current number of HTTP requests in progress',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # Response Size Metrics
        self.http_response_size = Summary(
            'http_response_size_bytes', 'HTTP response size in bytes',
            ['method', 'endpoint'],
            registry=self.registry
        )

        # Error Metrics
        self.http_errors_total = Counter(
            'http_errors_total', 'Total number of HTTP errors',
            ['method', 'endpoint', 'error_type', 'status_code'],
            registry=self.registry
        )

        # Dependency injection for services
        self.http_server: Optional[Any] = None

    def metrics_route(self, path: str = "/metrics"):
        """
        Decorator to register metrics endpoint.

        Usage in HttpServer setup:
            @http_server.route("/metrics", "GET")
            @metrics_adapter.metrics_route("/metrics")
            async def get_metrics():
                pass
        """
        def metrics_handler(request):
            # Return Prometheus metrics
            return web.Response(
                text=generate_latest(self.registry).decode('utf-8'),
                content_type="text/plain",
                headers={'Cache-Control': 'no-cache, no-store, must-revalidate'}
            )
        return metrics_handler

    async def start(self):
        """
        Initialize metrics collection.
        """
        self.app.logger.info("HTTP Metrics adapter initialized")
        self.app.logger.info("Metrics will be available at /metrics endpoint")

        # Register metrics in DI container for other components
        if hasattr(self.app.container, '_singletons'):
            self.app.container._singletons[HTTPMetricsAdapter] = self

    def on_config_update(self, config):
        """
        Handle dynamic configuration updates for metrics collection.
        """
        # Check for metrics collection settings
        metrics_enabled = config.get("METRICS_ENABLED", True)
        metrics_interval = config.get("METRICS_COLLECTION_INTERVAL", 60)  # seconds

        # Log configuration changes
        self.app.logger.info(f"Metrics configuration updated - enabled: {metrics_enabled}, interval: {metrics_interval}s")

        # In a real implementation, you might:
        # - Start/stop metrics collection based on enabled setting
        # - Adjust collection intervals for periodic metrics
        # - Update Prometheus registry settings

        if not metrics_enabled:
            self.app.logger.warning("Metrics collection is disabled via configuration")
            # Note: In production, you might want to provide a way to
            # temporarily disable metrics collection

    async def stop(self):
        """
        Cleanup metrics collection.
        """
        self.app.logger.info("HTTP Metrics adapter stopped")

    def middleware(self):
        """
        Create aiohttp middleware for automatic HTTP metrics collection.

        Usage:
            # In HttpServer setup:
            http_server.web_app.middlewares.append(metrics_adapter.middleware())

        Or integrate automatically with HTTP server lifecycle.
        """
        @web.middleware
        async def http_metrics_middleware(request, handler):
            start_time = time.time()

            # Track request in progress
            self.http_requests_in_progress.labels(
                method=request.method,
                endpoint=request.path_qs
            ).inc()

            client_ip = self._get_client_ip(request)
            status_code = "unknown"
            response_size = 0

            try:
                # Process the request
                response = await handler(request)
                status_code = str(response.status)

                # Track response size if available
                if hasattr(response, 'body') and response.body:
                    response_size = len(response.body) if isinstance(response.body, bytes) else len(str(response.body))

                return response

            except Exception as e:
                # Track errors
                status_code = "500"  # Internal Server Error
                self.http_errors_total.labels(
                    method=request.method,
                    endpoint=request.path_qs,
                    error_type=type(e).__name__,
                    status_code=status_code
                ).inc()
                raise

            finally:
                # Always track metrics, regardless of success/failure
                duration = time.time() - start_time

                # Metric: Request total count
                self.http_requests_total.labels(
                    method=request.method,
                    endpoint=request.path_qs,
                    status_code=status_code,
                    client_ip=client_ip
                ).inc()

                # Metric: Request duration
                self.http_request_duration.labels(
                    method=request.method,
                    endpoint=request.path_qs,
                    status_code=status_code
                ).observe(duration)

                # Decrement in-progress count
                self.http_requests_in_progress.labels(
                    method=request.method,
                    endpoint=request.path_qs
                ).dec()

                # Metric: Response size
                if response_size > 0:
                    self.http_response_size.labels(
                        method=request.method,
                        endpoint=request.path_qs
                    ).observe(response_size)

        return http_metrics_middleware

    def _get_client_ip(self, request) -> str:
        """
        Extract client IP address from request headers.
        Handles proxy headers like X-Forwarded-For, etc.
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


# Convenience decorators for business metrics
def counter(name: str, description: str, labelnames=None):
    """
    Decorator to create a Prometheus counter for business logic.

    Example:
        @counter('user_logins_total', 'Total user logins', ['user_type', 'login_method'])
        def login_user(user, method):
            ...
            login_count.inc()  # Increment the counter

    The decorated function gets a 'counter' attribute containing the Prometheus Counter.
    """
    def decorator(func):
        counter_metric = Counter(name, description, labelnames or [])

        def wrapped(*args, **kwargs):
            # Store the counter on the function for access
            args[0].counter = counter_metric if hasattr(args[0], '__self__') else counter_metric


            return func(*args, **kwargs)

        wrapped.counter = counter_metric
        return wrapped
    return decorator


def histogram(name: str, description: str, labelnames=None, buckets=None):
    """
    Decorator to create a Prometheus histogram for measuring durations/values.

    Example:
        @histogram('task_duration_seconds', 'Time spent processing tasks', ['task_type'])
        def process_task(task, task_type):
            start_time = time.time()
            try:
                # Your task processing logic
                yield from process(task)
            finally:
                duration = time.time() - start_time
                process_task.histogram.labels(task_type=task_type).observe(duration)
    """
    def decorator(func):
        histogram_metric = Histogram(
            name, description, labelnames or [],
            buckets=buckets or Histogram.DEFAULT_BUCKETS
        )

        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        wrapped.histogram = histogram_metric
        return wrapped
    return decorator


def gauge(name: str, description: str, labelnames=None):
    """
    Decorator to create a Prometheus gauge for measuring values.

    Example:
        @gauge('active_connections', 'Current active connections', ['service'])
        def handle_connection(service_name):
            # Increment gauge when connection starts
            handle_connection.gauge.labels(service=service_name).inc()

            try:
                yield from handle_connection_logic()
            finally:
                # Decrement gauge when connection ends
                handle_connection.gauge.labels(service=service_name).dec()
    """
    def decorator(func):
        gauge_metric = Gauge(name, description, labelnames or [])

        def wrapped(*args, **kwargs):
            return func(*args, **kwargs)

        wrapped.gauge = gauge_metric
        return wrapped
    return decorator
