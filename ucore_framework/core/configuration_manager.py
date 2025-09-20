"""Configuration management logic module (decomposed from app.py)."""

from .config import ConfigManager
from .event_bus import EventBus
from .event_types import ConfigurationChangedEvent
from loguru import logger

class ConfigurationManager:
    """
    Handles loading, parsing, and accessing configuration settings for the application.
    Wraps ConfigManager and manages config reloads, environment loading, and event publishing.
    """
    def __init__(self, container, app_logger=None):
        self.container = container
        self.logger = app_logger or logger
        self.config = self.container.get(ConfigManager)

    def reload_config(self, config_path: str = None):
        """
        Reloads configuration from file and environment.
        Notifies all components of configuration changes.
        """
        config = self.config
        old_config = config.get_all().copy()

        if config_path:
            self.logger.info(f"Loading configuration from file: {config_path}")
            config.reload()

        self.logger.info("Loading configuration from environment variables")
        config._load_from_env()

        new_config = config.get_all()
        updated_keys = [k for k in new_config if old_config.get(k) != new_config.get(k)]
        old_values = {k: old_config.get(k) for k in updated_keys}
        new_values = {k: new_config.get(k) for k in updated_keys}

        event_bus = self.container.get(EventBus)
        update_event = ConfigurationChangedEvent(
            changed_keys=updated_keys,
            old_values=old_values,
            new_values=new_values
        )
        event_bus.publish(update_event)

        # Notify all registered components of config update (if container provides them)
        if hasattr(self.container, "get_all_components"):
            for component in self.container.get_all_components():
                if hasattr(component, 'on_config_update'):
                    try:
                        component.on_config_update(config)
                    except Exception as e:
                        self.logger.error(f"Error updating config for component {component.__class__.__name__}: {e}")

        self.logger.info("Configuration reloaded and components notified")

    def update_log_level(self, level: str):
        logger.level(level.upper())
        self.logger.info(f"Log level updated to {level.upper()}")

    def load_config(self, config_path: str):
        self.reload_config(config_path)
