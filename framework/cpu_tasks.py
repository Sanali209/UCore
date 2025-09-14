import functools
from concurrent.futures import ThreadPoolExecutor, Future
from PySide6.QtCore import QMetaObject, Qt, QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication
from .component import Component
from .config import Config


class QtCallbackInvoker(QObject):
    """
    A Qt QObject that handles thread-safe callback invocation.
    """

    # Signal for triggering callbacks
    invoke = Signal(object, object)  # callback, arguments

    def __init__(self, parent=None):
        super().__init__(parent)
        self.invoke.connect(self._do_invoke)

    def _do_invoke(self, callback, args):
        """Actually execute the callback with the provided arguments."""
        try:
            if isinstance(args, (list, tuple)):
                callback(*args)
            else:
                callback(args)
        except Exception as e:
            print(f"Callback execution error: {e}")

    def invoke_callback(self, callback, args):
        """Public method to trigger callback invocation."""
        if isinstance(args, (list, tuple)):
            self.invoke.emit(callback, args)
        else:
            self.invoke.emit(callback, args)


class ConcurrentFuturesAdapter(Component):
    """
    Framework component for managing concurrent tasks with ThreadPoolExecutor.
    Provides Qt-safe threading utilities for UI applications.
    """

    def __init__(self, app):
        self.app = app
        self.executor = None
        self.max_workers = 4
        self.timeout = 30.0
        self.callback_invoker = None

    def start(self):
        """
        Initialize the ThreadPoolExecutor with config values.
        """
        try:
            config = self.app.container.get(Config)
            self.max_workers = config.get("CONCURRENT_WORKERS", 4)
            self.timeout = config.get("CONCURRENT_TIMEOUT", 30.0)
        except Exception as e:
            self.app.logger.warning(f"Could not get config for ConcurrentFuturesAdapter: {e}, using defaults")

        self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="UCore-CPU")

        # Initialize Qt callback invoker for thread-safe operations
        self.callback_invoker = QtCallbackInvoker()

        self.app.logger.info(f"ConcurrentFuturesAdapter started with {self.max_workers} workers")

    def stop(self):
        """
        Shutdown the ThreadPoolExecutor cleanly.
        """
        if self.executor:
            self.app.logger.info("Shutting down ThreadPoolExecutor...")
            self.executor.shutdown(wait=True)
            self.app.logger.info("ConcurrentFuturesAdapter stopped")

    def update_config(self, workers=None, timeout=None):
        """
        Update configuration at runtime and restart executor if workers change.
        """
        needs_restart = False

        if workers is not None and workers != self.max_workers:
            self.max_workers = workers
            needs_restart = True

        if timeout is not None:
            self.timeout = timeout

        if needs_restart:
            # Shutdown current executor
            if self.executor:
                self.app.logger.info(f"Restarting ThreadPoolExecutor with {self.max_workers} workers")
                self.executor.shutdown(wait=True)

            # Start new executor with updated settings
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers, thread_name_prefix="UCore-CPU")
        self.app.logger.info(f"ConcurrentFuturesAdapter restarted with {self.max_workers} workers")

    def on_config_update(self, config):
        """
        Handle runtime configuration updates.
        """
        # Get updated configuration values
        new_workers = config.get("CONCURRENT_WORKERS")
        new_timeout = config.get("CONCURRENT_TIMEOUT")

        # Apply changes if they differ from current values
        if new_workers != self.max_workers or new_timeout != self.timeout:
            self.app.logger.info(f"Updating concurrent adapter: workers={new_workers}, timeout={new_timeout}")
            self.update_config(workers=new_workers, timeout=new_timeout)

    def submit_task(self, func, *args, **kwargs):
        """
        Submit a task to the executor.
        Returns a Future object.
        """
        if not self.executor:
            raise RuntimeError("ThreadPoolExecutor not initialized. Call start() first.")

        return self.executor.submit(func, *args, **kwargs)

    def submit_with_callback(self, func, success_callback=None, error_callback=None, timeout=None, *args, **kwargs):
        """
        Submit a task with Qt-safe callbacks.
        Callbacks will be invoked in the main thread.
        """
        if not self.executor:
            raise RuntimeError("ThreadPoolExecutor not initialized. Call start() first.")

        # Remove unsupported parameters to avoid errors
        filtered_kwargs = {k: v for k, v in kwargs.items()
                          if k in ['query', 'max_results', 'result', 'download_path', 'base_filename']}

        task_timeout = timeout or self.timeout
        future = self.executor.submit(func, *args, **filtered_kwargs)

        def on_future_done(fut):
            try:
                result = fut.result(timeout=task_timeout)
                if success_callback:
                    # Use Qt signal-slot mechanism for thread-safe callback
                    self.callback_invoker.invoke_callback(success_callback, result)
            except Exception as e:
                if error_callback:
                    # Use Qt signal-slot mechanism for thread-safe error callback
                    self.callback_invoker.invoke_callback(error_callback, e)
                else:
                    self.app.logger.error(f"Task execution error: {e}", exc_info=True)

        future.add_done_callback(on_future_done)

    def _get_qt_app(self):
        """
        Get the Qt application instance (fallback if not available in app).
        """
        # This is a fallback - ideally the app should have qt_app set
        # For example, in PySide6Adapter, qt_app is available
        pass

    def invoke_in_main_thread(self, callable):
        """
        Utility to run a callable in the main thread safely.
        """
        # Assume there's a Qt app instance
        # This would need to be connected in the application startup
        pass


def create_concurrent_adapter():
    """
    Factory function for dependency injection.
    """
    def factory(app):
        adapter = ConcurrentFuturesAdapter(app)
        return adapter
    return factory
