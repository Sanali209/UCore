from typing import Any, List
from PySide6.QtWidgets import QWidget, QVBoxLayout
from .datatable import DataTemplate
from .hierarchical_datatable import HierarchicalDataTemplate
from .base import ObservableList

def build_widgets_from_list(data_list: ObservableList, context: dict = None) -> QWidget:
    """
    Dynamically build a QWidget containing child widgets for each item in data_list,
    using DataTemplate resolution.
    """
    container = QWidget()
    layout = QVBoxLayout(container)
    for item in data_list:
        widget = DataTemplate.resolve(item, context or {})
        layout.addWidget(widget)
    container.setLayout(layout)
    return container

def build_hierarchical_widget(data: Any, context: dict = None) -> QWidget:
    """
    Build a hierarchical widget (e.g., tree) from data using HierarchicalDataTemplate resolution.
    """
    widget = HierarchicalDataTemplate.resolve(data, context or {})
    return widget
