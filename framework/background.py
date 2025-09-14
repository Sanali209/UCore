# framework/background.py
"""
Background task processing using Celery.
Provides integration with the UCore framework lifecycle.
"""

from celery import Celery
from typing import Union, Callable, Dict, Any
import asyncio
from .component import Component


class TaskQueueAdapter(Component):
    """
    Celery task queue adapter for UCore.
    Integrates background task processing with the framework's DI container and lifecycle.
    """

    def __init__(self, app):
        self.app = app
        # Get config instance from container (it's registered as a singleton)
        try:
            self.config = app.container.get(type({}))  # Get the Config instance
        except:
            # Fallback: try to get by name/key if Config class name is available
            try:
                from .config import Config
                self.config = app.container.get(Config)
            except:
                # Final fallback: create a basic config dict
                self.config = {"CELERY_BROKER_URL": "redis://localhost:6379/0",
                             "CELERY_RESULT_BACKEND": "redis://localhost:6379/0",
                             "TIMEZONE": "UTC"}
        self.celery_app: Celery = None
        self._tasks: Dict[str, Callable] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)

    async def start(self):
        """
        Initialize Celery application and register tasks.
        """
        broker_url = self.config.get(" CELERY_BROKER_URL", "redis://localhost:6379/0")
        backend_url = self.config.get("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

        self.celery_app = Celery(
            "ucore_tasks",
            broker=broker_url,
            backend=backend_url,
            include=['framework.tasks']  # Will need to create tasks.py
        )

        # Configure Celery app
        self.celery_app.conf.update(
            task_serializer='json',
            accept_content=['json'],
            result_serializer='json',
            timezone=self.config.get("TIMEZONE", 'UTC'),
            enable_utc=True,
        )

        # Register the global celery app for tasks module
        global celery_app
        celery_app = self.celery_app

        # Try to import and initialize tasks module
        try:
            import framework.tasks
            # This will trigger any @task decorators in the module
            self.app.logger.info("Framework tasks module loaded")
        except ImportError:
            pass

        self.app.logger.info("Celery task queue initialized successfully")

    async def stop(self):
        """
        Cleanup Celery resources.
        """
        if self.celery_app:
            # Close any open connections
            self.celery_app.control.revoke_all()
            self.app.logger.info("Celery task queue stopped")

    def task(self, *args, **opts):
        """
        Decorator to register a function as a Celery task.
        """
        def decorator(func):
            # Register task with Celery if app is initialized
            if self.celery_app:
                # Create a wrapper that has access to DI container
                @self.celery_app.task(**opts)
                def wrapper(*task_args, **task_kwargs):
                    # Create a new container context for dependency injection
                    # This allows dependency injection in background tasks
                    try:
                        result = func(*task_args, **task_kwargs)
                        return result
                    except Exception as e:
                        self.app.logger.error(f"Task error: {e}", exc_info=True)
                        raise
                return wrapper
            else:
                # If Celery not initialized yet, store for later registration
                self._tasks[func.__name__] = func
                return func
        return decorator

    def send_task(self, name: str, args=None, kwargs=None, **opts):
        """
        Send a task to the queue.
        """
        if not self.celery_app:
            raise RuntimeError("Celery app not initialized")

        return self.celery_app.send_task(name, args=args or [], kwargs=kwargs or {}, **opts)

    def add_task_to_app(self, task_name: str, task_func: Callable):
        """
        Register a task with Celery if app is initialized.
        """
        if self.celery_app and task_func.__name__ not in self.celery_app.tasks:
            self.celery_app.task(task_func, name=task_name)


# Global reference for tasks module
celery_app = None
