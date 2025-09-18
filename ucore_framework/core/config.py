"""
Unified Configuration Management for UCore Framework

This module provides a centralized configuration management system that can merge
settings from multiple YAML files and environment variables.
"""

import os
import yaml
from typing import Any, Dict, Optional, List, Union
from pathlib import Path
from loguru import logger


class Config:
    """
    Unified configuration class that loads from multiple YAML files and environment variables.
    
    Features:
    - Multiple YAML configuration files with deep merging
    - Environment variable overrides with nested key support
    - Type casting for environment variables
    - Secrets manager integration
    - Global instance management
    """
    def __init__(self, env_prefix: str = "UCORE", env_separator: str = "_", base_dir: Optional[Union[str, Path]] = None):
        self.data: Dict[str, Any] = {}
        self.env_prefix = env_prefix
        self.env_separator = env_separator
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()

    def load_from_files(self, filepaths: List[str]) -> None:
        """
        Loads configuration from multiple YAML files in order.
        Later files override earlier ones with deep merging.
        """
        for filepath in filepaths:
            self.load_from_file(filepath)
    
    def load_from_file(self, filepath: str) -> None:
        """
        Loads configuration from a single YAML file.
        Merges dictionaries recursively instead of shallow update.
        """
        config_path = self.base_dir / filepath if not Path(filepath).is_absolute() else Path(filepath)
        
        try:
            if config_path.exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = yaml.safe_load(f) or {}
                self._deep_merge(self.data, file_config)
                logger.info(f"Loaded configuration from {config_path}")
            else:
                logger.debug(f"Configuration file {config_path} not found, skipping")
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file {config_path}: {e}")
            raise RuntimeError(f"Error parsing YAML file {config_path}: {e}") from e
        except Exception as e:
            logger.error(f"Error loading configuration from {config_path}: {e}")
            raise RuntimeError(f"Error loading configuration from {config_path}: {e}") from e

    def load_from_env(self) -> None:
        """
        Loads configuration from environment variables, overriding existing values.
        Nested keys can be specified using a separator (e.g., UCORE_DATABASE_HOST).
        """
        prefix = f"{self.env_prefix}{self.env_separator}"
        
        try:
            from ucore_framework.resource.secrets import EnvVarSecretsManager
            secrets_manager = EnvVarSecretsManager()
        except ImportError:
            secrets_manager = None
            logger.debug("SecretsManager not available, using direct environment access")
        
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and split into nested keys
                config_key = key[len(prefix):].lower()
                keys = config_key.split(self.env_separator)
                
                # Use SecretsManager for secret-like keys if available
                if secrets_manager and any(s in key.lower() for s in ["secret", "password", "key"]):
                    secret_value = secrets_manager.get_secret(key)
                    parsed_value = self._cast_value(secret_value) if secret_value is not None else self._cast_value(value)
                else:
                    parsed_value = self._cast_value(value)
                
                self._set_nested(self.data, keys, parsed_value)

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """
        Retrieves a configuration value using dot notation for nested keys.
        """
        keys = key.split('.')
        value = self.data
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any) -> None:
        """
        Sets a configuration value using dot notation for nested keys.
        If key is empty, replaces the entire config data.
        """
        if not key:
            self.data = value
        else:
            keys = key.split('.')
            self._set_nested(self.data, keys, value)

    def load_unified_config(self, 
                          config_files: Optional[List[str]] = None,
                          include_env: bool = True) -> Dict[str, Any]:
        """
        Load and merge configuration from all sources.
        
        Args:
            config_files: List of config files to load. Defaults to standard files.
            include_env: Whether to include environment variable overrides
            
        Returns:
            Unified configuration dictionary
        """
        if config_files is None:
            config_files = [
                'app_config.yml',
                'config.yml', 
                'custom_settings.yml'
            ]
        
        # Load from files
        self.load_from_files(config_files)
        
        # Override with environment variables if requested
        if include_env:
            self.load_from_env()
        
        logger.info(f"Unified configuration loaded with {len(self.data)} top-level keys")
        return self.data

    def load_from_dict(self, config_dict: dict) -> None:
        """
        Loads configuration from a provided dictionary, merging recursively.
        """
        self._deep_merge(self.data, config_dict)

    def save_to_file(self, filepath: str) -> None:
        """
        Saves the current configuration to a YAML file.
        """
        try:
            with open(filepath, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise RuntimeError(f"Error saving configuration to {filepath}: {e}") from e

    def to_dict(self) -> Dict[str, Any]:
        """Get the complete configuration as a dictionary."""
        return self.data.copy()
    
    def _deep_merge(self, dict1: Dict[str, Any], dict2: Dict[str, Any]) -> None:
        """
        Deep merge dict2 into dict1, with dict2 taking precedence.
        """
        for key, value in dict2.items():
            if key in dict1 and isinstance(dict1[key], dict) and isinstance(value, dict):
                self._deep_merge(dict1[key], value)
            else:
                dict1[key] = value

    def _set_nested(self, data: Dict, keys: list, value: Any) -> None:
        """
        Helper to set a value in a nested dictionary.
        """
        for key in keys[:-1]:
            data = data.setdefault(key, {})
        data[keys[-1]] = value

    @staticmethod
    def _cast_value(value: str) -> Any:
        """
        Automatically casts a string value to a more specific type if possible.
        """
        if not isinstance(value, str):
            return value
            
        # Handle boolean values
        if value.lower() in ('true', 'yes', '1', 'on'):
            return True
        elif value.lower() in ('false', 'no', '0', 'off'):
            return False
        
        # Try to parse as number
        try:
            if '.' in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            pass
        
        return value


# Global instance for easy access
_global_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global Config instance."""
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config


def load_unified_config(config_files: Optional[List[str]] = None, 
                       include_env: bool = True) -> Dict[str, Any]:
    """
    Convenience function to load unified configuration.
    
    Args:
        config_files: List of config files to load
        include_env: Whether to include environment variables
        
    Returns:
        Unified configuration dictionary
    """
    config = get_config()
    return config.load_unified_config(config_files, include_env)


def get_config_value(key_path: str, default: Any = None) -> Any:
    """
    Convenience function to get a configuration value.
    
    Args:
        key_path: Dot-separated path to the configuration key
        default: Default value if key is not found
        
    Returns:
        Configuration value or default
    """
    config = get_config()
    return config.get(key_path, default)


def set_config_value(key_path: str, value: Any) -> None:
    """
    Convenience function to set a configuration value.
    
    Args:
        key_path: Dot-separated path to the configuration key
        value: Value to set
    """
    config = get_config()
    config.set(key_path, value)
