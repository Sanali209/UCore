# examples/background_tasks/main.py
"""
Background Tasks Example - Publisher-Subscriber Pattern

This example demonstrates:
- HTTP endpoint that publishes tasks to Celery
- Background workers processing those tasks
- Integration with framework lifecycle and DI

Usage:
1. Start Redis server
2. Run this application: python main.py
3. In another terminal, start worker: ucore worker start
4. Test endpoints:
   - POST /process-data with JSON: {"data": "hello"}
   - POST /send-email with JSON: {"to": "user@example.com", "subject": "Test", "body": "Hello"}
   - POST /backup with JSON: {"database_url": "sqlite:///test.db"}
   - POST /cleanup with JSON: {"days": 30}
   - GET /task-result/<task_id> - Check task status/result
"""

import sys
sys.path.insert(0, 'd:/UCore')

from framework import App
from framework.web import HttpServer
from framework.processing.background import TaskQueueAdapter
from framework.core.di import Depends
import asyncio
from aiohttp import web


def get_task_adapter(task_adapter: TaskQueueAdapter):
    """Dependency provider for TaskQueueAdapter"""
    return task_adapter


def create_background_app():
    """
    Create an application with background task processing.
    """
    app = App(name="BackgroundTasksExample")

    # Create components
    http_server = HttpServer(app)
    task_adapter = TaskQueueAdapter(app)

    # Register components
    app.register_component(lambda: http_server)
    app.register_component(lambda: task_adapter)

    # ---- Background Task Endpoints ----

    @http_server.route("/process-data", "POST")
    async def process_data_endpoint(request: web.Request, adapter=Depends(get_task_adapter)):
        """
        POST /process-data
        JSON: {"data": "your data here"}

        Publishes a data processing task and returns task ID.
        """
        data = await request.json()
        input_data = data.get('data', 'test data')

        # Send task to Celery
        task_result = adapter.send_task(
            'framework.processing.tasks.process_data',
            args=[input_data]
        )

        return web.json_response({
            "message": "Data processing task published",
            "task_id": task_result.id,
            "queue": "processing"
        }, status=202)

    @http_server.route("/send-email", "POST")
    async def send_email_endpoint(request: web.Request, adapter=Depends(get_task_adapter)):
        """
        POST /send-email
        JSON: {"to": "user@example.com", "subject": "Test", "body": "Hello"}

        Publishes an email sending task.
        """
        data = await request.json()
        to_email = data.get('to', 'user@example.com')
        subject = data.get('subject', 'Test Subject')
        body = data.get('body', 'Test body')

        task_result = adapter.send_task(
            'framework.processing.tasks.send_email',
            args=[to_email, subject, body]
        )

        return web.json_response({
            "message": "Email sending task published",
            "task_id": task_result.id,
            "recipient": to_email
        }, status=202)

    @http_server.route("/backup", "POST")
    async def backup_endpoint(request: web.Request, adapter=Depends(get_task_adapter)):
        """
        POST /backup
        JSON: {"database_url": "sqlite:///myapp.db"}

        Publishes a database backup task.
        """
        data = await request.json()
        db_url = data.get('database_url', 'sqlite:///test.db')

        task_result = adapter.send_task(
            'framework.processing.tasks.backup_database',
            args=[db_url]
        )

        return web.json_response({
            "message": "Database backup task published",
            "task_id": task_result.id,
            "database": db_url
        }, status=202)

    @http_server.route("/cleanup", "POST")
    async def cleanup_endpoint(request: web.Request, adapter=Depends(get_task_adapter)):
        """
        POST /cleanup
        JSON: {"days": 30}

        Publishes a file cleanup task.
        """
        data = await request.json()
        days = data.get('days', 30)

        task_result = adapter.send_task(
            'cleanup_old_files',
            args=[days]
        )

        return web.json_response({
            "message": f"File cleanup task published (files older than {days} days)",
            "task_id": task_result.id,
            "cleanup_criteria": f"older_than_{days}_days"
        }, status=202)

    @http_server.route("/task-result/{task_id}", "GET")
    async def get_task_result(request: web.Request):
        """
        GET /task-result/{task_id}

        Check the status and result of a background task.
        """
        task_id = request.match_info['task_id']

        # In a real implementation, you would query Celery for task status
        # For this example, we'll simulate a pending task

        return web.json_response({
            "task_id": task_id,
            "status": "PENDING",
            "current": 0,
            "total": 100,
            "state": "RECEIVED",
            "result": None
        })

    # ---- Information Endpoints ----

    @http_server.route("/", "GET")
    async def root_endpoint():
        """
        GET /

        Returns API information and available endpoints.
        """
        return web.json_response({
            "message": "UCore Background Tasks Example API",
            "version": "v1.0",
            "endpoints": {
                "POST /process-data": "Process data in background",
                "POST /send-email": "Send email in background",
                "POST /backup": "Create database backup",
                "POST /cleanup": "Clean up old files",
                "GET /task-result/{id}": "Check task status",
                "GET /": "This information"
            },
            "worker_command": "ucore worker start",
            "requirements": "Redis server running",
            "celery_broker": "redis://localhost:6379/0"
        })

    return app


def main():
    """
    Main entry point for the background tasks example.
    """
    print("🚀 UCore Background Tasks Example")
    print("=" * 50)
    print()
    print("This example demonstrates:")
    print("• HTTP endpoints publishing tasks to Celery")
    print("• Background workers processing those tasks")
    print("• Framework lifecycle integration")
    print()
    print("Requirements:")
    print("  ✅ Redis server running (redis://localhost:6379/0)")
    print("  ❌ Run worker in separate terminal: 'ucore worker start'")
    print()
    print("Test with:")
    print("  curl -X POST http://localhost:8080/process-data -H 'Content-Type: application/json' -d '{\"data\": \"hello world\"}'")
    print()

    # Create and run the application
    background_app = create_background_app()
    background_app.run()


if __name__ == "__main__":
    main()
