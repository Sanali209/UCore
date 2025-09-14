# plugins/hello_plugin.py
from framework.plugins import Plugin
from framework.component import Component

class HelloComponent(Component):
    def __init__(self, message="Hello from the plugin!"):
        self.message = message

    def start(self):
        print(self.message)

class HelloPlugin(Plugin):
    def register(self, app):
        # This plugin registers the HelloComponent with the app's lifecycle
        app.register_component(HelloComponent, message="Hello from the HelloPlugin!")
