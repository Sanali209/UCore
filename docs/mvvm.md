# ucore_framework MVVM Abstraction Guide

## Overview

This guide describes the MVVM (Model-View-ViewModel) abstraction layer in ucore_framework, designed for extensibility, modularity, and OOP best practices.

## Core Components

### ModelBase
Base class for data models. Extend this for your domain data.

### ViewModelBase
- Property change notification (observer pattern)
- Command pattern support
- Property storage and access

#### Example:
```python
from ucore_framework.mvvm.base import ViewModelBase

class MyViewModel(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.set_property("counter", 0)

    def increment(self):
        self.set_property("counter", self.get_property("counter") + 1)
```

### Command
Abstract base for actions that can be bound to UI events.

### ObservableList / ObservableDict
- List/dict with change notification for UI binding

#### Example:
```python
from ucore_framework.mvvm.base import ObservableList

items = ObservableList()
def on_change(action, value):
    print(f"Action: {action}, Value: {value}")
items.add_handler(on_change)
items.append("item1")
```

### ViewBase
Abstract base for UI views. Implement for your UI framework (e.g., PySide6).

## Usage Pattern

1. Define your Model, ViewModel, and View (subclassing the base classes).
2. Use property change and observable collections for data binding.
3. Implement commands for user actions.
4. Bind ViewModel to View using the framework's helpers.

## Next Steps

- See PySide6 realization for concrete UI binding examples.
- Extend ViewBase for your UI toolkit.
- Integrate with plugin and event bus systems for full app extensibility.
