import sys
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget, QFileDialog, QMessageBox
from PySide6.QtGui import QAction
from ucore_framework.core.plugins import PluginManager, PluginType
from ucore_framework.desktop.ui.tabbed_window import TabbedWindow, DocumentTabViewModel
from ucore_framework.core.app import App

class PluginNotepad(QMainWindow):
    def __init__(self, plugin_manager):
        super().__init__()
        self.setWindowTitle("PluginNotepad")
        self.tabs = TabbedWindow()
        self.setCentralWidget(self.tabs)
        self.plugin_manager = plugin_manager

        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")
        open_action = QAction("Open", self)
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open File", "", "All Files (*)")
        if not file_path:
            return
        ext = os.path.splitext(file_path)[1][1:].lower()
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        viewer_plugin = self.find_viewer_plugin(ext)
        if not viewer_plugin:
            QMessageBox.warning(self, "No Plugin", f"No viewer plugin for .{ext} files.")
            return
        # Create a simple content view model
        class ContentViewModel:
            def __init__(self, content):
                self.content = content
        
        content_vm = ContentViewModel(content)
        doc_vm = DocumentTabViewModel(os.path.basename(file_path), content_vm)
        
        # Widget factory that creates the plugin widget
        def widget_factory(content_vm):
            return viewer_plugin.create_widget(content_vm.content)
        
        self.tabs.add_document_tab(doc_vm, widget_factory)

    def find_viewer_plugin(self, ext):
        # Get all registered plugins and filter for viewer plugins
        for plugin in self.plugin_manager.registry.plugins.values():
            if hasattr(plugin, "plugin_type") and plugin.plugin_type == PluginType.VIEWER:
                if hasattr(plugin, "supported_formats") and ext in getattr(plugin, "supported_formats", []):
                    return plugin
        return None

def main():
    qt_app = QApplication(sys.argv)
    ucore_app = App("PluginNotepad")
    plugin_manager = PluginManager(ucore_app)
    plugin_manager.load_plugins("example/pluginnotepad/plugins")
    window = PluginNotepad(plugin_manager)
    window.resize(800, 600)
    window.show()
    sys.exit(qt_app.exec())

if __name__ == "__main__":
    main()
