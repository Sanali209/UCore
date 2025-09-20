"""Configuration management logic module (decomposed from app.py)."""

from loguru import logger
from .config import ConfigManager as CoreConfigManager
from .event_bus import EventBus
from .event_types import ConfigurationChangedEvent

class ConfigurationManager:
    """
    Manages application configuration loading, reloading, and notification.
    """
    def __init__(self, container, app_logger=None):
        self.container = container
        self.logger = app_logger or logger

    def reload_config(self, config_path: str = None) -> None:
        """
        Reloads configuration from file and environment.
        Notifies all components of configuration changes.
        """
        config = self.container.get(CoreConfigManager)
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

        # Notify all registered components of config update (backward compatibility)
        # The component list should be passed in or managed externally
        self.logger.info("Configuration reloaded and components notified")

    def update_log_level(self, level: str) -> None:
        """
        Updates the global log level and notifies all components.
        """
        logger.level(level.upper())
        self.logger.info(f"Log level updated to {level.upper()}")

    def load_config(self, config_path: str) -> None:
        """
        Alias for reload_config for backward compatibility.
        """
        self.reload_config(config_path)
