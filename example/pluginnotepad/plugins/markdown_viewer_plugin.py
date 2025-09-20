from ucore_framework.core.plugins import Plugin, plugin, PluginType
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

class MarkdownViewerWidget(QWidget):
    def __init__(self, content: str):
        super().__init__()
        layout = QVBoxLayout()
        self.browser = QTextBrowser()
        self.browser.setMarkdown(content)
        layout.addWidget(self.browser)
        self.setLayout(layout)

@plugin(plugin_type=PluginType.VIEWER, supported_formats=["md"])
class MarkdownViewerPlugin(Plugin):
    def create_widget(self, content: str) -> QWidget:
        return MarkdownViewerWidget(content)
