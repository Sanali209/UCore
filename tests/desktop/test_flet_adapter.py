import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, call
import flet as ft

from UCoreFrameworck.desktop.ui.flet.flet_adapter import FletAdapter


class TestFletAdapterInitialization:
    """Test FletAdapter initialization."""

    def test_init(self):
        """Test basic initialization."""
        app = Mock()
        target_func = Mock()

        adapter = FletAdapter(app, target_func)

        assert adapter.app == app
        assert adapter._target == target_func
        assert adapter._port == 8085  # default port
        assert adapter._flet_task is None

    def test_init_custom_port(self):
        """Test initialization with custom port."""
        app = Mock()
        target_func = Mock()

        adapter = FletAdapter(app, target_func, port=9090)

        assert adapter._port == 9090


class TestFletAdapterLifecyle:
    """Test FletAdapter start/stop lifecycle."""

    @patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async')
    def test_start_success(self, mock_app_async):
        """Test successful start of Flet application."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        target_func = Mock()
        adapter = FletAdapter(app, target_func, port=8080)

        # Mock the async task creation
        mock_task = Mock()
        mock_loop = Mock()
        mock_loop.create_task.return_value = mock_task

        with patch('asyncio.get_running_loop', return_value=mock_loop):
            asyncio.run(adapter.start())

        # Verify Flet app_async was called correctly
        mock_app_async.assert_called_once_with(
            target=target_func,
            port=8080,
            view=ft.WEB_BROWSER
        )

        # Verify task was created
        mock_loop.create_task.assert_called_once()

        # Verify logging
        logger.info.assert_any_call("Scheduling Flet app on port 8080...")
        logger.info.assert_any_call("Flet app is scheduled to run as a background task.")

        # Verify task was stored
        assert adapter._flet_task == mock_task

    @pytest.mark.asyncio
    async def test_start_async_context(self):
        """Test start in async context."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        target_func = Mock()
        adapter = FletAdapter(app, target_func, port=8080)

        # Mock the async task creation
        mock_task = Mock()
        mock_loop = Mock()
        mock_loop.create_task.return_value = mock_task

        with patch('asyncio.get_running_loop', return_value=mock_loop), \
             patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async') as mock_app_async:

            await adapter.start()

            mock_app_async.assert_called_once()
            mock_loop.create_task.assert_called_once()

    def test_stop_with_running_task(self):
        """Test stop method when task is running."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = FletAdapter(app, Mock())
        mock_task = Mock()
        mock_task.done.return_value = False
        adapter._flet_task = mock_task

        adapter.stop()

        # Verify task was cancelled
        mock_task.cancel.assert_called_once()

        # Verify logging
        logger.info.assert_called_once_with("Flet app task cancellation requested.")

    def test_stop_with_completed_task(self):
        """Test stop method when task is already completed."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = FletAdapter(app, Mock())
        mock_task = Mock()
        mock_task.done.return_value = True  # Task is done
        adapter._flet_task = mock_task

        adapter.stop()

        # Verify task was not cancelled since it's already done
        mock_task.cancel.assert_not_called()

        # Verify appropriate log message
        logger.info.assert_called_once_with("Flet app was not running or already stopped.")

    def test_stop_with_no_task(self):
        """Test stop method when no task has been created."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = FletAdapter(app, Mock())
        adapter._flet_task = None

        adapter.stop()

        # Verify appropriate log message
        logger.info.assert_called_once_with("Flet app was not running or already stopped.")


class TestFletAdapterErrorHandling:
    """Test FletAdapter error handling scenarios."""

    @pytest.mark.asyncio
    @patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async')
    async def test_start_with_flet_error(self, mock_app_async):
        """Test handling of errors during Flet app initialization."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        target_func = Mock()
        adapter = FletAdapter(app, target_func, port=8080)

        # Mock error during task creation
        mock_loop = Mock()
        mock_loop.create_task.side_effect = Exception("Task creation failed")

        with patch('asyncio.get_running_loop', return_value=mock_loop):
            with pytest.raises(Exception, match="Task creation failed"):
                await adapter.start()

        # Verify logging still occurred
        logger.info.assert_called()


class TestFletAdapterIntegration:
    """Test FletAdapter integration scenarios."""

    @pytest.mark.asyncio
    @patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async')
    async def test_multiple_start_stop_cycles(self, mock_app_async):
        """Test multiple start/stop cycles."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        target_func = Mock()
        adapter = FletAdapter(app, target_func, port=8080)

        # First start
        mock_task1 = Mock()
        mock_loop1 = Mock()
        mock_loop1.create_task.return_value = mock_task1

        with patch('asyncio.get_running_loop', return_value=mock_loop1):
            await adapter.start()

            assert adapter._flet_task == mock_task1

        # First stop
        adapter.stop()

        # Second start should create new task
        mock_task2 = Mock()
        mock_loop2 = Mock()
        mock_loop2.create_task.return_value = mock_task2

        with patch('asyncio.get_running_loop', return_value=mock_loop2):
            await adapter.start()

            assert adapter._flet_task == mock_task2

    @pytest.mark.asyncio
    @patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async')
    async def test_default_port_usage(self, mock_app_async):
        """Test that default port (8085) is used when not specified."""
        app = Mock()
        target_func = Mock()
        adapter = FletAdapter(app, target_func)

        mock_task = Mock()
        mock_loop = Mock()
        mock_loop.create_task.return_value = mock_task

        with patch('asyncio.get_running_loop', return_value=mock_loop):
            await adapter.start()

            # Verify default port was used
            mock_app_async.assert_called_once_with(
                target=target_func,
                port=8085,
                view=ft.WEB_BROWSER
            )

    def test_component_inheritance(self):
        """Test that FletAdapter properly inherits from Component."""
        from UCoreFrameworck.core.component import Component

        app = Mock()
        target_func = Mock()
        adapter = FletAdapter(app, target_func)

        # Should be an instance of Component
        assert isinstance(adapter, Component)
        assert hasattr(adapter, 'start')  # Should have Component methods
        assert hasattr(adapter, 'stop')   # Should have Component methods

    @pytest.mark.asyncio
    async def test_task_storage(self):
        """Test that the task is properly stored for lifecycle management."""
        app = Mock()
        target_func = Mock()
        adapter = FletAdapter(app, target_func)

        mock_task = Mock()
        mock_task.done.return_value = False  # Ensure cancel will be called
        mock_loop = Mock()
        mock_loop.create_task.return_value = mock_task

        with patch('asyncio.get_running_loop', return_value=mock_loop), \
             patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async'):

            await adapter.start()
            assert adapter._flet_task is not None
            assert adapter._flet_task == mock_task

            # Test accessing stored task in stop
            adapter.stop()
            mock_task.cancel.assert_called_once()

    @pytest.mark.asyncio
    @patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async')
    async def test_different_target_functions(self, mock_app_async):
        """Test with different target functions."""
        app = Mock()

        # Test with different function types
        def sync_target(page):
            pass

        async def async_target(page):
            pass

        lambda_target = lambda page: None

        targets = [sync_target, async_target, lambda_target]

        for target in targets:
            adapter = FletAdapter(app, target)

            mock_task = Mock()
            mock_loop = Mock()
            mock_loop.create_task.return_value = mock_task

            with patch('asyncio.get_running_loop', return_value=mock_loop):
                await adapter.start()

                # Each should have called app_async with the respective target
                assert adapter._target == target
                mock_app_async.assert_called_with(
                    target=target,
                    port=8085,
                    view=ft.WEB_BROWSER
                )

    @pytest.mark.asyncio
    @patch('UCoreFrameworck.desktop.ui.flet.flet_adapter.ft.app_async')
    async def test_port_range_variations(self, mock_app_async):
        """Test adapter with various port numbers."""
        app = Mock()
        target_func = Mock()

        test_ports = [3000, 5000, 8080, 9000, 9999]

        for port in test_ports:
            adapter = FletAdapter(app, target_func, port=port)

            mock_task = Mock()
            mock_loop = Mock()
            mock_loop.create_task.return_value = mock_task

            with patch('asyncio.get_running_loop', return_value=mock_loop):
                await adapter.start()

                mock_app_async.assert_called_with(
                    target=target_func,
                    port=port,
                    view=ft.WEB_BROWSER
                )
