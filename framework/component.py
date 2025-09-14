# framework/component.py
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .app import App
    from .config import Config

class Component:
    """
    Base class for components that have a lifecycle managed by the App.
    Components can be initialized with a reference to the main App instance.
    """
    def __init__(self, app: "App" = None):
        self.app = app

    def start(self) -> None:
        """
        Called when the application starts.
        This method can be a coroutine.
        """
        pass

    def stop(self) -> None:
        """
        Called when the application stops.
        This method can be a coroutine.
        """
        pass

    def on_config_update(self, config: "Config") -> None:
        """
        Called when the application configuration is updated at runtime.
        Components can implement this method to react to configuration changes.
        """
        pass
