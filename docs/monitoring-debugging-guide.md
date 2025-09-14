# Monitoring and Debugging Guide for UCore Framework
## Using Prometheus Metrics and OpenTelemetry Tracing for Production Applications

---

## 📋 Overview

Effective monitoring and debugging are crucial for maintaining reliable production applications. This comprehensive guide will teach you how to implement robust observability in UCore Framework applications using:

🔥 **Prometheus Metrics** - Collect and analyze performance metrics
🔍 **OpenTelemetry Tracing** - Track request flows across distributed systems
📊 **Real-time Dashboards** - Visualize system health and performance
🧹 **Debugging Strategies** - Identifying and resolving issues
📈 **Performance Optimization** - Monitoring and tuning application performance

---

## 🚀 Quick Start: Basic Metrics Integration

Let's start with a simple example of adding metrics to a UCore application:

```python
from framework.app import App
from framework.metrics import MetricsCollector
from prometheus_client import start_http_server
import time

class SampleMetricsApp(App):
    def __init__(self):
        super().__init__("SampleMetricsApp")
        self.metrics = None

    async def astart(self):
        await super().astart()

        # Initialize metrics collector
        self.metrics = MetricsCollector()

        # Create custom metrics
        self.metrics.add_counter('sample_requests_total', 'Total number of sample requests')
        self.metrics.add_gauge('sample_active_connections', 'Number of active connections')
        self.metrics.add_histogram(
            'sample_request_duration_seconds',
            'Request duration in seconds',
            ['method', 'endpoint']
        )

        # Start Prometheus HTTP server
        start_http_server(9090)
        self.logger.info("📊 Metrics server started on port 9090")

        # Start background worker
        await self.background_metrics_worker()

    async def background_metrics_worker(self):
        """Background task to update metrics."""
        while True:
            try:
                # Update gauge with synthetic data
                import random
                active_connections = random.randint(5, 25)

                # Get the gauge metric and set value
                gauge = self.metrics.get_gauge('sample_active_connections')
                gauge.set(active_connections)

                # Simulate request processing with histogram
                for i in range(random.randint(1, 5)):
                    await self.simulate_request()
                    self.metrics.get_counter('sample_requests_total').inc()

                self.logger.info(f"📊 Updated metrics - Active connections: {active_connections}")
                await asyncio.sleep(5)

            except Exception as e:
                self.logger.error(f"❌ Metrics worker error: {e}")
                await asyncio.sleep(1)

    async def simulate_request(self):
        """Simulate a request with timing."""
        with self.metrics.get_histogram('sample_request_duration_seconds').labels(
            method='GET', endpoint='/api/data'
        ).time():
            # Simulate some work
            await asyncio.sleep(random.uniform(0.1, 2.0))

app = SampleMetricsApp()

async def main():
    await app.astart()

if __name__ == "__main__":
    asyncio.run(main())
```

**What this example demonstrates:**
- **✅ Metrics setup** - Prometheus Counter, Gauge, Histogram
- **✅ Background collection** - Real-time metrics updates
- **✅ Label dimensions** - Method and endpoint categorization
- **✅ Exposure** - `/metrics` endpoint for Prometheus scraping

---

## 📊 Core Metrics Types in UCore Framework

### Understanding Prometheus Metric Types

| Metric Type | Description | UCore Usage |
|-------------|-------------|-------------|
| **Counter** | Monotonically increasing value | Request counts, errors, events |
| **Gauge** | Value that can go up or down | Active connections, queue size, memory usage |
| **Histogram** | Statistical distribution | Request latency, response sizes, operation timings |
| **Summary** | Client-side metrics | Request percentiles, complex statistical aggregations |

### UCore Framework Metrics Integration

UCore's `MetricsCollector` provides unified metrics management:

```python
from framework.metrics import MetricsCollector

# Initialize collector
metrics = MetricsCollector()

# Add metrics with labels
metrics.add_counter(
    'http_requests_total',
    'Total HTTP requests',
    labels=['method', 'endpoint', 'status']
)

metrics.add_histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint'],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]  # Custom bucket sizes
)

# Using metrics in application code
@metrics.time('http_request_duration_seconds', labels=['POST', '/api/users'])
async def create_user(request_data):
    # Your business logic here
    return await db.insert_user(request_data)
```

### Best Practices for Metric Naming

```python
# ✅ Good metric names and patterns
requests_errors_total     # Counter for total errors
api_response_time_seconds # Histogram for response times
memory_usage_bytes        # Gauge for memory usage
active_connections_total  # Gauge for connections

# ✅ Label conventions
metric_name_total{method="POST",endpoint="/api/users",status="200"}
request_duration_seconds_bucket{le="1.0"}  # Prometheus histogram buckets
```

---

## 🔍 OpenTelemetry Tracing Integration

### Setting Up Tracing with UCore Framework

First, install OpenTelemetry components:
```bash
pip install opentelemetry-distro opentelemetry-exporter-otlp-proto-grpc
```

```python
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export import ConsoleSpanExporter
from opentelemetry.trace import set_tracer_provider

# Initialize OpenTelemetry
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

# Add exporters
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",  # OTEL Collector endpoint
    insecure=True
)

# Also export to console for debugging
console_exporter = ConsoleSpanExporter()

# Set up batch processing
span_processor = BatchSpanProcessor(otlp_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)
trace.get_tracer_provider().add_span_processor(
    BatchSpanProcessor(console_exporter)
)
```

### Creating Traces in UCore Applications

```python
from framework.app import App
import opentelemetry.trace as trace

class TracedUCoreApp(App):
    def __init__(self):
        super().__init__("TracedApp")
        self.tracer = trace.get_tracer("ucore.tracer")

    async def process_order(self, order_data):
        """Process an order with comprehensive tracing."""
        with self.tracer.start_as_current_span("process_order") as span:
            span.set_attribute("order.id", order_data['id'])
            span.set_attribute("order.total", order_data['total_price'])
            span.set_attribute("order.user_id", order_data['user_id'])

            try:
                # Step 1: Validate order
                with self.tracer.start_as_current_span("validate_order") as child_span:
                    child_span.set_attribute("order.items", len(order_data.get('items', [])))
                    await self.validate_order(order_data)

                # Step 2: Process payment
                with self.tracer.start_as_current_span("process_payment") as child_span:
                    child_span.set_attribute("payment.amount", order_data['total_price'])
                    payment_result = await self.process_payment(order_data)

                # Step 3: Update inventory
                with self.tracer.start_as_current_span("update_inventory") as child_span:
                    for item in order_data['items']:
                        child_span.set_attribute(f"inventory.item_{item['id']}", item['quantity'])
                    await self.update_inventory(order_data['items'])

                # Step 4: Send notification
                with self.tracer.start_as_current_span("send_notification") as child_span:
                    child_span.set_attribute("notification.email", order_data['email'])
                    await self.send_notification(order_data)

                span.set_status(trace.Status(trace.StatusCode.OK))
                return {"status": "success", "order_id": order_data['id']}

            except Exception as ex:
                span.record_exception(ex)
                span.set_status(trace.Status(trace.StatusCode.ERROR, str(ex)))
                raise

    async def validate_order(self, order_data):
        """Validate order details."""
        with self.tracer.start_as_current_span("validate_items") as span:
            for item in order_data['items']:
                if item['quantity'] <= 0:
                    raise ValueError(f"Invalid quantity for item {item['id']}")

        with self.tracer.start_as_current_span("validate_total") as span:
            calculated_total = sum(item['price'] * item['quantity'] for item in order_data['items'])
            if abs(calculated_total - order_data['total_price']) > 0.01:
                raise ValueError("Price mismatch detected")

    async def process_payment(self, order_data):
        """Process payment with tracing."""
        await asyncio.sleep(0.5)  # Simulate payment processing
        return {"payment_id": f"pay_{order_data['id']}", "status": "completed"}

    async def update_inventory(self, items):
        """Update inventory with tracing."""
        for item in items:
            await asyncio.sleep(0.1)  # Simulate inventory update
            self.logger.info(f"Updated inventory for item {item['id']}")

    async def send_notification(self, order_data):
        """Send notification with tracing."""
        await asyncio.sleep(0.2)  # Simulate email sending
        self.logger.info(f"Sent confirmation email to {order_data['email']}")
```

### Tracing Context Propagation

```python
import opentelemetry.baggage as baggage
import opentelemetry.trace as trace

class DistributedTracingService(App):
    def __init__(self):
        super().__init__("DistributedService")
        self.tracer = trace.get_tracer(__name__)

    async def handle_request(self, request_data):
        """Handle incoming requests with context propagation."""
        with self.tracer.start_as_current_span("handle_request") as span:
            # Extract tracing context from request headers
            trace_id = request_data.get('X-Trace-Id')
            span_id = request_data.get('X-Span-Id')

            if trace_id and span_id:
                # Set parent span context
                parent_context = trace.set_span_in_context(
                    trace.NonRecordingSpan(trace.SpanContext(
                        trace_id=int(trace_id, 16),
                        span_id=int(span_id, 16),
                        is_remote=True
                    ))
                )
                with self.tracer.start_as_current_span("child_operation", context=parent_context) as child_span:
                    child_span.set_attribute("request.type", request_data['type'])
                    return await self.process_request(request_data)
            else:
                # Create new trace
                return await self.process_request(request_data)

    async def make_external_call(self, service_data):
        """Make calls to external services with trace propagation."""
        with self.tracer.start_as_current_span("external_service_call") as span:
            # Inject current trace context into headers
            span_context = span.get_span_context()

            headers = {
                'X-Trace-Id': format(span_context.trace_id, '016x'),
                'X-Span-Id': format(span_context.span_id, '016x'),
                'X-Trace-Flags': format(span_context.trace_flags, '02x')
            }

            span.set_attribute("service.name", service_data['service'])
            span.set_attribute("service.endpoint", service_data['endpoint'])

            # Make actual HTTP call with headers
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(service_data['endpoint']) as response:
                    result = await response.json()

                    # Add response timing and status
                    span.set_attribute("http.status_code", response.status)
                    span.set_attribute("http.response_time", response.elapsed.total_seconds())

                    return result
```

---

## 🏗️ Building Production Monitoring Dashboards

### Prometheus Configuration

Create a `prometheus.yml` configuration file:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  # The job name is added as a label `job=<job_name>` to any timeseries scraped from this config.
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'ucore_microservice'
    static_configs:
      - targets: ['localhost:8080']  # Your UCore app metrics port
    metrics_path: '/api/metrics'    # Custom metrics path

  - job_name: 'node'
    static_configs:
      - targets: ['localhost:9100']  # Node exporter for system metrics
```

### Grafana Dashboard Creation

#### UCore Application Dashboard

```json
{
  "dashboard": {
    "id": null,
    "title": "UCore Application Monitoring",
    "tags": ["ucore", "monitoring"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "HTTP Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total[5m])) by (method, status)",
            "legendFormat": "{{method}} {{status}}"
          }
        ]
      },
      {
        "id": 2,
        "title": "HTTP Request Latency",
        "type": "heatmap",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket[5m])) by (le, method))",
            "legendFormat": "95th percentile - {{method}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Active Connections",
        "type": "singlestat",
        "targets": [
          {
            "expr": "active_connections_total",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "id": 4,
        "title": "Error Rate",
        "type": "bargauge",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100",
            "legendFormat": "Error Rate %"
          }
        ]
      },
      {
        "id": 5,
        "title": "System Memory",
        "type": "graph",
        "targets": [
          {
            "expr": "node_memory_MemAvailable_bytes / node_memory_MemTotal_bytes * 100",
            "legendFormat": "Available Memory %"
          }
        ]
      },
      {
        "id": 6,
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "100 - (avg by (instance) (irate(node_cpu_seconds_total{mode=\"idle\"}[5m])) * 100)",
            "legendFormat": "CPU Usage %"
          }
        ]
      }
    ]
  }
}
```

### Advanced Grafana Panel Examples

```python
# Custom UCore metrics panels for Grafana
database_panels = [
    {
        "title": "Database Connections",
        "type": "graph",
        "targets": [
            {
                "expr": 'database_connections_active{instance="$instance"}',
                "legendFormat": "Active Connections"
            },
            {
                "expr": 'database_connections_idle{instance="$instance"}',
                "legendFormat": "Idle Connections"
            },
            {
                "expr": 'database_connections_total{instance="$instance"}',
                "legendFormat": "Total Connections"
            }
        ]
    },
    {
        "title": "Database Query Performance",
        "type": "heatmap",
        "targets": [
            {
                "expr": 'histogram_quantile(0.95, sum(rate(database_query_duration_seconds_bucket[$__interval])) by (le, query_type))',
                "legendFormat": "95th percentile - {{query_type}}"
            }
        ]
    }
]

redis_panels = [
    {
        "title": "Redis Memory Usage",
        "type": "graph",
        "targets": [
            {
                "expr": 'redis_memory_used_bytes / redis_memory_max_bytes * 100',
                "legendFormat": "Memory Usage %"
            }
        ]
    },
    {
        "title": "Redis Operations Rate",
        "type": "graph",
        "targets": [
            {
                "expr": 'rate(redis_keyspace_hits_total[$__rate_interval])',
                "legendFormat": "Key Hits"
            },
            {
                "expr": 'rate(redis_keyspace_misses_total[$__rate_interval])',
                "legendFormat": "Key Misses"
            }
        ]
    }
]
```

---

## 🧹 Debugging Strategies and Techniques

### Implementing Comprehensive Logging

```python
from framework.app import App
from framework.logging import Logging
import logging
import traceback

class DebuggableApp(App):
    def __init__(self):
        super().__init__("DebuggableApp")
        self.logger = Logging().get_logger("debuggable_app")

        # Configure different log levels for different components
        self.configure_structured_logging()

    def configure_structured_logging(self):
        """Setup structured logging with correlation IDs."""

        class StructuredFormatter(logging.Formatter):
            def format(self, record):
                # Add request ID to all log records
                if hasattr(record, 'request_id'):
                    record.request_id = getattr(record, 'request_id', 'no-id')
                else:
                    record.request_id = 'no-id'

                # Add component info
                record.component = getattr(record, 'component', 'unknown')

                return super().format(record)

        # Apply to all handlers
        formatter = StructuredFormatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"component": "%(component)s", "request_id": "%(request_id)s", '
            '"message": "%(message)s", "extra": "%(args)s"}'
        )

        # Add to existing logger
        for handler in self.logger.handlers:
            handler.setFormatter(formatter)

    async def handle_request_with_debug(self, request_data):
        """Handle requests with comprehensive debugging."""
        request_id = request_data.get('id', 'unknown')

        # Add context to logger
        extra = {
            'request_id': request_id,
            'component': 'request_handler',
            'user_id': request_data.get('user_id'),
            'request_size': len(str(request_data))
        }

        self.logger.info("📥 Processing request", extra={'request_id': request_id})
        self.logger.debug("Request details", extra={
            'request_id': request_id,
            'request_data': str(request_data)[:500] + "..." if len(str(request_data)) > 500 else str(request_data)
        })

        try:
            # Start timing
            start_time = time.time()

            result = await self.process_request(request_data)

            # Log timing and result
            duration = time.time() - start_time
            self.logger.info("✅ Request completed", extra={
                'request_id': request_id,
                'duration': duration,
                'response_size': len(str(result))
            })

            return result

        except Exception as e:
            # Comprehensive error logging
            self.logger.error("❌ Request failed", extra={
                'request_id': request_id,
                'error_type': type(e).__name__,
                'error_message': str(e),
                'stack_trace': traceback.format_exc()
            })

            # Also log to metrics
            self.metrics.get_counter('request_errors_total').inc()

            raise

    async def health_check_with_debug(self):
        """Enhanced health check with component-level details."""
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'services': {},
            'version': self.get_version(),
            'uptime': self.get_uptime_seconds()
        }

        # Check each service
        services_to_check = {
            'database': self.check_database_health,
            'redis': self.check_redis_health,
            'metrics': self.check_metrics_health
        }

        for service_name, checker in services_to_check.items():
            try:
                health_info = await checker()
                health_data['services'][service_name] = {
                    'status': 'healthy',
                    'details': health_info
                }
            except Exception as e:
                health_data['services'][service_name] = {
                    'status': 'unhealthy',
                    'error': str(e)
                }

        # Log health check results
        unhealthy_services = [
            name for name, info in health_data['services'].items()
            if info['status'] != 'healthy'
        ]

        if unhealthy_services:
            self.logger.warning("⚠️ Health check found unhealthy services", extra={
                'component': 'health_check',
                'unhealthy_services': unhealthy_services
            })
        else:
            self.logger.info("✅ All services healthy", extra={
                'component': 'health_check'
            })

        return health_data

    def get_uptime_seconds(self):
        """Get application uptime in seconds."""
        if hasattr(self, 'start_time'):
            return time.time() - self.start_time
        return 0

    def get_version(self):
        """Get application version."""
        return getattr(self, 'version', '1.0.0')
```

### Implementing Circuit Breaker Pattern

```python
class CircuitBreaker:
    """Circuit breaker for external service calls."""

    def __init__(self, failure_threshold=5, recovery_timeout=60, name="external_service"):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.name = name

        self.state = "closed"  # "closed", "open", "half-open"
        self.failure_count = 0
        self.last_failure_time = None

        self.request_count = 0
        self.success_count = 0
        self.failure_count_total = 0

    async def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        if self.state == "open":
            if self._should_attempt_recovery():
                self.state = "half-open"
            else:
                raise CircuitBreakerOpen(f"Circuit breaker {self.name} is open")

        self.request_count += 1

        try:
            result = await func(*args, **kwargs)

            if self.state == "half-open":
                # First success in half-open state means recovery
                self._reset()

            self.success_count += 1
            return result

        except Exception as e:
            self.failure_count += 1
            self.failure_count_total += 1
            self.last_failure_time = time.time()

            if self.state == "closed" and self.failure_count >= self.failure_threshold:
                self.state = "open"

            raise e

    def _should_attempt_recovery(self):
        """Check if we should attempt recovery."""
        if not self.last_failure_time:
            return True

        return time.time() - self.last_failure_time >= self.recovery_timeout

    def _reset(self):
        """Reset circuit breaker state."""
        self.state = "closed"
        self.failure_count = 0

    def get_stats(self):
        """Get circuit breaker statistics."""
        return {
            'state': self.state,
            'request_count': self.request_count,
            'success_count': self.success_count,
            'failure_count_total': self.failure_count_total,
            'failure_rate': self.failure_count_total / max(1, self.request_count)
        }

# Usage in UCore app
class CircuitBreakerApp(App):
    def __init__(self):
        super().__init__("CircuitBreakerApp")
        self.external_service_breaker = CircuitBreaker(
            name="external_api",
            failure_threshold=3,
            recovery_timeout=30
        )
        self.metrics = MetricsCollector()

        # Add circuit breaker metrics
        self.metrics.add_gauge('circuit_breaker_state', 'Circuit breaker state', ['service'])
        self.metrics.add_counter('circuit_breaker_calls', 'Circuit breaker calls', ['service', 'result'])

    async def call_external_service(self, request_data):
        """Call external service with circuit breaker protection."""
        try:
            result = await self.external_service_breaker.call(
                self._make_external_call,
                request_data
            )

            self.metrics.get_counter('circuit_breaker_calls').labels(
                service='external_api',
                result='success'
            ).inc()

            return result

        except CircuitBreakerOpen:
            self.metrics.get_counter('circuit_breaker_calls').labels(
                service='external_api',
                result='circuit_open'
            ).inc()
            raise

        except Exception as e:
            self.metrics.get_counter('circuit_breaker_calls').labels(
                service='external_api',
                result='error'
            ).inc()
            raise

        finally:
            # Update circuit breaker state metric
            state_value = {'closed': 0, 'half-open': 0.5, 'open': 1}[self.external_service_breaker.state]
            self.metrics.get_gauge('circuit_breaker_state').labels(
                service='external_api'
            ).set(state_value)

    async def _make_external_call(self, request_data):
        """Actual external service call."""
        # Simulate external call
        await asyncio.sleep(0.1)
        return {"result": "success", "data": request_data}
```

---

## 📊 Performance Monitoring and Optimization

### Memory Profiling and Leak Detection

```python
import gc
import psutil
from framework.app import App

class PerformanceMonitor(App):
    def __init__(self):
        super().__init__("PerformanceMonitor")
        self.memory_snapshots = []
        self.process = psutil.Process()
        self.gc_stats = None

    async def astart(self):
        await super().astart()
        # Start background performance monitoring
        await self.start_performance_monitoring()

    async def start_performance_monitoring(self):
        """Monitor memory usage and performance."""
        while True:
            try:
                # Memory usage
                memory_info = self.process.memory_info()
                memory_usage_mb = memory_info.rss / 1024 / 1024

                # CPU usage
                cpu_percent = self.process.cpu_percent(interval=1)

                # Garbage collection stats
                self.gc_stats = {
                    'collection_count': gc.get_count(),
                    'stats': gc.get_stats()
                }

                # Store snapshot
                snapshot = {
                    'timestamp': time.time(),
                    'memory_mb': memory_usage_mb,
                    'cpu_percent': cpu_percent,
                    'gc_collections': self.gc_stats['collection_count'],
                    'objects_count': len(gc.get_objects())
                }

                self.memory_snapshots.append(snapshot)

                # Keep only last 10 minutes of snapshots
                cutoff_time = time.time() - 600
                self.memory_snapshots = [
                    snap for snap in self.memory_snapshots
                    if snap['timestamp'] > cutoff_time
                ]

                await asyncio.sleep(10)  # Check every 10 seconds

            except Exception:
                await asyncio.sleep(5)

    async def get_memory_report(self):
        """Generate memory usage report."""
        if not self.memory_snapshots:
            return {"error": "No memory snapshots available"}

        snapshots = self.memory_snapshots[-50:]  # Last 50 samples

        if len(snapshots) >= 2:
            recent = snapshots[-1]
            previous = snapshots[-2]

            memory_delta = recent['memory_mb'] - previous['memory_mb']
            cpu_delta = recent['cpu_percent'] - previous['cpu_percent']
        else:
            memory_delta = 0
            cpu_delta = 0

        return {
            'current_memory_mb': recent['memory_mb'],
            'memory_delta_mb': memory_delta,
            'current_cpu_percent': recent['cpu_percent'],
            'cpu_delta_percent': cpu_delta,
            'gc_collections': recent['gc_collections'],
            'objects_count': recent['objects_count'],
            'snapshot_count': len(self.memory_snapshots)
        }

    async def trigger_garbage_collection(self):
        """Manually trigger garbage collection for debugging."""
        self.logger.info("🧹 Triggering garbage collection for debugging")

        before_objects = len(gc.get_objects())

        # Force garbage collection
        collected = gc.collect()

        after_objects = len(gc.get_objects())

        report = {
            'objects_collected': collected,
            'objects_before': before_objects,
            'objects_after': after_objects,
            'memory_after_mb': self.process.memory_info().rss / 1024 / 1024
        }

        self.logger.info(f"🧹 GC completed: {collected} objects collected")
        return report

    async def get_thread_info(self):
        """Get information about active threads."""
        import threading

        threads = []
        for thread in threading.enumerate():
            threads.append({
                'name': thread.name,
                'id': thread.ident,
                'is_alive': thread.is_alive(),
                'is_daemon': thread.daemon
            })

        return {
            'total_threads': len(threads),
            'threads': threads
        }

    async def analyze_object_growth(self):
        """Analyze object growth patterns for memory leak detection."""
        if len(self.memory_snapshots) < 10:
            return {"error": "Not enough data for analysis"}

        recent_memory = [snap['memory_mb'] for snap in self.memory_snapshots[-10:]]

        # Calculate trending (simple linear regression)
        y_values = recent_memory
        x_values = list(range(len(y_values)))

        slope = self._calculate_slope(x_values, y_values)

        analysis = {
            'memory_trend_slope': slope,
            'memory_growth_mb_per_minute': slope * 6,  # 10 samples over ~10 minutes
            'recent_average_mb': sum(recent_memory) / len(recent_memory),
            'max_recent_mb': max(recent_memory),
            'min_recent_mb': min(recent_memory),
            'trend_interpretation': self._interpret_trend(slope)
        }

        return analysis

    def _calculate_slope(self, x_values, y_values):
        """Calculate slope of linear regression."""
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        sum_x_squared = sum(x * x for x in x_values)

        denominator = n * sum_x_squared - sum_x * sum_x
        if denominator == 0:
            return 0

        return (n * sum_xy - sum_x * sum_y) / denominator

    def _interpret_trend(self, slope):
        """Interpret memory trend slope."""
        if slope > 0.5:
            return "⚠️ Memory is growing rapidly - potential leak"
        elif slope > 0:
            return "📊 Memory is growing slowly"
        elif slope > -0.5:
            return "✅ Memory is stable"
        else:
            return "📉 Memory is decreasing - good!"

    async def detect_memory_leak(self):
        """Detect potential memory leaks."""
        analysis = await self.analyze_object_growth()

        if analysis.get('memory_trend_slope', 0) > 1.0:
            # Potential memory leak detected
            alert = {
                'severity': 'high',
                'type': 'memory_leak',
                'description': 'Memory usage is growing rapidly',
                'analysis': analysis,
                'recommendations': [
                    'Run garbage collection: /api/debug/gc',
                    'Check object references in code',
                    'Monitor gc stats for reference cycles',
                    'Consider memory profiling with tracemalloc'
                ]
            }

            return alert

        return {"status": "memory_usage_normal", "analysis": analysis}

# API endpoints for debugging
async def setup_debugging_endpoints(app, performance_monitor):
    """Setup debugging API endpoints."""

    router = app.app.router  # Assume aiohttp-style router

    router.add_get('/api/debug/memory', lambda r: performance_monitor.get_memory_report())
    router.add_post('/api/debug/gc', lambda r: performance_monitor.trigger_garbage_collection())
    router.add_get('/api/debug/threads', lambda r: performance_monitor.get_thread_info())
    router.add_get('/api/debug/memory-analysis', lambda r: performance_monitor.analyze_object_growth())
    router.add_get('/api/debug/memory-leak-check', lambda r: performance_monitor.detect_memory_leak())

    router.add_get('/api/debug/health-detailed', lambda r: app.health_check_with_debug())
    router.add_post('/api/debug/force-error', lambda r: app.force_error_for_testing())
    router.add_get('/api/debug/config-dump', lambda r: app.get_config_for_debugging())
    router.add_get('/api/debug/environment-info', lambda r: app.get_environment_info())

    return router
```

### Application Performance Profiling

```python
import cProfile
import pstats
import io
from functools import wraps
from framework.app import App

class PerformanceProfiler(App):
    def __init__(self):
        super().__init__("PerformanceProfiler")
        self.active_profiles = {}
        self.profile_results = {}
        self.metrics = MetricsCollector()

        # Add profiling metrics
        self.metrics.add_counter('profile_started_total', 'Total profiles started')
        self.metrics.add_counter('profile_completed_total', 'Total profiles completed')

    def profile_function(self, name, print_stats=True):
        """Decorator to profile function performance."""
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                profile_id = f"{name}_{time.time()}_{random.randint(1000, 9999)}"

                # Start profiling
                profiler = cProfile.Profile()
                profiler.enable()

                self.metrics.get_counter('profile_started_total').inc()

                try:
                    result = await func(*args, **kwargs)
                    return result
                finally:
                    # Stop profiling
                    profiler.disable()

                    # Get stats
                    s = io.StringIO()
                    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
                    ps.print_stats(20)

                    stats_str = s.getvalue()

                    # Store results
                    self.profile_results[profile_id] = {
                        'name': name,
                        'timestamp': time.time(),
                        'stats': stats_str,
                        'function_calls': len(ps.stats),
                        'total_time': sum([value[2] for value in ps.stats.values()]) if ps.stats else 0
                    }

                    self.metrics.get_counter('profile_completed_total').inc()

                    if print_stats:
                        self.logger.info(f"📊 Profile {profile_id} completed")
                        print(f"\n🔬 Profile Results for {name}:")
                        print("-" * 50)
                        print(stats_str)
                        print("-" * 50)

            return wrapper
        return decorator

    async def profile_request_handler(self, request_data):
        """Profile a request handler."""
        @self.profile_function(f"request_{request_data.get('endpoint', 'unknown')}")
        async def profiled_handler():
            # Simulate request processing
            await asyncio.sleep(0.1)
            for i in range(100):
                result = i * 2
            await asyncio.sleep(0.05)
            return {"result": result}

        return await profiled_handler()

    async def get_profile_stats(self, profile_id=None):
        """Get profiling statistics."""
        if profile_id and profile_id in self.profile_results:
            return {"profile_id": profile_id, "stats": self.profile_results[profile_id]}
        elif profile_id is None:
            return {"profiles": list(self.profile_results.keys())}
        else:
            return {"error": f"Profile {profile_id} not found"}

    async def cleanup_old_profiles(self, max_age_hours=24):
        """Clean up old profiling results."""
        current_time = time.time()
        cutoff_time = current_time - (max_age_hours * 3600)

        old_profiles = [
            profile_id for profile_id, profile_data in self.profile_results.items()
            if profile_data['timestamp'] < cutoff_time
        ]

        for profile_id in old_profiles:
            del self.profile_results[profile_id]

        return {"cleaned_profiles": len(old_profiles)}

    async def find_performance_issues(self):
        """Analyze profiling data for performance issues."""
        if not self.profile_results:
            return {"error": "No profiling data available"}

        # Analyze recent profiles for common issues
        recent_profiles = {
            pid: pdata for pid, pdata in self.profile_results.items()
            if time.time() - pdata['timestamp'] < 3600  # Last hour
        }

        issues = []

        for profile_id, profile_data in recent_profiles.items():
            stats_lines = profile_data['stats'].split('\n')

            # Look for common inefficient operations
            for line in stats_lines[:20]:  # Check top 20 functions
                if 'ncalls' in line.lower():
                    continue

                # Look for functions that take significant time
                if 'cumulative' in line and 'toime' in line:
                    parts = line.split()
                    try:
                        cumtime = float(parts[-1]) if parts else 0
                        if cumtime > 0.1:  # More than 100ms
                            function_name = ' '.join(parts[:-4]) if len(parts) > 4 else 'unknown'
                            issues.append({
                                'type': 'slow_function',
                                'profile_id': profile_id,
                                'function': function_name,
                                'cumulative_time': cumtime,
                                'threshold': 0.1
                            })
                    except ValueError:
                        continue

        return {
            'total_profiles_analyzed': len(recent_profiles),
            'performance_issues': issues,
            'overall_health': 'good' if len(issues) == 0 else 'needs_attention'
        }
```

---

## 🚀 Production Deployment Best Practices

### Scaling Configuration

```python
# production_config.py
production_config = {
    # Prometheus Configuration
    'PROMETHEUS_PUSHGATEWAY_URL': 'http://pushgateway:9091',
    'PROMETHEUS_JOB_NAME': 'ucore_microservice',
    'PROMETHEUS_METRICS_PREFIX': 'ucore_',

    # OpenTelemetry Configuration
    'OTLP_TRACES_ENDPOINT': 'http://otel-collector:4317/v1/traces',
    'OTLP_METRICS_ENDPOINT': 'http://otel-collector:4317/v1/metrics',
    'SERVICE_NAME': 'ucore-production-service',
    'SERVICE_VERSION': '2.1.0',

    # Logging Configuration
    'LOG_LEVEL': 'INFO',
    'LOG_FORMATTER': 'json',
    'LOG_FILE_PATH': '/var/log/ucore/application.log',

    # Performance Configuration
    'ENABLE_PROFILING': False,  # Enable in development only
    'METRICS_UPDATE_INTERVAL': 15,  # seconds
    'HEALTH_CHECK_CIRCUIT_BREAKER': True,

    # Security Configuration
    'METRICS_AUTH_ENABLED': True,
    'METRICS_USERNAME': os.getenv('METRICS_USERNAME'),
    'METRICS_PASSWORD': os.getenv('METRICS_PASSWORD'),

    # Database Configuration
    'POOL_SIZE': 20,
    'MAX_OVERFLOW': 30,
    'POOL_TIMEOUT': 30,
    'POOL_RECYCLE': 3600,
}

# Health Check Configuration
health_check_config = {
    'timeout': 5,  # seconds
    'retries': 3,
    'backoff_factor': 2,
    'health_check_interval': 30,  # seconds
    'unhealthy_threshold': 2,
    'healthy_threshold': 1
}

# Alert Configuration
alert_config = {
    'enable_prometheus_alerting': True,
    'slack_webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
    'alert_rules': [
        {
            'name': 'HighErrorRate',
            'query': 'rate(http_requests_total{status=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.1',
            'for_duration': '5m',
            'severity': 'critical'
        },
        {
            'name': 'HighMemoryUsage',
            'query': 'process_resident_memory_bytes > 1024*1024*1024',  # 1GB
            'for_duration': '3m',
            'severity': 'warning'
        },
        {
            'name': 'SlowRequests',
            'query': 'histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 5',
            'for_duration': '10m',
            'severity': 'warning'
        }
    ]
}
```

### Monitoring Stack Setup (Docker Compose)

```yaml
# docker-compose.monitoring.yml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    environment:
      - GF_INSTALL_PLUGINS=grafana-clock-panel,grafana-simple-json-datasource
      - GF_SECURITY_ADMIN_PASSWORD=admin123
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning

  jaeger:
    image: jaegertracing/all-in-one:latest
    ports:
      - "16686:16686"
      - "14268:14268"
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true

  otel-collector:
    image: otel/opentelemetry-collector:latest
    ports:
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP
      - "55579:55579" # Debug endpoint
    volumes:
      - ./monitoring/otel-config.yml:/etc/otel-collector/config.yml

volumes:
  prometheus_data:
  grafana_data:
```

---

## 🎯 Quick Troubleshooting Guide

### Common Issues and Solutions

| Issue | Symptom | Solution |
|-------|---------|----------|
| High memory usage | Application memory grows constantly | Check for reference cycles, run garbage collection |
| Slow response times | API response time > 1s | Profile functions, check database queries, review async patterns |
| Not receiving metrics | No data in Grafana/Prometheus | Check `/metrics` endpoint, verify Prometheus configuration |
| Missing traces | No spans in Jaeger | Verify OTLP exporter configuration, check exporter endpoint |
| Circuit breaker open | Service calls failing | Check downstream service health, adjust failure threshold |
| Missing request IDs | Poor request correlation | Implement correlation ID injection in request middleware |

### Debugging Commands

```bash
# Check application health
curl http://localhost:8080/api/debug/health-detailed

# Force garbage collection
curl -X POST http://localhost:8080/api/debug/gc

# Get memory analysis
curl http://localhost:8080/api/debug/memory-analysis

# Check for memory leaks
curl http://localhost:8080/api/debug/memory-leak-check

# View current metrics
curl http://localhost:8080/api/metrics

# Check thread information
curl http://localhost:8080/api/debug/threads

# Get environment info
curl http://localhost:8080/api/debug/environment-info
```

This comprehensive monitoring and debugging guide provides everything you need to effectively monitor, troubleshoot, and optimize UCore Framework applications using industry-standard tools like Prometheus, OpenTelemetry, and Grafana!
