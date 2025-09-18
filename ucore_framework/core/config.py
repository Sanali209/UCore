# framework/config.py
import os
import yaml
from typing import Any, Dict, Optional

class Config:
    """
    A configuration class that loads from YAML files and environment variables.
    - Supports nested keys in environment variables (e.g., UCORE_LOGGING_LEVEL).
    - Automatically casts environment variable values to bool, int, or float.
    """
    def __init__(self, env_prefix: str = "UCORE", env_separator: str = "_"):
        self.data: Dict[str, Any] = {}
        self.env_prefix = env_prefix
        self.env_separator = env_separator

    def load_from_file(self, filepath: str) -> None:
        """
        Loads configuration from a YAML file.
        Merges dictionaries recursively instead of shallow update.
        """
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and isinstance(d.get(k), dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v

        try:
            with open(filepath, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    deep_update(self.data, file_config)
        except FileNotFoundError:
            # This is not an error, the file might be optional.
            pass
        except yaml.YAMLError as e:
            raise RuntimeError(f"Error parsing YAML file {filepath}: {e}") from e
        except Exception as e:
            raise RuntimeError(f"Error loading configuration from {filepath}: {e}") from e

    def load_from_env(self) -> None:
        """
        Loads configuration from environment variables, overriding existing values.
        Nested keys can be specified using a separator (e.g., UCORE_DATABASE_HOST).
        """
        prefix = f"{self.env_prefix}{self.env_separator}"
        from UCoreFrameworck.resource.secrets import EnvVarSecretsManager
        secrets_manager = EnvVarSecretsManager()
        for key, value in os.environ.items():
            if key.startswith(prefix):
                # Remove prefix and split into nested keys
                keys = key[len(prefix):].lower().split(self.env_separator)
                # Use SecretsManager for secret-like keys
                if any(s in key.lower() for s in ["secret", "password", "key"]):
                    secret_value = secrets_manager.get_secret(key)
                    self._set_nested(self.data, keys, self._cast_value(secret_value) if secret_value is not None else self._cast_value(value))
                else:
                    self._set_nested(self.data, keys, self._cast_value(value))

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

    def load_from_dict(self, config_dict: dict) -> None:
        """
        Loads configuration from a provided dictionary, merging recursively.
        """
        def deep_update(d, u):
            for k, v in u.items():
                if isinstance(v, dict) and isinstance(d.get(k), dict):
                    deep_update(d[k], v)
                else:
                    d[k] = v
        deep_update(self.data, config_dict)

    def save_to_file(self, filepath: str) -> None:
        """
        Saves the current configuration to a YAML file.
        """
        try:
            with open(filepath, 'w') as f:
                yaml.dump(self.data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            raise RuntimeError(f"Error saving configuration to {filepath}: {e}") from e

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
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value
