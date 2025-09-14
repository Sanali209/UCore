# examples/metrics_demo/main.py
"""
HTTP Metrics Demo - Prometheus Integration

This example demonstrates:
- Automatic HTTP request metrics collection
- Custom business metrics
- Metrics endpoint for Prometheus scraping
- Integration with UCore's component system

Usage:
1. Run this application: python main.py
2. Make requests: curl http://localhost:8080/hello
3. View metrics: curl http://localhost:8080/metrics
4. Use Prometheus/Grafana to scrape metrics from /metrics

Metrics Collected:
- http_requests_total: Total requests by method, endpoint, status
- http_request_duration_seconds: Request duration histogram
- http_requests_in_progress: Current active requests
- http_response_size_bytes: Response size summary
- business_metrics_total: Custom business counters
- order_value_histogram: Custom histogram for business data
"""

import sys
import asyncio
import random
import time
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.http import HttpServer
from framework.metrics import HTTPMetricsAdapter, counter, histogram, gauge
from framework.di import Depends
import aiohttp
from aiohttp import web


def get_metrics_adapter(metrics_adapter: HTTPMetricsAdapter):
    """Dependency provider for HTTPMetricsAdapter"""
    return metrics_adapter


def create_metrics_app():
    """
    Create an HTTP application with comprehensive metrics monitoring.
    """
    app = App(name="MetricsDemo")

    # Create components
    http_server = HttpServer(app)
    metrics_adapter = HTTPMetricsAdapter(app)

    # Register components
    app.register_component(lambda: http_server)
    app.register_component(lambda: metrics_adapter)

    # ---- Application Routes ----

    @http_server.route("/hello", "GET")
    async def hello_endpoint():
        """
        Simple hello endpoint that returns JSON response.
        """
        return web.json_response({
            "message": "Hello from UCore Metrics Demo!",
            "timestamp": int(time.time()),
            "version": "1.0"
        })

    @http_server.route("/delay/{seconds}", "GET")
    async def delay_endpoint(request: web.Request):
        """
        Endpoint that simulates processing delay.
        Good for testing request duration metrics.
        """
        try:
            seconds = float(request.match_info['seconds'])
            if seconds < 0 or seconds > 10:
                return web.json_response({
                    "error": "Seconds must be between 0 and 10"
                }, status=400)

            await asyncio.sleep(seconds)

            return web.json_response({
                "message": f"Waited {seconds} seconds",
                "actual_delay": seconds
            })
        except ValueError:
            return web.json_response({
                "error": "Invalid seconds parameter"
            }, status=400)

    @http_server.route("/order", "POST")
    async def order_endpoint(request: web.Request):
        """
        Simulate processing an order with custom business metrics.
        """
        try:
            data = await request.json()
            order_value = data.get('value', 100.0)
            order_type = data.get('type', 'standard')

            # Simulate order processing
            processing_time = random.uniform(0.1, 0.5)
            await asyncio.sleep(processing_time)

            # Custom business metric tracking
            process_order.metrics_counter.labels(order_type=order_type).inc()
            process_order.value_histogram.labels(order_type=order_type).observe(order_value)

            success = random.choice([True, True, False])  # 66% success rate

            if success:
                return web.json_response({
                    "message": "Order processed successfully",
                    "order_id": f"order_{random.randint(1000, 9999)}",
                    "value": order_value,
                    "type": order_type,
                    "processing_time": processing_time
                }, status=201)
            else:
                # Simulate occasional errors
                return web.json_response({
                    "error": "Payment processing failed",
                    "retry": True
                }, status=500)

        except Exception as e:
            return web.json_response({
                "error": f"Server error: {str(e)}"
            }, status=500)

    @http_server.route("/stats", "GET")
    async def stats_endpoint(metrics_adapter=Depends(get_metrics_adapter)):
        """
        Custom endpoint that tracks its own metrics.
        """
        # This endpoint will be tracked by the HTTP middleware
        # plus we can add custom business metrics here
        stats_endpoint.custom_requests.inc()

        return web.json_response({
            "message": "System statistics endpoint",
            "uptime_seconds": int(time.time() - getattr(metrics_adapter, '_start_time', time.time())),
            "components": ["HttpServer", "HTTPMetricsAdapter"],
            "total_custom_requests": stats_endpoint.custom_requests._value
        })

    @http_server.route("/metrics", "GET")
    async def metrics_endpoint():
        """
        Endpoint to serve Prometheus metrics.
        This will be scraped by Prometheus for monitoring.
        """
        from framework.metrics import generate_latest, CONTENT_TYPE_LATEST

        metrics_output = generate_latest().decode('utf-8')

        # Log some basic stats about the metrics
        lines = metrics_output.split('\n')
        metric_count = len([line for line in lines if line.startswith('#')])
        series_count = len([line for line in lines if line.startswith('http_')])

        return web.Response(
            text=metrics_output,
            content_type=CONTENT_TYPE_LATEST,
            headers={'Cache-Control': 'no-cache, no-store, must-revalidate'}
        )

    @http_server.route("/load-test", "GET")
    async def load_test_endpoint():
        """
        Generate some load for testing metrics under pressure.
        Makes multiple internal requests simultaneously.
        """
        async def make_request():
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get('http://localhost:8080/hello') as resp:
                        return resp.status
                except Exception:
                    return 500

        # Make multiple concurrent requests
        tasks = [make_request() for _ in range(10)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        success_count = sum(1 for r in results if r == 200)
        error_count = len(results) - success_count

        return web.json_response({
            "message": "Load test completed",
            "concurrent_requests": len(tasks),
            "successful": success_count,
            "errors": error_count,
            "results": results
        })

    @http_server.route("/", "GET")
    async def root_endpoint():
        """
        Root endpoint with API documentation and usage information.
        """
        return web.json_response({
            "message": "UCore HTTP Metrics Demo",
            "version": "1.0",
            "description": "Demonstrates Prometheus metrics integration",
            "endpoints": {
                "GET /hello": "Simple JSON response",
                "GET /delay/{seconds}": "Simulates delay (0-10 seconds)",
                "POST /order": "Process order with business metrics",
                "GET /stats": "System statistics with custom metrics",
                "GET /load-test": "Generate concurrent requests for testing",
                "GET /metrics": "Prometheus metrics endpoint",
                "GET /": "This documentation"
            },
            "monitoring_features": [
                "HTTP request/response metrics",
                "Request duration histograms",
                "Error rate tracking",
                "Business metric counters",
                "Custom histograms for order values",
                "Active request gauge"
            ],
            "curl_examples": [
                "curl http://localhost:8080/hello",
                "curl http://localhost:8080/delay/0.5",
                "curl -X POST http://localhost:8080/order -H 'Content-Type: application/json' -d '{\"value\": 99.99, \"type\": \"premium\"}'",
                "curl http://localhost:8080/metrics | head -20"
            ]
        })

    # ---- Setup Custom Metrics ----

    # Order processing metrics
    process_order = lambda: None  # Placeholder for attaching metrics
    process_order.metrics_counter = counter(
        'orders_processed_total',
        'Total number of orders processed',
        ['order_type']
    )
    process_order.value_histogram = histogram(
        'order_value_amount',
        'Order value histogram',
        ['order_type'],
        buckets=[10, 25, 50, 100, 250, 500, 1000]
    )

    # Stats endpoint custom metrics
    stats_endpoint.custom_requests = counter(
        'stats_endpoint_requests_total',
        'Total requests to stats endpoint'
    )

    return app


def main():
    """
    Main entry point for the metrics demo.
    """
    print("🚀 UCore HTTP Metrics Demo")
    print("=" * 70)
    print()
    print("This application demonstrates:")
    print("• Automatic HTTP request metrics collection")
    print("• Custom business metrics")
    print("• Prometheus integration ready")
    print("• Performance monitoring")
    print()
    print("Usage:")
    print("1. Start the application: python main.py")
    print("2. Make requests to see metrics")
    print("3. Check /metrics endpoint for Prometheus format")
    print()
    print("Try these commands:")
    print("  curl http://localhost:8080/hello")
    print("  curl http://localhost:8080/delay/0.2")
    print("  curl -X POST http://localhost:8080/order -H 'Content-Type: application/json' -d '{\"value\": 49.99}'")
    print("  curl http://localhost:8080/metrics")
    print("  curl http://localhost:8080/load-test")
    print()
    print("Metrics include:")
    print("  • http_requests_total (by method, endpoint, status)")
    print("  • http_request_duration_seconds (histogram)")
    print("  • http_requests_in_progress (active requests)")
    print("  • orders_processed_total (business metric)")
    print("  • order_value_amount (business histogram)")
    print()
    print("⚡ Ready for monitoring and metrics collection...")
    print("=" * 70)

    # Create and run the application
    metrics_app = create_metrics_app()
    metrics_app.run()


if __name__ == "__main__":
    main()
