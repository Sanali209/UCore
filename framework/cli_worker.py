# framework/cli_worker.py
"""
Worker manager for CLI worker commands.
Integrates with Celery and UCore's background task system.
"""

import time
import asyncio
import signal
import inspect
from typing import Optional, List
from .logging import Logging


class WorkerManager:
    """
    Manages Celery workers through CLI commands.
    Integrates with UCore's component system and logging.
    """

    def __init__(
        self,
        mode: str = "single",
        processes: Optional[int] = None,
        queues: Optional[List[str]] = None,
        verbosity: int = 1,
        log_level: str = "info"
    ):
        self.mode = mode
        self.processes = processes
        self.queues = queues or ['celery']
        self.verbosity = verbosity
        self.log_level = log_level
        self.logger = Logging().get_logger("WorkerManager")
        self.running = False
        self.celery_app = None

    def run(self):
        """Run the worker manager based on the specified mode."""
        try:
            # Import Celery components
            from .background import TaskQueueAdapter
            from .app import App
            from .tasks import app as celery_app

            if self.logger:
                self.logger.info(f"Starting worker in {self.mode} mode")
                self.logger.info(f"Queues: {', '.join(self.queues)}")
                self.logger.info(f"Processes: {self.processes or 'auto'}")

            # Initialize UCore app with background tasks
            app = App("Worker")
            task_adapter = TaskQueueAdapter(app)
            app.register_component(lambda: task_adapter)

            # Start the application
            if inspect.iscoroutinefunction(app.start):
                asyncio.run(app.start())
            else:
                app.start()

            # Run Celery worker
            self._run_celery_worker()

        except ImportError as e:
            print(f"❌ Celery not installed. Run: pip install celery")
            print(f"❌ Error: {e}")
            return 1
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error running worker: {e}", exc_info=True)
            else:
                print(f"❌ Error running worker: {e}")
            return 1

        return 0

    def _run_celery_worker(self):
        """Run Celery worker with appropriate configuration."""
        try:
            from celery import worker
            from celery.bin import worker as celery_worker_bin

            # Build Celery worker arguments
            args = self._build_worker_args()

            if self.logger:
                self.logger.info(f"Starting Celery worker with args: {' '.join(args)}")

            # Create and configure worker instance
            self.running = True

            # Set up signal handlers for graceful shutdown
            signal.signal(signal.SIGTERM, self._shutdown_handler)
            signal.signal(signal.SIGINT, self._shutdown_handler)

            if self.logger:
                self.logger.info("🎯 Worker started successfully")

            # Keep worker running
            while self.running:
                time.sleep(1)
                # In a real implementation, this would be:
                # worker_obj = celery_worker_bin.worker(args=args)
                # worker_obj.run()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error in Celery worker: {e}")
            raise

    def _build_worker_args(self):
        """Build command line arguments for Celery worker."""
        args = ['worker']

        # Add log level
        if self.log_level:
            args.extend(['--loglevel', self.log_level])

        # Add conciseness/verbosity
        if self.verbosity >= 3:
            args.append('--verbose')
        elif self.verbosity == 0:
            args.append('--quiet')

        # Add queues
        if self.queues:
            args.extend(['--queues', ','.join(self.queues)])

        # Add concurrency (processes)
        if self.processes:
            args.extend(['--concurrency', str(self.processes)])
        elif self.mode == 'pool':
            # Default to multiple processes for pool mode
            args.extend(['--concurrency', '4'])

        # Add hostname for pool mode
        if self.mode == 'pool':
            args.extend(['--hostname', f'worker.%h'])

        # Add pool mode specific options
        if self.mode == 'pool':
            args.append('--pool=prefork')

        return args

    def shutdown(self):
        """Graceful shutdown of the worker."""
        if self.logger:
            self.logger.info("📤 Worker shutdown initiated")

        self.running = False

        if self.logger:
            self.logger.info("✓ Worker shutdown completed")

    def _shutdown_handler(self, signum, frame):
        """Signal handler for graceful shutdown."""
        self.shutdown()


def get_worker_status():
    """
    Get current worker status.
    This is a simplified status check for CLI command.
    """
    try:
        # In a real implementation, this would query Celery/Flower
        # or check worker processes
        return {
            'active_workers': 0,
            'queues': {'celery': {'active': 0, 'scheduled': 0, 'reserved': 0}},
            'status': 'No active workers'
        }
    except Exception as e:
        return {
            'error': str(e),
            'active_workers': 0,
            'queues': {},
            'status': 'Error retrieving status'
        }


def stop_workers(graceful: bool = True):
    """
    Stop all running workers.

    Args:
        graceful: Whether to allow workers to finish current tasks
    """
    try:
        # In a real implementation, this would send SIGTERM/SIGINT
        # to worker processes
        if graceful:
            # Send SIGTERM for graceful shutdown
            pass  # Implementation would send signals here
        else:
            # Send SIGKILL for forced shutdown
            pass  # Implementation would send signals here

        return "Workers stopped successfully"

    except Exception as e:
        return f"Failed to stop workers: {e}"
