"""
UCore Framework - Desktop UI Domain
===================================

Advanced PySide6-based user interface components with sophisticated MVC architecture.

This domain provides:
- PySide6Adapter: Bridge to Qt event loop
- Hierarchical tree and list widgets (MVVM pattern)
- Resource provider integration
- Advanced data views for large datasets

Components:
- PySide6Adapter: Qt application lifecycle management
- HierarchicalDataViewModel: MVVM ViewModel for tree/list synchronization
"""

from .pyside6_adapter import PySide6Adapter
# from .advanced_tree_list_view_model import HierarchicalDataViewModel

# Try to import MongoDB-integrated version
try:
    from ucore_framework.data.mongo_list_view_model import MongoHierarchicalDataViewModel
    MONGO_AVAILABLE = True
except ImportError:
    MONGO_AVAILABLE = False
    MongoHierarchicalDataViewModel = None

__all__ = [
    "PySide6Adapter",
    # "HierarchicalDataViewModel",
]

# Add MongoDB integration if available
if MONGO_AVAILABLE:
    __all__.append("MongoHierarchicalDataViewModel")
