from abc import ABC, abstractmethod
from typing import Callable, Any, List
from loguru import logger
from tqdm import tqdm
import threading

class Task(ABC):
    """
    Base class for background tasks.
    """
    @abstractmethod
    def run(self):
        pass

class TaskRunner:
    """
    Runs background tasks with progress and logging.
    """
    def __init__(self):
        self.tasks: List[Task] = []

    def add_task(self, task: Task):
        self.tasks.append(task)
        logger.info(f"Task added: {task}")

    def run_all(self):
        for task in tqdm(self.tasks, desc="Running tasks"):
            thread = threading.Thread(target=self._run_task, args=(task,))
            thread.start()
            thread.join()

    def _run_task(self, task: Task):
        logger.info(f"Starting task: {task}")
        try:
            task.run()
            logger.info(f"Completed task: {task}")
        except Exception as e:
            logger.error(f"Task failed: {task} - {e}")
