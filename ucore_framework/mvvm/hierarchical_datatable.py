from typing import Callable, Any, Dict, List
from .datatable import DataTemplate

class HierarchicalDataTemplate(DataTemplate):
    """
    Extends DataTemplate for hierarchical/recursive data (e.g., trees).
    Supports child item templates and parent-child relationships.
    """
    _hierarchical_registry: Dict[Any, "HierarchicalDataTemplate"] = {}

    def __init__(
        self,
        data_type: type,
        widget_factory: Callable[[Any, dict], Any],
        children_selector: Callable[[Any], List[Any]],
        child_template: "HierarchicalDataTemplate" = None,
        predicate: Callable[[Any], bool] = None
    ):
        super().__init__(data_type, widget_factory, predicate)
        self.children_selector = children_selector
        self.child_template = child_template

    @classmethod
    def register(
        cls,
        data_type: type,
        widget_factory: Callable[[Any, dict], Any],
        children_selector: Callable[[Any], List[Any]],
        child_template: "HierarchicalDataTemplate" = None,
        predicate: Callable[[Any], bool] = None
    ):
        template = cls(data_type, widget_factory, children_selector, child_template, predicate)
        cls._hierarchical_registry[data_type] = template
        return template

    @classmethod
    def resolve(cls, data: Any, context: dict = None):
        # Try predicate-based templates first
        for template in cls._hierarchical_registry.values():
            if template.predicate and template.predicate(data):
                return template._build_widget(data, context or {})
        # Fallback to type-based templates
        template = cls._hierarchical_registry.get(type(data))
        if template:
            return template._build_widget(data, context or {})
        raise ValueError(f"No HierarchicalDataTemplate registered for type {type(data)}")

    def _build_widget(self, data: Any, context: dict):
        widget = self.widget_factory(data, context)
        children = self.children_selector(data)
        if self.child_template and children:
            child_widgets = [self.child_template._build_widget(child, context) for child in children]
            # Attach child widgets to parent widget (customize as needed)
            if hasattr(widget, "add_child"):
                for cw in child_widgets:
                    widget.add_child(cw)
            elif hasattr(widget, "addItem"):
                for cw in child_widgets:
                    widget.addItem(cw)
            elif hasattr(widget, "addWidget"):
                for cw in child_widgets:
                    widget.addWidget(cw)
        return widget

    @classmethod
    def clear_registry(cls):
        cls._hierarchical_registry.clear()
