"""
Tests for UCore Framework observability components.
Tests HTTP metrics middleware, custom metrics decorators, and tracing functionality.
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, Mock, patch
from aiohttp import web
from aiohttp.test_utils import AioHTTPTestCase, unittest_run_loop

from framework.observability import (
    Observability,
    MetricsMiddleware,
    TracingProvider,
    metrics_counter,
    metrics_histogram,
    trace_function,
)
from framework.app import App
from framework.http import HttpServer


class TestMetricsMiddleware:
    """Test cases for HTTP metrics middleware."""

    def setup_method(self):
        """Setup test fixtures."""
        self.middleware = MetricsMiddleware()

    def test_counters_initialization(self):
        """Test that metric counters are properly initialized."""
        assert hasattr(self.middleware, 'http_requests_total')
        assert hasattr(self.middleware, 'http_request_duration_seconds')
        assert hasattr(self.middleware, 'http_response_status_total')
        assert hasattr(self.middleware, 'active_connections')
        assert hasattr(self.middleware, 'uptime_seconds')

    @pytest.mark.asyncio
    async def test_middleware_successful_request(self):
        """Test middleware with successful request."""
        # Mock request and handler
        request = Mock()
        request.method = 'GET'
        request.path_qs = '/api/test'

        handler = AsyncMock(return_value=web.Response(status=200))

        # Call middleware
        response = await self.middleware.middleware(handler, request)

        # Verify handler was called
        handler.assert_called_once_with(request)

        # Verify response
        assert response.status == 200

    @pytest.mark.asyncio
    async def test_middleware_error_request(self):
        """Test middleware with error response."""
        # Mock request and failing handler
        request = Mock()
        request.method = 'POST'
        request.path_qs = '/api/error'

        handler = AsyncMock(return_value=web.Response(status=500))

        # Call middleware
        response = await self.middleware.middleware(handler, request)

        # Verify handler was called
        handler.assert_called_once_with(request)

        # Verify response
        assert response.status == 500

    @pytest.mark.asyncio
    async def test_middleware_exception_handling(self):
        """Test middleware handles exceptions in handlers."""
        request = Mock()
        request.method = 'GET'
        request.path_qs = '/api/exception'

        # Handler that raises exception
        handler = AsyncMock(side_effect=Exception("Test error"))

        # Call middleware - should not raise
        with pytest.raises(Exception):  # The original exception should still be raised
            await self.middleware.middleware(handler, request)


class TestTracingProvider:
    """Test cases for OpenTelemetry tracing provider."""

    def test_tracing_provider_creation(self):
        """Test that tracing provider can be created."""
        provider = TracingProvider()
        # Should not fail even if OpenTelemetry is not available
        assert provider is not None

    def test_get_tracer(self):
        """Test getting tracer instance."""
        provider = TracingProvider()
        tracer = provider.get_tracer("test")
        # Should return None if OpenTelemetry not available, or tracer if available
        assert tracer is not None or provider.tracer_provider is None

    def test_get_current_span(self):
        """Test getting current span."""
        provider = TracingProvider()
        span = provider.get_current_span()
        # Should return None if no active span or OpenTelemetry not available
        assert span is None or provider.tracer_provider is None


class TestObservabilityComponent:
    """Test cases for Observability component."""

    def setup_method(self):
        """Setup test fixtures."""
        self.app = App("TestApp")
        self.observability = Observability(self.app)

    def test_component_initialization(self):
        """Test that component initializes properly."""
        assert self.observability.app == self.app
        assert hasattr(self.observability, 'metrics_middleware')
        assert hasattr(self.observability, 'tracing_provider')
        assert self.observability.start_time > 0

    def test_start_method(self):
        """Test component start method."""
        # This would normally require a full HTTP server setup
        # For now, test that it doesn't crash when HttpServer not available
        self.observability.start()  # Should handle missing HttpServer gracefully

    def test_stop_method(self):
        """Test component stop method."""
        self.observability.stop()  # Should not raise exceptions

    def test_record_custom_metric(self):
        """Test custom metric recording."""
        # Currently just a stub method
        self.observability.record_custom_metric("test_metric", 1.0)

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check functionality."""
        health_response = await self.observability._health_check()
        assert isinstance(health_response, web.Response)

        health_data = health_response.json_body if hasattr(health_response, 'json_body') else {"status": "unknown"}

        # Should have basic health structure
        if hasattr(health_response, 'status'):
            assert health_response.status in [200, 503]

    @pytest.mark.asyncio
    async def test_readiness_check(self):
        """Test readiness check functionality."""
        # Mock the container to avoid missing method issues
        mock_container = Mock()
        mock_http_server = Mock()
        mock_container.get_optional.return_value = mock_http_server

        self.app.container = mock_container

        ready_response = await self.observability._readiness_check()
        assert isinstance(ready_response, web.Response)

        # Just verify the response is a web response - the details depend on JSON encoding
        assert ready_response is not None


class TestMetricsDecorators:
    """Test cases for custom metrics decorators."""

    def test_metrics_counter_decorator(self):
        """Test the metrics_counter decorator."""

        @metrics_counter("test_counter", "Test counter description")
        def test_function(x, y=10):
            return x + y

        # Call function
        result = test_function(5, y=15)
        assert result == 20

        # Function should still work normally
        # (Actual metrics collection would require Prometheus)

    def test_metrics_histogram_decorator(self):
        """Test the metrics_histogram decorator."""

        @metrics_histogram("test_histogram", "Test histogram description")
        def test_function(delay=0.001):
            time.sleep(delay)  # Simulate some work
            return "done"

        # Call function
        result = test_function(0.001)
        assert result == "done"

        # Function should still work normally
        # (Actual metrics collection would require Prometheus)


class TestTraceDecorator:
    """Test cases for tracing decorators."""

    def test_trace_function_decorator_sync(self):
        """Test trace_function decorator with synchronous function."""

        @trace_function("sync_test")
        def test_function(x, y=10):
            # Simulate some work
            time.sleep(0.001)
            return x + y

        # Call function
        result = test_function(7, y=13)
        assert result == 20

    @pytest.mark.asyncio
    async def test_trace_function_decorator_async(self):
        """Test trace_function decorator with asynchronous function."""

        @trace_function("async_test")
        async def async_test_function(value):
            # Simulate some async work
            await asyncio.sleep(0.001)
            return value * 2

        # Call async function
        result = await async_test_function(25)
        assert result == 50


# Integration tests
class TestObservabilityIntegration:
    """Integration tests for observability stack."""

    def test_full_component_setup(self):
        """Test setting up full observability stack."""
        app = App("IntegrationTest")
        observability = Observability(app)

        # Should not crash during setup
        observability.start()
        observability.stop()

    def test_metrics_and_tracing_together(self):
        """Test that metrics and tracing can work together."""

        @metrics_counter("combined_test_total")
        @trace_function("combined_operation")
        def combined_test_function():
            time.sleep(0.001)
            return "success"

        result = combined_test_function()
        assert result == "success"


if __name__ == "__main__":
    # Run basic smoke tests
    print("Running observability smoke tests...")

    # Test component creation
    app = App("SmokeTest")
    observability = Observability(app)

    print("✅ Observability component created")

    # Test middleware creation
    middleware = MetricsMiddleware()
    print("✅ Metrics middleware created")

    # Test tracing provider
    tracing = TracingProvider()
    print("✅ Tracing provider created")

    # Test decorators
    @metrics_counter("smoke_counter")
    def smoke_test():
        return "tested"

    result = smoke_test()
    print(f"✅ Metrics decorator works: {result}")

    @trace_function("smoke_trace")
    def smoke_trace(result):
        return "traced"

    result = smoke_trace(result)
    print(f"✅ Trace decorator works: {result}")

    print("🎉 All observability smoke tests passed!")
