# Monitoring & Observability

This section documents the monitoring, health checks, metrics, tracing, and logging capabilities of UCore.

---

## Overview

UCore provides built-in monitoring and observability features to ensure application health, performance, and reliability.

- Health checks for core services and resources
- Metrics collection and reporting
- Distributed tracing support
- Structured logging with loguru

---

## Key Components

- **HealthChecker:**  
  Periodically checks the health of resources and components.

- **MetricsCollector:**  
  Collects and aggregates metrics (counters, gauges, histograms).

- **TracingProvider:**  
  Integrates with distributed tracing systems.

- **Logger (loguru):**  
  Structured, async-safe logging for all modules.

---

## Health Checks

Health checks are performed on resources (e.g., database, file system) and core components.

```python
from ucore_framework.monitoring.health_checker import HealthChecker

checker = HealthChecker(resources=[db_resource, files_db])
await checker.run_checks()
```

---

## Metrics

Metrics can be collected and reported for performance monitoring.

```python
from ucore_framework.monitoring.metrics import MetricsCollector

metrics = MetricsCollector()
metrics.increment("files_uploaded")
metrics.observe("db_query_time", 0.123)
```

---

## Tracing

Distributed tracing is supported for tracking requests and operations across services.

```python
from ucore_framework.monitoring.tracing_provider import TracingProvider

tracer = TracingProvider()
with tracer.start_span("process_file"):
    # do work
    pass
```

---

## Logging

All modules use `loguru` for structured logging.

```python
from loguru import logger

logger.info("Application started")
logger.error("An error occurred", exc_info=True)
```

---

## Best Practices

- Integrate health checks into your deployment pipeline.
- Use metrics and tracing to identify bottlenecks and failures.
- Configure loguru for file, console, or remote logging as needed.

---

See also:  
- [Core Framework](core.md)  
- [File System Resource Management](fs.md)
