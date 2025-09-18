from PySide6.QtWidgets import QApplication, QLabel
from ucore_framework.desktop.ui.tabbed_window import TabbedWindow, DocumentTabViewModel, ToolTabViewModel
from ucore_framework.mvvm.base import ViewModelBase
import sys

class DummyEditorViewModel(ViewModelBase):
    def __init__(self, text):
        super().__init__()
        self.set_property("text", text)

def editor_widget_factory(vm):
    return QLabel(f"Editor: {vm.get_property('text')}")

class DummyToolViewModel(ViewModelBase):
    def __init__(self, name):
        super().__init__()
        self.set_property("name", name)

def tool_widget_factory(vm):
    return QLabel(f"Tool: {vm.get_property('name')}")

def main():
    app = QApplication(sys.argv)
    window = TabbedWindow()

    # Add document tabs
    doc1_vm = DocumentTabViewModel("Readme.md", DummyEditorViewModel("This is the README."))
    doc2_vm = DocumentTabViewModel("main.py", DummyEditorViewModel("print('Hello World')"))
    window.add_document_tab(doc1_vm, editor_widget_factory)
    window.add_document_tab(doc2_vm, editor_widget_factory)

    # Add tool tabs
    tool1_vm = ToolTabViewModel("Terminal", DummyToolViewModel("Terminal"))
    tool2_vm = ToolTabViewModel("Search", DummyToolViewModel("Search"))
    window.add_tool_tab(tool1_vm, tool_widget_factory)
    window.add_tool_tab(tool2_vm, tool_widget_factory)

    window.setWindowTitle("TabbedWindow MVVM Demo")
    window.resize(800, 600)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
