"""
UCore Framework Example: Unified Resource Management & Best Practices

This example demonstrates:
- Resource lifecycle management using UnifiedResourceRegistry and a custom Resource subclass
- Async initialization, connection, health check, disconnection, and cleanup
- Logging with loguru
- Progress visualization with tqdm
- Event-driven integration

Usage:
    python -m examples.resource_demo.main

Requirements:
    pip install loguru tqdm

Demonstrates unified resource management, event-driven patterns, and best practices.
"""

from ucore_framework.resource.manager import ResourceManager
from ucore_framework.resource.resource import Resource, ResourceHealth
from ucore_framework.resource.ucore_registry import UCoreResourceRegistry
from ucore_framework.resource.unified_registry import UnifiedResourceRegistry
from ucore_framework.messaging.event_bus import EventBus, Event
from loguru import logger
from tqdm import tqdm
import asyncio

class ResourceLifecycleEvent(Event):
    def __init__(self, resource_name, action):
        self.resource_name = resource_name
        self.action = action

class MockResource(Resource):
    async def _initialize(self):
        logger.info(f"MockResource {self.name}: _initialize called")
        await asyncio.sleep(0.1)

    async def _connect(self):
        logger.info(f"MockResource {self.name}: _connect called")
        await asyncio.sleep(0.1)

    async def _disconnect(self):
        logger.info(f"MockResource {self.name}: _disconnect called")
        await asyncio.sleep(0.1)

    async def _health_check(self):
        logger.info(f"MockResource {self.name}: _health_check called")
        await asyncio.sleep(0.05)
        return ResourceHealth.HEALTHY

    async def _cleanup(self):
        logger.info(f"MockResource {self.name}: _cleanup called")
        await asyncio.sleep(0.05)

async def main_async():
    logger.info("Resource demo started")
    manager = ResourceManager()
    ucore_registry = UCoreResourceRegistry(manager)
    unified_registry = UnifiedResourceRegistry(ucore_registry, ucore_registry)
    event_bus = EventBus()

    resource = MockResource(name="demo_resource", resource_type="demo_type")
    unified_registry.register(resource)
    logger.info(f"Registered resource: {resource.name}")

    # Event handler example
    def on_lifecycle_event(event):
        logger.info(f"Event: Resource {event.resource_name} {event.action}")

    event_bus.add_handler(ResourceLifecycleEvent, on_lifecycle_event)

    steps = [
        ("initialize", resource.initialize),
        ("connect", resource.connect),
        ("health_check", resource.health_check),
        ("disconnect", resource.disconnect),
        ("cleanup", resource.cleanup)
    ]

    for action, coro in tqdm(steps, desc="Resource Lifecycle", unit="step"):
        event_bus.publish(ResourceLifecycleEvent(resource.name, action))
        result = await coro()
        if action == "health_check":
            logger.success(f"Resource {resource.name} health: {result}")
        else:
            logger.success(f"Resource {resource.name} {action} complete, state: {resource.state}")

    logger.success("Resource demo completed")

def main():
    asyncio.run(main_async())

if __name__ == "__main__":
    main()
