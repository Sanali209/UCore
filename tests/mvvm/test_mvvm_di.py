from ucore_framework.core.di import container
from ucore_framework.mvvm.base import AdvancedViewModelFactory, inject_mvvm_features, ViewModelBase

def test_factory_injects_mvvm_features():
    factory = AdvancedViewModelFactory(container)
    class MyVM(ViewModelBase):
        def __init__(self, data_provisioning=None, transformation=None, grouping=None):
            self.data_provisioning = data_provisioning
            self.transformation = transformation
            self.grouping = grouping
    vm = factory.create(MyVM)
    assert vm.data_provisioning is not None
    assert vm.transformation is not None
    assert vm.grouping is not None

def test_decorator_injects_mvvm_features():
    @inject_mvvm_features
    class MyVM(ViewModelBase):
        def __init__(self, data_provisioning=None, transformation=None, grouping=None):
            self.data_provisioning = data_provisioning
            self.transformation = transformation
            self.grouping = grouping
    vm = MyVM()
    assert vm.data_provisioning is not None
    assert vm.transformation is not None
    assert vm.grouping is not None
