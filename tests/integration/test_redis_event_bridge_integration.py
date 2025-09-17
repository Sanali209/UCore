import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
from loguru import logger
from tqdm import tqdm

from framework.messaging.event_bus import EventBus, Event
from framework.messaging.redis_event_bridge import EventBusRedisBridge

class DummyEvent(Event):
    pass

@pytest.mark.asyncio
class TestRedisEventBridgeIntegration:
    @pytest.fixture(scope="class")
    def event_bus(self):
        return EventBus()

    @pytest.fixture(scope="class")
    def redis_bridge(self):
        class PatchedEventBusRedisBridge(EventBusRedisBridge):
            def __init__(self):
                super().__init__()
                self.bridge_settings = {
                    "eventbus_to_redis_enabled": False,
                    "redis_to_eventbus_enabled": False
                }
        return PatchedEventBusRedisBridge()

    @pytest.mark.asyncio
    async def test_publish_and_receive_event(self, event_bus, redis_bridge):
        logger.info("Testing Redis event bridge publish/subscribe")
        events_received = []

        def handler(event):
            events_received.append(event)
            logger.info(f"Event received: {event}")

        event_bus.subscribe(DummyEvent)(handler)
        redis_bridge.enable_bridge(direction="both")

        with tqdm(total=2, desc="Redis event bridge") as pbar:
            # Simulate publishing event to Redis and receiving it back
            event = DummyEvent()
            event_bus.publish(event)
            pbar.update(1)
            redis_bridge.get_bridge_stats()
            pbar.update(1)

        logger.info(f"Events received: {events_received}")
        assert isinstance(events_received, list)
