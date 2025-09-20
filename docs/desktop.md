# Desktop UI & Plugins

This section documents the desktop UI integration and plugin support in UCore, enabling rich desktop applications and extensible UI components.

---

## Overview

UCore supports desktop application development with:
- UI adapters for PySide6 and Flet
- Plugin system for desktop UI extensions
- Event-driven architecture for UI updates
- Integration with MVVM and resource management

---

## Key Components

- **TabbedWindow:**  
  Main window class for tabbed desktop UIs.

- **EditorTextPlugin, ViewerImagePlugin:**  
  Example plugins for text editing and image viewing.

- **DesktopEventBus:**  
  Event bus for desktop-specific events.

- **Settings, Plugin API:**  
  Classes for managing user settings and plugin APIs.

---

## Usage Example

```python
from ucore_framework.desktop.ui.tabbed_window import TabbedWindow
from ucore_framework.desktop.plugins.editor_text import EditorTextPlugin

window = TabbedWindow()
window.add_plugin(EditorTextPlugin())
window.show()
```

---

## Plugin Integration

- Create new desktop plugins by subclassing the plugin base classes.
- Register plugins with the main window or via configuration.
- Use the event bus to communicate between plugins and the core app.

---

## UI Adapters

- **PySide6Adapter:**  
  For native desktop UIs with PySide6.

- **FletAdapter:**  
  For cross-platform UIs with Flet (if available).

---

## Extending Desktop Functionality

- Add new plugins for custom editors, viewers, or tools.
- Integrate with MVVM viewmodels for reactive UIs.
- Use resource management for file and data access.

---

See also:  
- [MVVM & UI Utilities](mvvm.md)  
- [Core Framework](core.md)
