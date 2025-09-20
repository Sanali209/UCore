"""Metrics collection logic module (decomposed from observability.py)."""

import time
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    CollectorRegistry,
    CONTENT_TYPE_LATEST,
    generate_latest
)
from aiohttp import web
from functools import wraps

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

    async def middleware(self, handler, request: web.Request) -> web.Response:
        start_time = time.time()
        method = request.method
        path = request.path_qs

        try:
            response = await handler(request)
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

        except Exception:
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

def metrics_counter(name: str, description: str = "", labels: list = None):
    """
    Decorator to create a counter metric for function calls.
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
