# MVVM & UI Utilities

This section documents the MVVM (Model-View-ViewModel) and UI helper modules in UCore, supporting desktop and UI-driven applications.

---

## Overview

UCore provides utilities for building desktop and UI applications using the MVVM pattern.  
Features include:
- Observable models and viewmodels
- Data binding and transformation pipelines
- UI adapters for PySide6 and other frameworks
- Plugin support for UI components

---

## Key Components

- **BaseViewModel:**  
  Base class for observable viewmodels.

- **DataProvider, DataProvisioning:**  
  Classes for providing and transforming data to the UI.

- **TransformationPipeline:**  
  Compose data transformations for UI binding.

- **PySide6Adapter:**  
  Integration layer for PySide6-based UIs.

- **PluginTemplate, AbstractViews:**  
  Templates and abstractions for custom UI plugins.

---

## Usage Example

```python
from ucore_framework.mvvm.base import BaseViewModel

class CounterViewModel(BaseViewModel):
    def __init__(self):
        super().__init__()
        self.count = 0

    def increment(self):
        self.count += 1
        self.notify_observers("count")
```

Bind this viewmodel to a UI using the provided adapters.

---

## Data Binding and Transformation

Use `DataProvider` and `TransformationPipeline` to bind and transform data for the UI.

```python
from ucore_framework.mvvm.data_provider import DataProvider
from ucore_framework.mvvm.transformation_pipeline import TransformationPipeline

provider = DataProvider(source=my_model)
pipeline = TransformationPipeline([lambda x: x * 2])
provider.set_pipeline(pipeline)
```

---

## UI Adapters

- **PySide6Adapter:**  
  Connects viewmodels to PySide6 widgets for reactive UIs.

- **FletAdapter:**  
  (If available) Adapter for Flet-based UIs.

---

## Extending MVVM Utilities

- Create new viewmodels by subclassing `BaseViewModel`.
- Implement custom data providers and transformation steps.
- Add new UI adapters for other frameworks as needed.

---

See also:  
- [Core Framework](core.md)  
- [Examples](examples.md)
