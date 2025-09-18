from ucore_framework.desktop.plugins.api import PluginBase
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from ucore_framework.mvvm.base import ViewModelBase

class TextEditorViewModel(ViewModelBase):
    def __init__(self, text=""):
        super().__init__()
        self.set_property("text", text)

class TextEditorWidget(QWidget):
    def __init__(self, vm: TextEditorViewModel):
        super().__init__()
        self.vm = vm
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(vm.get_property("text"))
        layout = QVBoxLayout(self)
        layout.addWidget(self.text_edit)
        self.setLayout(layout)
        self.text_edit.textChanged.connect(self.on_text_changed)
        if hasattr(vm, "add_property_changed_handler"):
            vm.add_property_changed_handler(self.on_vm_change)

    def on_text_changed(self):
        self.vm.set_property("text", self.text_edit.toPlainText())

    def on_vm_change(self, name, old, new):
        if name == "text" and self.text_edit.toPlainText() != new:
            self.text_edit.setPlainText(new)

class TextEditorPlugin(PluginBase):
    def __init__(self, **kwargs):
        self.vm = TextEditorViewModel(kwargs.get("text", ""))

    def activate(self, app_context):
        pass

    def deactivate(self):
        pass

    def get_metadata(self):
        return {"type": "editor", "name": "TextEditor"}

    def create_widget(self):
        return TextEditorWidget(self.vm)
