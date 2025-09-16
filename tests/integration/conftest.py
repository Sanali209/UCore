"""
Integration test fixtures and configuration for UCore framework.

This module provides real system components for comprehensive integration testing
rather than mocked components used in unit tests.
"""

import pytest
import asyncio
import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Iterator, AsyncGenerator

from framework.core.app import App
from framework.core.config import Config
from framework.core.di import Container
from framework.messaging.events import Event, ComponentStartedEvent, ComponentStoppedEvent


class TestApp(App):
    """
    Specialized app instance for integration testing.

    Provides real component integration with test-specific configuration.
    """

    def __init__(self, name: str = "TestApp"):
        super().__init__(name)
        self.test_mode = True
        self.test_data = {}
        # Register and start database adapters for integration tests
        try:
            from framework.data.db import SQLAlchemyAdapter
            from framework.data.mongo_adapter import MongoDBAdapter
            self.container.register(SQLAlchemyAdapter)
            self.container.register(MongoDBAdapter)
            # Instantiate and start adapters so they appear in _components
            self._components = []
            for Adapter in [SQLAlchemyAdapter, MongoDBAdapter]:
                try:
                    adapter_instance = Adapter(self)
                    self._components.append(adapter_instance)
                except Exception as e:
                    print(f"DEBUG: Failed to instantiate {Adapter}: {e}")
        except Exception as e:
            print("DEBUG: Failed to register DB adapters in TestApp:", e)

    async def _main_loop(self):
        """
        Override main loop for testing - runs until stopped.
        """
        while not self._shutdown_event.is_set():
            await asyncio.sleep(0.1)
            # Allow test to control shutdown
            if hasattr(self, '_test_shutdown_flag'):
                break

    def test_shutdown(self):
        """Trigger test shutdown."""
        self._test_shutdown_flag = True
        if hasattr(self, '_shutdown_event'):
            self._shutdown_event.set()

    def get_component_status(self, component_name: str) -> Dict[str, Any]:
        """Get component health status for testing."""
        for event in self.events.get_by_type(ComponentStartedEvent):
            if getattr(event, 'component_name', None) == component_name:
                return {'status': 'healthy', 'last_started': event.timestamp}

        for event in self.events.get_by_type(ComponentStoppedEvent):
            if getattr(event, 'component_name', None) == component_name:
                return {'status': 'stopped', 'last_stopped': event.timestamp}

        return {'status': 'unknown'}


@pytest.fixture(scope="session")
def event_loop():
    """
    Create and teardown the asyncio event loop for session scope.

    This ensures all async tests use the same event loop.
    """
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def integration_app():
    """
    Create a real UCore application instance with all components.

    This fixture provides a fully functional application for integration testing.
    """
    # Create test configuration
    test_config = {
        "DATABASE_URL": "sqlite+aiosqlite:///./test_ucore.db",
        "REDIS_HOST": "redis-16460.c1.asia-northeast1-1.gce.cloud.redislabs.com",
        "REDIS_PORT": 16460,
        "REDIS_PASSWORD": None,
        "HTTP_HOST": "localhost",
        "HTTP_PORT": 8081,
        "LOG_LEVEL": "INFO",
        "DEBUG_MODE": True,
        "TEST_MODE": True
    }

    # Initialize application
    app = TestApp("IntegrationTestApp")

    # Override default configuration for testing
    config = Config()
    config.load_from_dict(test_config)
    # Register config as instance, not as type
    app.container.register_instance(config)

    import argparse
    try:
        # Bootstrap the application (will register all components)
        result = app.bootstrap(argparse.Namespace(log_level="INFO", config=None, plugins_dir=None))
        if asyncio.iscoroutine(result):
            await result

        # Wait a moment for all components to initialize
        await asyncio.sleep(0.5)

        yield app

    finally:
        # Ensure proper cleanup
        try:
            await app.stop()
        except Exception:
            pass  # Ignore cleanup errors in tests


@pytest.fixture(scope="function")
async def fresh_app():
    """
    Create a fresh application instance for each test function.

    Provides clean isolation between tests.
    """
    app = TestApp("FreshTestApp")

    try:
        # Basic configuration
        config = Config()
        config.load_from_dict({
            "DATABASE_URL": "sqlite+aiosqlite:///./test_fresh.db",
            "HTTP_HOST": "localhost",
            "HTTP_PORT": 8082,
        })
        app.container.register_instance(Config, config)

        yield app

    finally:
        try:
            await app.stop()
        except Exception:
            pass


@pytest.fixture(scope="session")
def temp_dir():
    """
    Create a temporary directory for test files.

    This directory is cleaned up after all tests complete.
    """
    temp_path = tempfile.mkdtemp(prefix="ucore_integration_")
    yield temp_path

    # Cleanup after tests
    import shutil
    shutil.rmtree(temp_path, ignore_errors=True)


@pytest.fixture(scope="function")
def clean_temp_files():
    """
    Ensure no temporary test files persist between tests.
    """
    temp_files = []
    yield temp_files

    # Cleanup any created
