"""
Unified Configuration and Settings Management for UCore Framework

This module provides a centralized configuration and settings management system:
- Unified YAML-based config/settings loading and saving
- Environment variable overrides
- Runtime change callbacks for settings
- Thread safety
- App-specific helpers (window geometry, download directory, etc.)
- OOP, extensibility, and loguru for logging

Usage:
    from ucore_framework.core.config import ConfigManager, get_config, set_config_value

    config = get_config()
    value = config.get("some_key")
    config.set("some_key", "new_value")
    # Legacy Config class is removed; use ConfigManager everywhere.
"""

import os
import yaml
from typing import Any, Dict, Callable, Optional, List, Union
from pathlib import Path
import threading
from loguru import logger
from pydantic import BaseModel, Field
from ucore_framework.core.resource.secrets import EnhancedSecretsManager

class ConfigSchema(BaseModel):
    """
    Pydantic schema for application configuration.

    Attributes:
        app_name: Application name.
        version: Application version.
        download_directory: Default download directory.
        recent_directories: List of recently used directories.
        max_results: Maximum number of results to fetch.
        workers: Number of worker threads.
        timeout: Default timeout for operations.
        log_level: Logging level.
        window_geometry: Window geometry settings (width, height, x, y).
    """
    app_name: str = Field(default="DuckDuckGo Search")
    version: str = Field(default="1.0.0")
    download_directory: str = Field(default_factory=lambda: str(Path.home() / "Downloads" / "duckduckgo_images"))
    recent_directories: List[str] = Field(default_factory=list)
    max_results: int = 200
    workers: int = 4
    timeout: float = 30.0
    log_level: str = "INFO"
    window_geometry: Dict[str, int] = Field(default_factory=lambda: {"width": 1200, "height": 800, "x": 100, "y": 100})

class ConfigManager:
    """
    Unified configuration and settings manager for UCore.

    Responsibilities:
        - Load and merge configuration from YAML files and environment variables
        - Provide runtime change callbacks and thread safety
        - Validate configuration using Pydantic schemas
        - Support app-specific helpers (window geometry, download directory, etc.)
        - Integrate with secrets manager for secure values

    Example:
        config = ConfigManager()
        value = config.get("app_name")
        config.set("workers", 8)
        config.save()
    """
    def __init__(self, config_files: Optional[Union[str, List[str]]] = None, env_prefix: str = "UCORE", env_separator: str = "_"):
        self.env_prefix = env_prefix
        self.env_separator = env_separator
        self._lock = threading.RLock()
        self._callbacks: Dict[str, List[Callable]] = {}
        self._data: Dict[str, Any] = {}
        
        # Handle both single string and list of config files
        if config_files is None:
            self.config_files = [
                "app_config.yml",
                "config.yml",
                "custom_settings.yml"
            ]
        elif isinstance(config_files, str):
            self.config_files = [config_files]
        else:
            self.config_files = config_files
            
        self._load_all()

    def _load_all(self):
        self._load_from_files(self.config_files)
        self._load_from_env()
        self._load_defaults_if_needed()
        # --- Inject secrets from EnhancedSecretsManager if alias keys are present ---
        secrets_manager = EnhancedSecretsManager()
        # Example: secret_key_alias, database_url_alias
        for secret_field in ["secret_key", "database_url"]:
            alias_key = f"{secret_field}_alias"
            if alias_key in self._data:
                secret_value = secrets_manager.get_secret(self._data[alias_key])
                if secret_value:
                    self._data[secret_field] = secret_value
                else:
                    logger.error(f"Failed to retrieve secret for alias '{self._data[alias_key]}'")
        # Validate and store as ConfigSchema
        try:
            from ucore_framework.core.validation import ConfigModel
            self.validated_config = ConfigModel(**self._data)
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise SystemExit("Exiting due to invalid configuration.")
        self._schema = ConfigSchema(**self._data)

    def _load_from_files(self, filepaths: List[str]):
        for filepath in filepaths:
            config_path = Path(filepath)
            try:
                if config_path.exists():
                    with open(config_path, 'r', encoding='utf-8') as f:
                        file_config = yaml.safe_load(f) or {}
                    self._deep_merge(self._data, file_config)
                    logger.info(f"Loaded configuration from {config_path}")
                else:
                    logger.debug(f"Configuration file {config_path} not found, skipping")
            except yaml.YAMLError as e:
                logger.error(f"Error parsing YAML file {config_path}: {e}")
            except Exception as e:
                logger.error(f"Error loading configuration from {config_path}: {e}")

    def _load_from_env(self):
        prefix = f"{self.env_prefix}{self.env_separator}"
        for key, value in os.environ.items():
            if key.startswith(prefix):
                config_key = key[len(prefix):].lower()
                # For simple keys like UCORE_MAX_RESULTS -> max_results, don't split further
                # Only split if there are nested separators beyond the main one
                self._data[config_key] = self._cast_value(value)

    def _load_defaults_if_needed(self):
        defaults = {
            "app_name": "DuckDuckGo Search",
            "version": "1.0.0",
            "download_directory": str(Path.home() / "Downloads" / "duckduckgo_images"),
            "recent_directories": [],
            "max_results": 200,
            "workers": 4,
            "timeout": 30.0,
            "log_level": "INFO",
            "window_geometry": {
                "width": 1200,
                "height": 800,
                "x": 100,
                "y": 100
            },
        }
        for key, value in defaults.items():
            if key not in self._data:
                self._data[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        with self._lock:
            # Prefer schema attribute if available
            if hasattr(self, "_schema") and hasattr(self._schema, key):
                return getattr(self._schema, key)
            return self._data.get(key, default)

    def set(self, key: str, value: Any, save_immediately: bool = True):
        with self._lock:
            old_value = self._data.get(key)
            if old_value != value:
                self._data[key] = value
                # Update schema if possible
                if hasattr(self, "_schema") and hasattr(self._schema, key):
                    setattr(self._schema, key, value)
                if save_immediately:
                    self.save()
                if key in self._callbacks:
                    for callback in self._callbacks[key]:
                        try:
                            callback(key, value, old_value)
                        except Exception as e:
                            logger.warning(f"Settings callback error for {key}: {e}")
                logger.info(f"Setting updated: {key} = {value}")

    def subscribe(self, key: str, callback: Callable) -> bool:
        with self._lock:
            if key not in self._callbacks:
                self._callbacks[key] = []
            self._callbacks[key].append(callback)
            return True

    def unsubscribe(self, key: str, callback: Callable) -> bool:
        with self._lock:
            if key in self._callbacks and callback in self._callbacks[key]:
                self._callbacks[key].remove(callback)
                return True
            return False

    def save(self) -> bool:
        try:
            with self._lock:
                # Save to the first config file
                config_path = Path(self.config_files[0])
                with open(config_path, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(self._data, f, default_flow_style=False, allow_unicode=True)
                logger.info(f"Settings saved to {config_path}")
                return True
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
            return False

    def reload(self) -> bool:
        try:
            with self._lock:
                self._data.clear()
                self._load_all()
                # Re-validate schema after reload
                self._schema = ConfigSchema(**self._data)
            logger.info("Settings reloaded from YAML and environment")
            return True
        except Exception as e:
            logger.error(f"Failed to reload settings: {e}")
            return False

    def get_all(self) -> Dict:
        with self._lock:
            return self._data.copy()

    # App-specific helpers
    def get_download_directory(self) -> str:
        return self.get("download_directory")

    def set_download_directory(self, directory: str):
        if os.path.isdir(directory):
            self.set("download_directory", directory)
            recent = self.get("recent_directories", [])
            if directory in recent:
                recent.remove(directory)
            recent.insert(0, directory)
            recent = recent[:10]
            self.set("recent_directories", recent)
            return True
        return False

    def get_recent_directories(self) -> list:
        return self.get("recent_directories", [])

    def get_window_geometry(self) -> Dict:
        return self.get("window_geometry", {"width": 1200, "height": 800, "x": 100, "y": 100})

    def set_window_geometry(self, geometry: Dict):
        self.set("window_geometry", geometry)

    def create_download_subdir(self, query: str) -> str:
        base_dir = self.get_download_directory()
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in query)
        safe_name = safe_name[:50]
        download_dir = os.path.join(base_dir, safe_name)
        os.makedirs(download_dir, exist_ok=True)
        return download_dir

    # Internal helpers
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> None:
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                self._deep_merge(dict1[key], value)
            else:
                dict1[key] = value

    def _set_nested(self, data: Dict, keys: list, value: Any) -> None:
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value

    @staticmethod
    def _cast_value(value: str) -> Any:
        if not isinstance(value, str):
            return value
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        return value

# Global instance for easy access
_global_config: Optional[ConfigManager] = None

def get_config() -> ConfigManager:
    """
    Get the global ConfigManager instance.

    Returns:
        ConfigManager: The global configuration manager.
    """
    global _global_config
    if _global_config is None:
        _global_config = ConfigManager()
    return _global_config

def set_config_value(key: str, value: Any):
    """
    Set a configuration value globally.

    Args:
        key: Configuration key.
        value: Value to set.
    """
    config = get_config()
    config.set(key, value)

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value globally.

    Args:
        key: Configuration key.
        default: Default value if key is not found.

    Returns:
        The configuration value or default.
    """
    config = get_config()
    return config.get(key, default)
