# Project Structure Guide

This guide explains the directory and module structure of UCore, and how to navigate and extend the project.

---

## Top-Level Structure

- `UCoreFrameworck/` — Main UCoreFrameworck code, organized by domain (core, data, desktop, messaging, monitoring, processing, resource, web)
- `tests/` — Unit and integration tests, mirroring the UCoreFrameworck structure
- `docs/` — Documentation and guides
- `examples/` — Example projects and usage demos
- `plugins/` — Example plugins

---

## Key Directories

### UCoreFrameworck/core
- App orchestration, component system, DI, config, plugins, settings

### UCoreFrameworck/data
- SQLAlchemy DB, disk cache, MongoDB ODM, data view models

### UCoreFrameworck/desktop
- UI adapters for Flet (web) and PySide6 (desktop/Qt)

### UCoreFrameworck/messaging
- EventBus, event types, Redis adapter, distributed event bridge

### UCoreFrameworck/monitoring
- Logging (loguru), Prometheus metrics, observability, health checks, tracing

### UCoreFrameworck/processing
- Task queue, CLI, worker management, CPU task adapters

### UCoreFrameworck/resource
- ResourceManager, resource types, pooling, health monitoring

### UCoreFrameworck/web
- HttpServer, routing, middleware, async endpoints

---

## Extending the Project

- Add new domains as subdirectories in `UCoreFrameworck/`
- Implement new components by subclassing `Component`
- Register plugins in `UCoreFrameworck/core/plugins.py`
- Add tests in the corresponding `tests/` subdirectory

---

## Example: Adding a New Component

```python
from UCoreFrameworck.core.component import Component

class MyComponent(Component):
    def start(self):
        print("Component started")
```

---

## See Also

- [UCore Framework Guide](ucore-UCoreFrameworck-guide.md)
- [Domain-Driven Architecture](domain-driven-architecture.md)
