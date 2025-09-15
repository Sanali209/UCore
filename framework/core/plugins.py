# framework/plugins.py
from __future__ import annotations
import os
import importlib.util
import inspect
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .app import App

class Plugin(ABC):
    """
    Abstract base class for plugins. Plugins are extensions that can be
    dynamically loaded to add functionality to the application.
    """
    @abstractmethod
    def register(self, app: App) -> None:
        """
        Registers the plugin with the application. This method is called
        when the plugin is loaded.
        """
        raise NotImplementedError

class PluginManager:
    """
    Manages the discovery, loading, and registration of plugins.
    """
    def __init__(self, app: App):
        self.app = app
        self.logger = app.logger.getChild("PluginManager")

    def load_plugins(self, plugins_dir: str) -> None:
        """
        Discovers and loads plugins from a specified directory.
        """
        self.logger.info(f"Loading plugins from: {plugins_dir}")
        if not os.path.isdir(plugins_dir):
            self.logger.warning(f"Plugins directory not found: {plugins_dir}")
            return

        for filename in os.listdir(plugins_dir):
            if filename.endswith('.py') and not filename.startswith('__'):
                self._load_plugin_from_file(os.path.join(plugins_dir, filename))

    def _load_plugin_from_file(self, filepath: str) -> None:
        """
        Loads a single plugin from a file.
        """
        module_name = f"plugins.{os.path.basename(filepath)[:-3]}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, filepath)
            if spec is None:
                raise ImportError(f"Could not create module spec for {filepath}")
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            for name, obj in inspect.getmembers(module, inspect.isclass):
                if issubclass(obj, Plugin) and obj is not Plugin:
                    plugin_instance = obj()
                    plugin_instance.register(self.app)
                    self.logger.info(f"Registered plugin: {name}")

        except Exception as e:
            self.logger.error(f"Failed to load plugin from {filepath}: {e}", exc_info=True)
