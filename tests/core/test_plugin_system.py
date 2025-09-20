import pytest
import sys
import types
from pathlib import Path
from ucore_framework.core.plugins import PluginManager, PluginRegistry, PluginType, plugin

@pytest.fixture
def plugin_dir_fixture(tmp_path):
    # Create a temporary plugin file
    plugin_code = '''
from ucore_framework.core.plugins import Plugin, PluginType, PluginMetadata

class EditorPlugin(Plugin):
    def register(self, app):
        pass
    
    def get_metadata(self):
        return PluginMetadata(
            name="EditorPlugin",
            plugin_type=PluginType.EDITOR,
            capabilities=["edit_text"],
            supported_formats=["txt"]
        )

class ViewerPlugin(Plugin):
    def register(self, app):
        pass
    
    def get_metadata(self):
        return PluginMetadata(
            name="ViewerPlugin", 
            plugin_type=PluginType.VIEWER,
            capabilities=["view_image"],
            supported_formats=["jpg"]
        )
'''
    plugin_file = tmp_path / "my_test_plugin.py"
    plugin_file.write_text(plugin_code)
    return tmp_path

@pytest.fixture
def plugin_manager_fixture(plugin_dir_fixture):
    # Create a mock App object if needed
    class MockApp:
        pass
    manager = PluginManager(MockApp())
    manager.load_plugins(str(plugin_dir_fixture))
    return manager

def test_plugin_manager_loads_plugins(plugin_dir_fixture):
    class MockApp:
        pass
    manager = PluginManager(MockApp())
    manager.load_plugins(str(plugin_dir_fixture))
    assert len(manager.registry.plugins) == 2

def test_registry_query_by_type(plugin_manager_fixture):
    editors = plugin_manager_fixture.registry.get_plugins_by_type(PluginType.EDITOR)
    assert len(editors) == 1
    assert editors[0].plugin_class.__name__ == "EditorPlugin"

def test_registry_query_by_capability(plugin_manager_fixture):
    plugins = plugin_manager_fixture.registry.get_plugins_by_capability("edit_text")
    assert len(plugins) == 1
    assert plugins[0].plugin_class.__name__ == "EditorPlugin"
