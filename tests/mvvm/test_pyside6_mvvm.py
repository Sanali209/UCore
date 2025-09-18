import pytest
from ucore_framework.mvvm.base import ViewModelBase, ObservableList
from ucore_framework.mvvm.pyside6 import ListViewWidget
from PySide6.QtWidgets import QApplication, QLabel

@pytest.fixture(scope="module")
def app():
    import sys
    app = QApplication.instance() or QApplication(sys.argv)
    yield app

def test_listviewwidget_binding(app):
    class VM(ViewModelBase):
        def __init__(self):
            super().__init__()
            self.set_property("items", ObservableList(["a", "b", "c"]))
    vm = VM()
    widget = ListViewWidget(vm, lambda item, parent: QLabel(str(item)))
    assert widget.count() == 3
    vm.set_property("items", ObservableList(["x", "y"]))
    assert widget.count() == 2
