import pytest
from ucore_framework.mvvm.base import ViewModelBase, ObservableList
from ucore_framework.mvvm.data_provider import InMemoryProvider
from ucore_framework.mvvm.grouping_filter import GroupingFilterMixin
from ucore_framework.mvvm.data_provisioning import DataProvisioningMixin
from ucore_framework.mvvm.transformation_pipeline import TransformationPipelineMixin
from ucore_framework.mvvm.datatable import DataTemplate
from ucore_framework.mvvm.hierarchical_datatable import HierarchicalDataTemplate
from ucore_framework.messaging.event_bus import EventBus
from loguru import logger

def test_mvvm_and_data():
    class VM(ViewModelBase, GroupingFilterMixin, DataProvisioningMixin, TransformationPipelineMixin):
        def __init__(self, data):
            ViewModelBase.__init__(self)
            GroupingFilterMixin.__init__(self)
            DataProvisioningMixin.__init__(self)
            TransformationPipelineMixin.__init__(self)
            self.provider = InMemoryProvider(data)
            self.set_property("items", ObservableList(self.provider.get_data()))

    vm = VM(["a", "b", "c", "d"])
    vm.set_group_func(lambda x: x)
    assert vm.group_data(vm.get_property("items"))["a"] == ["a"]
    vm.set_filter_func(lambda x: x in ("a", "b"))
    assert set(vm.filter_data(vm.get_property("items"))) == {"a", "b"}
    vm.add_transformation(lambda items: [x.upper() for x in items])
    assert vm.transform(["a", "b"]) == ["A", "B"]

def test_event_bus():
    from ucore_framework.messaging.events import Event
    bus = EventBus()
    events = []
    class TestEvent(Event):
        def __init__(self, value):
            super().__init__()
            self.value = value
    def handler(event):
        events.append(event.value)
    bus.subscribe(TestEvent, handler)
    bus.publish(TestEvent("hello"))
    assert events == ["hello"]

def test_logging_usage():
    logger.info("Framework logging test")
    assert True  # If no exception, logging works

def test_datatemplate_and_hierarchical():
    DataTemplate.clear_registry()
    DataTemplate.register(str, lambda data, ctx: f"str:{data}")
    assert DataTemplate.resolve("abc") == "str:abc"

    HierarchicalDataTemplate.clear_registry()
    HierarchicalDataTemplate.register(
        dict,
        lambda data, ctx: f"node:{data['name']}",
        lambda data: data.get("children", [])
    )
    tree = {"name": "root", "children": [{"name": "child", "children": []}]}
    assert HierarchicalDataTemplate.resolve(tree) == "node:root"
