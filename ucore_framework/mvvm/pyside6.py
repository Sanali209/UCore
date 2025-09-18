from PySide6.QtCore import QObject, Signal, Slot, Property
from PySide6.QtWidgets import QWidget, QListWidget, QListWidgetItem, QTreeWidget, QTreeWidgetItem, QVBoxLayout
from PySide6.QtCore import Qt

class ListViewWidget(QListWidget):
    """
    MVVM ListView for PySide6, binds to ViewModel and supports dynamic templates.
    """
    def __init__(self, viewmodel, template_resolver):
        super().__init__()
        self.viewmodel = viewmodel
        self.template_resolver = template_resolver
        self.refresh()
        if hasattr(viewmodel, "add_property_changed_handler"):
            viewmodel.add_property_changed_handler(self.on_vm_change)

    def on_vm_change(self, name, old, new):
        if name == "items":
            self.refresh()

    def refresh(self):
        self.clear()
        items = self.viewmodel.get_property("items")
        if items:
            for item in items:
                widget = self.template_resolver(item, self)
                list_item = QListWidgetItem()
                self.addItem(list_item)
                self.setItemWidget(list_item, widget)

class TreeViewWidget(QTreeWidget):
    """
    MVVM TreeView for PySide6, binds to ViewModel and supports hierarchical templates.
    """
    def __init__(self, viewmodel, template_resolver, children_selector):
        super().__init__()
        self.viewmodel = viewmodel
        self.template_resolver = template_resolver
        self.children_selector = children_selector
        self.setHeaderLabels(["Name"])
        self.refresh()
        if hasattr(viewmodel, "add_property_changed_handler"):
            viewmodel.add_property_changed_handler(self.on_vm_change)

    def on_vm_change(self, name, old, new):
        if name == "tree_data":
            self.refresh()

    def refresh(self):
        self.clear()
        data = self.viewmodel.get_property("tree_data")
        if data:
            root_item = self.build_tree(data)
            self.addTopLevelItem(root_item)
            self.expandAll()

    def build_tree(self, data):
        item = self.template_resolver(data, self)
        children = self.children_selector(data)
        for child in children:
            child_item = self.build_tree(child)
            item.addChild(child_item)
        return item

from PySide6.QtWidgets import QWidget
from .base import ViewBase, ViewModelBase, ObservableList, ObservableDict
from loguru import logger

class PySide6ViewBase(QWidget, ViewBase):
    """Base class for PySide6 Views with ViewModel binding."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._viewmodel = None

    def bind_viewmodel(self, viewmodel: ViewModelBase):
        self._viewmodel = viewmodel
        self.on_viewmodel_bound(viewmodel)

    def on_viewmodel_bound(self, viewmodel: ViewModelBase):
        """Override to connect signals/slots and update UI."""
        pass

def bind_property(widget: QObject, widget_prop: str, viewmodel: ViewModelBase, vm_prop: str):
    """Bind a widget property to a ViewModel property (one-way)."""
    def update_widget(name, old, new):
        if name == vm_prop:
            setattr(widget, widget_prop, new)
            logger.debug(f"Widget property '{widget_prop}' updated to {new}")
    viewmodel.add_property_changed_handler(update_widget)
    # Set initial value
    setattr(widget, widget_prop, viewmodel.get_property(vm_prop))

def bind_bidirectional(widget: QObject, widget_prop: str, viewmodel: ViewModelBase, vm_prop: str, widget_signal: str):
    """Bind a widget property to a ViewModel property (two-way)."""
    bind_property(widget, widget_prop, viewmodel, vm_prop)
    signal = getattr(widget, widget_signal)
    def update_vm(*args):
        value = getattr(widget, widget_prop)
        viewmodel.set_property(vm_prop, value)
        logger.debug(f"ViewModel property '{vm_prop}' updated to {value}")
    signal.connect(update_vm)

def bind_command(widget: QObject, signal_name: str, command):
    """Bind a widget signal to a ViewModel command."""
    signal = getattr(widget, signal_name)
    signal.connect(lambda *args, **kwargs: command.execute(*args, **kwargs))
