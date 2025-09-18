# ucore_framework MVVM with PySide6

## Overview

This guide explains how to use the MVVM abstraction in ucore_framework with PySide6 for building modular, extensible desktop apps.

## ListView and TreeView Widgets

- `ListViewWidget`: Binds to a ViewModel's `items` property, supports dynamic templates, grouping, filtering, and transformation.
- `TreeViewWidget`: Binds to a ViewModel's `tree_data` property, supports hierarchical templates and children selectors.

### Example: ListView and TreeView

```python
from ucore_framework.mvvm.pyside6 import ListViewWidget, TreeViewWidget
from PySide6.QtWidgets import QLabel, QTreeWidgetItem

def list_template(item, parent):
    return QLabel(str(item))

def tree_template(data, parent):
    return QTreeWidgetItem([data["name"]])

def children_selector(data):
    return data.get("children", [])
```

See `examples/mvvm_advanced_demo/pyside6_demo.py` for a full runnable example.

## Advanced MVVM Features

- Grouping, filtering, transformation, and data provisioning are supported in ViewModels and reflected in the UI.
- Use DI, factory, or decorator to inject advanced features into ViewModels.

## Key Components

- `PySide6ViewBase`: Base QWidget for MVVM views.
- `bind_property`: One-way property binding from ViewModel to widget.
- `bind_bidirectional`: Two-way binding between ViewModel and widget.
- `bind_command`: Connects widget signals to ViewModel commands.
- `ObservableListModel`: Qt ListModel for ObservableList.

## Example: Counter Widget

```python
from PySide6.QtWidgets import QApplication, QVBoxLayout, QPushButton, QLabel
from ucore_framework.mvvm.base import ViewModelBase, Command
from ucore_framework.mvvm.pyside6 import PySide6ViewBase, bind_property, bind_command

class IncrementCommand(Command):
    def __init__(self, viewmodel):
        self._viewmodel = viewmodel
    def execute(self, *args, **kwargs):
        count = self._viewmodel.get_property("count")
        self._viewmodel.set_property("count", count + 1)

class CounterViewModel(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.set_property("count", 0)
        self.increment_command = IncrementCommand(self)

class CounterView(PySide6ViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel("0")
        self.button = QPushButton("Increment")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.setLayout(layout)
    def on_viewmodel_bound(self, viewmodel):
        bind_property(self.label, "text", viewmodel, "count")
        bind_command(self.button, "clicked", viewmodel.increment_command)
```

## Observable List Example

```python
from ucore_framework.mvvm.base import ObservableList
from ucore_framework.mvvm.pyside6_helpers import ObservableListModel

items = ObservableList(["a", "b"])
model = ObservableListModel(items)
# Use model in QListView, QTableView, etc.
```

## Extending

- Subclass `PySide6ViewBase` for your widgets.
- Use helpers for property and command binding.
- Use `ObservableListModel` for list widgets.
- Integrate with plugin/event bus for extensibility.

## Tips

- Keep ViewModel logic UI-agnostic.
- Use loguru for debugging bindings.
- Use OOP for all MVVM components.
