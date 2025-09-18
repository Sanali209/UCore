"""
Example: Using TimeMeasure with Prometheus metrics in UCore

Requirements:
- prometheus-client
- matplotlib (for plotting, optional)
"""

import time
import threading
from UCoreFrameworck.core.timemeasure import TimeMeasure

from prometheus_client import start_http_server

def simulate_work(tm: TimeMeasure, timer_name: str):
    tm.start_timer(timer_name, step=2)
    for i in range(6):
        time.sleep(0.2 + 0.1 * i)
        tm.lap(timer_name, label=f"step-{i+1}")
    tm.export_laps(timer_name, f"{timer_name}_laps.csv")
    # Plotting is optional and may block in some environments
    try:
        tm.plot(timer_name)
    except Exception as e:
        print(f"Plot error: {e}")

if __name__ == "__main__":
    # Start Prometheus metrics server on port 8000
    start_http_server(8000)
    print("Prometheus metrics available at http://localhost:8000/metrics")

    tm = TimeMeasure()
    # Run simulated work in the main thread for simplicity
    simulate_work(tm, "demo")
    print("Done. Check metrics and CSV output.")
    # Keep process alive for Prometheus scraping
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting.")
