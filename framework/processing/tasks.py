# framework/tasks.py
"""
Celery tasks for UCore framework.
This module provides decorators and task definitions.
"""

from .background import celery_app
from typing import Any

# Task decorator for easy task definition
def task(*args, **kwargs):
    """
    Decorator to register a function as a Celery task.

    Example usage:
        @task()
        def my_background_task(x, y):
            return x + y

        @task(queue='priority')
        def priority_task(data):
            # Process high-priority work
            return processed_data
    """
    def decorator(func):
        if celery_app is not None:
            # Register with Celery when available
            from .background import TaskQueueAdapter
            # Get adapter instance if one exists globally
            import inspect
            frame = inspect.currentframe()
            while frame:
                if 'task_queue_adapter' in frame.f_globals:
                    adapter = frame.f_globals['task_queue_adapter']
                    return adapter.task(*args, **kwargs)(func)
                frame = frame.f_back

            # Fallback: use celery app directly if available
            if celery_app:
                return celery_app.task(*args, **kwargs)(func)

        # Return function unchanged if no adapter available
        return func
    return decorator

# Example tasks
@task()
def send_email(to: str, subject: str, body: str) -> bool:
    """
    Send an email (example task).
    In a real implementation, this would connect to an email service.
    """
    print(f"Sending email to {to}: {subject}")
    # Simulate sending email
    import time
    time.sleep(1)  # Simulate network delay
    return True

@task(queue='processing')
def process_data(data: Any) -> Any:
    """
    Process data in background (example task).
    This represents heavy computation or data processing.
    """
    print(f"Processing data: {data}")

    # Simulate data processing
    import time
    time.sleep(2)  # Simulate heavy processing

    # Example: convert to uppercase if it's a string
    if isinstance(data, str):
        return data.upper()
    elif isinstance(data, list):
        return [process_data(item) for item in data]

    return {"processed": True, "input": data}

@task()
def backup_database(database_url: str) -> bool:
    """
    Create database backup (example task).
    """
    print(f"Creating backup for database: {database_url}")

    # Simulate backup creation
    import time
    time.sleep(3)

    # In real implementation, this would:
    # 1. Connect to database
    # 2. Create dump/file backup
    # 3. Upload to cloud storage
    # 4. Send notification

    return True

@task(name='cleanup_old_files')
def cleanup_files(older_than_days: int = 30) -> dict:
    """
    Clean up old files (example task).
    """
    print(f"Cleaning up files older than {older_than_days} days")

    # Simulate cleanup
    import time
    time.sleep(1)

    cleanup_stats = {
        "files_removed": 125,
        "space_freed_mb": 512,
        "errors": 0
    }

    return cleanup_stats

# Task for periodic database maintenance
@task(name='database_maintenance')
def database_maintenance_operation(operation: str) -> dict:
    """
    Perform database maintenance operations.

    Args:
        operation: Type of maintenance ('optimize', 'analyze', 'cleanup')

    Returns:
        Status and results of maintenance operation
    """
    print(f"Performing database maintenance: {operation}")

    # Simulate maintenance operations
    import time
    if operation == 'optimize':
        time.sleep(5)
        duration = 5.2
    elif operation == 'analyze':
        time.sleep(2)
        duration = 2.1
    else:
        time.sleep(1)
        duration = 1.0

    return {
        "operation": operation,
        "duration_seconds": duration,
        "success": True,
        "tables_processed": 42
    }
