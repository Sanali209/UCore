import pytest
import asyncio
import os
import signal
from unittest.mock import AsyncMock
from ucore_framework.core.app import App, Component

@pytest.mark.asyncio
async def test_full_app_lifecycle():
    class MockComponent(Component):
        def __init__(self):
            super().__init__(name="mock")
        def start(self):
            pass
        def stop(self):
            pass

    mock_component = MockComponent()
    mock_component.start = AsyncMock()
    mock_component.stop = AsyncMock()

    app = App(name="test_app")
    app.register_component(mock_component)

    async def run_app():
        await app._main_loop()

    task = asyncio.create_task(run_app())
    await asyncio.sleep(0.1)
    os.kill(os.getpid(), signal.SIGINT)
    await task

    mock_component.start.assert_awaited_once()
    mock_component.stop.assert_awaited_once()
