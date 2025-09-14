# UCore Framework
"""
UCore: Enterprise-Grade Framework for Python Applications

This framework provides:
- Component-based architecture with dependency injection
- Comprehensive observability (Prometheus + OpenTelemetry)
- Background task processing with Redis/Celery
- Professional CLI tools and user interfaces
- Database operations with SQLAlchemy
- Plugin system for extensibility
- Configuration management with YAML support
- Simulation and entity management
"""

__version__ = "1.0.0"
__author__ = "UCore Team"

# Core exports
from .app import App
from .component import Component
from .config import Config
from .di import Container, Scope

# Simulation exports
from . import simulation

# UI exports
from . import ui

# Utility exports
from .logging import Logging
from .plugins import Plugin

# Concurrent tasks exports
from . import cpu_tasks

__all__ = [
    '__version__',
    '__author__',
    'App',
    'Component',
    'Config',
    'Container',
    'Scope',
    'simulation',
    'ui',
    'Logging',
    'Plugin',
    'cpu_tasks'
]
