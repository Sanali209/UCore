# Example Applications & Usage Patterns

This section highlights example applications included with UCore and demonstrates common usage patterns for the framework.

---

## Overview

UCore provides several example apps to illustrate real-world usage of its features:
- Event-driven workflows
- Plugin-based extensibility
- MVVM desktop apps
- RESTful APIs and resource management

---

## Example Apps

### 1. QuickTask

A minimal task management app demonstrating core, data, and resource features.

- Location: `example/quicktask/`
- Features: CRUD tasks, resource management, event bus integration

**Run:**
```sh
python example/quicktask/main.py
```

---

### 2. Plugin Demo

Shows how to build and register plugins for dynamic extensibility.

- Location: `example/plugin_demo/`
- Features: Plugin system, dynamic loading, event handling

---

### 3. EventBus Demo

Demonstrates advanced event bus usage, including priorities and async handlers.

- Location: `example/eventbus_demo/`
- Features: Event publishing, subscription, and background processing

---

### 4. MVVM Counter

A desktop app using MVVM pattern and UI adapters.

- Location: `example/mvvm_counter/`
- Features: Observable viewmodel, data binding, PySide6 integration

---

### 5. Image Gallery

A more complex app with file management, resource adapters, and REST API.

- Location: `example/imagegallery/`
- Features: File system resource, REST API, MongoDB integration

---

## Usage Patterns

- **Event Bus:**  
  See `example/eventbus_demo/main.py` for advanced event handling.

- **Plugins:**  
  See `example/plugin_demo/` for plugin registration and usage.

- **MVVM:**  
  See `example/mvvm_counter/main.py` for viewmodel and UI binding.

- **REST API:**  
  See `example/imagegallery/api.py` for API resource usage.

---

See also:  
- [Core Framework](core.md)  
- [Testing](testing.md)
