# Project Structure Guide

This guide explains the directory and module structure of UCore, and how to navigate and extend the project.

---

## Top-Level Structure

- `framework/` — Main framework code, organized by domain (core, data, desktop, messaging, monitoring, processing, resource, web)
- `tests/` — Unit and integration tests, mirroring the framework structure
- `docs/` — Documentation and guides
- `examples/` — Example projects and usage demos
- `plugins/` — Example plugins

---

## Key Directories

### framework/core
- App orchestration, component system, DI, config, plugins, settings

### framework/data
- SQLAlchemy DB, disk cache, MongoDB ODM, data view models

### framework/desktop
- UI adapters for Flet (web) and PySide6 (desktop/Qt)

### framework/messaging
- EventBus, event types, Redis adapter, distributed event bridge

### framework/monitoring
- Logging (loguru), Prometheus metrics, observability, health checks, tracing

### framework/processing
- Task queue, CLI, worker management, CPU task adapters

### framework/resource
- ResourceManager, resource types, pooling, health monitoring

### framework/web
- HttpServer, routing, middleware, async endpoints

---

## Extending the Project

- Add new domains as subdirectories in `framework/`
- Implement new components by subclassing `Component`
- Register plugins in `framework/core/plugins.py`
- Add tests in the corresponding `tests/` subdirectory

---

## Example: Adding a New Component

```python
from framework.core.component import Component

class MyComponent(Component):
    def start(self):
        print("Component started")
```

---

## See Also

- [UCore Framework Guide](ucore-framework-guide.md)
- [Domain-Driven Architecture](domain-driven-architecture.md)
