# Desktop Domain Guide

## Purpose

The desktop domain provides UI integration for desktop applications, supporting both Flet (web-based UI) and PySide6 (native Qt desktop UI).

---

## Main Classes & Components

- `FletAdapter`: Integrates Flet web UI with the UCore component system.
- `PySide6Adapter`: Integrates PySide6/Qt desktop UI with UCore.

---

## Usage Example

```python
from UCoreFrameworck.desktop.ui.flet.flet_adapter import FletAdapter

flet_adapter = FletAdapter(app, target_func=my_ui_func, port=8085)
```

---

## PySide6 Example

```python
from UCoreFrameworck.desktop.ui.pyside6_adapter import PySide6Adapter

pyside_adapter = PySide6Adapter(app)
```

---

## Extensibility & OOP

- Subclass adapters for custom UI logic.
- Integrate with UCore components and event system.

---

## Integration Points

- UI adapters can be used alongside web and API servers.
- Supports real-time updates and event-driven UI.

---

## See Also

- [Project Structure Guide](project-structure-guide.md)
- [UCore Framework Guide](ucore-UCoreFrameworck-guide.md)
