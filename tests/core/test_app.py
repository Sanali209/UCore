# tests/test_app.py
import unittest
from unittest.mock import patch, MagicMock
import sys
import asyncio

from framework.app import App
from framework.core.component import Component

class TestApp(unittest.TestCase):

    def setUp(self):
        """Set up a new App instance for each test."""
        self.app = App(name="TestApp")

    def test_app_initialization(self):
        """Test that the App can be initialized properly."""
        self.assertIsNotNone(self.app.logger)
        self.assertEqual(self.app.logger.name, "TestApp")
        self.assertIsNotNone(self.app.container)
        self.assertIsInstance(self.app._components, list)
        self.assertEqual(len(self.app._components), 0)

    def test_register_component(self):
        """Test component registration."""
        class MockComponent(Component):
            pass

        self.app.register_component(MockComponent)
        self.assertEqual(len(self.app._components), 1)
        self.assertIsInstance(self.app._components[0], MockComponent)
        # Test that the component has a reference to the app
        self.assertIs(self.app._components[0].app, self.app)

    @patch('argparse.ArgumentParser')
    def test_bootstrap(self, mock_arg_parser):
        """Test that the App can bootstrap without running the event loop."""
        mock_args = MagicMock()
        mock_args.config = None
        mock_args.log_level = "DEBUG"
        mock_args.plugins_dir = None
        mock_arg_parser.return_value.parse_args.return_value = mock_args

        try:
            self.app.bootstrap(mock_args)
            self.assertIsNotNone(self.app.logger)
            self.assertEqual(self.app.logger.name, "TestApp")
        except Exception as e:
            self.fail(f"App.bootstrap() raised an exception unexpectedly: {e}")

    @patch('asyncio.Event.wait')
    def test_start_and_stop_components(self, mock_event_wait):
        """Test component lifecycle management."""
        class TestComponent(Component):
            def __init__(self, app: App):
                super().__init__(app)
                self.started = False
                self.stopped = False

            async def start(self):
                self.started = True

            async def stop(self):
                self.stopped = True
        
        self.app.register_component(TestComponent)
        component_instance = self.app._components[0]

        async def test_lifecycle():
            # We patch the event wait to prevent the main loop from blocking
            await self.app._main_loop()
            await self.app.stop()

        asyncio.run(test_lifecycle())

        self.assertTrue(component_instance.started)
        self.assertTrue(component_instance.stopped)

if __name__ == '__main__':
    unittest.main()
