# tests/test_ui_adapters.py
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from PySide6.QtWidgets import QApplication, QWidget
import qasync
import flet as ft

from framework.app import App
from framework.ui.pyside6_adapter import PySide6Adapter
from framework.ui.flet_adapter import FletAdapter
from framework.config import Config

@pytest.fixture
def ucore_app():
    """Fixture to create a new App instance for each test."""
    return App(name="TestUIApp")

def test_pyside6_adapter_initialization(ucore_app):
    """
    Tests that the PySide6Adapter correctly initializes the QApplication
    and provides a QEventLoop.
    """
    adapter = PySide6Adapter(ucore_app)
    ucore_app.register_component(adapter)

    # Manually trigger the loop selection logic from the App.run() method
    loop = adapter.get_event_loop()
    
    assert QApplication.instance() is not None
    assert isinstance(loop, qasync.QEventLoop)
    
    # Clean up the QApplication instance
    QApplication.quit()

def test_pyside6_adapter_widget_creation_with_di(ucore_app):
    """
    Tests the dependency injection capability of the PySide6Adapter.
    """
    # A dummy class that needs a Config dependency
    class MyWidget(QWidget):
        def __init__(self, config: Config):
            super().__init__()
            self.config = config

    adapter = PySide6Adapter(ucore_app)
    ucore_app.register_component(adapter)

    # Use the factory method to create the widget
    widget_instance = adapter.create_widget(MyWidget)

    assert isinstance(widget_instance, MyWidget)
    assert isinstance(widget_instance.config, Config)
    
    # Clean up
    QApplication.quit()

@pytest.mark.asyncio
async def test_flet_adapter_start_and_stop(ucore_app):
    """
    Tests that the FletAdapter correctly schedules and cancels its task.
    """
    # Mock the flet app_async function using AsyncMock to avoid actually starting a web server
    mock_coro = AsyncMock()
    with patch.object(ft, 'app_async', return_value=mock_coro) as mock_flet_app:
        # Dummy target function for Flet
        def flet_target(page):
            pass

        adapter = FletAdapter(ucore_app, target_func=flet_target)

        # The App's start method is now async
        await adapter.start()

        # Check that a task was created
        assert adapter._flet_task is not None
        assert isinstance(adapter._flet_task, asyncio.Task)

        # Check that flet.app_async was called
        mock_flet_app.assert_called_once()

        # Cancel the task to simulate proper cleanup
        adapter._flet_task.cancel()
