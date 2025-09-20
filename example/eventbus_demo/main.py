import asyncio
from loguru import logger
from ucore_framework.core.event_bus import EventBus
from ucore_framework.core.event_types import Event

class PrintEvent(Event):
    def __init__(self, message):
        self.message = message
        super().__init__(source="eventbus_demo")

async def print_handler(event):
    logger.info(f"Handled event: {event.message}")

async def background_publisher(bus):
    for i in range(5):
        await asyncio.sleep(1)
        await bus.publish_async(PrintEvent(f"Event #{i+1}"))

async def main():
    bus = EventBus()
    bus.start()  # Start the event bus (not async)
    
    # Subscribe using add_handler method
    bus.add_handler(PrintEvent, print_handler)
    
    logger.info("Starting background event publisher...")
    await background_publisher(bus)
    await asyncio.sleep(2)  # Wait for handlers to finish
    bus.shutdown()  # Properly stop the event bus

if __name__ == "__main__":
    asyncio.run(main())
