import pytest
from ucore_framework.mvvm.base import ViewModelBase, Command, ObservableList, ObservableDict

class TestCommand(Command):
    def __init__(self):
        self.executed = False
        self.args = None

    def execute(self, *args, **kwargs):
        self.executed = True
        self.args = args

class DummyViewModel(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.set_property("value", 0)
        self.test_command = TestCommand()

def test_property_change_notification():
    vm = DummyViewModel()
    changes = []
    def handler(name, old, new):
        changes.append((name, old, new))
    vm.add_property_changed_handler(handler)
    vm.set_property("value", 42)
    assert changes == [("value", 0, 42)]

def test_command_execution():
    vm = DummyViewModel()
    vm.test_command.execute(1, 2)
    assert vm.test_command.executed
    assert vm.test_command.args == (1, 2)

def test_observable_list():
    ol = ObservableList()
    events = []
    ol.add_handler(lambda action, value: events.append((action, value)))
    ol.append("a")
    ol.remove("a")
    ol.clear()
    assert events[0][0] == "append"
    assert events[1][0] == "remove"
    assert events[2][0] == "clear"

def test_observable_dict():
    od = ObservableDict()
    events = []
    od.add_handler(lambda action, key, value: events.append((action, key, value)))
    od["x"] = 1
    del od["x"]
    assert events[0][0] == "set"
    assert events[1][0] == "delete"
