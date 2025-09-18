from typing import Callable, Any, Dict, Type

class DataTemplate:
    """
    Maps a data type or predicate to a widget constructor for dynamic GUI generation.
    """
    _registry: Dict[Any, "DataTemplate"] = {}

    def __init__(self, data_type: type, widget_factory: Callable[[Any, dict], Any], predicate: Callable[[Any], bool] = None):
        self.data_type = data_type
        self.widget_factory = widget_factory
        self.predicate = predicate

    @classmethod
    def register(cls, data_type: type, widget_factory: Callable[[Any, dict], Any], predicate: Callable[[Any], bool] = None):
        template = cls(data_type, widget_factory, predicate)
        cls._registry[data_type] = template
        return template

    @classmethod
    def resolve(cls, data: Any, context: dict = None):
        # Try predicate-based templates first
        for template in cls._registry.values():
            if template.predicate and template.predicate(data):
                return template.widget_factory(data, context or {})
        # Fallback to type-based templates
        template = cls._registry.get(type(data))
        if template:
            return template.widget_factory(data, context or {})
        raise ValueError(f"No DataTemplate registered for type {type(data)}")

    @classmethod
    def clear_registry(cls):
        cls._registry.clear()
