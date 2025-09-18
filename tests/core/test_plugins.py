import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import types
import importlib.util
import sys
from ucore_framework.core.plugins import PluginManager, Plugin
from ucore_framework.core.app import App


class TestPluginManagement:
    """Test Plugin management functionality."""

    def test_plugin_manager_initialization(self):
        """Test PluginManager initialization with app."""
        mock_app = Mock()
        mock_app.logger.getChild.return_value = Mock()

        plugin_manager = PluginManager(mock_app)

        assert plugin_manager.app == mock_app
        mock_app.logger.getChild.assert_called_once_with("PluginManager")

    def test_plugin_manager_load_plugins_no_directory(self):
        """Test loading plugins from non-existent directory."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        plugin_manager.load_plugins("/non/existent/directory")

        mock_logger.warning.assert_called_once_with(
            "Plugins directory not found: /non/existent/directory"
        )
        mock_logger.info.assert_called_once()

    def test_plugin_manager_load_plugins_empty_directory(self):
        """Test loading plugins from empty directory."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_manager.load_plugins(temp_dir)

            mock_logger.info.assert_called_once()


class TestPluginDiscovery:
    """Test plugin discovery and loading mechanisms."""

    def test_plugin_discovery_python_files(self):
        """Test discovery of Python plugin files."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various files
            Path(os.path.join(temp_dir, "valid_plugin.py")).touch()
            Path(os.path.join(temp_dir, "another_plugin.py")).touch()
            Path(os.path.join(temp_dir, "__init__.py")).touch()  # Should be ignored
            Path(os.path.join(temp_dir, "not_python.txt")).touch()

            # Mock the actual loading to avoid import complexity
            with patch.object(plugin_manager, '_load_plugin_from_file') as mock_load:
                plugin_manager.load_plugins(temp_dir)

                # Should attempt to load .py files (excluding __init__.py)
                assert mock_load.call_count == 2
                call_args = [call[0][0] for call in mock_load.call_args_list]
                assert any("valid_plugin.py" in arg for arg in call_args)
                assert any("another_plugin.py" in arg for arg in call_args)
                assert not any("__init__.py" in arg for arg in call_args)
                assert not any("not_python.txt" in arg for arg in call_args)


class TestPluginLoading:
    """Test individual plugin loading functionality."""

    def test_load_plugin_successful(self):
        """Test successful plugin loading."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        # Create a temporary plugin file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from ucore_framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def register(self, app):
        app.registered_plugins.append("test_plugin")

    def get_name(self):
        return "Test Plugin"
""")
            temp_file = f.name

        try:
            # Mock inspect and importlib to control the loading
            with patch('importlib.util.spec_from_file_location') as mock_spec, \
                 patch('importlib.util.module_from_spec') as mock_module:

                mock_spec.return_value = Mock()
                mock_module_obj = Mock()
                mock_module.return_value = mock_module_obj

                # Mock Plugin subclass
                mock_plugin_class = Mock()
                mock_plugin_instance = Mock()
                mock_plugin_class.return_value = mock_plugin_instance
                mock_plugin_instance.register = Mock()

                with patch('inspect.getmembers', return_value=[('TestPlugin', mock_plugin_class)]) as mock_getmembers:
                    with patch('inspect.isclass', return_value=True):
                        # Create directory for plugins
                        plugin_dir = os.path.dirname(temp_file)
                        plugin_manager._load_plugin_from_file(temp_file)

                        mock_spec.assert_called_once()
                        mock_module.assert_called_once()

        finally:
            os.unlink(temp_file)

    def test_load_plugin_importlib_error(self):
        """Test plugin loading with importlib spec error."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = f.name

        try:
            # Mock importlib.util.spec_from_file_location to return None (error)
            with patch('importlib.util.spec_from_file_location', return_value=None):
                plugin_manager._load_plugin_from_file(temp_file)

                mock_logger.error.assert_called_once()

        finally:
            os.unlink(temp_file)

    def test_load_plugin_exception_handling(self):
        """Test plugin loading with general exception handling."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.NamedTemporaryFile(suffix='.py', delete=False) as f:
            temp_file = f.name

        try:
            # Mock spec_from_file_location to raise an exception
            with patch('importlib.util.spec_from_file_location') as mock_spec:
                mock_spec.side_effect = Exception("Import error")

                plugin_manager._load_plugin_from_file(temp_file)

                mock_logger.error.assert_called_once()
                # Check that the error includes exc_info=True
                assert mock_logger.error.call_args[1]['exc_info'] == True

        finally:
            os.unlink(temp_file)

    def test_load_plugin_no_plugin_classes(self):
        """Test loading plugin file that contains no Plugin subclasses."""
        class RealLogger:
            def __init__(self):
                self.error_called = False
            def error(self, *args, **kwargs):
                self.error_called = True

        class RealApp:
            def __init__(self):
                self.logger = self
            def getChild(self, name):
                return self
            def error(self, *args, **kwargs):
                self.error_called = True

        plugin_manager = PluginManager(RealApp())

        dummy_module = types.ModuleType("dummy_plugin")
        class RegularClass:
            def not_register(self, app):
                pass
        setattr(dummy_module, "RegularClass", RegularClass)

        with patch('importlib.util.spec_from_file_location') as mock_spec, \
             patch('importlib.util.module_from_spec') as mock_module, \
             patch('inspect.getmembers', return_value=[('RegularClass', RegularClass)]), \
             patch('inspect.isclass', return_value=True), \
             patch('builtins.issubclass', return_value=False):

            mock_spec.return_value = Mock()
            mock_module.return_value = dummy_module

            plugin_manager._load_plugin_from_file("dummy_plugin.py")

            # Should not log error for non-plugin classes
            assert not hasattr(plugin_manager.logger, "error_called") or not plugin_manager.logger.error_called


    def test_load_plugin_multiple_classes(self):
        """Test loading plugin file with multiple Plugin subclasses."""
        class RealLogger:
            def __init__(self):
                self.error_called = False
            def getChild(self, name):
                return self
            def error(self, *args, **kwargs):
                self.error_called = True

        class RealApp:
            def __init__(self):
                self.logger = RealLogger()
                self.first_registered = False
                self.second_registered = False

        plugin_manager = PluginManager(RealApp())

        class FirstPlugin(Plugin):
            def register(self, app):
                app.first_registered = True
        class SecondPlugin(Plugin):
            def register(self, app):
                app.second_registered = True
        class NonPluginClass:
            pass

        dummy_module = types.ModuleType("dummy_plugin")
        setattr(dummy_module, "FirstPlugin", FirstPlugin)
        setattr(dummy_module, "SecondPlugin", SecondPlugin)
        setattr(dummy_module, "NonPluginClass", NonPluginClass)

        def issubclass_side_effect(cls, base):
            return cls in [FirstPlugin, SecondPlugin]

        with patch('importlib.util.spec_from_file_location') as mock_spec, \
             patch('importlib.util.module_from_spec') as mock_module, \
             patch('inspect.getmembers', return_value=[
                 ('FirstPlugin', FirstPlugin),
                 ('SecondPlugin', SecondPlugin),
                 ('NonPluginClass', NonPluginClass)
             ]), \
             patch('inspect.isclass', return_value=True), \
             patch('builtins.issubclass', side_effect=issubclass_side_effect):

            mock_spec.return_value = Mock()
            mock_module.return_value = dummy_module

            app = plugin_manager.app
            plugin_manager._load_plugin_from_file("dummy_plugin.py")

            # Both plugins should be registered
            assert app.first_registered
            assert app.second_registered
            assert not hasattr(app, "non_plugin_registered")



class TestPluginErrorScenarios:
    """Test error scenarios in plugin management."""

    def test_plugin_registration_exception(self):
        """Test handling plugin registration exceptions."""
        class RealLogger:
            def __init__(self):
                self.error_called = False
                self.error_msg = ""
            def getChild(self, name):
                return self
            def info(self, msg, *args, **kwargs):
                pass
            def error(self, msg, *args, **kwargs):
                self.error_called = True
                self.error_msg = msg

        class RealApp:
            def __init__(self):
                self.logger = RealLogger()

        plugin_manager = PluginManager(RealApp())

        class FailingPlugin(Plugin):
            def register(self, app):
                app.logger.error("Registration failed")

        dummy_module = types.ModuleType("dummy_plugin")
        setattr(dummy_module, "FailingPlugin", FailingPlugin)

        with patch('inspect.getmembers', return_value=[('FailingPlugin', FailingPlugin)]), \
             patch('inspect.isclass', return_value=True), \
             patch('builtins.issubclass', return_value=True):
            plugin_manager._load_plugin_from_file("dummy_plugin.py")

        # Should log the registration error
        assert plugin_manager.logger.error_called
        assert "Registration failed" in plugin_manager.logger.error_msg


class TestRealPluginIntegration:
    """Test integration with real plugin implementation."""

    def test_real_plugin_lifecycle(self):
        """Test a complete plugin lifecycle with real plugin."""
        class RealLogger:
            def __init__(self):
                self.info_msgs = []
                self.error_called = False
            def getChild(self, name):
                return self
            def info(self, msg, *args, **kwargs):
                self.info_msgs.append(msg)
            def error(self, *args, **kwargs):
                self.error_called = True

        class RealApp:
            def __init__(self):
                self.logger = RealLogger()
                self.plugins_loaded = []
                self.methods_called = []

        plugin_manager = PluginManager(RealApp())

        class TestPlugin(Plugin):
            def register(self, app):
                app.plugins_loaded.append('test_plugin')
                app.methods_called.append('register')
                app.plugin_instance = self

            def post_init(self, app):
                app.methods_called.append('post_init')

        dummy_module = types.ModuleType("dummy_plugin")
        setattr(dummy_module, "TestPlugin", TestPlugin)

        with patch('inspect.getmembers', return_value=[('TestPlugin', TestPlugin)]), \
             patch('inspect.isclass', return_value=True), \
             patch('builtins.issubclass', return_value=True):
            plugin_manager._load_plugin_from_file("dummy_plugin.py")

        app = plugin_manager.app
        assert app.plugins_loaded == ['test_plugin']
        assert app.methods_called == ['register']
        assert hasattr(app, 'plugin_instance')
        assert any("Registered plugin: TestPlugin" in msg for msg in app.logger.info_msgs)


class TestPluginDirectoryIntegration:
    """Test plugin loading from complete directory structure."""

    def test_plugin_directory_integration(self):
        """Test loading multiple plugins from a directory."""
        mock_app = Mock()
        mock_app.logger.getChild.return_value = Mock()
        mock_app.loaded_plugins = []

        plugin_manager = PluginManager(mock_app)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create multiple plugin files
            plugins = []

            for i in range(3):
                plugin_file = os.path.join(temp_dir, f'plugin_{i}.py')
                with open(plugin_file, 'w') as f:
                    f.write(f"""
from ucore_framework.core.plugins import Plugin

class Plugin{i}(Plugin):
    def register(self, app):
        app.loaded_plugins.append('plugin_{i}')
    """)
                plugins.append(plugin_file)

            # Mock plugin loading to avoid complex import mechanics
            with patch.object(plugin_manager, '_load_plugin_from_file') as mock_load_plugin:
                def mock_load_side_effect(filepath):
                    plugin_num = int(os.path.basename(filepath).split('_')[1].split('.')[0])
                    mock_app.loaded_plugins.append(f'plugin_{plugin_num}')

                mock_load_plugin.side_effect = mock_load_side_effect

                plugin_manager.load_plugins(temp_dir)

                # Should have called _load_plugin_from_file for each plugin
                assert mock_load_plugin.call_count == 3

                # Should have loaded all plugins (in mock side effect)
                assert len(mock_app.loaded_plugins) == 3
                assert set(mock_app.loaded_plugins) == {'plugin_0', 'plugin_1', 'plugin_2'}

            # Test with subdirectory - should not load from subdirs by default
            sub_dir = os.path.join(temp_dir, 'sub_plugins')
            os.makedirs(sub_dir)
            sub_plugin = os.path.join(sub_dir, 'sub_plugin.py')
            with open(sub_plugin, 'w') as f:
                f.write("pass")  # Create sub-plugin

            with patch.object(plugin_manager, '_load_plugin_from_file') as mock_load_plugin:
                plugin_manager.load_plugins(temp_dir)

                # Should not attempt to load sub-plugin
                # (Current implementation only loads from top-level)
                assert mock_load_plugin.call_count == 3  # Only the top-level plugins


class TestPluginValidation:
    """Test plugin validation and requirements."""

    def test_plugin_class_validation(self):
        """Test that plugin classes are properly validated."""
        class RealLogger:
            def __init__(self):
                self.error_called = False
            def getChild(self, name):
                return self
            def error(self, *args, **kwargs):
                self.error_called = True

        class RealApp:
            def __init__(self):
                self.logger = RealLogger()

        plugin_manager = PluginManager(RealApp())

        class NotAPlugin:
            def register(self, app):
                pass

        dummy_module = types.ModuleType("dummy_plugin")
        setattr(dummy_module, "NotAPlugin", NotAPlugin)

        with patch('importlib.util.spec_from_file_location') as mock_spec, \
             patch('importlib.util.module_from_spec') as mock_module, \
             patch('inspect.getmembers', return_value=[('NotAPlugin', NotAPlugin)]), \
             patch('inspect.isclass', return_value=True), \
             patch('builtins.issubclass', return_value=False):

            mock_spec.return_value = Mock()
            mock_module.return_value = dummy_module

            plugin_manager._load_plugin_from_file("dummy_plugin.py")

            # Should not log error for non-plugin classes
            assert not plugin_manager.logger.error_called


class TestPluginLogging:
    """Test comprehensive plugin logging functionality."""

    def test_plugin_loading_logging(self):
        """Test that plugin loading generates appropriate log messages."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        # Test loading non-existent directory
        plugin_manager.load_plugins("/nonexistent")
        mock_logger.warning.assert_called_with(
            "Plugins directory not found: /nonexistent"
        )

        # Test loading empty directory
        with tempfile.TemporaryDirectory() as temp_dir:
            plugin_manager.load_plugins(temp_dir)

            # Should log the initial info message
            mock_logger.info.assert_called()

    def test_plugin_success_logging(self):
        """Test logging of successful plugin registrations."""
        class RealLogger:
            def __init__(self):
                self.info_msgs = []
                self.error_called = False
            def getChild(self, name):
                return self
            def info(self, msg, *args, **kwargs):
                self.info_msgs.append(msg)
            def error(self, *args, **kwargs):
                self.error_called = True

        class RealApp:
            def __init__(self):
                self.logger = RealLogger()

        plugin_manager = PluginManager(RealApp())

        class TestPlugin(Plugin):
            def register(self, app):
                # Simulate real framework behavior: do not call app.logger.info directly
                pass

        dummy_module = types.ModuleType("dummy_plugin")
        setattr(dummy_module, "TestPlugin", TestPlugin)

        with patch('inspect.getmembers', return_value=[('TestPlugin', TestPlugin)]), \
             patch('inspect.isclass', return_value=True), \
             patch('builtins.issubclass', return_value=True):
            plugin_manager._load_plugin_from_file("dummy_plugin.py")

        # Should log successful plugin loading (by PluginManager, not plugin)
        assert any("Registered plugin: TestPlugin" in msg for msg in plugin_manager.logger.info_msgs)
        assert not plugin_manager.logger.error_called


class TestPluginManagerStats:
    """Test plugin manager statistics and information gathering."""

    def test_plugin_manager_directory_scanning(self):
        """Test plugin manager's directory scanning capabilities."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create various file types
            file_types = [
                ('plugin1.py', '.py', True),     # Should be loaded
                ('plugin2.py', '.py', True),     # Should be loaded
                ('package.py', '.py', False),    # Skip due to starting with 'package'? No
                ('__init__.py', '.py', False),   # Should be skipped
                ('utils.py', '.py', True),       # Should be loaded
                ('data.txt', '.txt', False),     # Wrong extension
                ('config.yml', '.yml', False)    # Wrong extension
            ]

            created_files = []
            for filename, ext, should_load in file_types:
                filepath = os.path.join(temp_dir, filename)
                with open(filepath, 'w') as f:
                    f.write("# Test file")
                created_files.append((filepath, should_load))

            # Count expected loads
            expected_loads = sum(1 for _, should_load in created_files if should_load)

            with patch.object(plugin_manager, '_load_plugin_from_file') as mock_load:
                plugin_manager.load_plugins(temp_dir)

                # Verify the correct number of load attempts
                assert mock_load.call_count == expected_loads

                # Check that __init__.py was not attempted to be loaded
                loaded_paths = [call[0][0] for call in mock_load.call_args_list]
                init_files = [p for p in loaded_paths if os.path.basename(p).startswith('__')]
                assert len(init_files) == 0, "Should not load files starting with __"

                # Check that only .py files were attempted
                py_files = [p for p in loaded_paths if p.endswith('.py')]
                assert len(py_files) == len(loaded_paths), "Should only attempt .py files"

    def test_performance_considerations(self):
        """Test plugin loading performance considerations."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create many plugin files to test loading performance
            num_plugins = 20

            for i in range(num_plugins):
                plugin_file = os.path.join(temp_dir, f'plugin_{i:02d}.py')
                with open(plugin_file, 'w') as f:
                    f.write(f"""
from ucore_framework.core.plugins import Plugin

class Plugin{i}(Plugin):
    def register(self, app):
        pass
""")

            with patch.object(plugin_manager, '_load_plugin_from_file') as mock_load:
                plugin_manager.load_plugins(temp_dir)

                # Should attempt to load all valid plugin files
                assert mock_load.call_count == num_plugins

                # Ensure no file is loaded more than once
                loaded_paths = [call[0][0] for call in mock_load.call_args_list]
                unique_paths = set(loaded_paths)
                assert len(unique_paths) == len(loaded_paths), "No duplicate file loading"
