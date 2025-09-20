from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QPushButton, QLabel
from ucore_framework.mvvm.base import ViewModelBase, Command

class CounterCommand(Command):
    def __init__(self, func):
        self.func = func
    
    def execute(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    
    def __call__(self, *args, **kwargs):
        return self.execute(*args, **kwargs)

class CounterViewModel(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.set_property("count", 0)
        self.increment_command = CounterCommand(self.increment)
        self.decrement_command = CounterCommand(self.decrement)

    @property
    def count(self):
        return self.get_property("count")

    @count.setter
    def count(self, value):
        self.set_property("count", value)

    def increment(self):
        self.count += 1

    def decrement(self):
        self.count -= 1

class CounterView(QWidget):
    def __init__(self, vm: CounterViewModel):
        super().__init__()
        self.vm = vm
        self.setWindowTitle("UCore MVVM Counter")
        layout = QVBoxLayout()
        self.label = QLabel(str(self.vm.count))
        btn_inc = QPushButton("Increment")
        btn_dec = QPushButton("Decrement")
        layout.addWidget(self.label)
        layout.addWidget(btn_inc)
        layout.addWidget(btn_dec)
        self.setLayout(layout)

        btn_inc.clicked.connect(self.vm.increment_command)
        btn_dec.clicked.connect(self.vm.decrement_command)
        self.vm.add_property_changed_handler(self.on_property_changed)

    def on_property_changed(self, property_name, old_value, new_value):
        if property_name == "count":
            self.label.setText(str(new_value))

if __name__ == "__main__":
    app = QApplication([])
    vm = CounterViewModel()
    view = CounterView(vm)
    view.show()
    app.exec()
