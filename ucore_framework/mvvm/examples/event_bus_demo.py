from ucore_framework.mvvm.base import ViewModelBase

class SimpleEventBus:
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, event_type: str, handler):
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event_type: str, event):
        for handler in self._subscribers.get(event_type, []):
            handler(event)

class IncrementedEvent:
    def __init__(self, new_value):
        self.new_value = new_value

class CounterViewModel(ViewModelBase):
    def __init__(self, event_bus: SimpleEventBus):
        super().__init__()
        self.set_property("count", 0)
        self.event_bus = event_bus

    def increment(self):
        new_count = self.get_property("count") + 1
        self.set_property("count", new_count)
        self.event_bus.publish("counter.incremented", IncrementedEvent(new_count))

# Example usage
if __name__ == "__main__":
    bus = SimpleEventBus()
    def on_incremented(event):
        print(f"Counter incremented to {event.new_value}")
    bus.subscribe("counter.incremented", on_incremented)

    vm = CounterViewModel(bus)
    vm.increment()
    vm.increment()
