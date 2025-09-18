# Project Structure Guide

This guide explains the directory and module structure of UCore, and how to navigate and extend the project.

---

## Top-Level Structure

- `ucore_framework/` — Main ucore_framework code, organized by domain (core, data, desktop, messaging, monitoring, processing, resource, web)
- `tests/` — Unit and integration tests, mirroring the ucore_framework structure
- `docs/` — Documentation and guides
- `examples/` — Example projects and usage demos
- `plugins/` — Example plugins

---

## Key Directories

### ucore_framework/core
- App orchestration, component system, DI, config, plugins, settings

### ucore_framework/data
- SQLAlchemy DB, disk cache, MongoDB ODM, data view models

### ucore_framework/desktop
- UI adapters for Flet (web) and PySide6 (desktop/Qt)

### ucore_framework/messaging
- EventBus, event types, Redis adapter, distributed event bridge

### ucore_framework/monitoring
- Logging (loguru), Prometheus metrics, observability, health checks, tracing

### ucore_framework/processing
- Task queue, CLI, worker management, CPU task adapters

### ucore_framework/resource
- ResourceManager, resource types, pooling, health monitoring

### ucore_framework/web
- HttpServer, routing, middleware, async endpoints

---

## Extending the Project

- Add new domains as subdirectories in `ucore_framework/`
- Implement new components by subclassing `Component`
- Register plugins in `ucore_framework/core/plugins.py`
- Add tests in the corresponding `tests/` subdirectory

---

## Example: Adding a New Component

```python
from ucore_framework.core.component import Component

class MyComponent(Component):
    def start(self):
        print("Component started")
```

---

## See Also

- [UCore Framework Guide](ucore-ucore_framework-guide.md)
- [Domain-Driven Architecture](domain-driven-architecture.md)
