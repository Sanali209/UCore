# Monitoring & Debugging Guide

This guide covers monitoring, logging, metrics, and debugging tools in UCore, including best practices for observability and troubleshooting.

---

## Logging

- Uses [loguru](https://github.com/Delgan/loguru) for structured, configurable logging.
- Logs are emitted by all major components and can be customized per domain.
- Example:
  ```python
  from loguru import logger
  logger.info("Service started")
  ```

---

## Metrics

- Prometheus-compatible metrics via `UCoreFrameworck/monitoring/metrics.py`.
- HTTP metrics, custom counters, histograms, and gauges.
- Exposed at `/metrics` endpoint for scraping.
- Example:
  ```python
  from UCoreFrameworck.monitoring.metrics import counter

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

- Tracing hooks available in `UCoreFrameworck/monitoring/observability.py`.
- Integrates with OpenTelemetry for distributed tracing (optional).
- Example:
  ```python
  from UCoreFrameworck.monitoring.observability import trace_function

  @trace_function("my_operation")
  def do_work():
      ...
  ```

---

## Debugging Tools

- Use tqdm for progress visualization in CLI and batch jobs.
- Debug utilities in `UCoreFrameworck/debug_utilities.py` for profiling, event inspection, and performance reports.
- Example:
  ```python
  from tqdm import tqdm

  for i in tqdm(range(100)):
      ...
  ```

---

## Best Practices

- Use structured logging for all components.
- Expose metrics and health endpoints in production.
- Use tracing for async and distributed operations.
- Profile and inspect events during development.

---

## See Also

- [UCore Framework Guide](ucore-UCoreFrameworck-guide.md)
- [Project Structure Guide](project-structure-guide.md)
