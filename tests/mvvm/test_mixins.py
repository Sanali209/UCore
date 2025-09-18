import pytest
from ucore_framework.mvvm.grouping_filter import GroupingFilterMixin
from ucore_framework.mvvm.data_provisioning import DataProvisioningMixin
from ucore_framework.mvvm.transformation_pipeline import TransformationPipelineMixin

class DummyVM(GroupingFilterMixin, DataProvisioningMixin, TransformationPipelineMixin):
    def __init__(self, data):
        GroupingFilterMixin.__init__(self)
        DataProvisioningMixin.__init__(self)
        TransformationPipelineMixin.__init__(self)
        self.data = data

def test_grouping_filter():
    vm = DummyVM(["apple", "banana", "carrot", "avocado"])
    vm.set_group_func(lambda x: x[0])
    grouped = vm.group_data(vm.data)
    assert grouped["a"] == ["apple", "avocado"]
    vm.set_filter_func(lambda x: "a" in x)
    filtered = vm.filter_data(vm.data)
    assert set(filtered) == {"apple", "banana", "carrot", "avocado"}
    vm.undo_grouping()
    assert "b" not in vm.group_data(vm.data)

def test_data_provisioning():
    vm = DummyVM(list(range(10)))
    vm.set_provision_mode("visible")
    visible = vm.provide_data(vm.data, visible_indices=[1, 3, 5])
    assert visible == [1, 3, 5]
    vm.set_batch_size(4)
    batches = vm.provide_data_in_batches(vm.data)
    assert batches[0] == [0, 1, 2, 3]
    assert batches[2] == [8, 9]

def test_transformation_pipeline():
    vm = DummyVM([1, 2, 3])
    vm.add_transformation(lambda items: [x * 2 for x in items])
    vm.add_transformation(lambda items: [x + 1 for x in items])
    result = vm.transform(vm.data)
    assert result == [3, 5, 7]
    vm.invalidate_cache()
    vm.clear_transformations()
    assert vm.transform(vm.data) == [1, 2, 3]
