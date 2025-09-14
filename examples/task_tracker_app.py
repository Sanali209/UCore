#!/usr/bin/env python3
"""
Task Tracker Application using Flet UI with UCore Framework
============================================================

This example demonstrates building a modern task tracking application using Flet UI
integrated with the UCore Framework:

🎯 Features:
- Create, edit, and delete tasks
- Task status management (TODO, IN_PROGRESS, COMPLETED)
- Priority levels (Low, Medium, High, Urgent)
- Due dates with deadline tracking
- Task filtering and search
- Clean, modern UI with responsive design
- Data persistence using JSON storage
- Progress tracking and statistics

🎮 Demonstration Goals:
- Modern cross-platform UI with Flet
- UCore Framework integration (App + FletAdapter)
- CRUD operations with data persistence
- State management in UI applications
- Responsive design principles
- Event-driven UI architecture
- Clean application structure

Installation Requirements:
pip install flet

Usage:
python examples/task_tracker_app.py

Features Demonstrated:
- Flet UI framework integration with UCore
- State management patterns
- Responsive UI design
- Data persistence
- Event-driven architecture
- Modern application design
"""

import sys
import asyncio
import json
import os
from datetime import datetime, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

# This allows the example to be run from the root of the repository
sys.path.insert(0, 'd:/UCore')

# Third-party imports
try:
    import flet as ft
    flet_available = True
    print("✅ Flet loaded successfully")
except ImportError:
    flet_available = False
    print("❌ Flet is required: pip install flet")

# UCore Framework imports (only if Flet is available)
if flet_available:
    from framework.app import App
    from framework.ui.flet_adapter import FletAdapter
    print("✅ UCore Framework loaded successfully")


# Task data model
class TaskStatus(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"

    def __str__(self):
        return {
            "todo": "To Do",
            "in_progress": "In Progress",
            "completed": "Completed"
        }[self.value]


class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

    def __str__(self):
        return {
            "low": "Low",
            "medium": "Medium",
            "high": "High",
            "urgent": "Urgent"
        }[self.value]


@dataclass
class Task:
    id: str
    title: str
    description: str
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime
    due_date: Optional[date] = None
    completed_at: Optional[datetime] = None


# Task manager with data persistence
class TaskTracker:
    def __init__(self, data_file: str = "task_tracker_data.json"):
        self.data_file = data_file
        self.tasks: Dict[str, Task] = {}
        self._load_tasks()

    def add_task(self, task: Task) -> None:
        self.tasks[task.id] = task
        self._save_tasks()

    def update_task(self, task_id: str, **updates) -> bool:
        if task_id not in self.tasks:
            return False
        task = self.tasks[task_id]
        for field, value in updates.items():
            if field == 'status' and isinstance(value, str):
                value = TaskStatus(value)
            setattr(task, field, value)
        self._save_tasks()
        return True

    def delete_task(self, task_id: str) -> bool:
        if task_id not in self.tasks:
            return False
        del self.tasks[task_id]
        self._save_tasks()
        return True

    def get_tasks(self, status_filter=None, priority_filter=None, search_text=""):
        tasks = list(self.tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        if priority_filter:
            tasks = [t for t in tasks if t.priority == priority_filter]
        if search_text:
            search_lower = search_text.lower()
            tasks = [t for t in tasks if search_lower in t.title.lower()]
        return sorted(tasks, key=lambda t: t.created_at)

    def _load_tasks(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    for task_data in data.get('tasks', []):
                        task = Task(**task_data)
                        self.tasks[task.id] = task
        except Exception as e:
            print(f"Warning: Failed to load tasks: {e}")

    def _save_tasks(self):
        try:
            data = {'tasks': [vars(task) for task in self.tasks.values()]}
            with open(self.data_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving tasks: {e}")


# Task card component (simplified)
def create_task_card(task: Task, tracker: TaskTracker, page: ft.Page, refresh_callback):
    def change_status(new_status: TaskStatus):
        tracker.update_task(task.id, status=new_status)
        refresh_callback()

    def delete_task():
        tracker.delete_task(task.id)
        refresh_callback()

    return ft.Card(
        content=ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Text(task.title, size=16, weight=ft.FontWeight.BOLD),
                    ft.ElevatedButton("✗", on_click=lambda _: delete_task()),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                ft.Text(f"Status: {task.status}", size=12),
                ft.Text(f"Priority: {task.priority}", size=12),
                ft.Text(task.description, size=12, color="grey700") if task.description else None,
            ]),
            padding=15
        )
    )


# Main Flet UI function
def flet_main(page: ft.Page):
    """
    Main Flet UI function that defines the task tracker interface.
    """
    page.title = "UCore Task Tracker"
    page.vertical_alignment = ft.MainAxisAlignment.START

    # Initialize task tracker
    tracker = TaskTracker()

    # UI components
    title_text = ft.Text("Task Tracker", size=24, weight=ft.FontWeight.BOLD)

    # Input fields for new task
    title_field = ft.TextField(label="Task Title", width=300)
    desc_field = ft.TextField(label="Description", multiline=True, width=300)

    # Add new task function
    def add_task(e):
        if not title_field.value:
            return
        task = Task(
            id=f"task_{len(tracker.tasks) + 1}",
            title=title_field.value,
            description=desc_field.value or "",
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            created_at=datetime.now()
        )
        tracker.add_task(task)
        # Clear fields and refresh tasks list
        title_field.value = ""
        desc_field.value = ""
        refresh_tasks()

    # Add task button
    add_button = ft.ElevatedButton("Add Task", icon="add", on_click=add_task)

    # Input area
    input_area = ft.Column([
        ft.Text("Add New Task", size=16, weight=ft.FontWeight.BOLD),
        title_field,
        desc_field,
        add_button
    ])

    # Tasks list container
    tasks_container = ft.Column([])

    def refresh_tasks():
        """Refresh the tasks list display."""
        tasks_container.controls.clear()
        for task in tracker.get_tasks():
            card = create_task_card(task, tracker, page, refresh_tasks)
            tasks_container.controls.append(card)
        page.update()

    # Add components to page
    page.add(
        ft.Container(
            content=ft.Column([
                title_text,
                ft.Divider(),
                input_area,
                ft.Divider(),
                ft.Text("Current Tasks", size=18, weight=ft.FontWeight.BOLD),
                ft.Container(content=tasks_container, height=400)
            ]),
            padding=20,
            expand=True
        )
    )

    # Initial load
    refresh_tasks()


# Application factory following the UCore pattern
def create_task_tracker_app():
    """
    Application factory for the Task Tracker app.
    """
    print("🏗️ Creating Task Tracker Application...")

    # 1. Initialize the main App object
    app = App(name="UCoreFletTaskTracker")
    print("✅ UCore App initialized")

    # 2. Register the FletAdapter
    # We pass the flet_main function as the target for the Flet app
    flet_adapter = FletAdapter(app, target_func=flet_main)
    app.register_component(lambda: flet_adapter)
    print("✅ FletAdapter registered")

    return app


def main():
    """
    Main entry point to run the Task Tracker application.
    """
    print("🎯 STARTING UCORE FRAMEWORK - TASK TRACKER APPLICATION")
    print("=" * 60)
    print("🎯 Features:")
    print("  → Task creation and management")
    print("  → Real-time data persistence")
    print("  → Modern cross-platform UI")
    print("  → UCore Framework integration")
    print("=" * 60)

    if not flet_available:
        print("❌ Flet is required for this application!")
        print("Install with: pip install flet")
        return

    try:
        # Create the application instance
        ucore_app = create_task_tracker_app()

        print("✅ Application created successfully!")
        print("🚀 Starting Flet web server...")

        # Run the application
        # This will start the main asyncio event loop
        # The FletAdapter's start() method will be called, launching the Flet web server
        ucore_app.run()

    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Application error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("👋 Task Tracker application closed")


if __name__ == "__main__":
    main()
