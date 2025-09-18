# Monitoring Domain Guide

## Purpose

The monitoring domain provides observability features for UCore, including logging, metrics, health checks, and tracing.

---

## Main Classes & Components

- `Logging`: Structured logging using loguru.
- `Metrics`: Prometheus-compatible metrics (counters, histograms, gauges).
- `Observability`: Tracing and distributed tracing hooks.
- `Health`: Health check endpoints and status reporting.

---

## Usage Example

```python
from loguru import logger
logger.info("Service started")

from ucore_framework.monitoring.metrics import counter

@counter("my_counter", "Example counter")
def my_function():
    ...
```

---

## Health Checks

- Built-in `/health` endpoint for liveness/readiness.
- Health status for all components and resources.

---

## Tracing

```python
from ucore_framework.monitoring.observability import trace_function

@trace_function("my_operation")
def do_work():
    ...
```

---

## Extensibility & OOP

- Add custom metrics and health checks.
- Integrate tracing with OpenTelemetry.

---

## Integration Points

- Used by all domains for logging, metrics, and health.
- Metrics and health endpoints are exposed via web server.

---

## See Also

- [Monitoring & Debugging Guide](monitoring-debugging-guide.md)
- [Project Structure Guide](project-structure-guide.md)
