# QuickTask: Minimal UCore CLI To-Do Example

This example demonstrates the basics of the UCore Framework:
- Application lifecycle and DI
- Component registration
- Typer-based CLI

## Usage

1. **Install dependencies:**
   ```
   pip install typer
   ```

2. **Run the CLI:**
   ```
   python main.py [COMMAND]
   ```

## Commands

- `add "Task description"` — Add a new task.
- `list` — List all tasks.
- `complete INDEX` — Mark a task as completed (1-based index).

## Example

```bash
python main.py add "Buy milk"
python main.py add "Write docs"
python main.py list
python main.py complete 1
python main.py list
```

## Files

- `main.py` — Entry point, CLI, and app setup.
- `task_service.py` — Simple in-memory task manager.
