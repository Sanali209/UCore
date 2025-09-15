"""
Core Framework Components

This package contains the fundamental building blocks of the UCore framework:
- App: Main application orchestrator
- Component: Base component class for all framework components
- DI Container: Dependency injection system
- Config: Configuration management
- Plugin: Plugin system for extensibility
"""

from .app import App
from .component import Component
from .di import Container, Scope
from .config import Config
from .plugins import Plugin
from .settings import SettingsManager as Settings

__all__ = ['App', 'Component', 'Container', 'Scope', 'Config', 'Plugin', 'Settings']
