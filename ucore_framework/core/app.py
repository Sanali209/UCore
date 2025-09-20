"""
UCore Framework Application Entry Point.

This module defines the App class, which manages the lifecycle of a UCore application,
including configuration, dependency injection, component management, plugin loading,
and graceful shutdown. It provides the main orchestration logic for both CLI and GUI apps.

Classes:
    App: Main application class for UCore.
"""

import argparse
import asyncio
import inspect
import signal
import sys
from typing import List, Type
from .config import ConfigManager
from .di import Container, Scope
# Logging is now handled via standalone loguru; see https://github.com/Delgan/loguru
from loguru import logger
from .component import Component
from .component_manager import ComponentManager
from .plugins import PluginManager
from .event_bus import EventBus
from .event_types import AppStartedEvent, AppStoppedEvent, ComponentStartedEvent, ComponentStoppedEvent, ConfigurationChangedEvent
from .configuration_manager import ConfigurationManager

class App:
    """
    The main application class that manages the lifecycle of the UCoreFrameworck.
    It is responsible for configuration, dependency injection, component
    management, and graceful shutdown.
    """
    def __init__(self, name: str):
        self.name = name
        self.container = Container()
        self._setup_core_services()
        self.plugin_manager = PluginManager(self)
        self.config_manager = ConfigurationManager(self.container, logger.bind(app=self.name))
        self.component_manager = ComponentManager(self.container, self.logger)

    def _setup_core_services(self) -> None:
        """
        Initializes and registers core services like Config and Logging.
        """
        self.container.register(ConfigManager, scope=Scope.SINGLETON)
        # Logging is now handled via standalone loguru; no Logging class registration needed
        self.container.register(EventBus, scope=Scope.SINGLETON)

        # Make the App instance itself available for injection
        self.container.register_instance(self)

        self.logger = logger.bind(app=self.name)

    def run(self) -> None:
        """
        Parses command-line arguments and starts the application's event loop.
        """
        parser = self._create_arg_parser()
        try:
            args = parser.parse_args()
        except SystemExit:
            # Try again with unknown args ignored (for pytest compatibility)
            args, _ = parser.parse_known_args()
        self.bootstrap(args)

        loop = self._get_event_loop()
        self._setup_signal_handlers(loop)

        try:
            loop.run_until_complete(self._main_loop())

            # Check if any component is a PySide6Adapter (GUI app)
            has_qt_adapter = any(hasattr(component, 'qt_app') for component in self.component_manager.get_all_components())

            if has_qt_adapter:
                self.logger.info("GUI application detected - transferring control to Qt event loop")
                import sys

                # Find Qt app from any PySide6Adapter
                qt_app = None
                for component in self.component_manager.get_all_components():
                    if hasattr(component, 'qt_app') and component.qt_app:
                        qt_app = component.qt_app
                        self.logger.info(f"Found Qt app from {component.__class__.__name__}")
                        break

                if qt_app:
                    self.logger.info("Starting Qt event loop with Qt application")
                    # Run Qt event loop - this will keep GUI active
                    sys.exit(qt_app.exec())
                    self.logger.info("Qt event loop finished")
                else:
                    self.logger.error("Qt application found but no valid Qt app instance - cannot start GUI")
            else:
                # CLI app - normal shutdown
                pass

        except KeyboardInterrupt:
            self.logger.info("Shutdown requested via KeyboardInterrupt.")
        finally:
            self.logger.info("Application shutdown.")

    def bootstrap(self, args: argparse.Namespace) -> None:
        """
        Initializes the application, loads configuration, and loads plugins.
        """
        self.logger = logger.bind(app=self.name)
        self.config_manager.update_log_level(args.log_level)
        self.logger.info("Bootstrapping application...")

        if args.config:
            self.config_manager.reload_config(args.config)
        else:
            self.config_manager.reload_config()

        if args.plugins_dir:
            self.plugin_manager.load_plugins(args.plugins_dir)
        
        self.logger.info("Bootstrap complete.")

    def register_component(self, component) -> None:
        """
        Registers a component using the component manager.
        """
        self.component_manager.register_component(component)

    async def start(self) -> None:
        """
        Starts all registered components using the component manager.
        """
        await self.component_manager.start()

    async def stop(self) -> None:
        """
        Stops all registered components using the component manager.
        """
        await self.component_manager.stop()

    async def _main_loop(self) -> None:
        """
        The main execution loop for the application.
        """
        await self.start()

        # Publish application started event
        event_bus = self.container.get(EventBus)
        started_event = AppStartedEvent(app_name=self.name)
        event_bus.publish(started_event)

        self.logger.info("Application is ready.")
        # In a real-world scenario, a more robust stop event would be used.
        # For simplicity, we'll just wait indefinitely until a signal is caught.
        stop_event = asyncio.Event()
        await stop_event.wait()

    def _create_arg_parser(self) -> argparse.ArgumentParser:
        """
        Creates and configures the command-line argument parser.
        """
        parser = argparse.ArgumentParser(description=f"{self.name} Application")
        parser.add_argument("--config", help="Path to the configuration file")
        parser.add_argument("--log-level", default="INFO", help="Set the log level")
        parser.add_argument("--plugins-dir", help="Directory to load plugins from")
        return parser

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Determines and returns the appropriate event loop.
        First checks if any registered component can provide an event loop.
        """
        # Check if any component can provide an event loop
        for component in self.component_manager.get_all_components():
            if hasattr(component, 'get_event_loop'):
                try:
                    self.logger.info(f"Using event loop from {component.__class__.__name__}")
                    return component.get_event_loop()
                except Exception as e:
                    self.logger.warning(f"Failed to get event loop from {component.__class__.__name__}: {e}")

        # Default to asyncio event loop
        self.logger.info("Using default asyncio event loop")
        return asyncio.get_event_loop()

    def _setup_signal_handlers(self, loop: asyncio.AbstractEventLoop) -> None:
        """
        Sets up signal handlers for graceful shutdown.
        """
        stop_event = asyncio.Event()

        def shutdown_handler():
            if not stop_event.is_set():
                stop_event.set()

                # Publish application stopped event
                event_bus = self.container.get(EventBus)
                stopped_event = AppStoppedEvent(reason='signal')
                event_bus.publish(stopped_event)

                # This will stop the _main_loop's wait
                loop.call_soon_threadsafe(lambda: asyncio.create_task(self.stop()))

        if sys.platform != "win32":
            loop.add_signal_handler(signal.SIGINT, shutdown_handler)
            loop.add_signal_handler(signal.SIGTERM, shutdown_handler)
        else:
            self.logger.info("Signal handlers not fully supported on Windows. Use Ctrl+C.")
