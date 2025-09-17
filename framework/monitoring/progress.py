"""
ProgressManager and Visualizers with loguru/tqdm integration.

Provides modular progress tracking and visualization for CLI and logging.
"""

from typing import List, Callable, Optional
from loguru import logger
from tqdm import tqdm

class ProgressVisualizer:
    def update_progress(self, progress: int, max_progress: int, message: str, description: str):
        pass

class TqdmProgressVisualizer(ProgressVisualizer):
    def __init__(self, max_progress: int, description: str = ""):
        self.pbar = tqdm(total=max_progress, desc=description)
        self.last_progress = 0

    def update_progress(self, progress: int, max_progress: int, message: str, description: str):
        delta = progress - self.last_progress
        if self.pbar is not None:
            if delta > 0:
                self.pbar.update(delta)
            self.pbar.set_description_str(description)
            self.pbar.set_postfix_str(message)
            self.last_progress = progress
            if progress >= max_progress:
                self.pbar.close()
        else:
            self.last_progress = progress

class LoguruProgressVisualizer(ProgressVisualizer):
    def update_progress(self, progress: int, max_progress: int, message: str, description: str):
        logger.info(f"[{description}] {progress}/{max_progress}: {message}")

class ProgressManager:
    def __init__(self, max_progress: int = 100, description: str = "", event_bus=None):
        self.visualizers: List[ProgressVisualizer] = []
        self.progress = 0
        self.max_progress = max_progress
        self.message = ""
        self.description = description
        self.event_bus = event_bus

    def add_visualizer(self, visualizer: ProgressVisualizer):
        self.visualizers.append(visualizer)

    def set_description(self, description: str):
        self.description = description
        self.update()

    def step(self, message: str = ""):
        self.progress += 1
        self.message = message
        self.update()

    def reset(self):
        self.progress = 0
        self.message = ""
        self.description = ""
        self.update()

    def update(self):
        for visualizer in self.visualizers:
            visualizer.update_progress(self.progress, self.max_progress, self.message, self.description)
        if self.event_bus:
            try:
                self.event_bus.publish(
                    "progress.update",
                    {
                        "progress": self.progress,
                        "max_progress": self.max_progress,
                        "message": self.message,
                        "description": self.description,
                    }
                )
            except Exception as e:
                from loguru import logger
                logger.error(f"Failed to emit progress event: {e}")

    def set_progress(self, value: int, message: str = ""):
        self.progress = value
        self.message = message
        self.update()
