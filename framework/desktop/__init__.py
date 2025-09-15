"""
Desktop Application Components

This package contains desktop GUI application components:
- PySide6Adapter: Native Qt/PySide6 desktop interface
- FletAdapter: Web-based desktop interface
- Desktop UI components and adapters
"""

# Optional imports - handle missing GUI dependencies gracefully
try:
    from .ui.pyside6_adapter import PySide6Adapter
    _pyside6_available = True
except ImportError:
    _pyside6_available = False

# Flet might be available even if PySide6 is not
try:
    from .ui.flet_adapter import FletAdapter
    _flet_available = True
except ImportError:
    _flet_available = False

# Conditional exports
__all__ = []
if _pyside6_available:
    __all__.append('PySide6Adapter')
if _flet_available:
    __all__.append('FletAdapter')
