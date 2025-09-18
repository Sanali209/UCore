from ucore_framework.core.component import Component
from loguru import logger
import time
import asyncio
from typing import Dict, List, Optional, Any
try:
    from prometheus_client import Summary
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False

class TimerLap:
    def __init__(self, duration: float, label: Optional[str] = None):
        self.duration = duration
        self.label = label

class TimeMeasure(Component):
    def __init__(self):
        super().__init__()
        self._timers: Dict[str, Dict] = {}
        self._metrics = {} if PROMETHEUS_AVAILABLE else None

    def start_timer(self, name: str, step: int = 1):
        self._timers[name] = {
            "step": step,
            "start_time": time.time(),
            "laps": [],
            "count": 0
        }
        if PROMETHEUS_AVAILABLE and self._metrics is not None and name not in self._metrics:
            from prometheus_client import Summary
            self._metrics[name] = Summary(f"time_measure_{name}", f"Timing for {name}")
        logger.info(f"Timer '{name}' started.")

    def lap(self, name: str, label: Optional[str] = None):
        timer = self._timers.get(name)
        if not timer:
            self.start_timer(name)
            timer = self._timers[name]
        end = time.time()
        duration = end - timer["start_time"]
        timer["count"] += 1
        if timer["count"] == timer["step"]:
            timer["laps"].append(TimerLap(duration, label))
            timer["count"] = 0
            if PROMETHEUS_AVAILABLE and self._metrics is not None and name in self._metrics:
                self._metrics[name].observe(duration)
        timer["start_time"] = end
        logger.info(f"Lap for '{name}': {duration:.4f}s")
        # Optionally: self.emit_event("lap", {"name": name, "duration": duration, "label": label})

    def get_laps(self, name: str) -> List[TimerLap]:
        return self._timers.get(name, {}).get("laps", [])

    def reset_timer(self, name: str):
        if name in self._timers:
            del self._timers[name]
            logger.info(f"Timer '{name}' reset.")

    def plot(self, name: str):
        import matplotlib.pyplot as plt
        laps = self.get_laps(name)
        values = [lap.duration for lap in laps]
        plt.plot(values)
        plt.title(f"Laps for {name}")
        plt.xlabel("Lap")
        plt.ylabel("Duration (s)")
        plt.show()

    def export_laps(self, name: str, file_path: str):
        import csv
        laps = self.get_laps(name)
        with open(file_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Lap", "Duration", "Label"])
            for i, lap in enumerate(laps):
                writer.writerow([i + 1, lap.duration, lap.label or ""])
        logger.info(f"Laps for '{name}' exported to {file_path}")

    async def async_timer(self, name: str, step: int = 1):
        self.start_timer(name, step)
        try:
            yield
        finally:
            self.lap(name)

    def timer(self, name: str, step: int = 1):
        from contextlib import contextmanager
        @contextmanager
        def _timer():
            self.start_timer(name, step)
            try:
                yield
            finally:
                self.lap(name)
        return _timer()
