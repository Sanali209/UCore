import typer
from ucore_framework.core.app import App
from ucore_framework.core.component import Component
from ucore_framework.core.di import Scope, Container
from example.quicktask.task_service import TaskService

app_cli = typer.Typer()

class TaskComponent(Component):
    def __init__(self, container):
        super().__init__(name="TaskComponent")
        self._container = container

    def start(self):
        service = self._container.get(TaskService)
        print(f"TaskComponent started. TaskService loaded with {len(service.list_tasks())} tasks.")

# Instantiate the main UCore app
ucore_app = App("QuickTask")
ucore_app.container.register(TaskService, scope=Scope.SINGLETON)
ucore_app.register_component(TaskComponent(ucore_app.container))

@app_cli.command()
def add(description: str):
    """Add a new task."""
    service = ucore_app.container.get(TaskService)
    service.add_task(description)
    typer.echo(f"Task added: {description}")

@app_cli.command()
def list():
    """List all tasks."""
    service = ucore_app.container.get(TaskService)
    tasks = service.list_tasks()
    if not tasks:
        typer.echo("No tasks found.")
    for t in tasks:
        status = "✓" if t["completed"] else " "
        typer.echo(f"{t['index']+1}. [{status}] {t['description']}")

@app_cli.command()
def complete(index: int):
    """Mark a task as completed (1-based index)."""
    service = ucore_app.container.get(TaskService)
    if service.complete_task(index - 1):
        typer.echo(f"Task {index} marked as completed.")
    else:
        typer.echo(f"Task {index} not found.")

if __name__ == "__main__":
    app_cli()
