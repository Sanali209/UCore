from ucore_framework.core.plugins import PluginManager
from ucore_framework.core.app import App

class HelloPlugin:
    """A simple hello plugin."""
    name = "hello"
    def run(self):
        print("Hello from plugin!")

class GoodbyePlugin:
    """A simple goodbye plugin."""
    name = "goodbye"
    def run(self):
        print("Goodbye from plugin!")

def main():
    # Create a minimal app to get the plugin manager
    app = App("plugin_demo")
    plugin_manager = app.plugin_manager
    
    # Register plugins manually in the registry
    registry = plugin_manager.registry
    registry.register_plugin(HelloPlugin)
    registry.register_plugin(GoodbyePlugin)

    print("Available plugins:", [p.name for p in [HelloPlugin, GoodbyePlugin]])
    for plugin_cls in [HelloPlugin, GoodbyePlugin]:
        plugin = plugin_cls()
        print(f"Running plugin: {plugin.name}")
        plugin.run()

if __name__ == "__main__":
    main()
