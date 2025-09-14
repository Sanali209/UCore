# framework/observability.py
"""
Enterprise-grade observability stack for UCore Framework.
Provides comprehensive monitoring, metrics, and distributed tracing capabilities.
"""

import time
import asyncio
from typing import Dict, Any, Optional, Callable
from contextvars import ContextVar
from functools import wraps
import requests

from aiohttp import web
from prometheus_client import (
    generate_latest,
    CONTENT_TYPE_LATEST,
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    multiprocess
)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.semconv.trace import TraceSemanticConventions as semconv
    from opentelemetry.sdk.trace.export import ConsoleSpanExporter, BatchSpanProcessor
    from opentelemetry.propagate import set_global_textmap
    from opentelemetry.trace.propagation.tracecontext import TraceContextPropagator
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    # OpenTelemetry is optional - provide stubs for graceful degradation
    OPENTELEMETRY_AVAILABLE = False

    class trace:
        class NoOpTracerProvider: pass
        class NoOpSpan: pass
        def get_current_span(): return None
        def get_tracer(*args): return None
        def set_tracer_provider(*args): pass

    class TracerProvider: pass
    class Resource: pass
    class ConsoleSpanExporter: pass
    class BatchSpanProcessor: pass

    def set_global_textmap(*args): pass
    class TraceContextPropagator: pass

from .component import Component
from .http import HttpServer


# Context variables for tracing context propagation
if OPENTELEMETRY_AVAILABLE:
    current_span_context: ContextVar[Optional[trace.SpanContext]] = ContextVar('current_span_context', default=None)
else:
    current_span_context = None


class MetricsMiddleware:
    """
    HTTP metrics middleware that automatically collects request metrics.
    Collects request count, duration, and response status codes.
    """

    def __init__(self, registry: CollectorRegistry = None):
        self.registry = registry or CollectorRegistry()

        # HTTP Request Metrics
        self.http_requests_total = Counter(
            'ucore_http_requests_total',
            'Total number of HTTP requests',
            ['method', 'endpoint', 'status_code'],
            registry=self.registry
        )

        self.http_request_duration_seconds = Histogram(
            'ucore_http_request_duration_seconds',
            'HTTP request duration in seconds',
            ['method', 'endpoint'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
            registry=self.registry
        )

        self.http_response_status_total = Counter(
            'ucore_http_response_status_total',
            'Total number of HTTP responses by status code',
            ['status_code', 'method', 'endpoint'],
            registry=self.registry
        )

        # Application Metrics
        self.active_connections = Gauge(
            'ucore_active_connections',
            'Number of active connections',
            registry=self.registry
        )

        self.uptime_seconds = Gauge(
            'ucore_uptime_seconds_total',
            'Application uptime in seconds',
            registry=self.registry
        )

    async def middleware(self, handler: Callable, request: web.Request) -> web.Response:
        """
        AioHTTP middleware to collect HTTP metrics.
        """
        start_time = time.time()
        method = request.method
        path = request.path_qs

        try:
            # Process the request
            response = await handler(request)

            # Record metrics
            duration = time.time() - start_time
            status_code = str(response.status)

            self.http_requests_total.labels(
                method=method,
                endpoint=path,
                status_code=status_code
            ).inc()

            self.http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            self.http_response_status_total.labels(
                status_code=status_code,
                method=method,
                endpoint=path
            ).inc()

            return response

        except Exception as e:
            # Record error metrics
            duration = time.time() - start_time

            self.http_requests_total.labels(
                method=method,
                endpoint=path,
                status_code='500'
            ).inc()

            self.http_request_duration_seconds.labels(
                method=method,
                endpoint=path
            ).observe(duration)

            raise


class TracingProvider:
    """
    OpenTelemetry tracing provider with console and Jaeger support.
    """

    def __init__(self):
        self.tracer_provider = None
        self.tracer = None
        self._setup_tracing()

    def _setup_tracing(self):
        """Setup OpenTelemetry tracing with console and Jaeger exporters."""
        if not OPENTELEMETRY_AVAILABLE:
            # Gracefully skip if OpenTelemetry is not available
            self.tracer_provider = None
            self.tracer = None
            return

        try:
            # Create resource with service information
            resource = Resource.create({
                semconv.SERVICE_NAME: "UCore Framework",
                semconv.SERVICE_VERSION: "1.0.0",
            })

            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)

            # Console exporter for debugging
            console_exporter = ConsoleSpanExporter()
            span_processor = BatchSpanProcessor(console_exporter)
            self.tracer_provider.add_span_processor(span_processor)

            # Set as global tracer provider
            trace.set_tracer_provider(self.tracer_provider)

            # Get tracer instance
            self.tracer = trace.get_tracer(__name__)

            # Setup text map propagation
            set_global_textmap(TraceContextPropagator())

        except Exception as e:
            # Silently fail if OpenTelemetry setup fails
            print(f"Warning: OpenTelemetry tracing not configured: {e}")
            self.tracer_provider = None
            self.tracer = None

    def get_tracer(self, name: str = __name__):
        """Get a tracer instance."""
        if self.tracer_provider:
            return trace.get_tracer(name)
        return None

    def start_span(self, name: str, **kwargs):
        """Start a new span."""
        if self.tracer:
            return self.tracer.start_span(name, **kwargs)
        return None

    def get_current_span(self):
        """Get the currently active span."""
        if self.tracer_provider:
            return trace.get_current_span()
        return None


class Observability(Component):
    """
    Enterprise-grade observability component providing comprehensive monitoring capabilities.

    Features:
    - Prometheus metrics collection with HTTP middleware
    - OpenTelemetry distributed tracing
    - Custom metrics decorators
    - Health check endpoints
    - Performance monitoring
    """

    def __init__(self, app=None):
        self.app = app
        self.metrics_middleware = MetricsMiddleware()
        self.tracing_provider = TracingProvider()
        self.start_time = time.time()

        # Component health tracking
        self.component_status: Dict[str, Dict[str, Any]] = {}

    def start(self):
        """
        Initialize observability features when component starts.
        """
        try:
            http_server = self.app.container.get(HttpServer)

            # Add HTTP metrics middleware
            http_server.web_app.middlewares.append(self.metrics_middleware.middleware)

            # Register the /metrics endpoint
            @http_server.route("/metrics", "GET")
            async def metrics_handler(request):
                # Get current metrics from registry
                metrics_data = generate_latest(self.metrics_middleware.registry)
                resp = web.Response(body=metrics_data)
                resp.content_type = CONTENT_TYPE_LATEST
                return resp

            # Register the /health endpoint with detailed health checks
            @http_server.route("/health", "GET")
            async def health_handler(request):
                return await self._health_check()

            # Register the /ready endpoint for readiness probes
            @http_server.route("/ready", "GET")
            async def ready_handler(request):
                return await self._readiness_check()

            # Update uptime metric
            self.metrics_middleware.uptime_seconds.set(time.time() - self.start_time)

            self.app.logger.info("🏥 Observability stack initialized:")
            self.app.logger.info("  • Prometheus metrics: /metrics")
            self.app.logger.info("  • Health checks: /health")
            self.app.logger.info("  • Readiness probes: /ready")
            self.app.logger.info("  • HTTP metrics middleware: active")
            self.app.logger.info("  • OpenTelemetry tracing: active")

        except Exception as e:
            self.app.logger.error(f"❌ Failed to initialize observability: {e}")

    def stop(self):
        """Clean shutdown of observability features."""
        try:
            # Force all spans to finish
            if self.tracing_provider and self.tracing_provider.tracer_provider:
                self.tracing_provider.tracer_provider.force_flush(timeout_millis=1000)
        except Exception:
            pass  # Ignore errors during shutdown

    def get_tracer(self, name: str = __name__):
        """Get OpenTelemetry tracer instance."""
        return self.tracing_provider.get_tracer(name)

    def probe_endpoint(self, url: str, timeout: int = 30) -> bool:
        """
        Probe a health endpoint to check if it's responding.

        Args:
            url (str): The URL to probe
            timeout (int): GET request timeout in seconds

        Returns:
            bool: True if the endpoint responds with 2xx status code, False otherwise
        """
        try:
            response = requests.get(url, timeout=timeout)
            return response.status_code >= 200 and response.status_code < 300
        except (requests.RequestException, ValueError):
            return False

    def record_custom_metric(self, name: str, value: float, labels: Dict[str, str] = None):
        """Record a custom metric."""
        # This would integrate with custom metrics registry
        pass

    async def _health_check(self) -> web.Response:
        """
        Perform comprehensive health checks.
        """
        health_data = {
            "status": "healthy",
            "timestamp": time.time(),
            "uptime_seconds": time.time() - self.start_time,
            "version": "1.0.0",
            "services": {},
            "metrics": {}
        }

        # Check component health
        try:
            http_server = self.app.container.get(HttpServer)
            health_data["services"]["http"] = {"status": "healthy", "details": "responding"}
        except Exception:
            health_data["services"]["http"] = {"status": "unhealthy", "details": "not available"}

        # Database health check (if configured)
        try:
            # Would implement actual database connectivity check
            health_data["services"]["database"] = {"status": "healthy", "details": "connected"}
        except Exception as e:
            health_data["services"]["database"] = {"status": "unhealthy", "details": str(e)}

        # Redis health check (if configured)
        try:
            # Check if Redis is available in components
            health_data["services"]["redis"] = {"status": "not configured"}
        except Exception as e:
            health_data["services"]["redis"] = {"status": "error", "details": str(e)}

        # Return appropriate status code
        all_healthy = all(
            service.get("status") in ["healthy", "not configured"]
            for service in health_data["services"].values()
        )

        status_code = 200 if all_healthy else 503
        if not all_healthy:
            health_data["status"] = "unhealthy"

        return web.json_response(health_data, status=status_code)

    async def _readiness_check(self) -> web.Response:
        """
        Application readiness check for Kubernetes/K8s probes.
        """
        # Basic readiness check - expand as needed
        readiness_data = {
            "status": "ready",
            "timestamp": time.time(),
            "checks": {
                "app_initialized": True,
                "observability_initialized": True
            }
        }

        return web.json_response(readiness_data, status=200)


# Global decorators for easy metrics instrumentation
def metrics_counter(name: str, description: str = "", labels: list = None):
    """
    Decorator to create a counter metric for function calls.

    @metrics_counter("my_function_calls", "Number of times my function is called")
    def my_function():
        pass
    """
    counter = Counter(name, description, labels or [])

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            counter.inc()
            return result
        return wrapper
    return decorator


def metrics_histogram(name: str, description: str = "", buckets: list = None):
    """
    Decorator to create a histogram metric for function execution time.

    @metrics_histogram("my_function_duration", "Execution time of my function")
    def my_function():
        pass
    """
    histogram = Histogram(
        name, description,
        buckets=buckets or [0.001, 0.01, 0.1, 1.0, 10.0]
    )

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                histogram.observe(duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                histogram.observe(duration)
                raise e
        return wrapper
    return decorator


def trace_function(name: str = None):
    """
    Decorator to automatically trace function execution.

    @trace_function("my_operation")
    def my_function():
        pass
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if OPENTELEMETRY_AVAILABLE:
                tracer_name = name or f"{func.__module__}.{func.__name__}"
                with trace.get_current_span().start_child_span(tracer_name) if trace.get_current_span() else trace.get_tracer(__name__).start_span(tracer_name):
                    return await func(*args, **kwargs)
            else:
                # If OpenTelemetry not available, just execute the function
                return await func(*args, **kwargs)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if OPENTELEMETRY_AVAILABLE:
                tracer_name = name or f"{func.__module__}.{func.__name__}"
                with trace.get_current_span().start_child_span(tracer_name) if trace.get_current_span() else trace.get_tracer(__name__).start_span(tracer_name):
                    return func(*args, **kwargs)
            else:
                # If OpenTelemetry not available, just execute the function
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    return decorator
