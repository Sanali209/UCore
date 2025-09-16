# framework/settings.py
"""
UCore Settings Management Module - YAML Only

Simple settings persistence with YAML files:
- Initial configuration loading from YAML
- Runtime settings changes with callbacks
- Tracking of download directory and app-specific settings
- Easy integration with UCore framework
"""

import os
import yaml
from typing import Any, Dict, Callable, Optional
from pathlib import Path
import threading


class SettingsManager:
    """YAML-based settings management for UCore applications"""

    def __init__(self, config_file: str = "app_config.yml"):
        self.config_file = config_file
        self._settings = {}
        self._callbacks = {}
        self._lock = threading.RLock()

        # Load initial settings
        self._load_yaml_config()
        self._load_defaults_if_needed()

    def _load_yaml_config(self):
        """Load settings from YAML file if it exists"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_settings = yaml.safe_load(f)
                    if loaded_settings and isinstance(loaded_settings, dict):
                        self._settings.update(loaded_settings)
                        print(f"✅ Loaded settings from {self.config_file}")
                    else:
                        print(f"⚠️ Empty or invalid YAML in {self.config_file}")
        except Exception as e:
            print(f"⚠️ Failed to load YAML config from {self.config_file}: {e}")

    def _load_defaults_if_needed(self):
        """Load default settings if file doesn't exist or key is missing"""
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

        # Set defaults only if not already set
        for key, value in defaults.items():
            if key not in self._settings:
                self._settings[key] = value

        # Save defaults to create the config file
        if not os.path.exists(self.config_file):
            self.save()
            print(f"✅ Created default settings file: {self.config_file}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value"""
        with self._lock:
            return self._settings.get(key, default)

    def set(self, key: str, value, save_immediately: bool = True):
        """Set a setting value and optionally save to YAML"""
        with self._lock:
            old_value = self._settings.get(key)

            # Check if value changed
            if old_value != value:
                self._settings[key] = value

                # Save if requested (support both save_immediately and legacy 's' kwarg)
                if save_immediately:
                    self.save()

                # Notify listeners
                if key in self._callbacks:
                    for callback in self._callbacks[key]:
                        try:
                            callback(key, value, old_value)
                        except Exception as e:
                            print(f"⚠️ Settings callback error for {key}: {e}")

                print(f"✅ Setting updated: {key} = {value}")

    def subscribe(self, key: str, callback: Callable) -> bool:
        """Subscribe to setting changes"""
        with self._lock:
            if key not in self._callbacks:
                self._callbacks[key] = []
            self._callbacks[key].append(callback)
            return True

    def unsubscribe(self, key: str, callback: Callable) -> bool:
        """Unsubscribe from setting changes"""
        with self._lock:
            if key in self._callbacks and callback in self._callbacks[key]:
                self._callbacks[key].remove(callback)
                return True
            return False

    def save(self) -> bool:
        """Save current settings to YAML file"""
        try:
            with self._lock:
                with open(self.config_file, 'w', encoding='utf-8') as f:
                    yaml.safe_dump(self._settings, f, default_flow_style=False,
                                 encoding='utf-8')

                print(f"✅ Settings saved to {self.config_file}")
                return True

        except Exception as e:
            print(f"❌ Failed to save settings: {e}")
            return False

    def reload(self) -> bool:
        """Reload settings from YAML file"""
        try:
            with self._lock:
                self._load_yaml_config()
            print("✅ Settings reloaded from YAML")
            return True
        except Exception as e:
            print(f"❌ Failed to reload settings: {e}")
            return False

    def get_all(self) -> Dict:
        """Get all settings"""
        with self._lock:
            return self._settings.copy()

    # Specialized methods for DuckDuckGo app
    def get_download_directory(self) -> str:
        """Get the current download directory"""
        return self.get("download_directory")

    def set_download_directory(self, directory: str):
        """Set the download directory and add to recent list"""
        if os.path.isdir(directory):
            self.set("download_directory", directory)

            # Add to recent directories
            recent = self.get("recent_directories", [])
            if directory in recent:
                recent.remove(directory)
            recent.insert(0, directory)
            recent = recent[:10]  # Keep max 10
            self.set("recent_directories", recent)

            return True
        return False

    def get_recent_directories(self) -> list:
        """Get recently used directories"""
        return self.get("recent_directories", [])

    def get_window_geometry(self) -> Dict:
        """Get window geometry settings"""
        return self.get("window_geometry", {"width": 1200, "height": 800, "x": 100, "y": 100})

    def set_window_geometry(self, geometry: Dict):
        """Save window geometry"""
        self.set("window_geometry", geometry)

    def create_download_subdir(self, query: str) -> str:
        """Create and return a subdirectory for download"""
        base_dir = self.get_download_directory()

        # Sanitize query for directory name
        safe_name = "".join(c if c.isalnum() or c in " -_" else "_" for c in query)
        safe_name = safe_name[:50]  # Limit length

        download_dir = os.path.join(base_dir, safe_name)

        # Create directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)

        return download_dir
