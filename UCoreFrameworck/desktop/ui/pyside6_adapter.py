# framework/ui/pyside6_adapter.py
import asyncio
import inspect
import sys
from PySide6.QtWidgets import QApplication
import qasync
from ...core.component import Component
from loguru import logger

class PySide6Adapter(Component):
    """
    An adapter to integrate a PySide6 Qt application with the asyncio event loop.
    """
    def __init__(self, app):
        self.app = app
        # PySide6 needs proper QApplication instance management
        self.qt_app = None
        self.event_loop = None
        self.windows = []
        self._shutdown_handler = None
        logger.info("PySide6Adapter initialized")

    def set_shutdown_handler(self, handler):
        """
        Receives the application's shutdown handler.
        """
        self._shutdown_handler = handler
        if self.qt_app is not None and hasattr(self.qt_app, "aboutToQuit"):
            self.qt_app.aboutToQuit.connect(self._shutdown_handler)
            logger.info("Shutdown handler connected to aboutToQuit")
        else:
            logger.warning("qt_app is None or missing aboutToQuit; shutdown handler not connected")

    def add_window(self, window):
        """
        Keep a reference to the window to prevent it from being garbage collected.
        """
        self.windows.append(window)
        logger.debug(f"Window added: {window}")

    def create_widget(self, widget_class, *args, **kwargs):
        """
        Instantiates a widget, injecting dependencies from the container.
        """
        # Get constructor parameters
        params = inspect.signature(widget_class.__init__).parameters
        
        # Resolve dependencies from the container
        dependencies = {}
        for name, param in params.items():
            if name == 'self':
                continue
            # If the argument is already provided, use it
            if name in kwargs:
                dependencies[name] = kwargs[name]
                continue
            # Otherwise, try to resolve from the container
            if param.annotation is not inspect.Parameter.empty:
                try:
                    dependencies[name] = self.app.container.get(param.annotation)
                except Exception:
                    # If not in container, it might be a regular arg/kwarg
                    pass
        
        # Create the widget instance with resolved dependencies
        try:
            return widget_class(*args, **dependencies)
        except TypeError as e:
            logger.error(f"Widget instantiation failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Widget instantiation failed: {e}")
            raise

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Creates and returns a qasync event loop.
        This method is called by the main App class before the loop starts.
        """
        logger.info("Initializing PySide6 event loop...")
        if hasattr(self.app, "logger"):
            self.app.logger.info("Initializing PySide6 event loop...")

        # Create QApplication if it doesn't exist (CRITICAL for Qt widget creation)
        if not self.qt_app:
            try:
                # Set sys.argv for Qt if not already set - must be done before QApplication
                if not hasattr(sys, 'argv') or len(sys.argv) == 0:
                    sys.argv = ['UCore']  # Set basic argv for Qt

                existing_app = QApplication.instance()
                if existing_app:
                    self.qt_app = existing_app
                else:
                    self.qt_app = QApplication(sys.argv)
                logger.info("QApplication created and ready for Qt widgets")
                if hasattr(self.app, "logger"):
                    self.app.logger.info("QApplication created and ready for Qt widgets")
            except Exception as e:
                logger.error(f"Failed to create QApplication: {e}")
                if hasattr(self.app, "logger"):
                    self.app.logger.error(f"Failed to create QApplication: {e}")
                raise SystemExit(f"Critical: Cannot create Qt application: {e}")

        # Create qasync event loop
        if self.event_loop is not None:
            return self.event_loop
        try:
            self.event_loop = qasync.QEventLoop(self.qt_app)
            logger.info("PySide6 event loop created successfully - QApplication ready")
            if hasattr(self.app, "logger"):
                self.app.logger.info("PySide6 event loop created successfully - QApplication ready")
        except Exception as e:
            logger.error(f"Failed to create PySide6 event loop: {e}")
            if hasattr(self.app, "logger"):
                self.app.logger.error(f"Failed to create PySide6 event loop: {e}")
            # Fallback to regular asyncio loop if qasync fails
            self.event_loop = asyncio.get_event_loop_policy().new_event_loop()

        return self.event_loop

    def ensure_qt_ready(self):
        """
        Ensure that QApplication and event loop are properly initialized.
        This should be called before creating any Qt widgets.
        """
        if not self.qt_app:
            return False
        return self.qt_app is not None

    def start(self):
        """
        The component start method. The Qt app is already running at this point.
        """
        logger.info("PySide6Adapter started. Qt event loop is running.")
        if hasattr(self.app, "logger"):
            self.app.logger.info("PySide6Adapter started. Qt event loop is running.")
        # Verify Qt is properly set up
        if not self.qt_app:
            logger.warning("QApplication not found in start() - critical Qt initialization issue")
            if hasattr(self.app, "logger"):
                self.app.logger.warning("QApplication not found in start() - critical Qt initialization issue")
        else:
            logger.info("QApplication confirmed ready for Qt widget creation")
            if hasattr(self.app, "logger"):
                self.app.logger.info("QApplication confirmed ready for Qt widget creation")

    def stop(self):
        """
        The component stop method.
        """
        # Disconnect the signal to prevent issues on restart
        if self._shutdown_handler:
            try:
                self.qt_app.aboutToQuit.disconnect(self._shutdown_handler)
            except (RuntimeError, TypeError):
                pass # May already be disconnected or gone
        
        if self.qt_app:
            # This will be called as part of the graceful shutdown
            logger.info("PySide6 adapter is stopping.")
            if hasattr(self.app, "logger"):
                self.app.logger.info("PySide6 adapter is stopping.")
        else:
            logger.info("PySide6 adapter stop called but qt_app is None.")
            if hasattr(self.app, "logger"):
                self.app.logger.info("PySide6 adapter stop called but qt_app is None.")
