from PySide6.QtWidgets import QWidget, QTabWidget, QVBoxLayout
from ucore_framework.mvvm.base import ViewModelBase
from loguru import logger

class DocumentTabViewModel(ViewModelBase):
    def __init__(self, title, content_vm):
        super().__init__()
        self.set_property("title", title)
        self.set_property("content_vm", content_vm)

class ToolTabViewModel(ViewModelBase):
    def __init__(self, title, tool_vm):
        super().__init__()
        self.set_property("title", title)
        self.set_property("tool_vm", tool_vm)

class TabbedWindow(QWidget):
    """
    Main window with tabbed document and tool areas (MVVM).
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.doc_tabs = QTabWidget()
        self.tool_tabs = QTabWidget()
        layout = QVBoxLayout(self)
        layout.addWidget(self.doc_tabs)
        layout.addWidget(self.tool_tabs)
        self.setLayout(layout)
        self.doc_vm_list = []
        self.tool_vm_list = []

    def add_document_tab(self, vm: DocumentTabViewModel, widget_factory):
        widget = widget_factory(vm.get_property("content_vm"))
        idx = self.doc_tabs.addTab(widget, vm.get_property("title"))
        self.doc_vm_list.append(vm)
        logger.info(f"Added document tab: {vm.get_property('title')}")
        return idx

    def add_tool_tab(self, vm: ToolTabViewModel, widget_factory):
        widget = widget_factory(vm.get_property("tool_vm"))
        idx = self.tool_tabs.addTab(widget, vm.get_property("title"))
        self.tool_vm_list.append(vm)
        logger.info(f"Added tool tab: {vm.get_property('title')}")
        return idx

    def close_document_tab(self, idx):
        self.doc_tabs.removeTab(idx)
        del self.doc_vm_list[idx]
        logger.info(f"Closed document tab at index {idx}")

    def close_tool_tab(self, idx):
        self.tool_tabs.removeTab(idx)
        del self.tool_vm_list[idx]
        logger.info(f"Closed tool tab at index {idx}")
