from ucore_framework.desktop.plugins.api import PluginBase
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtGui import QPixmap
from ucore_framework.mvvm.base import ViewModelBase

class ImageViewerViewModel(ViewModelBase):
    def __init__(self, image_path=""):
        super().__init__()
        self.set_property("image_path", image_path)

class ImageViewerWidget(QWidget):
    def __init__(self, vm: ImageViewerViewModel):
        super().__init__()
        self.vm = vm
        self.label = QLabel()
        layout = QVBoxLayout(self)
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.update_image()
        if hasattr(vm, "add_property_changed_handler"):
            vm.add_property_changed_handler(self.on_vm_change)

    def update_image(self):
        path = self.vm.get_property("image_path")
        if path:
            pixmap = QPixmap(path)
            self.label.setPixmap(pixmap)

    def on_vm_change(self, name, old, new):
        if name == "image_path":
            self.update_image()

class ImageViewerPlugin(PluginBase):
    def __init__(self, **kwargs):
        self.vm = ImageViewerViewModel(kwargs.get("image_path", ""))

    def activate(self, app_context):
        pass

    def deactivate(self):
        pass

    def get_metadata(self):
        return {"type": "viewer", "name": "ImageViewer"}

    def create_widget(self):
        return ImageViewerWidget(self.vm)
