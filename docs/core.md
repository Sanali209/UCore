# Core Framework

This section covers the core modules of UCore, including the event bus, plugin system, dependency injection, configuration management, and architectural principles.

---

## Event Bus

The Event Bus is the central asynchronous messaging system in UCore.  
It supports:
- Priority-based event dispatching
- Throttling and circuit breaker integration
- Async handler support (coroutines and sync functions)
- Background event queue processing

**Key Classes:**
- `EventBus`: Main event dispatcher
- `Event`: Base class for events

**Usage Example:**
```python
from ucore_framework.core.event_bus import EventBus

bus = EventBus()

@bus.subscribe("user_registered")
async def handle_user_registered(event):
    print("User registered:", event)

await bus.publish_with_priority({"user_id": 1}, priority=1)
```

---

## Plugin System

UCore supports dynamic plugin loading and registration for extensibility.

**Key Classes:**
- `Plugin`: Base class for plugins
- `PluginRegistry`: Manages plugin discovery and lifecycle

**Usage Example:**
```python
from ucore_framework.core.plugins import Plugin

class HelloPlugin(Plugin):
    def on_load(self, app):
        print("Hello plugin loaded!")
```

Plugins can be registered via configuration or dynamically at runtime.

---

## Dependency Injection (DI)

UCore uses a simple DI container for managing dependencies and component lifecycles.

**Key Concepts:**
- Register components and services in the DI container
- Resolve dependencies automatically in constructors

**Usage Example:**
```python
from ucore_framework.core.di import Container

container = Container()
container.register("config", config_obj)
my_service = container.resolve("my_service")
```

---

## Configuration Management

Configuration is unified and YAML-based, with support for environment variable overrides and runtime updates.

**Key Classes:**
- `ConfigManager`: Loads, merges, and validates configuration
- `ConfigSchema`: Pydantic schema for config structure

**Usage Example:**
```python
from ucore_framework.core.config import get_config

config = get_config()
value = config.get("app_name")
config.set("workers", 8)
```

---

## Architectural Principles

- **OOP and Modularity:** All core components are designed for extensibility and testability.
- **Separation of Concerns:** Each module has a clear responsibility.
- **Logging:** Uses `loguru` for structured, async-safe logging.
- **Progress Visualization:** Use `tqdm` for progress bars in CLI/data tasks.

---

See other docs for details on data, file system, monitoring, UI, and more.
