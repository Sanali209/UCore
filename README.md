# UCore Framework

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/)
[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](#)
[![Tests](https://img.shields.io/badge/tests-pytest-green.svg)](#)

A modular, extensible Python framework for building scalable, event-driven, and plugin-based applications.  
UCore provides a robust foundation for desktop, backend, and data-centric systems, with a focus on OOP, testability, and maintainability.

---

## Documentation

Full documentation is available in the [`docs/`](docs/overview.md) directory:

- [Overview & Architecture](docs/overview.md)
- [Architecture Diagram](docs/architecture.md)
- [Core Framework](docs/core.md)
- [Data Layer & MongoDB ORM](docs/data.md)
- [File System Resource Management](docs/fs.md)
- [Monitoring & Observability](docs/monitoring.md)
- [MVVM & UI Utilities](docs/mvvm.md)
- [Web & HTTP Utilities](docs/web.md)
- [Desktop UI & Plugins](docs/desktop.md)
- [Examples & Usage Patterns](docs/examples.md)
- [Testing](docs/testing.md)
- [Contributing](docs/contributing.md)

---

## Table of Contents

- [Features](#features)
- [Documentation](#documentation)
- [Architecture](#architecture)
- [Directory Structure](#directory-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Minimal Example](#minimal-example)
  - [Plugin System](#plugin-system)
  - [Event Bus](#event-bus)
  - [MongoDB ORM](#mongodb-orm)
  - [Resource Management](#resource-management)
  - [Monitoring & Logging](#monitoring--logging)
- [Testing](#testing)
- [Development & Contribution](#development--contribution)
- [FAQ](#faq)
- [License](#license)
- [Credits](#credits)

---

## Features

- **Plugin System:** Dynamically load, register, and manage plugins for extensibility.
- **Event Bus:** Asynchronous, prioritized event dispatching with circuit breaker and throttling support.
- **Resource Management:** Unified interface for files, databases, secrets, and more.
- **MongoDB ORM:** Async, extensible ODM with test adapters, batching, and reference fields.
- **Redis Integration:** Pub/sub and stream support for distributed eventing.
- **MVVM Utilities:** Helpers for desktop and UI-driven apps.
- **Monitoring:** Health checks, metrics, tracing, and logging (loguru).
- **OOP & Extensibility:** Designed for modularity, future-proofing, and code reuse.
- **Testing:** Rich test suite with pytest, test adapters, and mockable components.

---

## Architecture

```
+-------------------+      +-------------------+      +-------------------+
|    Plugins        |<---->|     Event Bus     |<---->|   Core Services   |
+-------------------+      +-------------------+      +-------------------+
        |                        |                           |
        v                        v                           v
+-------------------+      +-------------------+      +-------------------+
|   Resource Mgmt   |<---->|   MongoDB ORM     |<---->|   Redis Adapter   |
+-------------------+      +-------------------+      +-------------------+
        |                        |                           |
        v                        v                           v
+-------------------+      +-------------------+      +-------------------+
|   Monitoring      |      |    MVVM/UI        |      |   Example Apps    |
+-------------------+      +-------------------+      +-------------------+
```

- **Event Bus:** Central async event dispatcher, supports priorities, throttling, and circuit breaker.
- **Plugins:** Extend core functionality, auto-discovered and loaded at runtime.
- **Resource Management:** Unified access to files, databases, secrets, etc.
- **MongoDB ORM:** Async ODM with batching, test adapters, and reference fields.
- **Redis Adapter:** Distributed eventing via pub/sub and streams.
- **Monitoring:** Health checks, metrics, tracing, and logging.
- **MVVM/UI:** Helpers for desktop and UI-driven apps.

---

## Directory Structure

```
ucore_framework/
    core/         # Core framework modules (event bus, plugins, config, DI, etc.)
    data/         # Data adapters, MongoDB ORM, test adapters
    fs/           # File system resource management
    monitoring/   # Health checks, metrics, tracing
    mvvm/         # MVVM and UI helpers
    web/          # Web and HTTP utilities
    desktop/      # Desktop UI and plugin support
example/          # Example applications and demos
tests/            # Unit, integration, and e2e tests
ai/               # AI integration and planning tools
scripts/          # Utility scripts (e.g., set_secret.py)
docs/             # Project documentation (see section above)
```

---

## Installation

1. **Clone the repository:**
   ```sh
   git clone https://github.com/Sanali209/UCore.git
   cd UCore
   ```

2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

3. **Configure environment:**
   - Edit `app_config.yml` or use environment variables as needed.
   - Ensure MongoDB and Redis are running for full functionality.

---

## Configuration

- **YAML-based:** Main config in `app_config.yml`, supports environment variable overrides.
- **Secrets:** Use `ucore_framework/core/resource/secrets.py` for secure values.
- **Dynamic:** Runtime change callbacks, thread safety, and validation via Pydantic.
- **Example:**
  ```yaml
  app_name: MyApp
  version: 1.0.0
  download_directory: ~/Downloads/myapp
  redis_host: localhost
  mongo_uri: mongodb://localhost:27017
  ```

---

## Usage

### Minimal Example

```python
from ucore_framework.core.app import App

app = App()
app.run()
```

### Plugin System

```python
# plugins/hello_plugin.py
from ucore_framework.core.plugins import Plugin

class HelloPlugin(Plugin):
    def on_load(self, app):
        print("Hello plugin loaded!")

# Register plugin in app_config.yml or dynamically
```

### Event Bus

```python
from ucore_framework.core.event_bus import EventBus

bus = EventBus()

@bus.subscribe("user_registered")
async def handle_user_registered(event):
    print("User registered:", event)

await bus.publish_with_priority({"user_id": 1}, priority=1)
```

### MongoDB ORM

```python
from ucore_framework.data.mongo_orm import BaseMongoRecord, Field

class User(BaseMongoRecord):
    collection_name = "users"
    name = Field(str)
    email = Field(str)

# Inject db client (see tests/utils/test_mongo.py for setup)
User.inject_db_client(db, bulk_cache=None)

# Create and fetch user
await User.new_record(name="Alice", email="alice@example.com")
user = await User.get_by_id(user_id)
```

### Resource Management

```python
from ucore_framework.fs.resource import FilesDBResource

files_db = FilesDBResource(config, event_bus)
await files_db.add_file({"name": "report.pdf"})
```

### Monitoring & Logging

- **Logging:** Uses `loguru` for structured, async-safe logging.
- **Progress:** Use `tqdm` for progress bars in CLI/data tasks.
- **Health Checks:** Built-in health endpoints and metrics.

---

## Testing

- **Test Suite:**  
  - Unit, integration, and e2e tests in `tests/`
  - Use `pytest` for all tests.
  - Mock adapters and test-specific classes for isolation.
- **Run all tests:**
  ```sh
  pytest
  ```
- **Example test:**
  ```python
  @pytest.mark.asyncio
  async def test_insert_and_find_document(mongo_db_session):
      TestRecord.inject_db_client(mongo_db_session, bulk_cache=None)
      await TestRecord.collection().insert_one({"_id": "abc123", "name": "real_doc"})
      results = await TestRecord.find({"name": "real_doc"})
      assert len(results) == 1
  ```

---

## Development & Contribution

- **Coding standards:**  
  - OOP style, modularity, and extensibility.
  - Use `loguru` for logging and `tqdm` for progress visualization.
  - Write docstrings for all modules, classes, and functions.
- **Adding plugins:**  
  - Place new plugins in `ucore_framework/core/plugins.py` or `plugins/`.
  - Register plugins in config or via code.
- **Extending the framework:**  
  - Add new resource types, adapters, or event types in their respective modules.
  - Follow existing patterns for DI, event bus, and resource registration.
- **Testing:**  
  - Use pytest for all new features and bug fixes.
  - Mock adapters and use test-specific classes for isolation.
- **Pull Requests:**  
  - Fork, branch, and submit PRs with clear descriptions and tests.

---

## FAQ

**Q: What Python versions are supported?**  
A: Python 3.9+ is recommended.

**Q: Can I use UCore for desktop and backend apps?**  
A: Yes, UCore supports both desktop (MVVM, UI) and backend (event-driven, REST, data) architectures.

**Q: How do I add a new plugin?**  
A: Create a class inheriting from `Plugin`, place it in `plugins/`, and register it in config or at runtime.

**Q: How do I configure MongoDB/Redis?**  
A: Set connection details in `app_config.yml` or via environment variables.

**Q: Is UCore production-ready?**  
A: The framework is actively developed and tested, but review and adapt for your production needs.

---

## License

MIT License.  
See [LICENSE](LICENSE) for details.

---

## Credits

- Inspired by modern Python frameworks and best practices.
- Uses: loguru, tqdm, pydantic, redis, motor, pytest, and more.
- Maintained by [Sanali209](https://github.com/Sanali209) and contributors.
