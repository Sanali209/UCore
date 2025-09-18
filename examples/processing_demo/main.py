"""
UCore Framework Example: Processing Features & Best Practices

This example demonstrates:
- CPU-bound task with progress bar
- Background task using threading
- Logging with loguru
- Event-driven integration and modular task structure

Usage:
    python -m examples.processing_demo.main

Requirements:
    pip install loguru tqdm

Demonstrates background tasks, CLI, CPU tasks, chains, and event-driven patterns.
"""

from loguru import logger
from tqdm import tqdm
from ucore_framework.messaging.event_bus import EventBus, Event
import threading
import time

class TaskEvent(Event):
    def __init__(self, task_name, action, info=None):
        self.task_name = task_name
        self.action = action
        self.info = info

def cpu_task(n, event_bus):
    logger.info(f"CPU task started: n={n}")
    event_bus.publish(TaskEvent("cpu_task", "started", {"n": n}))
    total = 0
    for i in tqdm(range(n), desc="CPU Task Progress"):
        total += i * i
        time.sleep(0.01)
        if (i + 1) % 5 == 0 or i == n - 1:
            event_bus.publish(TaskEvent("cpu_task", "progress", {"step": i + 1, "total": n}))
    logger.success(f"CPU task completed: result={total}")
    event_bus.publish(TaskEvent("cpu_task", "completed", {"result": total}))
    return total

def background_task(event_bus):
    logger.info("Background task started")
    event_bus.publish(TaskEvent("background_task", "started"))
    for i in tqdm(range(5), desc="Background Progress"):
        time.sleep(0.2)
        logger.debug(f"Background step {i+1}/5")
        event_bus.publish(TaskEvent("background_task", "progress", {"step": i + 1, "total": 5}))
    logger.success("Background task finished")
    event_bus.publish(TaskEvent("background_task", "completed"))

def main():
    logger.info("Processing demo started")
    event_bus = EventBus()

    # Event handler example
    def on_task_event(event):
        logger.info(f"Event: Task '{event.task_name}' {event.action} {event.info if event.info else ''}")

    event_bus.add_handler(TaskEvent, on_task_event)

    # Run CPU-bound task in main thread
    cpu_task(20, event_bus)

    # Run background task in a separate thread
    thread = threading.Thread(target=background_task, args=(event_bus,))
    thread.start()
    thread.join()

    logger.success("Processing demo completed")

if __name__ == "__main__":
    main()
