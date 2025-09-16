# Core Domain Guide

## Purpose

The core domain provides the foundational infrastructure for UCore, including application orchestration, component lifecycle management, dependency injection, configuration, plugin system, and settings management.

---

## Main Classes & Components

- `App`: Main application orchestrator, manages components and lifecycle.
- `Component`: Base class for all components, supports OOP and extensibility.
- `Config`: Configuration loader and manager.
- `Container`: Dependency injection container.
- `Plugin`, `PluginManager`: Plugin registration and management.
- `SettingsManager`: Application and user settings.

---

## Usage Example

```python
from framework.core.app import App
from framework.core.component import Component

class MyComponent(Component):
    def start(self):
        print("Started!")

app = App("Demo")
app.register_component(MyComponent())
app.run()
```

---

## Extensibility & OOP

- Subclass `Component` for new features.
- Register plugins for modular extension.
- Use DI for testability and loose coupling.

---

## Integration Points

- All other domains depend on core for lifecycle, DI, and config.
- Plugins can extend any part of the framework via core.

---

## See Also

- [Project Structure Guide](project-structure-guide.md)
- [UCore Framework Guide](ucore-framework-guide.md)
