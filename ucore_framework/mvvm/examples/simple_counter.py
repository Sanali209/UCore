from PySide6.QtWidgets import QApplication, QVBoxLayout, QPushButton, QLabel, QWidget
from ucore_framework.mvvm.base import ViewModelBase, Command
from ucore_framework.mvvm.pyside6 import PySide6ViewBase, bind_property, bind_command
import sys

class IncrementCommand(Command):
    def __init__(self, viewmodel):
        self._viewmodel = viewmodel

    def execute(self, *args, **kwargs):
        count = self._viewmodel.get_property("count")
        self._viewmodel.set_property("count", count + 1)

class CounterViewModel(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.set_property("count", 0)
        self.increment_command = IncrementCommand(self)

class CounterView(PySide6ViewBase):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.label = QLabel("0")
        self.button = QPushButton("Increment")
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        layout.addWidget(self.button)
        self.setLayout(layout)

    def on_viewmodel_bound(self, viewmodel):
        bind_property(self.label, "text", viewmodel, "count")
        bind_command(self.button, "clicked", viewmodel.increment_command)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    vm = CounterViewModel()
    view = CounterView()
    view.bind_viewmodel(vm)
    view.show()
    sys.exit(app.exec())
