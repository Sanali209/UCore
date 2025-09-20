from ucore_framework.core.plugins import Plugin, plugin, PluginType
from PySide6.QtWidgets import QWidget, QTextEdit, QVBoxLayout

class TextViewerWidget(QWidget):
    def __init__(self, content: str):
        super().__init__()
        layout = QVBoxLayout()
        self.editor = QTextEdit()
        self.editor.setPlainText(content)
        self.editor.setReadOnly(True)
        layout.addWidget(self.editor)
        self.setLayout(layout)

@plugin(plugin_type=PluginType.VIEWER, supported_formats=["txt", "py"])
class TextViewerPlugin(Plugin):
    def create_widget(self, content: str) -> QWidget:
        return TextViewerWidget(content)
