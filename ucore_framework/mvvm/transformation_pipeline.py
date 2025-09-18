from typing import Any, Callable, List, Optional
from loguru import logger

class TransformationPipelineMixin:
    """
    Mixin for chaining, caching, and monitoring data transformations.
    """
    def __init__(self):
        self._transformations: List[Callable[[List[Any]], List[Any]]] = []
        self._cache: Optional[List[Any]] = None
        self._monitor_callback: Optional[Callable[[str, Any], None]] = None

    def add_transformation(self, func: Callable[[List[Any]], List[Any]]):
        logger.info("TransformationPipelineMixin: add_transformation")
        self._transformations.append(func)
        self._cache = None

    def clear_transformations(self):
        logger.info("TransformationPipelineMixin: clear_transformations")
        self._transformations.clear()
        self._cache = None

    def set_monitor_callback(self, callback: Callable[[str, Any], None]):
        logger.info("TransformationPipelineMixin: set_monitor_callback")
        self._monitor_callback = callback

    def transform(self, data: List[Any]) -> List[Any]:
        if self._cache is not None:
            return self._cache
        result = data
        for func in self._transformations:
            if self._monitor_callback:
                self._monitor_callback("before_transform", func)
            result = func(result)
            if self._monitor_callback:
                self._monitor_callback("after_transform", func)
        self._cache = result
        return result

    def invalidate_cache(self):
        logger.info("TransformationPipelineMixin: invalidate_cache")
        self._cache = None
