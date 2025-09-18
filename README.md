# 🚀 UCore Framework

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](https://opensource.org/licenses/MIT)

**UCore** is a modular, domain-driven, production-ready enterprise UCoreFrameworck for building modern, observable, and scalable Python services. It features a component-based architecture, strong OOP principles, and extensibility across 9 specialized domains.

---

## ✨ Key Features

- **Unified Resource Registry:** UnifiedResourceRegistry and UCoreResourceRegistry for modular resource discovery, registration, and orchestration.
- **Backend Provider:** Policy-driven backend selection (round-robin, health, tag), registry integration.
- **Secrets Management:** Secure, auditable secrets manager with config integration.
- **Event-Driven Architecture:** EventBus, Redis bridge, event filtering, cross-component events.
- **Multi-Platform:** Web (Flet), Desktop (PySide6), cross-platform support.
- **Component System:** Lifecycle management, dependency injection, plugin system.
- **Resource Provider System:** Unified orchestration, 4 resource types, connection pooling, health monitoring.
- **Observability:** Prometheus metrics, loguru logging, health checks, tracing, tqdm-based progress.
- **Background Processing:** Task queue, CLI, worker management.
- **Database & Cache:** MongoDB ODM, disk cache.
- **Comprehensive Testing:** Extensive unit and integration tests for all domains and features.
- **Undo/Redo System:** UndoSystem component for modular, extensible undo/redo functionality with loguru logging.

---

## 📁 Project Structure

- `UCoreFrameworck/core`: App, Component, Config, DI, Plugins, Settings
- `UCoreFrameworck/data`: DB, DiskCache, MongoDB Adapter/ORM
- `UCoreFrameworck/desktop/ui`: FletAdapter, PySide6Adapter
- `UCoreFrameworck/messaging`: Events, EventBus, RedisAdapter, Bridges
- `UCoreFrameworck/monitoring`: Logging, Metrics, Observability
- `UCoreFrameworck/processing`: TaskQueue, CLI, Worker, CPU tasks
- `UCoreFrameworck/resource`: ResourceManager, Resource types, Pooling
- `UCoreFrameworck/web`: HttpServer

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- pip
- (Optional) Redis for messaging features

### Installation

```bash
git clone <repository-url>
cd UCore
pip install -r requirements.txt
```

### Minimal Example

```python
from UCoreFrameworck import App
from UCoreFrameworck.web import HttpServer

app = App("MyService")
http_server = HttpServer(app)

@http_server.route("/", "GET")
async def hello():
    return {"message": "Hello from UCore!"}

if __name__ == "__main__":
    app.run()
```

---

## 🛠️ CLI Usage

```bash
ucore --help
ucore worker start --mode pool --processes 4
ucore status
ucore shell
```

---

## 📋 Feature Deep Dive

- **EventBus:** Type-safe events, async/sync, event filtering, Redis bridge.
- **Resource Management:** ResourceManager, 4 resource types, lifecycle, pooling, health checks.
- **Observability:** Prometheus metrics, logging, health endpoints, tracing.
- **Background Tasks:** Task queue, CLI, worker management.
- **Database/Cache:** MongoDB ODM, disk cache.
- **Web/Desktop UI:** Flet (web), PySide6 (desktop).
- **Undo/Redo System:** `UndoSystem` component for undo/redo stacks, OOP, and logging.

---

## 📝 Undo System Example

```python
from UCoreFrameworck.core.undo import UndoSystem

undo_system = UndoSystem()
undo_system.add_undo_item(lambda: print("undo!"), lambda: print("redo!"), description="Sample action")
undo_system.undo()
undo_system.redo()
```

---

## 🧪 Testing & Quality

- Comprehensive unit and integration tests for all domains.
- Run all tests:
  ```bash
  python -m pytest tests/
  ```

---

## 🏗️ Architecture & Design

- Component-based, OOP, extensible and modular.
- Dependency injection, plugin system, async/await.
- Error handling, logging, monitoring.

---

## 🚀 Production Deployment

- Docker and Kubernetes ready.
- Health checks, metrics, graceful shutdown.

---

## 🤝 Contributing

- Fork, branch, install dev dependencies, run tests/linters.
- See CONTRIBUTING.md for details.

---

## 📜 License

MIT License. See LICENSE for details.

---

## 📚 Documentation

- See [`docs/index.md`](docs/index.md) for the full documentation index and all guides.
- Explore the [`examples/`](examples/) directory for runnable demos of all major features.
