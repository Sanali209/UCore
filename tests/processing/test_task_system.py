import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import time
from framework.processing.tasks import task, send_email, process_data, backup_database, cleanup_files, database_maintenance_operation


class TestTaskDecorator:
    """Test the @task decorator functionality."""

    def test_task_decorator_without_args(self):
        """Test task decorator without arguments."""
        @task()
        def simple_task(x, y):
            return x + y

        # Verify function is callable and returns expected result
        assert callable(simple_task)
        assert simple_task(3, 5) == 8

    def test_task_decorator_with_queue(self):
        """Test task decorator with queue specification."""
        @task(queue='priority')
        def priority_task(value):
            return f"priority: {value}"

        assert callable(priority_task)
        assert priority_task("test") == "priority: test"

    def test_task_decorator_with_name(self):
        """Test task decorator with custom name."""
        @task(name='custom_task_name')
        def named_task(value):
            return f"custom: {value}"

        assert callable(named_task)
        assert named_task("test") == "custom: test"


class TestBackgroundTasks:
    """Test predefined background tasks."""

    @patch('time.sleep', side_effect=lambda x: asyncio.sleep(0.001))  # Mock sleep for testing
    def test_send_email_task(self, mock_sleep):
        """Test email sending task."""
        result = send_email("test@example.com", "Test Subject", "Test Body")

        # Should return bool (simulated success)
        assert isinstance(result, bool)
        assert result is True

        # Verify print statement would work (can't test print easily)
        # This is more of an integration test

    def test_process_data_task_string(self):
        """Test data processing task with string."""
        result = process_data("hello world")

        # Should uppercase the string
        assert isinstance(result, str)
        assert result == "HELLO WORLD"

    def test_process_data_task_list(self):
        """Test data processing task with list."""
        result = process_data([1, 2, 3])

        # Should process list recursively
        assert isinstance(result, dict)
        assert result["processed"] is True
        assert "input" in result

    def test_process_data_task_other(self):
        """Test data processing task with other types."""
        result = process_data(42)

        # Should return processed dict
        assert isinstance(result, dict)
        assert result["processed"] is True
        assert result["input"] == 42

    @patch('time.sleep', side_effect=lambda x: asyncio.sleep(0.001))
    def test_backup_database_task(self, mock_sleep):
        """Test database backup task."""
        result = backup_database("sqlite:///test.db")

        # Should return bool (simulated success)
        assert isinstance(result, bool)
        assert result is True

    @patch('time.sleep', side_effect=lambda x: asyncio.sleep(0.001))
    def test_cleanup_files_task(self, mock_sleep):
        """Test file cleanup task."""
        result = cleanup_files(older_than_days=30)

        # Should return cleanup statistics
        assert isinstance(result, dict)
        assert "files_removed" in result
        assert "space_freed_mb" in result
        assert "errors" in result

    @patch('time.sleep', side_effect=lambda x: asyncio.sleep(0.001))
    def test_database_maintenance_task(self, mock_sleep):
        """Test database maintenance task with different operations."""
        result = database_maintenance_operation("optimize")

        # Should return operation results
        assert isinstance(result, dict)
        assert "operation" in result
        assert "duration_seconds" in result
        assert result["success"] is True
        assert "tables_processed" in result

    @patch('time.sleep', side_effect=lambda x: asyncio.sleep(0.001))
    def test_database_maintenance_analyze(self, mock_sleep):
        """Test database maintenance analyze operation."""
        result = database_maintenance_operation("analyze")

        assert isinstance(result, dict)
        assert result["operation"] == "analyze"
        assert result["success"] is True

    @patch('time.sleep', side_effect=lambda x: asyncio.sleep(0.001))
    def test_database_maintenance_default(self, mock_sleep):
        """Test database maintenance default operation."""
        result = database_maintenance_operation("cleanup")

        assert isinstance(result, dict)
        assert result["operation"] == "cleanup"
        assert result["success"] is True


class TestAsyncTaskOperations:
    """Test async task operations."""

    @pytest.mark.asyncio
    async def test_async_task_execution(self):
        """Test async task execution pattern."""

        @task()
        async def async_task(value):
            await asyncio.sleep(0.01)  # Simulate async work
            return f"async: {value}"

        result = await async_task("test")
        assert result == "async: test"

    @pytest.mark.asyncio
    async def test_task_error_handling(self):
        """Test task error handling."""

        @task()
        def error_task():
            raise ValueError("Task error")

        with pytest.raises(ValueError, match="Task error"):
            error_task()


class TestTaskQueueIntegration:
    """Test task queue integration."""

    def test_task_with_queue_routing(self):
        """Test task with queue routing."""

        @task(queue='emails', name='email_sender')
        def send_marketing_email(recipient, content):
            return f"Sent to {recipient}: {content}"

        result = send_marketing_email("user@example.com", "Special offer!")
        assert f"Sent to user@example.com" in result

    def test_multiple_queue_routing(self):
        """Test multiple tasks with different queues."""

        tasks = []

        @task(queue='priority')
        def urgent_task(data):
            return f"URGENT: {data}"

        @task(queue='batch')
        def batch_task(data):
            return f"BATCH: {data}"

        @task(queue='default')
        def normal_task(data):
            return f"NORMAL: {data}"

        tasks.extend([urgent_task, batch_task, normal_task])

        # Test results
        urgent_result = urgent_task("now")
        batch_result = batch_task("later")
        normal_result = normal_task("whenever")

        assert "URGENT:" in urgent_result
        assert "BATCH:" in batch_result
        assert "NORMAL:" in normal_result


class TestTaskSerialization:
    """Test task serialization for Celery."""

    def test_task_serialization_data(self):
        """Test task with serializable data."""
        import json

        # Test data that should be JSON serializable
        test_data = {
            "task": "process_data",
            "parameters": {
                "user_id": 123,
                "operation": "update",
                "data": {
                    "name": "John Doe",
                    "email": "john@example.com"
                }
            }
        }

        # Should be JSON serializable (for Celery)
        try:
            json.dumps(test_data)
            serializable = True
        except (TypeError, ValueError):
            serializable = False

        assert serializable is True

    def test_task_with_complex_result(self):
        """Test task returning complex result."""
        result = process_data({
            "users": [
                {"name": "Alice", "id": 1},
                {"name": "Bob", "id": 2}
            ],
            "metadata": {
                "source": "api",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        })

        # Should be a processed result dict
        assert isinstance(result, dict)
        assert "processed" in result
        assert result["processed"] is True


class TestTaskPerformance:
    """Test task performance and timing."""

    def test_task_execution_time(self):
        """Test task execution time is reasonable."""
        start_time = time.time()

        result = database_maintenance_operation("analyze")

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (simulated sleep is 2 seconds)
        assert duration < 3.0  # Allow some margin for test execution

        # Verify result
        assert result["operation"] == "analyze"
        assert result["success"] is True

    def test_concurrent_task_execution(self):
        """Test multiple tasks can execute concurrently."""
        import threading

        results = []
        errors = []

        def run_task(task_func, *args):
            try:
                result = task_func(*args)
                results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple tasks
        tasks = [
            (send_email, "test1@example.com", "Subject1", "Body1"),
            (send_email, "test2@example.com", "Subject2", "Body2"),
            (process_data, "test_data_1"),
            (process_data, "test_data_2"),
        ]

        threads = []
        for task_func, *args in tasks:
            thread = threading.Thread(target=run_task, args=(task_func, *args))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)  # 5 second timeout

        # Verify results
        assert len(results) == len(tasks)
        assert len(errors) == 0

        # Verify specific results
        email_results = [r for r in results if isinstance(r, bool)]
        data_results = [r for r in results if isinstance(r, dict)]

        assert len(email_results) == 2  # Two email tasks
        assert len(data_results) == 2   # Two data processing tasks


class TestTaskIntegration:
    """Test task integration with framework components."""

    def test_task_with_celery_mock(self):
        """Test task integration with mock Celery."""
        from unittest.mock import Mock

        # Mock celery app
        mock_celery_app = Mock()
        mock_celery_app.task = Mock()

        # Patch the import
        import framework.processing.background as bg_module
        bg_module.celery_app = mock_celery_app

        # Define task with mocked celery
        @task(queue='test_queue')
        def integrated_task(value):
            return f"integrated: {value}"

        # Verify celery app was used
        assert mock_celery_app.task.called

        # Test execution still works
        result = integrated_task("test")
        assert result == "integrated: test"

    def test_cli_worker_integration(self):
        """Test CLI worker integration for tasks."""
        # This would require actual CLI testing framework
        # For now, verify task functions are callable
        assert callable(send_email)
        assert callable(process_data)
        assert callable(backup_database)
        assert callable(cleanup_files)
        assert callable(database_maintenance_operation)

    def test_task_result_types(self):
        """Test various task result types."""
        # Email task returns bool
        email_result = send_email("test@example.com", "", "")
        assert isinstance(email_result, bool)

        # Data processing returns dict for non-string types
        data_result = process_data(123)
        assert isinstance(data_result, dict)
        assert "processed" in data_result

        # Data processing returns string for strings
        str_result = process_data("test")
        assert isinstance(str_result, str)
        assert str_result == "TEST"

        # Database tasks return appropriate types
        backup_result = backup_database("test.db")
        assert isinstance(backup_result, bool)

        cleanup_result = cleanup_files(7)
        assert isinstance(cleanup_result, dict)

        maintenance_result = database_maintenance_operation("optimize")
        assert isinstance(maintenance_result, dict)


class TestTaskErrorScenarios:
    """Test task error scenarios."""

    def test_task_with_invalid_parameters(self):
        """Test task behavior with invalid parameters."""
        # Test with None values
        email_result = send_email(None, None, None)
        assert isinstance(email_result, bool)  # Should handle gracefully

        # Test with empty values
        result = process_data("")
        assert isinstance(result, str)
        assert result == ""

    def test_task_failure_recovery(self):
        """Test task failure and recovery scenarios."""
        # Simulate a task that sometimes fails
        @task()
        def unreliable_task(should_fail=False):
            if should_fail:
                raise Exception("Simulated task failure")
            return "task completed"

        # Test successful execution
        success_result = unreliable_task(should_fail=False)
        assert success_result == "task completed"

        # Test failure
        with pytest.raises(Exception, match="Simulated task failure"):
            unreliable_task(should_fail=True)

    def test_task_resource_cleanup(self):
        """Test task resource cleanup scenarios."""
        # Tasks that should handle resource cleanup properly
        # This is more of an integration test

        @task()
        def resource_task():
            # Simulate resource usage
            resources = ["resource1", "resource2"]
            try:
                # Normally would use some resources
                return {"resources_used": len(resources)}
            finally:
                # Cleanup should happen here
                pass

        result = resource_task()
        assert isinstance(result, dict)
        assert "resources_used" in result


class TestBatchOperations:
    """Test batch operations with tasks."""

    def test_batch_task_execution(self):
        """Test executing multiple tasks in batch."""
        # Create a batch of tasks
        tasks = [
            lambda: process_data(f"item_{i}") for i in range(5)
        ]

        results = []
        for task_func in tasks:
            result = task_func()
            results.append(result)

        # Verify all tasks completed
        assert len(results) == 5
        assert all(isinstance(r, str) for r in results)  # All should be uppercase strings
        assert all(r.startswith("ITEM_") for r in results)  # All should be uppercased

    def test_batch_task_with_errors(self):
        """Test batch execution with some errors."""
        results = []
        errors = []

        def execute_task_safely(task_func):
            try:
                result = task_func()
                results.append(result)
                return True
            except Exception as e:
                errors.append(e)
                return False

        # Create tasks that might fail
        tasks = [
            lambda: process_data(f"item_{i}") for i in range(3)
        ]

        # Execute all tasks
        success_count = sum(1 for task in tasks if execute_task_safely(task))

        # All should succeed for string processing
        assert success_count == 3
        assert len(errors) == 0
        assert len(results) == 3
