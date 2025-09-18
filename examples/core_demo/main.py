"""
UCore Framework Example: Core Features

Demonstrates application/component system, dependency injection, configuration, and plugins.
"""

from ucore_framework.core.app import App
from ucore_framework.core.component import Component
from ucore_framework.core.config import Config
from ucore_framework.core.di import Container
import os

class HelloService:
    def say_hello(self):
        return "Hello from DI service!"

class HelloComponent(Component):
    def __init__(self, app):
        super().__init__(app)
        # Resolve HelloService from the app's DI container
        self.hello_service = app.container.get(HelloService)

    def run(self):
        print(self.hello_service.say_hello())

def main():
    # Configuration example
    config = Config()
    config.load_from_dict({"app_name": "CoreDemoApp"})
    print("Config loaded:", config.get("app_name"))

    # Dependency Injection example
    container = Container()
    container.register(HelloService)
    hello_service = container.get(HelloService)
    print("DI says:", hello_service.say_hello())

    # Application/component system
    app = App(name="CoreDemoApp")
    app.container.register(HelloService)
    app.register_component(HelloComponent)
    # Demonstrate plugin system
    plugins_dir = os.path.join(os.path.dirname(__file__), "plugins")
    app.plugin_manager.load_plugins(plugins_dir)
    # Run the component logic (not the full app loop for demo)
    for component in app._components:
        if isinstance(component, HelloComponent):
            component.run()

if __name__ == "__main__":
    main()
