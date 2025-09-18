from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List
from loguru import logger

class PropertyChangedEvent:
    def __init__(self):
        self._handlers: List[Callable[[str, Any, Any], None]] = []

    def add(self, handler: Callable[[str, Any, Any], None]):
        self._handlers.append(handler)

    def remove(self, handler: Callable[[str, Any, Any], None]):
        self._handlers.remove(handler)

    def notify(self, property_name: str, old_value: Any, new_value: Any):
        for handler in self._handlers:
            handler(property_name, old_value, new_value)

class ModelBase(ABC):
    """Base class for data models in MVVM."""
    pass

class ViewModelBase(ABC):
    """Base class for ViewModels with property change notification and command support."""
    def __init__(self):
        self._property_changed = PropertyChangedEvent()
        self._properties: Dict[str, Any] = {}

    def add_property_changed_handler(self, handler: Callable[[str, Any, Any], None]):
        self._property_changed.add(handler)

    def remove_property_changed_handler(self, handler: Callable[[str, Any, Any], None]):
        self._property_changed.remove(handler)

    def set_property(self, name: str, value: Any):
        old_value = self._properties.get(name)
        if old_value != value:
            self._properties[name] = value
            self._property_changed.notify(name, old_value, value)
            logger.debug(f"Property '{name}' changed from {old_value} to {value}")

    def get_property(self, name: str) -> Any:
        return self._properties.get(name)

class Command(ABC):
    """Command pattern for ViewModel actions."""
    @abstractmethod
    def execute(self, *args, **kwargs):
        pass

class ObservableList(list):
    """List with change notification support."""
    def __init__(self, *args):
        super().__init__(*args)
        self._handlers: List[Callable[[str, Any], None]] = []

    def add_handler(self, handler: Callable[[str, Any], None]):
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[str, Any], None]):
        self._handlers.remove(handler)

    def notify(self, action: str, value: Any):
        for handler in self._handlers:
            handler(action, value)

    def append(self, value):
        super().append(value)
        self.notify('append', value)

    def remove(self, value):
        super().remove(value)
        self.notify('remove', value)

    def clear(self):
        super().clear()
        self.notify('clear', None)

class ObservableDict(dict):
    """Dict with change notification support."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._handlers: List[Callable[[str, Any, Any], None]] = []

    def add_handler(self, handler: Callable[[str, Any, Any], None]):
        self._handlers.append(handler)

    def remove_handler(self, handler: Callable[[str, Any, Any], None]):
        self._handlers.remove(handler)

    def notify(self, action: str, key: Any, value: Any):
        for handler in self._handlers:
            handler(action, key, value)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        self.notify('set', key, value)

    def __delitem__(self, key):
        value = self[key]
        super().__delitem__(key)
        self.notify('delete', key, value)

class ViewBase(ABC):
    """Base class for Views, to be implemented for each UI framework."""
    @abstractmethod
    def bind_viewmodel(self, viewmodel: ViewModelBase):
        pass

# --- AdvancedViewModelFactory for DI-based MVVM construction ---
from ucore_framework.core.di import Container, NoProviderError

class AdvancedViewModelFactory:
    """
    Factory for creating advanced ViewModels with DI-resolved mixins/services.
    """
    def __init__(self, container: Container):
        self.container = container

    def create(self, vm_cls, *args, **kwargs):
        # Try to resolve mixins/services from DI container and inject if needed
        try:
            data_provisioning = self.container.get(
                __import__("UCoreFrameworck.mvvm.data_provisioning", fromlist=["DataProvisioningMixin"]).DataProvisioningMixin
            )
        except NoProviderError:
            data_provisioning = None
        try:
            transformation = self.container.get(
                __import__("UCoreFrameworck.mvvm.transformation_pipeline", fromlist=["TransformationPipelineMixin"]).TransformationPipelineMixin
            )
        except NoProviderError:
            transformation = None
        try:
            grouping = self.container.get(
                __import__("UCoreFrameworck.mvvm.grouping_filter", fromlist=["GroupingFilterMixin"]).GroupingFilterMixin
            )
        except NoProviderError:
            grouping = None
        # Pass resolved mixins/services as kwargs if accepted by vm_cls
        injected = {}
        if "data_provisioning" in vm_cls.__init__.__code__.co_varnames:
            injected["data_provisioning"] = data_provisioning
        if "transformation" in vm_cls.__init__.__code__.co_varnames:
            injected["transformation"] = transformation
        if "grouping" in vm_cls.__init__.__code__.co_varnames:
            injected["grouping"] = grouping
        injected.update(kwargs)
        return vm_cls(*args, **injected)

# --- Decorator for auto-injecting MVVM features via DI ---
def inject_mvvm_features(vm_cls):
    """
    Decorator to auto-inject DI-resolved MVVM mixins/services into ViewModel __init__.
    """
    from ucore_framework.core.di import container, NoProviderError
    orig_init = vm_cls.__init__
    def __init__(self, *args, **kwargs):
        try:
            data_provisioning = container.get(
                __import__("UCoreFrameworck.mvvm.data_provisioning", fromlist=["DataProvisioningMixin"]).DataProvisioningMixin
            )
        except NoProviderError:
            data_provisioning = None
        try:
            transformation = container.get(
                __import__("UCoreFrameworck.mvvm.transformation_pipeline", fromlist=["TransformationPipelineMixin"]).TransformationPipelineMixin
            )
        except NoProviderError:
            transformation = None
        try:
            grouping = container.get(
                __import__("UCoreFrameworck.mvvm.grouping_filter", fromlist=["GroupingFilterMixin"]).GroupingFilterMixin
            )
        except NoProviderError:
            grouping = None
        if "data_provisioning" in orig_init.__code__.co_varnames and "data_provisioning" not in kwargs:
            kwargs["data_provisioning"] = data_provisioning
        if "transformation" in orig_init.__code__.co_varnames and "transformation" not in kwargs:
            kwargs["transformation"] = transformation
        if "grouping" in orig_init.__code__.co_varnames and "grouping" not in kwargs:
            kwargs["grouping"] = grouping
        orig_init(self, *args, **kwargs)
    vm_cls.__init__ = __init__
    return vm_cls
