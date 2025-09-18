from ucore_framework.core.plugins import Plugin

class HelloPlugin(Plugin):
    def register(self, app):
        print("HelloPlugin registered with app:", app.name)
