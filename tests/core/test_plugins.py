# tests/test_plugins.py
import unittest
from unittest.mock import MagicMock
import sys
import os
import shutil

from framework.app import App
from framework.core.plugins import PluginManager

class TestPluginSystem(unittest.TestCase):

    def setUp(self):
        """Set up a test app and a dummy plugin directory."""
        self.app = App(name="TestPluginApp")
        self.plugins_dir = "test_plugins_dir"
        os.makedirs(self.plugins_dir, exist_ok=True)
        
        # Create a dummy plugin file
        self.plugin_file_path = os.path.join(self.plugins_dir, "dummy_plugin.py")
        with open(self.plugin_file_path, "w") as f:
            f.write("""
from framework.core.plugins import Plugin
from framework.core.component import Component
from framework.app import App

class DummyComponent(Component):
    def __init__(self, app: App):
        super().__init__(app)

class DummyPlugin(Plugin):
    def register(self, app: App):
        app.register_component(DummyComponent)
""")

    def tearDown(self):
        """Clean up the dummy plugin directory."""
        shutil.rmtree(self.plugins_dir)

    def test_plugin_loading_and_component_registration(self):
        """
        Tests that the PluginManager correctly loads a plugin and the plugin
        registers its components.
        """
        plugin_manager = PluginManager(self.app)
        plugin_manager.load_plugins(self.plugins_dir)

        # Check if the DummyComponent from the plugin was registered
        self.assertEqual(len(self.app._components), 1)
        self.assertEqual(self.app._components[0].__class__.__name__, "DummyComponent")

    def test_loading_from_nonexistent_directory(self):
        """
        Tests that the PluginManager handles a nonexistent plugin directory gracefully.
        """
        plugin_manager = PluginManager(self.app)
        # This should not raise an error
        plugin_manager.load_plugins("nonexistent_plugins_dir")
        self.assertEqual(len(self.app._components), 0)

    def test_loading_invalid_plugin(self):
        """
        Tests that the PluginManager handles a plugin with invalid syntax gracefully.
        """
        invalid_plugin_path = os.path.join(self.plugins_dir, "invalid_plugin.py")
        with open(invalid_plugin_path, "w") as f:
            f.write("this is not valid python code")

        plugin_manager = PluginManager(self.app)
        # This should not raise an error, but log it
        plugin_manager.load_plugins(self.plugins_dir)
        
        # The invalid plugin should be skipped, but the valid one should still be loaded
        self.assertEqual(len(self.app._components), 1)
        self.assertEqual(self.app._components[0].__class__.__name__, "DummyComponent")

if __name__ == '__main__':
    unittest.main()
