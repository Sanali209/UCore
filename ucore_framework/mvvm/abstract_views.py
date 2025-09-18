from abc import ABC, abstractmethod
from typing import Any, Callable, List, Optional
from ucore_framework.mvvm.base import ViewModelBase
from ucore_framework.mvvm.datatable import DataTemplate
from ucore_framework.mvvm.hierarchical_datatable import HierarchicalDataTemplate

class AbstractListView(ABC):
    """
    Abstract base for MVVM ListView with dynamic DataTemplate support and virtualization.
    """
    def __init__(self, viewmodel: ViewModelBase, template_resolver: Callable[[Any], Any]):
        self.viewmodel = viewmodel
        self.template_resolver = template_resolver

    @abstractmethod
    def set_items(self, items: List[Any]):
        pass

    @abstractmethod
    def refresh(self):
        pass

    @abstractmethod
    def set_virtualization(self, enabled: bool):
        pass

class AbstractTreeView(ABC):
    """
    Abstract base for MVVM TreeView with HierarchicalDataTemplate and virtualization.
    """
    def __init__(self, viewmodel: ViewModelBase, template_resolver: Callable[[Any], Any]):
        self.viewmodel = viewmodel
        self.template_resolver = template_resolver

    @abstractmethod
    def set_root(self, root: Any):
        pass

    @abstractmethod
    def refresh(self):
        pass

    @abstractmethod
    def set_virtualization(self, enabled: bool):
        pass

# Plugin registration example
class ListViewPluginBase(ABC):
    @abstractmethod
    def create_list_view(self, viewmodel: ViewModelBase) -> AbstractListView:
        pass

class TreeViewPluginBase(ABC):
    @abstractmethod
    def create_tree_view(self, viewmodel: ViewModelBase) -> AbstractTreeView:
        pass
