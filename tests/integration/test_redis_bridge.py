import pytest
import asyncio
from unittest.mock import AsyncMock
from ucore_framework.core.redis_adapter import RedisAdapter

@pytest.mark.asyncio
async def test_pubsub_roundtrip():
    # Setup
    class MockApp:
        def __init__(self):
            self.container = {}
            self.logger = AsyncMock()
    app = MockApp()
    adapter = RedisAdapter(app)
    await adapter.start()

    received = asyncio.Event()
    received_data = {}

    @adapter.subscribe("test-channel")
    async def handler(msg):
        received_data["msg"] = msg
        received.set()

    # Publish a message
    await adapter.publish("test-channel", {"foo": "bar"})
    await asyncio.wait_for(received.wait(), timeout=2)
    assert received_data["msg"]["foo"] == "bar"

    await adapter.stop()
