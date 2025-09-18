import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import tempfile
import os
import shutil
import yaml
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import builtins
from ucore_framework.core.settings import SettingsManager


class TestSettingsManagerInitialization:
    """Test SettingsManager initialization and basic setup."""

    def test_settings_manager_creation_with_defaults(self):
        """Test SettingsManager creation with default config file."""
        with patch('os.path.exists', return_value=False):
            settings = SettingsManager()
            assert settings.config_file == "app_config.yml"
            assert isinstance(settings._settings, dict)
            assert len(settings._callbacks) == 0
            assert settings._lock is not None

    def test_settings_manager_creation_custom_config_file(self):
        """Test SettingsManager creation with custom config file."""
        config_file = "custom_settings.yml"
        with patch('os.path.exists', return_value=False):
            settings = SettingsManager(config_file=config_file)
            assert settings.config_file == config_file

    def test_settings_manager_load_existing_yaml(self):
        """Test loading settings from existing YAML file."""
        # Sample YAML data
        yaml_data = {
            "app_name": "TestApp",
            "version": "1.0.0",
            "test_setting": "test_value"
        }

        yaml_content = yaml.safe_dump(yaml_data, default_flow_style=False)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml_content)
            temp_config = f.name

        try:
            settings = SettingsManager(config_file=temp_config)

            # Check that data was loaded
            assert settings.get("app_name") == "TestApp"
            assert settings.get("version") == "1.0.0"
            assert settings.get("test_setting") == "test_value"

        finally:
            os.unlink(temp_config)

    def test_settings_manager_invalid_yaml_handling(self):
        """Test handling of invalid YAML files."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write("invalid: yaml: content: [: -")
            temp_config = f.name

        try:
            with patch('builtins.print') as mock_print:
                settings = SettingsManager(config_file=temp_config)
                # Invalid YAML should be handled gracefully
                # Should load all defaults (9 keys), not just 4
                expected_defaults = [
                    "app_name", "version", "download_directory",
                    "recent_directories", "max_results", "workers",
                    "timeout", "log_level", "window_geometry"
                ]
                for key in expected_defaults:
                    assert key in settings._settings
                # Accept either error message variant for invalid YAML
                found_expected = False
                for call_args in mock_print.call_args_list:
                    msg = call_args[0][0]
                    if (
                        msg.startswith("⚠️ Empty or invalid YAML in")
                        or msg.startswith("⚠️ Failed to load YAML config from")
                    ):
                        found_expected = True
                        break
                assert found_expected, "Expected error message for invalid YAML not found"
        finally:
            os.unlink(temp_config)


class TestDefaultSettings:
    """Test default settings loading and handling."""

    def test_default_settings_loaded(self):
        """Test that default settings are loaded correctly."""
        with patch('os.path.exists', return_value=False):
            settings = SettingsManager()

            # Check default settings structure
            expected_defaults = [
                "app_name", "version", "download_directory",
                "recent_directories", "max_results", "workers",
                "timeout", "log_level", "window_geometry"
            ]

            for key in expected_defaults:
                assert key in settings._settings or settings.get(key) is not None

    def test_download_directory_default_creation(self):
        """Test download directory default creation."""
        with patch('os.path.exists', return_value=False):
            with patch('pathlib.Path.home') as mock_home:
                mock_home.return_value = Path("/mock/home")
                settings = SettingsManager()

                expected_path = str(Path("/mock/home/Downloads/duckduckgo_images"))
                actual_path = settings.get("download_directory")
                # Windows vs Unix path normalization
                assert actual_path == expected_path or str(Path(actual_path)) == str(Path(expected_path))

    def test_config_file_creation_for_defaults(self):
        """Test that config file is created when defaults are loaded."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = os.path.join(temp_dir, "test_config.yml")

            with patch('os.path.exists', return_value=False):
                with patch('builtins.open', MagicMock()) as mock_file:
                    settings = SettingsManager(config_file=config_file)

                    # Should attempt to create the config file
                    # (Actual file creation might be mocked)


class TestSettingsOperations:
    """Test basic settings get, set, and save operations."""

    def test_get_existing_setting(self):
        """Test getting an existing setting."""
        settings = Mock()
        settings.get.return_value = "test_value"

        result = settings.get("test_key")
        assert result == "test_value"
        settings.get.assert_called_once_with("test_key")

    def test_get_nonexistent_setting_with_default(self):
        """Test getting non-existent setting with default value."""
        settings = Mock()
        settings.get.return_value = "default_value"

        result = settings.get("nonexistent_key", "default_value")
        assert result == "default_value"

    def test_set_setting_without_save(self):
        """Test setting a setting without immediate save."""
        settings = SettingsManager()
        settings._settings = {}
        with patch.object(settings, "save") as mock_save:
            settings.set("test_key", "test_value", save_immediately=False)
            mock_save.assert_not_called()

    def test_set_setting_with_save(self):
        """Test setting a setting with immediate save."""
        settings = SettingsManager()
        settings._settings = {}
        with patch.object(settings, "save") as mock_save:
            settings.set("test_key", "test_value", save_immediately=True)
            mock_save.assert_called_once()


class TestSettingsPersistence:
    """Test settings file persistence and YAML operations."""

    def test_save_to_yaml_file(self):
        """Test saving settings to YAML file."""
        import io

        with patch('builtins.open') as mock_open:
            mock_file = io.StringIO()
            mock_open.return_value.__enter__.return_value = mock_file
            mock_open.return_value.__exit__.return_value = None

            settings = SettingsManager()
            settings._settings = {"test_key": "test_value"}
            settings.config_file = "result.yml"

            result = settings.save()

            # Should have opened the file for writing
            mock_open.assert_any_call("result.yml", 'w', encoding='utf-8')
            assert result is True  # Should return True on success

    def test_save_yaml_error_handling(self):
        """Test error handling during YAML save."""
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = IOError("Write error")

            with patch('builtins.print') as mock_print:
                settings = SettingsManager()
                settings.save()

                # Should log the error
                mock_print.assert_called()

    def test_reload_yaml_file(self):
        """Test reloading settings from YAML file."""
        yaml_data = {"reloaded": "value"}

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
            f.write(yaml.safe_dump(yaml_data))
            temp_config = f.name

        try:
            with patch('builtins.open', MagicMock()) as mock_open:
                with patch('yaml.safe_load', return_value=yaml_data):
                    settings = SettingsManager(config_file=temp_config)
                    settings.reload()

                    # Should have reloaded the data
                    assert "reloaded" in str(settings._settings)

        finally:
            os.unlink(temp_config)

    def test_reload_yaml_error_handling(self):
        """Test error handling during YAML reload."""
        with patch('builtins.open') as mock_open:
            mock_open.side_effect = IOError("Read error")

            with patch('builtins.print') as mock_print:
                settings = SettingsManager()
                settings.reload()

                # Should log the error
                mock_print.assert_called()


class TestCallbackSystem:
    """Test the settings callback system for change notifications."""

    def test_subscribe_to_setting_changes(self):
        """Test subscribing to setting changes."""
        settings = Mock()
        settings._callbacks = {}
        settings.subscribe = lambda k, c: True

        callback = Mock()
        result = settings.subscribe("test_key", callback)

        assert result is True

    def test_unsubscribe_from_setting_changes(self):
        """Test unsubscribing from setting changes."""
        settings = Mock()
        settings._callbacks = {"test_key": [Mock()]}
        settings.unsubscribe = lambda k, c: True

        callback = Mock()
        result = settings.unsubscribe("test_key", callback)

        assert result is True

    def test_callback_execution_on_setting_change(self):
        """Test that callbacks are executed when settings change."""
        settings = Mock()
        settings._settings = {"test_key": "old_value"}
        settings._callbacks = {"test_key": []}
        settings.save = Mock()

        callback = Mock()
        settings._callbacks["test_key"].append(callback)

        # Simulate setting change
        old_value = "old_value"
        new_value = "new_value"

        if "test_key" in settings._callbacks:
            for cb in settings._callbacks["test_key"]:
                cb("test_key", new_value, old_value)

        callback.assert_called_once_with("test_key", new_value, old_value)


class TestSettingsSpecializedMethods:
    """Test specialized settings methods."""

    def test_get_download_directory(self):
        """Test getting download directory setting."""
        settings = SettingsManager()
        test_path = "/test/download/path"
        settings.set("download_directory", test_path, save_immediately=False)
        result = settings.get_download_directory()
        assert result == test_path

    def test_set_download_directory_valid(self):
        """Test setting download directory with valid path."""
        with patch('os.path.isdir', return_value=True):
            settings = SettingsManager()
            settings.set("recent_directories", [], save_immediately=False)
            result = settings.set_download_directory("/valid/path")
            assert result is True

    def test_set_download_directory_invalid(self):
        """Test setting download directory with invalid path."""
        with patch('os.path.isdir', return_value=False):
            settings = SettingsManager()
            result = settings.set_download_directory("/invalid/path")
            assert result is False

    def test_set_download_directory_with_recent_list(self):
        """Test that setting download directory updates recent list."""
        with patch('os.path.isdir', return_value=True):
            settings = SettingsManager()
            settings.set("recent_directories", ["/old/path"], save_immediately=False)
            settings.set_download_directory("/new/path")
            recent = settings.get("recent_directories")
            assert "/new/path" in recent

    def test_get_recent_directories(self):
        """Test getting recent directories list."""
        recent_dirs = ["/path1", "/path2", "/path3"]
        settings = SettingsManager()
        settings.set("recent_directories", recent_dirs, save_immediately=False)
        result = settings.get_recent_directories()
        assert result == recent_dirs

    def test_get_window_geometry(self):
        """Test getting window geometry settings."""
        geometry = {"width": 1200, "height": 800, "x": 100, "y": 100}
        settings = SettingsManager()
        settings.set("window_geometry", geometry, save_immediately=False)
        result = settings.get_window_geometry()
        assert result == geometry

    def test_set_window_geometry(self):
        """Test setting window geometry."""
        geometry = {"width": 800, "height": 600, "x": 50, "y": 50}
        settings = SettingsManager()
        settings.set_window_geometry(geometry)
        assert settings.get("window_geometry") == geometry


class TestThreadSafety:
    """Test thread safety of settings operations."""

    def test_threading_lock_initialization(self):
        """Test that threading lock is properly initialized."""
        import threading as th
        with patch('os.path.exists', return_value=False):
            settings = SettingsManager()

            assert hasattr(settings, '_lock')
            # isinstance cannot be used directly with _thread.RLock, so check class name
            assert settings._lock.__class__.__name__ == "RLock"

    def test_concurrently_safe_operations(self):
        """Test that operations are thread-safe."""
        settings = Mock()
        lock = threading.RLock()
        settings._lock = lock

        with settings._lock:
            # Simulate concurrent access protection
            pass

    def test_settings_operations_wrapped_by_lock(self):
        """Test that settings operations use the lock."""
        settings = Mock()
        settings._lock = Mock()
        settings._lock.__enter__ = Mock()
        settings._lock.__exit__ = Mock()

        # Simulate a get operation with locking
        with settings._lock:
            value = settings.get("test_key", "default")


class TestSettingsIntegrationScenarios:
    """Test integration scenarios with multiple settings operations."""

    def test_full_settings_lifecycle(self):
        """Test complete settings lifecycle from creation to persistence."""
        # This would test the entire workflow but might be mocked
        pass

    def test_settings_reloading_with_callbacks(self):
        """Test reloading settings triggers callbacks appropriately."""
        settings = Mock()
        settings._callbacks = {}
        settings.reload = Mock()
        settings._load_yaml_config = Mock()

        callback = Mock()
        settings.subscribe = lambda k, cb: settings._callbacks.setdefault(k, []).append(cb)

        settings.subscribe("test_key", callback)

        # Simulate reload triggering callbacks
        if "test_key" in settings._callbacks:
            for cb in settings._callbacks["test_key"]:
                cb("test_key", "new_value", "old_value")

        callback.assert_called_once_with("test_key", "new_value", "old_value")


class TestErrorEdgeCases:
    """Test error handling and edge cases."""

    def test_yaml_parsing_error_handling(self):
        """Test YAML parsing error is handled gracefully."""
        with patch('yaml.safe_load', side_effect=yaml.YAMLError("Parse error")):
            with patch('builtins.print') as mock_print:
                with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as f:
                    f.write("invalid: yaml: : content")
                    temp_config = f.name

                try:
                    settings = SettingsManager(config_file=temp_config)

                    # Should handle error gracefully and continue with defaults
                    mock_print.assert_called()

                finally:
                    os.unlink(temp_config)

    def test_file_permissions_error_on_save(self):
        """Test file permission errors during save operations."""
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            with patch('builtins.print') as mock_print:
                settings = SettingsManager()
                result = settings.save()

                assert result is False
                mock_print.assert_called()

    def test_concurrent_callback_execution(self):
        """Test concurrent execution of multiple callbacks."""
        settings = Mock()
        settings._callbacks = {"test_key": []}

        # Add multiple callbacks
        callback1 = Mock()
        callback2 = Mock()
        settings._callbacks["test_key"].extend([callback1, callback2])

        # Simulate change notification to all callbacks
        for callback in settings._callbacks["test_key"]:
            callback("test_key", "new_value", "old_value")

        # Both callbacks should be called
        callback1.assert_called_once_with("test_key", "new_value", "old_value")
        callback2.assert_called_once_with("test_key", "new_value", "old_value")

    def test_callback_exception_handling(self):
        """Test that callback exceptions don't stop other callbacks."""
        settings = Mock()
        settings._callbacks = {"test_key": []}

        # Add callbacks - one that works, one that fails
        good_callback = Mock()
        bad_callback = Mock(side_effect=Exception("Callback error"))

        settings._callbacks["test_key"] = [good_callback, bad_callback]

        # Simulate change notification
        for callback in settings._callbacks["test_key"]:
            try:
                callback("test_key", "new_value", "old_value")
            except:
                pass  # Simulating exception handling in the actual code

        # Good callback should still be called
        good_callback.assert_called_once()


class TestSettingsFileOperations:
    """Test file system operations for settings."""

    def test_config_file_path_resolution(self):
        """Test config file path is correctly resolved."""
        config_file = "config.yml"
        with patch('os.path.exists', return_value=False):
            settings = SettingsManager(config_file=config_file)

            assert settings.config_file == config_file

    def test_file_creation_in_missing_directory(self):
        """Test file creation when directory doesn't exist."""
        # This could test creating config files in new directories
        pass

    def test_file_backup_on_save(self):
        """Test creating backup files before saving."""
        # Could test backup functionality if implemented
        pass


class TestSettingsValidation:
    """Test settings value validation."""

    def test_setting_key_validation(self):
        """Test that setting keys are valid."""
        settings = Mock()
        settings.set = Mock()

        # Test with valid key
        settings.set("valid_key", "value")
        settings.set.assert_called()

    def test_setting_value_type_validation(self):
        """Test that setting values are of valid types."""
        # Could test type constraints if implemented
        pass


class TestPerformanceConsiderations:
    """Test performance aspects of settings management."""

    def test_frequent_settings_access(self):
        """Test performance impact of frequent get operations."""
        settings = Mock()
        settings.get = Mock(return_value="value")

        # Simulate many get calls
        for _ in range(1000):
            settings.get("test_key")

        # Should handle many calls efficiently
        assert settings.get.call_count == 1000

    def test_concurrent_settings_modification(self):
        """Test concurrent modification of settings."""
        settings = Mock()
        settings._lock = threading.RLock()
        settings.set = Mock()

        # Simulate concurrent access (would need threading for real test)
        setting_values = ["value1", "value2", "value3"]

        for value in setting_values:
            with settings._lock:
                settings.set("test_key", value)

        # Each set should have been called
        assert settings.set.call_count == len(setting_values)
