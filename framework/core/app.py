# framework/app.py
import argparse
import asyncio
import inspect
import signal
import sys
from typing import List, Type
from .config import Config
from .di import Container, Scope
from ..monitoring.logging import Logging
from .component import Component
from .plugins import PluginManager
from ..messaging.event_bus import EventBus
from ..messaging.events import AppStartedEvent, AppStoppedEvent, ComponentStartedEvent, ComponentStoppedEvent, ConfigUpdatedEvent

class App:
    """
    The main application class that manages the lifecycle of the framework.
    It is responsible for configuration, dependency injection, component
    management, and graceful shutdown.
    """
    def __init__(self, name: str):
        self.name = name
        self.container = Container()
        self._components: List[Component] = []
        self._setup_core_services()
        self.plugin_manager = PluginManager(self)

    def _setup_core_services(self) -> None:
        """
        Initializes and registers core services like Config and Logging.
        """
        self.container.register(Config, scope=Scope.SINGLETON)
        self.container.register(Logging, scope=Scope.SINGLETON)
        self.container.register(EventBus, scope=Scope.SINGLETON)

        # Make the App instance itself available for injection
        self.container.register_instance(self)

        logging_instance = self.container.get(Logging)
        self.logger = logging_instance.get_logger(self.name)

    def run(self) -> None:
        """
        Parses command-line arguments and starts the application's event loop.
        """
        parser = self._create_arg_parser()
        args = parser.parse_args()
        self.bootstrap(args)

        loop = self._get_event_loop()
        self._setup_signal_handlers(loop)

        try:
            loop.run_until_complete(self._main_loop())

            # Check if any component is a PySide6Adapter (GUI app)
            has_qt_adapter = any(hasattr(component, 'qt_app') for component in self._components)

            if has_qt_adapter:
                self.logger.info("GUI application detected - transferring control to Qt event loop")
                import sys

                # Find Qt app from any PySide6Adapter
                qt_app = None
                for component in self._components:
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
        logging_instance = self.container.get(Logging)
        self.logger = logging_instance.get_logger(self.name, level=args.log_level.upper())
        self.logger.info("Bootstrapping application...")

        config = self.container.get(Config)
        if args.config:
            self.logger.info(f"Loading configuration from file: {args.config}")
            config.load_from_file(args.config)
        
        self.logger.info("Loading configuration from environment variables.")
        config.load_from_env()

        if args.plugins_dir:
            self.plugin_manager.load_plugins(args.plugins_dir)
        
        self.logger.info("Bootstrap complete.")

    def register_component(self, component) -> None:
        """
        Registers and instantiates a component, adding it to the lifecycle management.
        Accepts Component classes, instances, or factory functions (callables).
        """
        component_instance = None

        if inspect.isclass(component) and issubclass(component, Component):
            # Component is a class - instantiate it
            component_instance = component(self)
        elif isinstance(component, Component):
            # Component is already an instance
            component_instance = component
        elif callable(component):
            # Component is a factory function - call it and check result
            try:
                potential_instance = component()
                if isinstance(potential_instance, Component):
                    component_instance = potential_instance
                    # Set app reference if needed
                    if not hasattr(component_instance, 'app') or component_instance.app is None:
                        component_instance.app = self
                else:
                    self.logger.warning(f"Factory function returned a {type(potential_instance).__name__}, expected Component")
                    return
            except Exception as e:
                self.logger.warning(f"Factory function call failed: {e}")
                return
        else:
            self.logger.warning(f"Invalid component type: {type(component).__name__}. Must be Component class, instance, or factory function")
            return

        self._components.append(component_instance)
        self.logger.info(f"Registered component: {component_instance.__class__.__name__}")

    async def start(self) -> None:
        """
        Starts all registered components.
        """
        # Start the EventBus first to enable event publishing
        event_bus = self.container.get(EventBus)
        event_bus.start()

        self.logger.info("Starting components...")
        for component in self._components:
            await self._execute_lifecycle_method(component, 'start')

    async def stop(self) -> None:
        """
        Stops all registered components in reverse order.
        """
        self.logger.info("Stopping components...")
        for component in reversed(self._components):
            await self._execute_lifecycle_method(component, 'stop')

        # Shutdown the EventBus last to stop event publishing
        event_bus = self.container.get(EventBus)
        event_bus.shutdown()

    async def _main_loop(self) -> None:
        """
        The main execution loop for the application.
        """
        await self.start()

        # Publish application started event
        event_bus = self.container.get(EventBus)
        started_event = AppStartedEvent(app_name=self.name, component_count=len(self._components))
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
        for component in self._components:
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
                stopped_event = AppStoppedEvent(app_name=self.name, stop_reason='signal')
                event_bus.publish(stopped_event)

                # This will stop the _main_loop's wait
                loop.call_soon_threadsafe(lambda: asyncio.create_task(self.stop()))

        if sys.platform != "win32":
            loop.add_signal_handler(signal.SIGINT, shutdown_handler)
            loop.add_signal_handler(signal.SIGTERM, shutdown_handler)
        else:
            self.logger.info("Signal handlers not fully supported on Windows. Use Ctrl+C.")

    async def _execute_lifecycle_method(self, component: Component, method_name: str) -> None:
        """
        Executes a lifecycle method (start/stop) on a component,
        handling both sync and async methods.
        """
        method = getattr(component, method_name)
        try:
            if inspect.iscoroutinefunction(method):
                await method()
            else:
                method()
            self.logger.info(f"{method_name.capitalize()}d component: {component.__class__.__name__}")

            # Publish lifecycle event
            event_bus = self.container.get(EventBus)
            if method_name == 'start':
                event = ComponentStartedEvent(
                    component_name=component.__class__.__name__,
                    component_type=type(component)
                )
            elif method_name == 'stop':
                event = ComponentStoppedEvent(
                    component_name=component.__class__.__name__,
                    component_type=type(component)
                )
            event_bus.publish(event)

        except Exception as e:
            self.logger.error(f"Error {method_name}ing component {component.__class__.__name__}: {e}", exc_info=True)

    def reload_config(self, config_path: str = None) -> None:
        """
        Reloads configuration from file and environment.
        Notifies all components of configuration changes.
        """
        config = self.container.get(Config)

        # Track old config keys/values for change detection
        # TODO: Improve change detection with better Config API
        updated_keys = []  # Placeholder - implement based on Config class
        old_values = {}
        new_values = {}

        if config_path:
            self.logger.info(f"Loading configuration from file: {config_path}")
            config.load_from_file(config_path)

        # Always reload from environment to pick up changes
        self.logger.info("Loading configuration from environment variables")
        config.load_from_env()

        # Publish configuration update event
        event_bus = self.container.get(EventBus)
        update_event = ConfigUpdatedEvent(
            updated_keys=updated_keys,
            old_values=old_values,
            new_values=new_values
        )
        event_bus.publish(update_event)

        # Notify all registered components of config update (backward compatibility)
        for component in self._components:
            if hasattr(component, 'on_config_update'):
                try:
                    component.on_config_update(config)
                except Exception as e:
                    self.logger.error(f"Error updating config for component {component.__class__.__name__}: {e}")

        self.logger.info("Configuration reloaded and components notified")

    def update_log_level(self, level: str) -> None:
        """
        Updates the global log level and notifies all components.
        """
        # Update the logging instance level
        logging_instance = self.container.get(Logging)
        logging_instance.set_global_level(level.upper())

        self.logger.info(f"Log level updated to {level.upper()}")

    def load_config(self, config_path: str) -> None:
        """
        Alias for reload_config for backward compatibility.
        """
        self.reload_config(config_path)
