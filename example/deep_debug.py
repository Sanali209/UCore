#!/usr/bin/env python
"""
Example: Deep Debug App using UCore Framework Core Features

This script demonstrates:
- App lifecycle and dependency injection
- ConfigManager for configuration
- Custom Component with lifecycle hooks
- EventBus event publishing and handling
- PluginManager with a sample plugin
- ResourceManager with a mock resource
- Logging (loguru)
- UndoSystem and TimeMeasure utilities

Run: python example/deep_debug.py
"""
import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ucore_framework.core.app import App
from ucore_framework.core.config import ConfigManager
from ucore_framework.core.component import Component
from ucore_framework.core.plugins import PluginManager, Plugin
from ucore_framework.core.event_bus import EventBus
from ucore_framework.core.event_types import CoreEvent
from ucore_framework.core.resource.manager import ResourceManager
from ucore_framework.core.undo import UndoSystem
from ucore_framework.core.timemeasure import TimeMeasure
from loguru import logger

# --- Custom Event Example ---
class HelloEvent(CoreEvent):
    """A simple custom event."""
    def __init__(self, message):
        super().__init__()
        self.message = message

# --- Custom Component Example ---
class HelloComponent(Component):
    """A component that reacts to config and events."""
    def start(self):
        logger.info("[HelloComponent] start() called")
        if not self.app or not hasattr(self.app, "container"):
            logger.error("[HelloComponent] self.app or self.app.container is not set!")
            return
        config = self.app.container.get(ConfigManager)
        logger.info(f"[HelloComponent] Config value: app_name = {config.get('app_name')}")
        # Subscribe to HelloEvent
        event_bus = self.app.container.get(EventBus)
        event_bus.subscribe(HelloEvent)(self.on_hello_event)

    def stop(self):
        logger.info("[HelloComponent] stop() called")

    def on_config_update(self, config):
        logger.info(f"[HelloComponent] Config updated: app_name = {config.get('app_name')}")

    def on_hello_event(self, event):
        logger.info(f"[HelloComponent] Received HelloEvent: {event.message}")

# --- Custom Plugin Example ---
class HelloPlugin(Plugin):
    """A simple plugin that registers a component."""
    def register(self, app):
        logger.info("[HelloPlugin] Registering HelloComponent")
        app.register_component(HelloComponent)

# --- Main App Setup ---
def main():
    # Initialize the application
    app = App("DeepDebugApp")

    # Access and update config
    config = app.container.get(ConfigManager)
    logger.info(f"[App] Initial config: app_name = {config.get('app_name')}")
    config.set("app_name", "Deep Debug Example")

    # Register UndoSystem and TimeMeasure utilities
    undo = UndoSystem()
    timer = TimeMeasure()
    app.register_component(undo)
    app.register_component(timer)

    # Register ResourceManager as a component
    resource_manager = ResourceManager(app=app)
    app.register_component(resource_manager)

    # Register PluginManager and load HelloPlugin
    plugin_manager = PluginManager(app)
    app.plugin_manager = plugin_manager
    plugin_manager.registry.register_plugin(HelloPlugin)

    # Register HelloComponent directly (for demonstration)
    app.register_component(HelloComponent)

    # Publish a custom event after startup
    def after_start():
        event_bus = app.container.get(EventBus)
        event_bus.publish(HelloEvent("Hello from DeepDebug!"))
        logger.info("[App] Published HelloEvent")

        # Demonstrate UndoSystem
        undo.add_undo_item(lambda: logger.info("Undo!"), lambda: logger.info("Redo!"), "Sample Undo")
        undo.undo()
        undo.redo()

        # Demonstrate TimeMeasure
        timer.start_timer("example")
        import time
        time.sleep(0.1)
        timer.lap("example", "first")
        time.sleep(0.1)
        timer.lap("example", "second")
        logger.info(f"[App] Timer laps: {timer.get_laps('example')}")

    # Monkey-patch start to call after_start after normal startup
    orig_start = app.start
    async def patched_start():
        await orig_start()
        after_start()
    app.start = patched_start

    # Run the application (will block)
    app.run()

if __name__ == "__main__":
    main()
