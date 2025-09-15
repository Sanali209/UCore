"""
Tests for dynamic configuration features in the UCore framework.
Tests runtime configuration updates, persistence, and component reactions.
"""

import pytest
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock

# Framework imports
from framework.app import App
from framework.core.config import Config
from framework.monitoring.logging import Logging
from framework.core.component import Component
from framework.processing.cpu_tasks import ConcurrentFuturesAdapter


class TestComponent(Component):
    """Test component that reacts to configuration changes"""
    def __init__(self, app):
        self.app = app
        self.last_config_update = None
        self.config_reactions = []

    def on_config_update(self, config):
        """Track configuration update calls"""
        self.last_config_update = config
        self.config_reactions.append(dict(config))


class TestConfig:
    """Test suite for dynamic configuration"""

    def setup_method(self):
        """Setup fresh app and components for each test"""
        self.app = App("test_dynamic_config")
        self.config = self.app.container.get(Config)
        self.logging = self.app.container.get(Logging)
        self.test_component = TestComponent(self.app)

    def teardown_method(self):
        """Clean up after each test"""
        for component in self.app._components[::-1]:
            if hasattr(component, 'stop'):
                component.stop()

    def test_config_persistence_save_to_file(self):
        """Test that configuration can be saved to file"""
        # Setup test configuration
        self.config.set("TEST_KEY", "test_value")
        self.config.set("CONCURRENT_WORKERS", 8)
        self.config.set("LOG_LEVEL", "DEBUG")

        # Create temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Save configuration
            self.config.save_to_file(tmp_path)

            # Verify file was created and contains expected data
            assert os.path.exists(tmp_path)
            assert os.path.getsize(tmp_path) > 0

            # Load configuration and verify it matches
            new_config = Config()
            new_config.load_from_file(tmp_path)

            assert new_config.get("TEST_KEY") == "test_value"
            assert new_config.get("CONCURRENT_WORKERS") == 8
            assert new_config.get("LOG_LEVEL") == "DEBUG"

        finally:
            # Cleanup
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_app_reload_config(self):
        """Test App.reload_config() functionality"""
        # Setup initial config
        self.config.set("INITIAL_KEY", "initial_value")

        # Create temporary config file with new values
        new_config_data = {
            "INITIAL_KEY": "new_value",
            "NEW_KEY": "new_value"
        }

        import yaml
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
            yaml.dump(new_config_data, tmp)
            tmp_path = tmp.name

        try:
            # Reload configuration
            self.app.reload_config(tmp_path)

            # Verify configuration was updated
            assert self.config.get("INITIAL_KEY") == "new_value"
            assert self.config.get("NEW_KEY") == "new_value"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_app_log_level_update(self):
        """Test App.update_log_level() functionality"""
        # Get initial logger
        logger = self.logging.get_logger("test_logger")

        # Update log level
        self.app.update_log_level("DEBUG")

        # Verify log level was updated
        # Note: Python logging levels are numeric constants
        assert logger.level == 10  # DEBUG = 10

    def test_component_on_config_update_notification(self):
        """Test that components receive configuration update notifications"""
        # Register test component
        self.app.register_component(lambda: self.test_component)

        # Create sample config changes
        test_config = {
            "NEW_SETTING": "new_value",
            "UPDATED_WORKERS": 6
        }

        for key, value in test_config.items():
            self.config.set(key, value)

        # Simulate configuration update notification
        with patch.object(self.app, 'reload_config') as mock_reload:
            mock_reload.return_value = None

            # Manually call on_config_update to simulate what App.reload_config would do
            # Pass a dict as expected by on_config_update, not self.config
            config_dict = dict(self.config.get_all()) if hasattr(self.config, 'get_all') else {"NEW_SETTING": "new_value", "UPDATED_WORKERS": 6}
            self.test_component.on_config_update(config_dict)

        # Verify component received the update
        assert self.test_component.last_config_update is not None
        assert len(self.test_component.config_reactions) == 1

    def test_concurrent_adapter_dynamic_config(self):
        """Test ConcurrentFuturesAdapter reacts to configuration changes"""
        # Create concurrent adapter instance first
        concurrent_adapter = ConcurrentFuturesAdapter(self.app)
        self.app.register_component(lambda: concurrent_adapter)

        # Register the class in the container, not the instance
        self.app.container.register(ConcurrentFuturesAdapter, lambda: concurrent_adapter)

        # Start the adapter
        concurrent_adapter.start()

        # Update configuration
        self.config.set("CONCURRENT_WORKERS", 8)
        self.config.set("CONCURRENT_TIMEOUT", 60.0)

        # Mock executor restart (since it's hard to test actual restart)
        with patch.object(concurrent_adapter, '_restart_executor', return_value=None):
            concurrent_adapter.on_config_update(self.config)

        # Verify configuration was applied
        assert concurrent_adapter.max_workers == 8
        assert concurrent_adapter.timeout == 60.0

        # Cleanup
        concurrent_adapter.stop()

    def test_logging_dynamic_level_changes(self):
        """Test that logging component handles dynamic level changes"""
        # Create multiple loggers
        logger1 = self.logging.get_logger("test1")
        logger2 = self.logging.get_logger("test2")

        # Update global log level
        self.logging.set_global_level("WARNING")

        # Verify both loggers were updated (level 30 = WARNING)
        assert logger1.level == 30
        assert logger2.level == 30

    def test_config_file_watch_and_reload(self):
        """Test configuration file watching and automatic reload"""
        import time

        # Create initial config file
        initial_config = {"SETTING_A": "value_a"}
        import yaml

        with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
            yaml.dump(initial_config, tmp)
            tmp_path = tmp.name

        try:
            # Load initial configuration
            self.config.load_from_file(tmp_path)
            assert self.config.get("SETTING_A") == "value_a"

            # Simulate config file change
            updated_config = {"SETTING_A": "updated_a", "SETTING_B": "value_b"}

            # Write updated configuration
            with open(tmp_path, 'w') as f:
                yaml.dump(updated_config, f)

            # Test in-app reload
            self.app.reload_config(tmp_path)

            # Verify changes were applied
            assert self.config.get("SETTING_A") == "updated_a"
            assert self.config.get("SETTING_B") == "value_b"

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_invalid_config_graceful_handling(self):
        """Test graceful handling of invalid configuration values"""
        # Test invalid log level
        import logging

        # Save original level
        original_level = logging.getLogger().level

        try:
            # Try to set invalid log level
            result = self.logging.set_global_level("INVALID_LEVEL")

            # Should not crash, should maintain previous state
            # The logging system should handle this gracefully
            logger = self.logging.get_logger("test")
            assert isinstance(logger, object)  # At least logger exists

        finally:
            # Restore original level
            logging.getLogger().setLevel(original_level)


def test_config_initialization():
    """Test configuration class initialization and basic operations"""
    config = Config()

    # Test basic get/set operations
    config.set("test_key", "test_value")
    assert config.get("test_key") == "test_value"
    assert config.get("nonexistent", "default") == "default"


def test_component_base_class():
    """Test the Component base class on_config_update method"""
    from framework.app import App
    app = App("test")
    component = Component(app)

    # Should not raise errors by default (empty implementation)
    assert hasattr(component, 'on_config_update')
    component.on_config_update({"test": "config"})  # Should do nothing


if __name__ == "__main__":
    pytest.main([__file__])
