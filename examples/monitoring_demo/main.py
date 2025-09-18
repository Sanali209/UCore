"""
UCore Framework Example: Monitoring Features & Best Practices

This example demonstrates:
- Logging with loguru
- Metrics collection with Prometheus Counter
- Progress visualization with tqdm and TqdmProgressVisualizer
- Event-driven integration and unified registration

Usage:
    python -m examples.monitoring_demo.main

Requirements:
    pip install loguru prometheus_client tqdm

Demonstrates logging, metrics, observability, progress tracking, and event-driven patterns.
"""

from loguru import logger
from tqdm import tqdm
from prometheus_client import Counter
from UCoreFrameworck.monitoring.progress import TqdmProgressVisualizer
from UCoreFrameworck.messaging.event_bus import EventBus, Event
import time

class MetricUpdatedEvent(Event):
    def __init__(self, metric_name, value):
        self.metric_name = metric_name
        self.value = value

class ProgressStepEvent(Event):
    def __init__(self, step, total, description):
        self.step = step
        self.total = total
        self.description = description

def main():
    logger.info("Monitoring demo started")
    event_bus = EventBus()

    # Metric event handler
    def on_metric_updated(event):
        logger.info(f"Event: Metric '{event.metric_name}' updated to {event.value}")

    event_bus.add_handler(MetricUpdatedEvent, on_metric_updated)

    # Progress event handler
    def on_progress_step(event):
        logger.info(f"Event: Progress {event.step}/{event.total} - {event.description}")

    event_bus.add_handler(ProgressStepEvent, on_progress_step)

    # Metrics demo using Prometheus Counter
    demo_counter = Counter('demo_counter', 'Demo metric counter')
    demo_counter.inc()
    event_bus.publish(MetricUpdatedEvent('demo_counter', demo_counter._value.get()))
    logger.info(f"Metric 'demo_counter' incremented: {demo_counter._value.get()}")

    # Progress tracking demo with tqdm
    total = 10
    progress = TqdmProgressVisualizer(max_progress=total, description="Demo Progress")
    for i in tqdm(range(total), desc="Processing"):
        time.sleep(0.1)
        progress.update_progress(i + 1, total, f"Step {i+1}", "Demo Progress")
        event_bus.publish(ProgressStepEvent(i + 1, total, f"Step {i+1}"))

    logger.success("Monitoring demo completed")

if __name__ == "__main__":
    main()
