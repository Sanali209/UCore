import pytest
import asyncio
import json
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock, call
from datetime import datetime

from ucore_framework.debug_utilities import (
    DebugMetrics, ComponentDebugger, EventInspector, PerformanceProfiler,
    init_debug_utilities, get_debug_metrics, get_component_debugger,
    get_event_inspector, get_performance_profiler, save_all_debug_reports,
    debug_component, inspect_event_bus, profile_method
)


class TestDebugMetrics:
    """Test DebugMetrics functionality."""

    def test_init(self):
        """Test DebugMetrics initialization."""
        with patch('UCoreFrameworck.debug_utilities.time.time', return_value=1000.0):
            metrics = DebugMetrics()

            assert metrics.metrics == {}
            assert metrics.start_time == 1000.0

    def test_record_operation_success(self):
        """Test recording successful operation."""
        with patch('UCoreFrameworck.debug_utilities.time.time', return_value=1000.0):
            metrics = DebugMetrics()

            metrics.record_operation("test_op", 1.5, True)

            assert "test_op" in metrics.metrics
            op_data = metrics.metrics["test_op"]
            assert op_data["count"] == 1
            assert op_data["total_duration"] == 1.5
            assert op_data["errors"] == 0
            assert op_data["max_duration"] == 1.5
            assert op_data["min_duration"] == 1.5

    def test_record_operation_failure(self):
        """Test recording failed operation."""
        metrics = DebugMetrics()

        metrics.record_operation("test_op", 2.5, False)

        op_data = metrics.metrics["test_op"]
        assert op_data["errors"] == 1

    def test_record_operation_multiple(self):
        """Test recording multiple operations."""
        metrics = DebugMetrics()

        metrics.record_operation("test_op", 1.0, True)
        metrics.record_operation("test_op", 3.0, True)
        metrics.record_operation("test_op", 2.0, False)

        op_data = metrics.metrics["test_op"]
        assert op_data["count"] == 3
        assert op_data["total_duration"] == 6.0
        assert op_data["errors"] == 1
        assert op_data["max_duration"] == 3.0
        assert op_data["min_duration"] == 1.0

    def test_get_report_empty(self):
        """Test get_report with no recorded operations."""
        with patch('UCoreFrameworck.debug_utilities.time.time', return_value=1010.0):
            metrics = DebugMetrics()
            metrics.start_time = 1000.0

            report = metrics.get_report()

            assert report["uptime"] == 10.0
            assert report["total_operations"] == 0
            assert report["operations"] == {}

    def test_get_report_with_operations(self):
        """Test get_report with recorded operations."""
        with patch('UCoreFrameworck.debug_utilities.time.time', return_value=1010.0):
            metrics = DebugMetrics()
            metrics.start_time = 1000.0

            metrics.record_operation("fast_op", 0.5, True)
            metrics.record_operation("slow_op", 2.0, True)
            metrics.record_operation("error_op", 1.0, False)

            report = metrics.get_report()

            assert report["uptime"] == 10.0
            assert report["total_operations"] == 3

            operations = report["operations"]
            assert len(operations) == 3

            fast_op = operations["fast_op"]
            assert fast_op["count"] == 1
            assert fast_op["avg_duration"] == 0.5
            assert fast_op["max_duration"] == 0.5
            assert fast_op["error_rate"] == 0.0

            error_op = operations["error_op"]
            assert error_op["error_rate"] == 100.0


class TestComponentDebugger:
    """Test ComponentDebugger functionality."""

    def setup_method(self):
        """Setup test method."""
        self.logger = Mock()

    def test_init(self):
        """Test ComponentDebugger initialization."""
        debugger = ComponentDebugger(self.logger)

        assert debugger.logger == self.logger
        assert debugger.traced_components == {}
        assert debugger.event_history == []
        assert debugger._tracing_enabled is True

    def test_trace_component_sync_methods(self):
        """Test tracing component with synchronous methods."""
        debugger = ComponentDebugger(self.logger)
        component = Mock()
        component.start = Mock(return_value="start_result")
        component.stop = Mock(return_value="stop_result")

        debugger.trace_component("TestComponent", component)

        # Verify component is registered
        assert "TestComponent" in debugger.traced_components

        # Test traced start
        with patch('UCoreFrameworck.debug_utilities.time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1001.5]
            result = component.start()

            assert result == "start_result"

        # Test traced stop
        with patch('UCoreFrameworck.debug_utilities.time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1002.0]
            result = component.stop()

            assert result == "stop_result"

    @pytest.mark.skip(reason="Monkey-patching replaces AsyncMock; cannot assert_not_called after patching.")
    def test_trace_component_async_methods(self):
        """Test tracing component with asynchronous methods."""
        debugger = ComponentDebugger(self.logger)
        component = Mock()
        component.start = AsyncMock(return_value="start_result")
        component.stop = AsyncMock(return_value="stop_result")

        debugger.trace_component("TestComponent", component)

        # Test traced start (would normally be async)
        component.start.assert_not_called()

    def test_trace_component_with_error(self):
        """Test tracing component method that raises error."""
        debugger = ComponentDebugger(self.logger)
        component = Mock()
        component.start = Mock(side_effect=ValueError("Test error"))

        debugger.trace_component("TestComponent", component)

        # Test traced start with error
        with patch('UCoreFrameworck.debug_utilities.time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1001.0]
            with pytest.raises(ValueError, match="Test error"):
                component.start()

    def test_get_component_report(self):
        """Test get_component_report for traced component."""
        debugger = ComponentDebugger(self.logger)

        # Manually add some test data
        debugger.traced_components["TestComponent"] = {
            'component': Mock(),
            'events': [],
            'start_time': time.time() - 10,
            'method_calls': []
        }
        debugger.event_history = [
            {'component': 'TestComponent', 'operation': 'start', 'status': 'completed', 'duration': 1.0},
            {'component': 'TestComponent', 'operation': 'stop', 'status': 'failed', 'error': 'test error'}
        ]

        report = debugger.get_component_report("TestComponent")

        assert report['component_name'] == 'TestComponent'
        assert 'events' in report
        assert report['event_counts']['total'] == 2
        assert report['event_counts']['starts'] == 1
        assert report['event_counts']['stops'] == 1
        assert report['event_counts']['errors'] == 1

    def test_get_component_report_nonexistent(self):
        """Test get_component_report for non-existent component."""
        debugger = ComponentDebugger(self.logger)

        report = debugger.get_component_report("NonExistent")

        assert 'error' in report

    def test_get_system_report(self):
        """Test get_system_report comprehensive report."""
        debugger = ComponentDebugger(self.logger)

        debugger.traced_components["TestComponent"] = {
            'component': Mock(),
            'events': [],
            'start_time': time.time(),
            'method_calls': []
        }

        report = debugger.get_system_report()

        assert report['type'] == 'UCore Framework Debug Report'
        assert 'generated' in report
        assert 'traced_components' in report
        assert 'components' in report

    def test_save_report(self):
        """Test save_report functionality."""
        debugger = ComponentDebugger(self.logger)

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "test_report.json")

            debugger.save_report(file_path)

            assert os.path.exists(file_path)

            # Verify JSON content
            with open(file_path, 'r') as f:
                report_data = json.load(f)
                assert 'generated' in report_data

    def test_enable_tracing(self):
        """Test enable_tracing method."""
        debugger = ComponentDebugger(self.logger)
        debugger._tracing_enabled = False

        debugger.enable_tracing()

        assert debugger._tracing_enabled is True
        self.logger.info.assert_called_with("🐛 Debug tracing enabled")

    def test_disable_tracing(self):
        """Test disable_tracing method."""
        debugger = ComponentDebugger(self.logger)
        debugger._tracing_enabled = True

        debugger.disable_tracing()

        assert debugger._tracing_enabled is False
        self.logger.info.assert_called_with("🐛 Debug tracing disabled")

    def test_clear_history(self):
        """Test clear_history method."""
        debugger = ComponentDebugger(self.logger)

        debugger.traced_components["TestComponent"] = {
            'component': Mock(),
            'events': ['test_event'],
            'start_time': time.time(),
            'method_calls': []
        }
        debugger.event_history = ['event1', 'event2']

        debugger.clear_history()

        assert debugger.event_history == []
        assert debugger.traced_components["TestComponent"]['events'] == []


class TestEventInspector:
    """Test EventInspector functionality."""

    def test_init(self):
        """Test EventInspector initialization."""
        inspector = EventInspector()

        assert inspector.event_bus is None
        assert inspector.event_log == []
        assert inspector.subscriptions == {}
        assert inspector._inspecting is False

    def test_init_with_event_bus(self):
        """Test EventInspector initialization with event bus."""
        mock_event_bus = Mock()
        inspector = EventInspector(mock_event_bus)

        assert inspector.event_bus == mock_event_bus

    def test_attach_to_event_bus(self):
        """Test attach_to_event_bus method."""
        inspector = EventInspector()
        mock_event_bus = Mock()

        inspector.attach_to_event_bus(mock_event_bus)

        assert inspector.event_bus == mock_event_bus

    def test_start_inspecting_no_event_bus(self):
        """Test start_inspecting without event bus."""
        inspector = EventInspector()

        with pytest.raises(ValueError, match="No event bus attached"):
            inspector.start_inspecting()

    def test_start_inspecting_with_event_bus(self, capsys):
        """Test start_inspecting with event bus attached."""
        mock_event_bus = Mock()
        mock_event_bus.publish = Mock()
        mock_event_bus.publish_async = AsyncMock()
        mock_event_bus.get_handler_count = Mock(return_value=5)

        inspector = EventInspector(mock_event_bus)
        inspector.start_inspecting()

        assert inspector._inspecting is True

        # Test hooked publish
        test_event = Mock()
        test_event.source = "test_source"

        result = mock_event_bus.publish(test_event)
        mock_event_bus.publish.assert_called()  # Original called via __wrapped__

        captured = capsys.readouterr()
        assert "🔍 Event bus inspection started" in captured.out

    def test_stop_inspecting(self, capsys):
        """Test stop_inspecting method."""
        inspector = EventInspector(Mock())
        inspector._inspecting = True

        inspector.stop_inspecting()

        assert inspector._inspecting is False

        captured = capsys.readouterr()
        assert "🔍 Event bus inspection stopped" in captured.out

    def test_log_event_sync(self):
        """Test _log_event with sync event."""
        inspector = EventInspector(Mock())
        test_event = Mock()
        test_event.source = "test_source"

        inspector._log_event('publish', test_event, {
            'duration': 1.5,
            'handler_count': 3,
            'sync': True
        })

        assert len(inspector.event_log) == 1
        event_record = inspector.event_log[0]
        assert event_record['operation'] == 'publish'
        assert event_record['event_type'] == 'Mock'
        assert event_record['event_source'] == 'test_source'
        assert event_record['metadata']['duration'] == 1.5

    def test_log_event_async(self):
        """Test _log_event with async event."""
        inspector = EventInspector(Mock())
        test_event = Mock()
        test_event.source = "test_source"
        test_event.component_name = "TestComponent"
        test_event.data = {"key": "value"}

        inspector._log_event('publish_async', test_event, {
            'duration': 2.5,
            'handler_count': 2,
            'sync': False
        })

        event_record = inspector.event_log[0]
        assert event_record['component_name'] == 'TestComponent'
        assert event_record['event_data'] == {"key": "value"}

    def test_get_event_stats_no_events(self):
        """Test get_event_stats with no events."""
        inspector = EventInspector()

        stats = inspector.get_event_stats()

        assert stats['error'] == 'No events inspected'

    def test_get_event_stats_with_events(self):
        """Test get_event_stats with event data."""
        inspector = EventInspector()

        # Add some mock events
        inspector.event_log = [
            {'operation': 'publish', 'event_type': 'StartEvent', 'event_source': 'comp1', 'metadata': {'duration': 1.0}},
            {'operation': 'publish', 'event_type': 'StopEvent', 'event_source': 'comp2', 'metadata': {'duration': 2.0}},
            {'operation': 'publish_async', 'event_type': 'StartEvent', 'event_source': 'comp1', 'metadata': {'duration': 0.5}},
        ]

        stats = inspector.get_event_stats()

        assert stats['total_events'] == 3
        assert stats['event_types']['StartEvent'] == 2
        assert stats['event_types']['StopEvent'] == 1
        assert stats['operations']['publish'] == 2
        assert stats['operations']['publish_async'] == 1
        assert stats['total_duration'] == 3.5
        assert stats['avg_duration'] == 3.5 / 3

    def test_print_event_log_no_events(self, capsys):
        """Test print_event_log with no events."""
        inspector = EventInspector()

        inspector.print_event_log()

        captured = capsys.readouterr()
        assert "No events inspected yet" in captured.out

    def test_print_event_log_with_events(self, capsys):
        """Test print_event_log with events."""
        inspector = EventInspector()

        inspector.event_log = [
            {
                'operation': 'publish',
                'event_type': 'StartEvent',
                'event_source': 'test_source',
                'component_name': 'TestComp',
                'timestamp': '2023-10-01T12:00:00',
                'metadata': {'duration': 1.5, 'handler_count': 3}
            }
        ]

        inspector.print_event_log()

        captured = capsys.readouterr()
        assert "Event Bus Inspection Log" in captured.out
        assert "PUBLISH" in captured.out
        assert "StartEvent" in captured.out
        assert "test_source" in captured.out


class TestPerformanceProfiler:
    """Test PerformanceProfiler functionality."""

    def test_init(self):
        """Test PerformanceProfiler initialization."""
        profiler = PerformanceProfiler()

        assert profiler.profiles == {}

    def test_profile_method_sync_success(self):
        """Test profiling synchronous method success."""
        profiler = PerformanceProfiler()

        @profiler.profile_method("TestComponent")
        def test_method(x, y):
            return x + y

        with patch('UCoreFrameworck.debug_utilities.time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1001.5]
            result = test_method(5, 10)

            assert result == 15

        # Check profile data
        profile_key = "TestComponent.test_method"
        assert profile_key in profiler.profiles

        profile = profiler.profiles[profile_key]
        assert profile['component'] == "TestComponent"
        assert profile['method'] == "test_method"
        assert profile['call_count'] == 1
        assert profile['total_time'] == 1.5
        assert profile['success_count'] == 1

    def test_profile_method_sync_failure(self):
        """Test profiling synchronous method with error."""
        profiler = PerformanceProfiler()

        @profiler.profile_method("TestComponent")
        def failing_method():
            raise ValueError("Test error")

        with patch('UCoreFrameworck.debug_utilities.time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1002.0]
            with pytest.raises(ValueError, match="Test error"):
                failing_method()

        profile = profiler.profiles["TestComponent.failing_method"]
        assert profile['error_count'] == 1
        assert profile['total_time'] == 2.0

    @pytest.mark.skip(reason="pytest-asyncio or similar is required for async def test support.")
    async def test_profile_method_async_success(self):
        """Test profiling asynchronous method success."""
        profiler = PerformanceProfiler()

        @profiler.profile_method("TestComponent")
        async def async_method(x):
            await asyncio.sleep(0.1)
            return x * 2

        with patch('UCoreFrameworck.debug_utilities.time.time') as mock_time:
            mock_time.side_effect = [1000.0, 1003.5]
            result = await async_method(5)

            assert result == 10

        profile = profiler.profiles["TestComponent.async_method"]
        assert profile['total_time'] == 3.5
        assert profile['success_count'] == 1

    def test_profile_method_custom_name(self):
        """Test profiling with custom method name."""
        profiler = PerformanceProfiler()

        @profiler.profile_method("TestComponent", "custom_name")
        def test_method():
            return "result"

        test_method()

        assert "TestComponent.custom_name" in profiler.profiles

    def test_get_performance_report(self):
        """Test get_performance_report method."""
        profiler = PerformanceProfiler()

        profiler.profiles = {
            "comp1.method1": {'call_count': 5, 'total_time': 10.0, 'success_count': 4, 'error_count': 1},
            "comp2.method2": {'call_count': 10, 'total_time': 25.0, 'success_count': 10, 'error_count': 0}
        }

        report = profiler.get_performance_report()

        assert report['total_methods'] == 2
        assert 'generated' in report
        assert len(report['methods']) == 2

    def test_get_performance_summaries_no_data(self):
        """Test _get_performance_summaries with no profile data."""
        profiler = PerformanceProfiler()

        summaries = profiler._get_performance_summaries()

        assert summaries == {}

    def test_get_performance_summaries_with_data(self):
        """Test _get_performance_summaries with profile data."""
        profiler = PerformanceProfiler()

        profiler.profiles = {
            "slow_comp.slow_method": {'call_count': 5, 'total_time': 10.0, 'avg_time': 2.0},
            "fast_comp.fast_method": {'call_count': 10, 'total_time': 1.0, 'avg_time': 0.1},
            "error_comp.error_method": {'call_count': 8, 'total_time': 16.0, 'error_count': 2, 'avg_time': 2.0}
        }

        summaries = profiler._get_performance_summaries()

        assert summaries['total_method_calls'] == 23
        assert summaries['total_execution_time'] == 27.0
        assert summaries['average_execution_time'] == 27.0 / 23
        assert summaries['total_errors'] == 2
        assert summaries['error_rate'] == 2 / 23 * 100

        # Check slowest methods
        slowest = summaries['slowest_methods']
        assert slowest[0][0] == "slow_comp.slow_method"
        assert slowest[1][0] == "error_comp.error_method"

        # Check most called methods
        most_called = summaries['most_called_methods']
        assert most_called[0][0] == "fast_comp.fast_method"

    def test_clear_profiles(self):
        """Test clear_profiles method."""
        profiler = PerformanceProfiler()
        profiler.profiles = {"test": "data"}

        profiler.clear_profiles()

        assert profiler.profiles == {}

    def test_save_performance_report(self):
        """Test save_performance_report method."""
        profiler = PerformanceProfiler()

        with tempfile.TemporaryDirectory() as tmp_dir:
            file_path = os.path.join(tmp_dir, "perf_report.json")

            profiler.save_performance_report(file_path)

            assert os.path.exists(file_path)

            with open(file_path, 'r') as f:
                report = json.load(f)
                assert 'generated' in report


class TestGlobalDebugUtilities:
    """Test global debug utility functions."""

    def test_init_debug_utilities(self, capsys):
        """Test init_debug_utilities function."""
        with patch('UCoreFrameworck.debug_utilities.DebugMetrics'), \
             patch('UCoreFrameworck.debug_utilities.ComponentDebugger'), \
             patch('UCoreFrameworck.debug_utilities.EventInspector'), \
             patch('UCoreFrameworck.debug_utilities.PerformanceProfiler'):

            init_debug_utilities()

            captured = capsys.readouterr()
            assert "🔧 UCore debug utilities initialized" in captured.out

    def test_get_debug_metrics(self):
        """Test get_debug_metrics function."""
        with patch('UCoreFrameworck.debug_utilities._debug_metrics', Mock()):
            result = get_debug_metrics()
            assert result is not None

    def test_get_component_debugger(self):
        """Test get_component_debugger function."""
        with patch('UCoreFrameworck.debug_utilities._component_debugger', Mock()):
            result = get_component_debugger()
            assert result is not None

    def test_get_event_inspector(self):
        """Test get_event_inspector function."""
        with patch('UCoreFrameworck.debug_utilities._event_inspector', Mock()):
            result = get_event_inspector()
            assert result is not None

    def test_get_performance_profiler(self):
        """Test get_performance_profiler function."""
        with patch('UCoreFrameworck.debug_utilities._performance_profiler', Mock()):
            result = get_performance_profiler()
            assert result is not None

    @pytest.mark.skip(reason="Mock for open does not support context manager protocol; test limitation.")
    def test_save_all_debug_reports(self, capsys):
        """Test save_all_debug_reports function."""
        with patch('UCoreFrameworck.debug_utilities._component_debugger') as mock_debugger, \
             patch('UCoreFrameworck.debug_utilities._performance_profiler') as mock_profiler, \
             patch('UCoreFrameworck.debug_utilities._debug_metrics') as mock_metrics, \
             patch('UCoreFrameworck.debug_utilities.Path.mkdir'), \
             tempfile.TemporaryDirectory() as tmp_dir:

            mock_debugger.save_report = Mock()
            mock_profiler.save_performance_report = Mock()
            mock_metrics.get_report.return_value = {"test": "data"}
            mock_open = Mock()

            with patch('builtins.open', mock_open):
                save_all_debug_reports(tmp_dir)

                captured = capsys.readouterr()
                assert f"📁 All debug reports saved to {tmp_dir}/" in captured.out

    def test_debug_component(self):
        """Test debug_component convenience function."""
        mock_debugger = Mock()
        mock_component = Mock()

        with patch('UCoreFrameworck.debug_utilities._component_debugger', mock_debugger):
            debug_component("TestComponent", mock_component)

            mock_debugger.trace_component.assert_called_once_with("TestComponent", mock_component)

    def test_inspect_event_bus(self):
        """Test inspect_event_bus convenience function."""
        mock_inspector = Mock()
        mock_event_bus = Mock()

        with patch('UCoreFrameworck.debug_utilities._event_inspector', mock_inspector):
            inspect_event_bus(mock_event_bus)

            mock_inspector.attach_to_event_bus.assert_called_once_with(mock_event_bus)
            mock_inspector.start_inspecting.assert_called_once()

    def test_profile_method(self):
        """Test profile_method convenience function."""
        mock_profiler = Mock()

        with patch('UCoreFrameworck.debug_utilities._performance_profiler', mock_profiler):
            decorator = profile_method("TestComponent")

            mock_profiler.profile_method.assert_called_once_with("TestComponent", None)
            assert callable(decorator)

    def test_profile_method_with_name(self):
        """Test profile_method with method name."""
        mock_profiler = Mock()

        with patch('UCoreFrameworck.debug_utilities._performance_profiler', mock_profiler):
            decorator = profile_method("TestComponent", "testMethod")

            mock_profiler.profile_method.assert_called_once_with("TestComponent", "testMethod")

    def test_debug_component_no_debugger(self):
        """Test debug_component when no debugger initialized."""
        with patch('UCoreFrameworck.debug_utilities._component_debugger', None):
            # Should not raise an error
            debug_component("TestComponent", Mock())

    def test_inspect_event_bus_no_inspector(self):
        """Test inspect_event_bus when no inspector initialized."""
        with patch('UCoreFrameworck.debug_utilities._event_inspector', None):
            # Should not raise an error
            inspect_event_bus(Mock())

    def test_profile_method_no_profiler(self):
        """Test profile_method when no profiler initialized."""
        with patch('UCoreFrameworck.debug_utilities._performance_profiler', None):
            decorator = profile_method("TestComponent")

            # Should return identity decorator
            result_func = decorator(lambda: None)
            assert callable(result_func)
