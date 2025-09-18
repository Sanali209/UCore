# UCore Extension Points & Developer API

## Overview

UCore provides a modular, extensible architecture for building desktop apps with plugins, editors, viewers, tools, and custom file systems.

---

## Extension Points

### 1. Plugins

- **Base:** Inherit from `PluginBase` (`ucore_framework/desktop/plugins/api.py`)
- **Types:** Editor, Viewer, Tool, FileSystemAdapter
- **Lifecycle:** `activate(app_context)`, `deactivate()`, `get_metadata()`, `create_widget()`
- **Registration:** Use `PluginRegistry` to register and load plugins dynamically.

### 2. File System Adapters

- **Base:** Inherit from `FileSystemAdapter` (`ucore_framework/fs/adapter.py`)
- **Register:** Use `FileSystemAdapterRegistry` to add new schemes (e.g., "s3", "ftp", "zip").
- **Implement:** `list_dir`, `read_file`, `write_file`, `delete_file`, `move_file`, `copy_file`.

### 3. MVVM Components

- **ViewModelBase:** Extend for custom document/tool logic.
- **Dynamic Tabs:** Use `TabbedWindow`, `DocumentTabViewModel`, `ToolTabViewModel` for new tab types.

### 4. Event Bus

- **EventBus:** Use for decoupled messaging between UI, plugins, and core logic.
- **Subscribe/Publish:** Register handlers for custom events.

---

## Plugin Example

```python
from ucore_framework.desktop.plugins.api import PluginBase

class MyPlugin(PluginBase):
    def activate(self, app_context):
        # Setup resources, register commands, etc.
        pass
    def deactivate(self):
        # Cleanup
        pass
    def get_metadata(self):
        return {"type": "tool", "name": "MyTool"}
    def create_widget(self):
        # Return a QWidget or MVVM component
        ...
```

---

## File System Adapter Example

```python
from ucore_framework.fs.adapter import FileSystemAdapter

class MyCloudAdapter(FileSystemAdapter):
    def list_dir(self, path): ...
    def read_file(self, path): ...
    def write_file(self, path, data): ...
    def delete_file(self, path): ...
    def move_file(self, src, dst): ...
    def copy_file(self, src, dst): ...
```

---

## Developer Patterns

- Use OOP for all plugins/components.
- Register plugins and adapters at startup.
- Use loguru for logging and debugging.
- Use tqdm for progress in background tasks.
- Persist settings/state with `SettingsManager`.

---

## Monitoring & Debugging

- Use `loguru` for structured logging.
- Use `tqdm` for progress visualization in background tasks.
- Add error reporting and performance metrics via plugins or core logic.

---

## Further Reading

- See `docs/app_architecture_plan.md` for architecture overview.
- See `docs/mvvm_usage_guide.md` for MVVM usage.
- Explore `ucore_framework/desktop/plugins/` for plugin examples.
