"""
Example: Using UCore framework metrics for collection and visualization

Requirements:
- matplotlib
"""

import time
from UCoreFrameworck.monitoring.metrics import MetricsManager
import matplotlib.pyplot as plt

def simulate_metrics(metrics: MetricsManager, metric_name: str):
    for i in range(10):
        value = i * 2 + 1
        metrics.observe(metric_name, value)
        time.sleep(0.2)
    print(f"Collected values for '{metric_name}':", metrics.get_observations(metric_name))

def plot_metric(metrics: MetricsManager, metric_name: str):
    values = metrics.get_observations(metric_name)
    plt.plot(values, marker="o")
    plt.title(f"Metric: {metric_name}")
    plt.xlabel("Observation")
    plt.ylabel("Value")
    plt.show()

if __name__ == "__main__":
    metrics = MetricsManager()
    metric_name = "demo_metric"
    simulate_metrics(metrics, metric_name)
    plot_metric(metrics, metric_name)
