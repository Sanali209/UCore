"""
UCore Framework Example: Messaging Features

Demonstrates event bus, events, and Redis integration.
"""

from ucore_framework.messaging.event_bus import EventBus
from ucore_framework.messaging.events import Event
from ucore_framework.messaging.redis_adapter import RedisAdapter

class MyEvent(Event):
    def __init__(self, message):
        super().__init__()
        self.message = message

def main():
    # EventBus demo
    event_bus = EventBus()
    @event_bus.subscribe(MyEvent)
    def handler(event):
        print("Event received:", event.message)
    event_bus.start()
    event_bus.publish(MyEvent("Hello from EventBus!"))

    # Redis integration demo (mocked)
    class MockApp:
        def __init__(self):
            self.container = {}
            self.logger = type("Logger", (), {"info": print, "warning": print, "error": print, "debug": print})()
    redis_adapter = RedisAdapter(app=MockApp())
    print("RedisAdapter initialized:", redis_adapter)

    print("In a real app, the event bus and adapters would be registered and started by the UCoreFrameworck.")

if __name__ == "__main__":
    main()
