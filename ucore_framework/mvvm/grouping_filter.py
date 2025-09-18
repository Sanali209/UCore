from typing import Any, Callable, List, Dict, Optional
from ucore_framework.mvvm.base import ViewModelBase
from loguru import logger

class GroupingFilterMixin:
    """
    Mixin for grouping and filtering logic in ViewModels.
    Supports runtime updates, lazy evaluation, and undoable actions.
    """
    def __init__(self):
        self._group_func: Optional[Callable[[Any], Any]] = None
        self._filter_func: Optional[Callable[[Any], bool]] = None
        self._grouped_data: Optional[Dict[Any, List[Any]]] = None
        self._filtered_data: Optional[List[Any]] = None

    def set_group_func(self, func: Callable[[Any], Any]):
        logger.info("GroupingFilterMixin: set_group_func")
        self._group_func = func
        self._grouped_data = None  # Invalidate cache

    def set_filter_func(self, func: Callable[[Any], bool]):
        logger.info("GroupingFilterMixin: set_filter_func")
        self._filter_func = func
        self._filtered_data = None  # Invalidate cache

    def group_data(self, data: List[Any]) -> Dict[Any, List[Any]]:
        if self._grouped_data is not None:
            return self._grouped_data
        if not self._group_func:
            return {"all": data}
        grouped = {}
        for item in data:
            key = self._group_func(item)
            grouped.setdefault(key, []).append(item)
        self._grouped_data = grouped
        return grouped

    def filter_data(self, data: List[Any]) -> List[Any]:
        if self._filtered_data is not None:
            return self._filtered_data
        if not self._filter_func:
            return data
        filtered = [item for item in data if self._filter_func(item)]
        self._filtered_data = filtered
        return filtered

    def clear_grouping_filter_cache(self):
        self._grouped_data = None
        self._filtered_data = None

    def undo_grouping(self):
        self._group_func = None
        self._grouped_data = None

    def undo_filtering(self):
        self._filter_func = None
        self._filtered_data = None
