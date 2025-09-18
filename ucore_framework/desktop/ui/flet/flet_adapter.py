# framework/ui/flet_adapter.py
import flet as ft
import asyncio
from ucore_framework.core.component import Component

class FletAdapter(Component):
    """
    An adapter to run a Flet web application as a component.
    """
    def __init__(self, app, target_func, port=8085):
        self.app = app
        self._target = target_func
        self._port = port
        self._flet_task = None

    async def start(self):
        """
        Starts the Flet application as a background task on the main event loop.
        """
        self.app.logger.info(f"Scheduling Flet app on port {self._port}...")
        
        # Get the currently running event loop from the main app
        loop = asyncio.get_running_loop()
        
        # Schedule the flet app to run as a background task
        self._flet_task = loop.create_task(
            ft.app_async(
                target=self._target,
                port=self._port,
                view=ft.WEB_BROWSER
            )
        )
        self.app.logger.info("Flet app is scheduled to run as a background task.")

    def stop(self):
        """
        Cancels the Flet background task.
        """
        if self._flet_task and not self._flet_task.done():
            self._flet_task.cancel()
            self.app.logger.info("Flet app task cancellation requested.")
        else:
            self.app.logger.info("Flet app was not running or already stopped.")
