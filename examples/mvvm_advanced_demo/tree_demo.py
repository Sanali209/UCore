from ucore_framework.mvvm.base import ViewModelBase
from ucore_framework.mvvm.hierarchical_datatable import HierarchicalDataTemplate
from PySide6.QtWidgets import QApplication, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget
import sys

class TreeViewModel(ViewModelBase):
    def __init__(self, tree_data):
        super().__init__()
        self.set_property("tree_data", tree_data)

def tree_widget_factory(data, ctx):
    return QTreeWidgetItem([data["name"]])

def children_selector(data):
    return data.get("children", [])

def main():
    app = QApplication(sys.argv)
    # Register hierarchical template for dict nodes
    HierarchicalDataTemplate.register(
        dict,
        tree_widget_factory,
        children_selector
    )

    # Sample tree data
    tree_data = {
        "name": "Root",
        "children": [
            {"name": "Child 1", "children": []},
            {"name": "Child 2", "children": [
                {"name": "Grandchild", "children": []}
            ]}
        ]
    }
    vm = TreeViewModel(tree_data)

    # Build tree widget
    tree_widget = QTreeWidget()
    tree_widget.setHeaderLabels(["Name"])
    root_item = HierarchicalDataTemplate.resolve(vm.get_property("tree_data"))
    tree_widget.addTopLevelItem(root_item)
    tree_widget.expandAll()

    window = QWidget()
    layout = QVBoxLayout(window)
    layout.addWidget(tree_widget)
    window.setLayout(layout)
    window.setWindowTitle("MVVM TreeView Demo")
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
