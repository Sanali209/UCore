# examples/cli_demo/main.py
"""
CLI Demo - UCore Command Line Interface Showcase

This example demonstrates the complete UCore CLI functionality:
- Worker management commands
- Database migration commands
- Application management
- Task queue integration

Usage:
    # Show help
    python main.py --help

    # Worker commands
    python main.py worker start
    python main.py worker status
    python main.py worker stop

    # Database commands
    python main.py db init
    python main.py db status
    python main.py db migrate

    # App commands
    python main.py app create myapp
    python main.py app run

    # Version info
    python main.py version

This example shows how to:
1. Register CLI commands
2. Integrate with background tasks
3. Handle command arguments and options
4. Provide helpful usage information

Run this example to see CLI functionality in action!
"""

import sys
import os
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.background import TaskQueueAdapter
from framework.http import HttpServer
from framework.tasks import task


def create_demo_app():
    """
    Create the CLI demo application with background tasks.
    """

    app = App("CLIDemo")
    http_server = HttpServer(app)
    task_adapter = TaskQueueAdapter(app)

    # Register components
    app.register_component(lambda: http_server)
    app.register_component(lambda: task_adapter)

    # Define some demo tasks for the task queue
    @task()
    def send_welcome_email(user_id: str, email: str):
        """
        Demo task: Send welcome email
        This task would be processed by background workers
        """
        print(f"📧 Sending welcome email to {email} (user: {user_id})")
        import asyncio
        asyncio.sleep(2)  # Simulate processing time
        print(f"✅ Welcome email sent to {email}")
        return f"Email sent to {email}"

    @task()
    def process_data_batch(data_size: int, batch_id: str):
        """
        Demo task: Process data batch
        """
        print(f"📊 Processing data batch {batch_id} with {data_size} records")
        import asyncio
        asyncio.sleep(1.5)  # Simulate processing
        print(f"✅ Data batch {batch_id} processed successfully")
        return f"Processed {data_size} records"

    @task()
    def cleanup_old_files(days_old: int, path: str = "/tmp"):
        """
        Demo task: Cleanup old files
        """
        print(f"🧹 Cleaning up files in {path} older than {days_old} days")
        import asyncio
        asyncio.sleep(1)  # Simulate cleanup
        print(f"✅ Cleanup completed in {path}")
        return "Cleanup completed"

    # HTTP endpoints to trigger tasks (for demo purposes)
    @http_server.route("/email", "POST")
    async def trigger_email_endpoint(request, adapter=TaskQueueAdapter(app)):
        """
        POST /email
        {"user_id": "123", "email": "user@example.com"}
        """
        try:
            data = await request.json()
            user_id = data.get('user_id', 'demo_user')
            email = data.get('email', 'demo@example.com')

            # Send task to background queue
            task_result = adapter.send_task(
                'examples.cli_demo.main.send_welcome_email',
                args=[user_id, email]
            )

            return {
                "message": "Welcome email queued for sending",
                "user_id": user_id,
                "email": email,
                "task_id": str(task_result.id) if task_result else "queued"
            }

        except Exception as e:
            return {"error": f"Failed to queue email task: {str(e)}"}

    @http_server.route("/", "GET")
    async def root_endpoint():
        """
        Get demo information
        """
        return {
            "message": "UCore CLI Demo",
            "description": "Demonstrates CLI worker commands and background task processing",
            "endpoints": {
                "POST /email": "Queue email tasks for background processing",
                "GET /": "This help information"
            },
            "cli_commands": {
                "worker start": "Start background worker process",
                "worker status": "Check worker status",
                "worker stop": "Stop workers gracefully",
                "db init/migrate": "Database operations",
                "app create/run": "Application management",
                "version": "Show framework version"
            },
            "usage": [
                "1. Start worker: python main.py worker start",
                "2. Send test email: curl -X POST http://localhost:8080/email -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\"}'",
                "3. Check worker status: python main.py worker status"
            ]
        }

    return app


def show_demo_help():
    """
    Display helpful information for the CLI demo.
    """
    print("🚀 UCore CLI Demo")
    print("=" * 70)
    print()
    print("This demo showcases complete CLI functionality:")
    print("• Background worker management")
    print("• Task queue integration")
    print("• Database migration commands")
    print("• Application management")
    print()
    print("🧪 Test Commands:")
    print()
    print("1️⃣  Show available commands:")
    print("   python main.py --help")
    print()
    print("2️⃣ Worker commands:")
    print("   python main.py worker --help")
    print("   python main.py worker start --help")
    print()
    print("3️⃣ Database commands:")
    print("   python main.py db --help")
    print("   python main.py db status")
    print()
    print("4️⃣ Start a worker (in separate terminal):")
    print("   python main.py worker start")
    print()
    print("5️⃣ Run the demo web server:")
    print("   python examples/cli_demo/main.py")
    print("   curl http://localhost:8080/email -X POST -H 'Content-Type: application/json' -d '{\"email\":\"test@example.com\"}'")
    print()
    print("6️⃣ Check worker status:")
    print("   python main.py worker status")
    print()
    print("📚 See the complete UCore CLI reference in docs/")
    print("=" * 70)


def main():
    """
    Main CLI demo entry point.
    """
    # Check if no arguments provided - show demo help
    if len(sys.argv) == 1:
        show_demo_help()
        return

    # If arguments provided, run as CLI
    try:
        from framework.cli import main as cli_main
        cli_main()
    except SystemExit:
        # handle typer Exit
        pass
    except Exception as e:
        print(f"❌ CLI Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) == 1:
        # No CLI args - run web demo
        show_demo_help()
        print("\n🌐 Starting web server demo...")
        demo_app = create_demo_app()
        demo_app.run()
    else:
        # CLI args provided - run CLI command
        main()
