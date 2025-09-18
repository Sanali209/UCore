# DataTemplate & HierarchicalDataTemplate Usage in ucore_framework

## DataTemplate

**Purpose:**  
Map data types or predicates to widget constructors for dynamic GUI generation.

### Registering a DataTemplate

```python
from ucore_framework.mvvm.datatable import DataTemplate
from PySide6.QtWidgets import QLabel

# Register a template for str type
DataTemplate.register(
    str,
    lambda data, ctx: QLabel(f"String: {data}")
)

# Register a template for int type
DataTemplate.register(
    int,
    lambda data, ctx: QLabel(f"Number: {data}")
)
```

### Using DataTemplate to Build Widgets

```python
from ucore_framework.mvvm.template_helpers import build_widgets_from_list
from ucore_framework.mvvm.base import ObservableList

data = ObservableList(["hello", 42, "world"])
container = build_widgets_from_list(data)
# container is a QWidget with child QLabel widgets for each item
```

---

## HierarchicalDataTemplate

**Purpose:**  
Support recursive/hierarchical data (trees, outlines) with dynamic widget generation.

### Registering a HierarchicalDataTemplate

```python
from ucore_framework.mvvm.hierarchical_datatable import HierarchicalDataTemplate
from PySide6.QtWidgets import QTreeWidgetItem, QTreeWidget

def tree_widget_factory(data, ctx):
    item = QTreeWidgetItem([data["name"]])
    return item

def children_selector(data):
    return data.get("children", [])

# Register template for tree nodes
node_template = HierarchicalDataTemplate.register(
    dict,
    tree_widget_factory,
    children_selector
)
```

### Using HierarchicalDataTemplate

```python
from ucore_framework.mvvm.template_helpers import build_hierarchical_widget

tree_data = {
    "name": "Root",
    "children": [
        {"name": "Child 1", "children": []},
        {"name": "Child 2", "children": [
            {"name": "Grandchild", "children": []}
        ]}
    ]
}
tree_widget = build_hierarchical_widget(tree_data)
# tree_widget is a QTreeWidgetItem hierarchy
```

---

## Tips

- Use predicates for custom template selection logic.
- Combine with MVVM ViewModels for dynamic, data-driven UI.
- Extend widget factories for advanced layouts and interactivity.
