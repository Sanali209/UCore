# Processing Domain Guide

## Purpose

The processing domain provides background task execution, CLI tools, worker management, and CPU-bound task adapters for UCore.

---

## Main Classes & Components

- `TaskQueue`: Manages background and scheduled tasks.
- `CLIWorker`: Command-line worker process manager.
- `CPUWorker`: Adapter for CPU-bound task execution.
- `CLI`: Command-line interface for managing tasks and workers.

---

## Usage Example

```python
from ucore_framework.processing.tasks import TaskQueue

queue = TaskQueue(app)

@queue.task("my_task")
def my_task():
    print("Task executed")
```

---

## CLI Example

```bash
ucore worker start --mode pool --processes 4
ucore status
```

---

## Extensibility & OOP

- Register new tasks using decorators.
- Extend CLI commands for custom workflows.
- Implement custom worker adapters.

---

## Integration Points

- Used by resource, data, and web domains for background processing.
- Integrates with monitoring for task metrics and logging.

---

## See Also

- [Project Structure Guide](project-structure-guide.md)
- [UCore Framework Guide](ucore-ucore_framework-guide.md)
