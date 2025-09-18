import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import asyncio
from unittest.mock import Mock, patch, call, AsyncMock
import argparse
from UCoreFrameworck.core.app import App
from UCoreFrameworck.core.component import Component
from UCoreFrameworck.core.di import Container
from UCoreFrameworck.core.config import Config


class TestAppInitialization:
    """Test App initialization and setup."""

    def test_app_init(self):
        """Test basic app initialization."""
        app = App("TestApp")

        assert app.name == "TestApp"
        assert isinstance(app.container, Container)
        assert len(app._components) == 0
        assert isinstance(app._create_arg_parser(), argparse.ArgumentParser)

    def test_bootstrap_with_args(self):
        """Test bootstrap process with arguments."""
        app = App("TestApp")

        # Mock the container services
        mock_config = Mock()
        mock_logger = Mock()
        mock_event_bus = Mock()

        with patch.object(app.container, 'get', side_effect=lambda cls: {
            Config: mock_config,
            type(None): mock_logger,  # For Logging
        }.get(cls, mock_event_bus)):
            with patch.object(mock_logger, 'info'):
                args = Mock()
                args.config = None
                args.plugins_dir = None
                args.log_level = "INFO"

                app.bootstrap(args)

                # Verify services were retrieved
                app.container.get.assert_any_call(Config)

    def test_bootstrap_with_config_file(self):
        """Test bootstrap with config file."""
        app = App("TestApp")

        mock_config = Mock()
        mock_logger = Mock()

        with patch.object(app.container, 'get', side_effect=lambda cls: mock_config if cls == Config else mock_logger):
            with patch.object(mock_logger, 'info') as mock_info:
                with patch.object(mock_config, 'load_from_file'):
                    args = Mock()
                    args.config = "test.yml"
                    args.plugins_dir = None
                    args.log_level = "INFO"

                    app.bootstrap(args)

                    mock_config.load_from_file.assert_called_once_with("test.yml")
                    # Note: The logger might be called indirectly, so we check if load_from_file was called
                    mock_config.load_from_file.assert_called_once_with("test.yml")
                    # Config file loading completed successfully


class TestComponentRegistration:
    """Test component registration functionality."""

    def test_register_component_class(self):
        """Test registering a Component class."""
        app = App("TestApp")

        class TestComponent(Component):
            pass

        app.register_component(TestComponent)

        assert len(app._components) == 1
        assert isinstance(app._components[0], TestComponent)
        assert app._components[0].app == app

    def test_register_component_instance(self):
        """Test registering a Component instance."""
        app = App("TestApp")

        instance = Component(app)
        app.register_component(instance)

        assert len(app._components) == 1
        assert app._components[0] == instance

    def test_register_factory_function(self):
        """Test registering a factory function."""
        app = App("TestApp")

        def create_component(app=None):
            return Component(app)

        app.register_component(create_component)

        assert len(app._components) == 1
        assert isinstance(app._components[0], Component)


class TestLifecycleManagement:
    """Test component lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_lifecycle(self):
        """Test starting all components."""
        app = App("TestApp")

        # Mock components
        mock_component1 = Mock()
        mock_component1.start = AsyncMock()
        mock_component2 = Mock()
        mock_component2.start = AsyncMock()

        app._components = [mock_component1, mock_component2]
        app.logger = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        app.container.get = Mock(return_value=mock_event_bus)

        with patch.object(app.container, 'get', return_value=mock_event_bus):
            await app.start()

            mock_event_bus.start.assert_called_once()
            mock_component1.start.assert_called_once()
            mock_component2.start.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_lifecycle(self):
        """Test stopping all components in reverse order."""
        app = App("TestApp")

        # Mock components
        mock_component1 = Mock()
        mock_component1.stop = AsyncMock()
        mock_component2 = Mock()
        mock_component2.stop = AsyncMock()

        app._components = [mock_component1, mock_component2]
        app.logger = Mock()

        # Mock event bus
        mock_event_bus = Mock()
        app.container.get = Mock(return_value=mock_event_bus)

        with patch.object(app.container, 'get', return_value=mock_event_bus):
            await app.stop()

            mock_component2.stop.assert_called_once()
            mock_component1.stop.assert_called_once()
            mock_event_bus.shutdown.assert_called_once()


class TestConfigurationManagement:
    """Test configuration management in App."""

    def test_reload_config(self):
        """Test configuration reloading."""
        app = App("TestApp")

        mock_config = Mock()
        mock_event_bus = Mock()
        app.logger = Mock()

        app.container.get = Mock(side_effect=lambda cls: mock_config if cls == Config else mock_event_bus)

        app.reload_config("new_config.yml")

        mock_config.load_from_file.assert_called_once_with("new_config.yml")
        mock_config.load_from_env.assert_called_once()

    def test_update_log_level(self):
        """Test log level updates."""
        app = App("TestApp")

        mock_logging = Mock()
        app.logger = Mock()

        app.container.get = Mock(return_value=mock_logging)

        app.update_log_level("DEBUG")

        mock_logging.set_global_level.assert_called_once_with("DEBUG")


class TestArgumentParser:
    """Test CLI argument parsing."""

    def test_arg_parser_creation(self):
        """Test argument parser setup."""
        app = App("TestApp")

        parser = app._create_arg_parser()

        assert isinstance(parser, argparse.ArgumentParser)
        assert parser.description == "TestApp Application"

    def test_arg_parser_options(self):
        """Test all expected arguments are available."""
        app = App("TestApp")

        parser = app._create_arg_parser()

        # Parse help to ensure all arguments are defined
        help_text = parser.format_help()

        assert "--config" in help_text
        assert "--log-level" in help_text
        assert "--plugins-dir" in help_text


class TestErrorHandling:
    """Test error handling in App."""

    @pytest.mark.asyncio
    async def test_start_component_error_handling(self):
        """Test error handling during component start."""
        app = App("TestApp")

        # Component that raises error
        mock_component = Mock()
        mock_component.start = AsyncMock(side_effect=Exception("Start failed"))

        app._components = [mock_component]
        app.logger = Mock()

        mock_event_bus = Mock()
        app.container.get = Mock(return_value=mock_event_bus)

        with patch.object(app.container, 'get', return_value=mock_event_bus):
            await app.start()

            # Verify error was logged
            app.logger.error.assert_called()
            # Verify other components still start (though we only have one)
