import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from unittest.mock import Mock
from ucore_framework.core.app import App
from ucore_framework.core.component import Component
from ucore_framework.core.config import Config
from ucore_framework.monitoring.logging import Logging


@pytest.fixture
def sample_app():
    """Create a sample App instance for core testing."""
    app = App("TestApp")
    return app


@pytest.fixture
def async_component(sample_app):
    """Base test component for testing async lifecycle."""
    class TestAsyncComponent(Component):
        def __init__(self, app=None):
            super().__init__(app)
            self.start_called = False
            self.stop_called = False
            self.config_updated = False

        def start(self):
            self.start_called = True

        def stop(self):
            self.stop_called = True

        def on_config_update(self, config):
            self.config_updated = True

    return TestAsyncComponent(sample_app)


@pytest.fixture
def sync_component(sample_app):
    """Test component for testing sync lifecycle."""
    class TestSyncComponent(Component):
        def __init__(self, app=None):
            super().__init__(app)
            self.start_called = False
            self.stop_called = False

        def start(self):
            self.start_called = True

        def stop(self):
            self.stop_called = True

    return TestSyncComponent(sample_app)
