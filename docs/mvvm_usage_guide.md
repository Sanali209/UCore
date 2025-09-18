# ucore_framework MVVM Usage Guide

## 1. Setup

- Install dependencies: `pip install -r requirements.txt`
- Ensure PySide6 is installed for desktop UI: `pip install PySide6`
- Explore the `ucore_framework/mvvm/` directory for core MVVM modules.

## 2. Creating a ViewModel

```python
from ucore_framework.mvvm.base import ViewModelBase, ObservableList

class MyViewModel(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.set_property("items", ObservableList(["A", "B", "C"]))
```

## 3. Using Dependency Injection

- Register and resolve advanced MVVM features (grouping, filtering, transformation, provisioning) via DI.
- Use `AdvancedViewModelFactory` or `@inject_mvvm_features` decorator for auto-injection.

```python
from ucore_framework.core.di import container
from ucore_framework.mvvm.base import AdvancedViewModelFactory

factory = AdvancedViewModelFactory(container)

class MyVM(ViewModelBase):
    def __init__(self, data_provisioning=None, transformation=None, grouping=None):
        ...

vm = factory.create(MyVM)
```

## 4. ListView and TreeView with PySide6

### ListView

```python
from ucore_framework.mvvm.pyside6 import ListViewWidget
from PySide6.QtWidgets import QLabel

def list_template(item, parent):
    return QLabel(str(item))

list_vm = MyViewModel()
list_widget = ListViewWidget(list_vm, list_template)
```

### TreeView

```python
from ucore_framework.mvvm.pyside6 import TreeViewWidget
from PySide6.QtWidgets import QTreeWidgetItem

def tree_template(data, parent):
    return QTreeWidgetItem([data["name"]])

def children_selector(data):
    return data.get("children", [])

tree_vm = MyTreeViewModel()
tree_widget = TreeViewWidget(tree_vm, tree_template, children_selector)
```

## 5. Advanced Features

- **Grouping/Filtering:** Set group/filter functions on ViewModel for dynamic grouping/filtering in UI.
- **Transformation Pipelines:** Chain transformations for data before display.
- **Provisioning:** Control data loading (all/visible/batch/async).
- **Plugin Providers:** Register and use custom data providers at runtime.

## 6. Example: Full PySide6 MVVM App

See `examples/mvvm_advanced_demo/pyside6_demo.py` for a complete runnable example with ListView and TreeView.

## 7. Testing

- Run all tests: `python -m pytest tests/`
- See `tests/mvvm/test_pyside6_mvvm.py` for PySide6 MVVM integration tests.

## 8. Troubleshooting

- Ensure all dependencies are installed.
- Use loguru logging for debugging property changes and bindings.
- For UI issues, check ViewModel property names and template functions.

## 9. Further Reading

- [Advanced MVVM Features](mvvm_advanced_features.md)
- [PySide6 MVVM Guide](mvvm_pyside6.md)
- [Project Structure Guide](project-structure-guide.md)
