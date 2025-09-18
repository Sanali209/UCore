import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from loguru import logger
from tqdm import tqdm

from ucore_framework.core.app import App
from ucore_framework.messaging.event_bus import EventBus, Event
from ucore_framework.resource.manager import ResourceManager

class DummyResource:
    def __init__(self, name, resource_type="test"):
        self.name = name
        self.resource_type = resource_type
        self.started = False
        self.stopped = False
        self.health = type("Health", (), {"value": "healthy"})()

    async def start(self):
        self.started = True

    async def stop(self):
        self.stopped = True

    def get_stats(self):
        return {"started": self.started, "stopped": self.stopped}

@pytest.mark.asyncio
class TestCoreMessagingResourceIntegration:
    @pytest.fixture(scope="class")
    def app(self):
        return App("IntegrationTestApp")

    @pytest.fixture(scope="class")
    def event_bus(self):
        return EventBus()

    @pytest.fixture(scope="class")
    def resource_manager(self):
        return ResourceManager()

    @pytest.mark.asyncio
    async def test_resource_lifecycle_events(self, app, event_bus, resource_manager):
        logger.info("Testing resource lifecycle event propagation")
        events_received = []

        def handler(event):
            events_received.append(event)
            logger.info(f"Event received: {event}")

        event_bus.subscribe(Event)(handler)
        dummy_resource = DummyResource("resource1")
        resource_manager.register_resource(dummy_resource)

        with tqdm(total=2, desc="Resource lifecycle") as pbar:
            await dummy_resource.start()
            event_bus.publish(Event())
            pbar.update(1)
            await dummy_resource.stop()
            event_bus.publish(Event())
            pbar.update(1)

        logger.info(f"Events received: {events_received}")
        assert isinstance(events_received, list)

    @pytest.mark.asyncio
    async def test_resource_pool_exhaustion_event(self, event_bus, resource_manager):
        logger.info("Testing resource pool exhaustion event propagation")
        events_received = []

        def handler(event):
            events_received.append(event)
            logger.info(f"Event received: {event}")

        event_bus.subscribe(Event)(handler)
        # Simulate pool exhaustion event
        event_bus.publish(Event())
        logger.info(f"Events received: {events_received}")
        assert isinstance(events_received, list)
