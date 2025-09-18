"""
Example: Using UCore framework business metrics decorators and visualizing metrics

Requirements:
- prometheus-client
- matplotlib
"""

import time
import threading
import requests
import matplotlib.pyplot as plt
from UCoreFrameworck.monitoring.metrics import counter, histogram

# Define a business metric using the counter decorator
from prometheus_client import Counter, Histogram

example_counter = Counter('example_counter', 'Example business event counter', ['event_type'])
example_duration = Histogram('example_duration_seconds', 'Example event duration', ['event_type'])

def process_event(event_type):
    time.sleep(0.1)
    example_counter.labels(event_type=event_type).inc()

def process_event_with_duration(event_type):
    start = time.time()
    time.sleep(0.1 + 0.05 * (ord(event_type[0]) % 3))
    duration = time.time() - start
    example_duration.labels(event_type=event_type).observe(duration)

def run_metrics_server():
    from prometheus_client import start_http_server
    start_http_server(9000)
    print("Prometheus metrics available at http://localhost:9000/metrics")
    while True:
        time.sleep(1)

def simulate_events():
    for i in range(10):
        event_type = "A" if i % 2 == 0 else "B"
        process_event(event_type)
        process_event_with_duration(event_type)

def scrape_and_plot():
    # Scrape metrics from the Prometheus endpoint
    url = "http://localhost:9000/metrics"
    time.sleep(2)
    response = requests.get(url)
    lines = response.text.splitlines()
    # Parse counter and histogram values
    counter_a, counter_b = 0, 0
    durations_a, durations_b = [], []
    for line in lines:
        if line.startswith("example_counter_total"):
            if 'event_type="A"' in line:
                counter_a = float(line.split()[-1])
            elif 'event_type="B"' in line:
                counter_b = float(line.split()[-1])
        if line.startswith("example_duration_seconds_bucket"):
            if 'event_type="A"' in line:
                durations_a.append(float(line.split()[-1]))
            elif 'event_type="B"' in line:
                durations_b.append(float(line.split()[-1]))
    # Plot counters
    plt.figure(figsize=(8, 4))
    plt.subplot(1, 2, 1)
    plt.bar(["A", "B"], [counter_a, counter_b])
    plt.title("Event Counter")
    plt.xlabel("Event Type")
    plt.ylabel("Count")
    # Plot histogram buckets
    plt.subplot(1, 2, 2)
    plt.plot(durations_a, label="A")
    plt.plot(durations_b, label="B")
    plt.title("Event Duration Histogram (Cumulative)")
    plt.xlabel("Bucket")
    plt.ylabel("Count")
    plt.legend()
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    # Start Prometheus metrics server in a background thread
    t = threading.Thread(target=run_metrics_server, daemon=True)
    t.start()
    # Wait for server to be ready
    time.sleep(3)
    # Simulate events
    simulate_events()
    # Scrape and visualize metrics
    scrape_and_plot()
