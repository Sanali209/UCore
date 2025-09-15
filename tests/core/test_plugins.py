import pytest
import tempfile
import os
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
import importlib.util
import sys
from framework.core.plugins import PluginManager, Plugin
from framework.core.app import App


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
from framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def register(self, app):
        app.registered_plugins.append("test_plugin")

    def get_name(self):
        return "Test Plugin"
"""
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
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
# This file contains no Plugin subclasses
def regular_function():
    pass

class RegularClass:
    def not_register(self, app):
        pass
""")
            temp_file = f.name

        try:
            with patch('importlib.util.spec_from_file_location') as mock_spec, \
                 patch('importlib.util.module_from_spec') as mock_module:

                mock_spec.return_value = Mock()
                mock_module_obj = Mock()
                mock_module.return_value = mock_module_obj
                mock_module_obj.loader = Mock()
                mock_module_obj.loader.exec_module = Mock()

                # Mock inspect to return non-plugin classes
                with patch('inspect.getmembers') as mock_getmembers:
                    with patch('inspect.isclass') as mock_isclass:
                        mock_isclass.return_value = True

                        def getmembers_side_effect(*args, **kwargs):
                            # Return a regular class that doesn't inherit from Plugin
                            mock_regular_class = Mock()
                            return [('RegularClass', mock_regular_class)]

                        mock_getmembers.side_effect = getmembers_side_effect

                        # Mock issubclass to return False for regular classes
                        with patch('builtins.issubclass', return_value=False):
                            plugin_manager._load_plugin_from_file(temp_file)

                            # Should not create any plugin instances
                            mock_logger.error.assert_not_called()

        finally:
            os.unlink(temp_file)

    def test_load_plugin_multiple_classes(self):
        """Test loading plugin file with multiple Plugin subclasses."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from framework.core.plugins import Plugin

class FirstPlugin(Plugin):
    def register(self, app):
        pass

class SecondPlugin(Plugin):
    def register(self, app):
        pass

class NonPluginClass:
    pass
""")
            temp_file = f.name

        try:
            with patch('importlib.util.spec_from_file_location') as mock_spec, \
                 patch('importlib.util.module_from_spec') as mock_module:

                mock_spec.return_value = Mock()
                mock_module_obj = Mock()
                mock_module.return_value = mock_module_obj
                mock_module_obj.loader = Mock()
                mock_module_obj.loader.exec_module = Mock()

                # Mock Plugin classes
                mock_first_plugin = Mock()
                mock_second_plugin = Mock()
                mock_regular_class = Mock()

                mock_first_instance = Mock()
                mock_second_instance = Mock()

                mock_first_plugin.return_value = mock_first_instance
                mock_second_plugin.return_value = mock_second_instance

                with patch('inspect.getmembers') as mock_getmembers:
                    with patch('inspect.isclass') as mock_isclass:
                        mock_isclass.return_value = True

                        def getmembers_side_effect(*args, **kwargs):
                            return [
                                ('FirstPlugin', mock_first_plugin),
                                ('SecondPlugin', mock_second_plugin),
                                ('NonPluginClass', mock_regular_class)
                            ]

                        mock_getmembers.side_effect = getmembers_side_effect

                        # Mock issubclass to identify Plugin subclasses
                        def issubclass_side_effect(cls, base):
                            if cls in [mock_first_plugin, mock_second_plugin]:
                                return True
                            return False

                        with patch('builtins.issubclass', side_effect=issubclass_side_effect):
                            plugin_manager._load_plugin_from_file(temp_file)

                            # Should have instantiated both plugin classes
                            mock_first_plugin.assert_called_once()
                            mock_second_plugin.assert_called_once()
                            mock_regular_class.assert_not_called()

                            # Should have registered both plugins
                            mock_first_instance.register.assert_called_once_with(mock_app)
                            mock_second_instance.register.assert_called_once_with(mock_app)

        finally:
            os.unlink(temp_file)


class TestPluginErrorScenarios:
    """Test error scenarios in plugin management."""

    def test_plugin_registration_exception(self):
        """Test handling plugin registration exceptions."""
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        with patch('importlib.util.spec_from_file_location') as mock_spec, \
             patch('importlib.util.module_from_spec') as mock_module:

            mock_spec.return_value = Mock()
            mock_module_obj = Mock()
            mock_module.return_value = mock_module_obj

            mock_plugin_class = Mock()
            mock_plugin_instance = Mock()
            mock_plugin_class.return_value = mock_plugin_instance
            mock_plugin_instance.register.side_effect = Exception("Registration failed")

            with patch('inspect.getmembers', return_value=[('TestPlugin', mock_plugin_class)]):
                with patch('inspect.isclass', return_value=True):
                    with patch('builtins.issubclass', return_value=True):

                        # Create temporary plugin file
                        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                            f.write("class TestPlugin(Plugin): pass")
                            temp_file = f.name

                        try:
                            plugin_manager._load_plugin_from_file(temp_file)

                            # Should log the registration error
                            mock_logger.error.assert_called_once()
                            assert 'Registration failed' in str(mock_logger.error.call_args)

                        finally:
                            os.unlink(temp_file)


class TestRealPluginIntegration:
    """Test integration with real plugin implementation."""

    def test_real_plugin_lifecycle(self):
        """Test a complete plugin lifecycle with real plugin."""
        mock_app = Mock()
        mock_app.logger.getChild.return_value = Mock()
        mock_app.plugins_loaded = []
        mock_app.methods_called = []

        plugin_manager = PluginManager(mock_app)

        # Create a real temporary plugin file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
from framework.core.plugins import Plugin

class TestPlugin(Plugin):
    def register(self, app):
        app.plugins_loaded.append('test_plugin')
        app.methods_called.append('register')
        app.plugin_instance = self

    def post_init(self, app):
        app.methods_called.append('post_init')

def create_test_plugin():
    return TestPlugin()
""")
            temp_file = f.name

        try:
            # Add the temp directory to sys.path for import
            temp_dir = os.path.dirname(temp_file)
            plugin_name = os.path.basename(temp_file)[:-3]  # Remove .py

            # Use real plugin loading mechanism
            with patch('builtins.issubclass') as mock_issubclass:
                # Mock issubclass to work with real classes
                def issubclass_side_effect(cls, base):
                    if hasattr(cls, 'register') and callable(getattr(cls, 'register', None)):
                        # Check if it looks like a plugin class
                        return True if base.__name__ == 'Plugin' else False
                    return False

                mock_issubclass.side_effect = issubclass_side_effect

                # Load the plugin
                plugin_manager._load_plugin_from_file(temp_file)

                # Verify plugin was loaded and registered
                assert mock_app.plugins_loaded == ['test_plugin']
                assert mock_app.methods_called == ['register']
                assert hasattr(mock_app, 'plugin_instance')

                # Check that logger was informed
                plugin_manager.app.logger.getChild().info.assert_called()

        finally:
            os.unlink(temp_file)
            # Remove temp directory from sys.path if added
            if temp_dir in sys.path:
                sys.path.remove(temp_dir)


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
from framework.core.plugins import Plugin

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
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        # Test with class that has register method but doesn't inherit from Plugin
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("""
class NotAPlugin:
    def register(self, app):
        pass
""")
            temp_file = f.name

        try:
            with patch('importlib.util.spec_from_file_location') as mock_spec, \
                 patch('importlib.util.module_from_spec') as mock_module:

                mock_spec.return_value = Mock()
                mock_module_obj = Mock()
                mock_module.return_value = mock_module_obj

                with patch('inspect.getmembers') as mock_getmembers:
                    with patch('inspect.isclass', return_value=True):
                        mock_class = Mock()

                        def getmembers_side_effect(*args, **kwargs):
                            return [('NotAPlugin', mock_class)]

                        mock_getmembers.side_effect = getmembers_side_effect

                        # Mock issubclass to return False
                        with patch('builtins.issubclass', return_value=False):
                            plugin_manager._load_plugin_from_file(temp_file)

                            # Should not attempt to register non-plugin classes
                            mock_logger.error.assert_not_called()

        finally:
            os.unlink(temp_file)


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
        mock_logger = Mock()
        mock_app = Mock()
        mock_app.logger.getChild.return_value = mock_logger

        plugin_manager = PluginManager(mock_app)

        # Mock successful plugin loading process
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("class TestPlugin(Plugin): pass")
            temp_file = f.name

        try:
            with patch('importlib.util.spec_from_file_location') as mock_spec, \
                 patch('importlib.util.module_from_spec') as mock_module:

                mock_spec.return_value = Mock()
                mock_module_obj = Mock()
                mock_module.return_value = mock_module_obj

                mock_plugin_class = Mock()
                mock_plugin_instance = Mock()
                mock_plugin_class.return_value = mock_plugin_instance

                with patch('inspect.getmembers', return_value=[('TestPlugin', mock_plugin_class)]):
                    with patch('inspect.isclass', return_value=True):
                        with patch('builtins.issubclass', return_value=True):

                            plugin_manager._load_plugin_from_file(temp_file)

                            # Should log successful plugin loading
                            mock_logger.info.assert_any_call("Registered plugin: TestPlugin")
                            mock_logger.error.assert_not_called()

        finally:
            os.unlink(temp_file)


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
from framework.core.plugins import Plugin

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
