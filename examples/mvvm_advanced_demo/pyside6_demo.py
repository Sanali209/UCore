from ucore_framework.mvvm.base import ViewModelBase, ObservableList
from ucore_framework.mvvm.grouping_filter import GroupingFilterMixin
from ucore_framework.mvvm.data_provisioning import DataProvisioningMixin
from ucore_framework.mvvm.transformation_pipeline import TransformationPipelineMixin
from ucore_framework.mvvm.pyside6 import ListViewWidget, TreeViewWidget
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QSplitter, QTreeWidgetItem
import sys

class AdvancedListViewModel(ViewModelBase, GroupingFilterMixin, DataProvisioningMixin, TransformationPipelineMixin):
    def __init__(self, data):
        ViewModelBase.__init__(self)
        GroupingFilterMixin.__init__(self)
        DataProvisioningMixin.__init__(self)
        TransformationPipelineMixin.__init__(self)
        self.set_property("items", ObservableList(data))
        self.set_group_func(lambda x: x[0] if isinstance(x, str) else "other")
        self.set_filter_func(lambda x: isinstance(x, str))
        self.add_transformation(lambda items: [item.upper() if isinstance(item, str) else item for item in items])

class TreeViewModel(ViewModelBase):
    def __init__(self, tree_data):
        super().__init__()
        self.set_property("tree_data", tree_data)

def list_template(item, parent):
    return QLabel(str(item))

def tree_template(data, parent):
    return QTreeWidgetItem([data["name"]])

def children_selector(data):
    return data.get("children", [])

def main():
    app = QApplication(sys.argv)

    # ListView demo
    data = ["apple", "banana", "carrot", 1, 2, 3, "avocado"]
    list_vm = AdvancedListViewModel(data)
    list_widget = ListViewWidget(list_vm, list_template)

    # TreeView demo
    tree_data = {
        "name": "Root",
        "children": [
            {"name": "Child 1", "children": []},
            {"name": "Child 2", "children": [
                {"name": "Grandchild", "children": []}
            ]}
        ]
    }
    tree_vm = TreeViewModel(tree_data)
    tree_widget = TreeViewWidget(tree_vm, tree_template, children_selector)

    # Layout
    window = QWidget()
    layout = QVBoxLayout(window)
    splitter = QSplitter()
    splitter.addWidget(list_widget)
    splitter.addWidget(tree_widget)
    layout.addWidget(splitter)
    window.setLayout(layout)
    window.setWindowTitle("PySide6 MVVM ListView & TreeView Demo")
    window.resize(800, 400)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
