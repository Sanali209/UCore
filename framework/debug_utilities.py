"""
UCore Framework - Debug Utilities and Development Tools
Provides comprehensive debugging capabilities for framework components.
"""

import asyncio
import json
import logging
import sys
import time
import traceback
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
from datetime import datetime


class DebugMetrics:
    """Debug metrics collection and reporting."""

    def __init__(self):
        self.metrics = {}
        self.start_time = time.time()

    def record_operation(self, operation_name: str, duration: float, success: bool = True):
        """Record operation metrics."""
        if operation_name not in self.metrics:
            self.metrics[operation_name] = {
                'count': 0,
                'total_duration': 0.0,
                'errors': 0,
                'max_duration': 0.0,
                'min_duration': float('inf')
            }

        metric = self.metrics[operation_name]
        metric['count'] += 1
        metric['total_duration'] += duration
        metric['max_duration'] = max(metric['max_duration'], duration)
        metric['min_duration'] = min(metric['min_duration'], duration)

        if not success:
            metric['errors'] += 1

    def get_report(self) -> Dict[str, Any]:
        """Generate debug metrics report."""
        report = {
            'uptime': time.time() - self.start_time,
            'total_operations': sum(m['count'] for m in self.metrics.values()),
            'operations': {}
        }

        for op_name, data in self.metrics.items():
            if data['count'] > 0:
                avg_duration = data['total_duration'] / data['count']
                error_rate = (data['errors'] / data['count']) * 100
            else:
                avg_duration = 0.0
                error_rate = 0.0

            report['operations'][op_name] = {
                'count': data['count'],
                'avg_duration': avg_duration,
                'max_duration': data['max_duration'],
                'min_duration': data['min_duration'],
                'error_rate': error_rate
            }

        return report


class ComponentDebugger:
    """Debugger for framework components with lifecycle tracing."""

    def __init__(self, logger: Optional[logging.Logger] = None):
        self.logger = logger or logging.getLogger(__name__)
        self.traced_components = {}
        self.event_history = []
        self._tracing_enabled = True

        # Set up detailed logging
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def trace_component(self, component_name: str, component: Any):
        """Start tracing a component's operations."""
        if not self._tracing_enabled:
            return

        self.logger.info(f"🐛 Starting debug trace for component: {component_name}")

        self.traced_components[component_name] = {
            'component': component,
            'events': [],
            'start_time': time.time(),
            'method_calls': []
        }

        # Monkey patch key methods for tracing
        original_start = getattr(component, 'start', None)
        original_stop = getattr(component, 'stop', None)

        def traced_start():
            start_time = time.time()
            self._log_event(component_name, 'start', 'starting')
            try:
                if asyncio.iscoroutinefunction(original_start):
                    return asyncio.create_task(original_start())
                else:
                    result = original_start()
                duration = time.time() - start_time
                self._log_event(component_name, 'start', 'completed',
                               duration=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                self._log_event(component_name, 'start', 'failed',
                               error=str(e), duration=duration)
                raise

        def traced_stop():
            start_time = time.time()
            self._log_event(component_name, 'stop', 'starting')
            try:
                if asyncio.iscoroutinefunction(original_stop):
                    return asyncio.create_task(original_stop())
                else:
                    result = original_stop()
                duration = time.time() - start_time
                self._log_event(component_name, 'stop', 'completed',
                               duration=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                self._log_event(component_name, 'stop', 'failed',
                               error=str(e), duration=duration)
                raise

        # Replace methods
        if original_start:
            setattr(component, 'start', traced_start)
        if original_stop:
            setattr(component, 'stop', traced_stop)

    def _log_event(self, component_name: str, operation: str, status: str,
                   error: str = None, duration: float = None):
        """Log a component event."""
        if not self._tracing_enabled:
            return

        event = {
            'component': component_name,
            'operation': operation,
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'thread': asyncio.current_task().get_name() if asyncio.current_task() else 'main'
        }

        if error:
            event['error'] = error
        if duration:
            event['duration'] = duration

        self.event_history.append(event)

        # Log to logger
        if error:
            self.logger.error(f"🐛 {component_name}.{operation} - {status}: {error}")
        elif duration:
            self.logger.info(".3f"        else:
            self.logger.debug(f"🐛 {component_name}.{operation} - {status}")

    def get_component_report(self, component_name: str) -> Dict[str, Any]:
        """Get debugging report for a specific component."""
        if component_name not in self.traced_components:
            return {'error': f'Component {component_name} not being traced'}

        component_data = self.traced_components[component_name]
        events = [e for e in self.event_history if e['component'] == component_name]

        report = {
            'component_name': component_name,
            'trace_duration': time.time() - component_data['start_time'],
            'events': events,
            'event_counts': {
                'total': len(events),
                'starts': len([e for e in events if e['operation'] == 'start']),
                'stops': len([e for e in events if e['operation'] == 'stop']),
                'errors': len([e for e in events if 'error' in e])
            }
        }

        # Calculate performance metrics
        start_events = [e for e in events if e['operation'] == 'start' and 'duration' in e]
        if start_events:
            durations = [e['duration'] for e in start_events]
            report['performance'] = {
                'avg_start_duration': sum(durations) / len(durations),
                'max_start_duration': max(durations),
                'min_start_duration': min(durations),
                'total_start_time': sum(durations)
            }

        return report

    def get_system_report(self) -> Dict[str, Any]:
        """Get overall system debugging report."""
        report = {
            'type': 'UCore Framework Debug Report',
            'generated': datetime.now().isoformat(),
            'traced_components': list(self.traced_components.keys()),
            'total_events': len(self.event_history),
            'components': {}
        }

        for component_name in self.traced_components:
            report['components'][component_name] = self.get_component_report(component_name)

        return report

    def save_report(self, file_path: str = 'ucore_debug_report.json'):
        """Save debugging report to file."""
        report = self.get_system_report()

        try:
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"🐛 Debug report saved to {file_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save debug report: {e}")

    def enable_tracing(self):
        """Enable debug tracing."""
        self._tracing_enabled = True
        self.logger.info("🐛 Debug tracing enabled")

    def disable_tracing(self):
        """Disable debug tracing."""
        self._tracing_enabled = False
        self.logger.info("🐛 Debug tracing disabled")

    def clear_history(self):
        """Clear event history."""
        self.event_history.clear()
        for component_data in self.traced_components.values():
            component_data['events'].clear()
        self.logger.info("🧹 Event history cleared")


class EventInspector:
    """Inspector for framework event bus operations."""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.event_log = []
        self.subscriptions = {}
        self._inspecting = False

    def attach_to_event_bus(self, event_bus):
        """Attach inspector to an event bus."""
        self.event_bus = event_bus
        if self._inspecting:
            self.start_inspecting()

    def start_inspecting(self):
        """Start inspecting event bus operations."""
        if not self.event_bus:
            raise ValueError("No event bus attached for inspection")

        self._inspecting = True

        # Hook into event publishing
        original_publish = self.event_bus.publish
        original_publish_async = self.event_bus.publish_async

        def inspect_publish(event):
            start_time = time.time()
            result = original_publish(event)
            duration = time.time() - start_time

            self._log_event('publish', event, {
                'duration': duration,
                'handler_count': self.event_bus.get_handler_count(type(event)),
                'sync': True
            })

            return result

        async def inspect_publish_async(event):
            start_time = time.time()
            result = await original_publish_async(event)
            duration = time.time() - start_time

            self._log_event('publish_async', event, {
                'duration': duration,
                'handler_count': self.event_bus.get_handler_count(type(event)),
                'sync': False
            })

            return result

        # Replace methods
        self.event_bus.publish = inspect_publish
        self.event_bus.publish_async = inspect_publish_async

        print("🔍 Event bus inspection started")

    def stop_inspecting(self):
        """Stop inspecting event bus."""
        self._inspecting = False
        print("🔍 Event bus inspection stopped")

    def _log_event(self, operation: str, event: Any, metadata: Dict[str, Any]):
        """Log an event bus operation."""
        event_record = {
            'operation': operation,
            'event_type': type(event).__name__,
            'event_source': getattr(event, 'source', 'unknown'),
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata
        }

        # Add event-specific information
        if hasattr(event, 'component_name'):
            event_record['component_name'] = event.component_name
        if hasattr(event, 'data'):
            event_record['event_data'] = event.data

        self.event_log.append(event_record)
        print(f"🔍 Event: {operation} {event_record['event_type']} from {event_record['event_source']}")

    def get_event_stats(self) -> Dict[str, Any]:
        """Get statistics about inspected events."""
        if not self.event_log:
            return {'error': 'No events inspected'}

        stats = {
            'total_events': len(self.event_log),
            'event_types': {},
            'operations': {},
            'avg_duration': 0,
            'total_duration': 0
        }

        total_duration = 0

        for event in self.event_log:
            # Count event types
            event_type = event['event_type']
            stats['event_types'][event_type] = stats['event_types'].get(event_type, 0) + 1

            # Count operations
            operation = event['operation']
            stats['operations'][operation] = stats['operations'].get(operation, 0) + 1

            # Track duration
            if 'duration' in event['metadata']:
                total_duration += event['metadata']['duration']

        if self.event_log:
            stats['avg_duration'] = total_duration / len(self.event_log)
        stats['total_duration'] = total_duration

        return stats

    def print_event_log(self):
        """Print the event inspection log."""
        if not self.event_log:
            print("🔍 No events inspected yet")
            return

        print("🔍 Event Bus Inspection Log:")
        print("=" * 50)

        for event in self.event_log:
            print(f"[{event['timestamp']}] {event['operation'].upper()}")
            print(f"  Event Type: {event['event_type']}")
            print(f"  Source: {event['event_source']}")
            if 'component_name' in event:
                print(f"  Component: {event['component_name']}")
            if event['metadata']:
                print(f"  Duration: {event['metadata'].get('duration', 'N/A'):.4f}s")
                print(f"  Handler Count: {event['metadata'].get('handler_count', 'N/A')}")
            print()


class PerformanceProfiler:
    """Performance profiling for framework components."""

    def __init__(self):
        self.profiles = {}
        self._active_profilers = {}

    def profile_method(self, component_name: str, method_name: str = None):
        """Decorator to profile a method's performance."""
        def decorator(original_method):
            def wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    if asyncio.iscoroutinefunction(original_method):
                        result = asyncio.create_task(original_method(*args, **kwargs))
                    else:
                        result = original_method(*args, **kwargs)
                    duration = time.time() - start_time
                    success = True
                except Exception as e:
                    duration = time.time() - start_time
                    success = False
                    raise
                finally:
                    # Record performance data
                    self._record_profile(component_name,
                                       method_name or original_method.__name__,
                                       duration, success)

                return result

            async def async_wrapper(*args, **kwargs):
                start_time = time.time()

                try:
                    result = await original_method(*args, **kwargs)
                    duration = time.time() - start_time
                    success = True
                except Exception as e:
                    duration = time.time() - start_time
                    success = False
                    raise
                finally:
                    # Record performance data
                    self._record_profile(component_name,
                                       method_name or original_method.__name__,
                                       duration, success)

                return result

            # Return appropriate wrapper
            if asyncio.iscoroutinefunction(original_method):
                return async_wrapper
            else:
                return wrapper

        return decorator

    def _record_profile(self, component: str, method: str, duration: float, success: bool):
        """Record performance profile data."""
        key = f"{component}.{method}"

        if key not in self.profiles:
            self.profiles[key] = {
                'component': component,
                'method': method,
                'call_count': 0,
                'total_time': 0.0,
                'avg_time': 0.0,
                'max_time': 0.0,
                'min_time': float('inf'),
                'error_count': 0,
                'success_count': 0
            }

        profile = self.profiles[key]
        profile['call_count'] += 1
        profile['total_time'] += duration
        profile['avg_time'] = profile['total_time'] / profile['call_count']
        profile['max_time'] = max(profile['max_time'], duration)
        profile['min_time'] = min(profile['min_time'], duration)

        if success:
            profile['success_count'] += 1
        else:
            profile['error_count'] += 1

    def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report."""
        return {
            'generated': datetime.now().isoformat(),
            'total_methods': len(self.profiles),
            'methods': self.profiles,
            'summaries': self._get_performance_summaries()
        }

    def _get_performance_summaries(self) -> Dict[str, Any]:
        """Calculate performance summaries."""
        if not self.profiles:
            return {}

        total_calls = sum(p['call_count'] for p in self.profiles.values())
        total_time = sum(p['total_time'] for p in self.profiles.values())
        total_errors = sum(p['error_count'] for p in self.profiles.values())

        return {
            'total_method_calls': total_calls,
            'total_execution_time': total_time,
            'average_execution_time': total_time / max(total_calls, 1),
            'total_errors': total_errors,
            'error_rate': (total_errors / max(total_calls, 1)) * 100,

            'slowest_methods': sorted(
                [(k, v['avg_time']) for k, v in self.profiles.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5],

            'most_called_methods': sorted(
                [(k, v['call_count']) for k, v in self.profiles.items()],
                key=lambda x: x[1],
                reverse=True
            )[:5]
        }

    def clear_profiles(self):
        """Clear all performance profile data."""
        self.profiles.clear()

    def save_performance_report(self, file_path: str = 'ucore_performance_report.json'):
        """Save performance report to file."""
        report = self.get_performance_report()

        try:
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            print(f"📊 Performance report saved to {file_path}")
        except Exception as e:
            print(f"❌ Failed to save performance report: {e}")


# Global debug utilities
_debug_metrics = None
_component_debugger = None
_event_inspector = None
_performance_profiler = None


def init_debug_utilities():
    """Initialize global debugging utilities."""
    global _debug_metrics, _component_debugger, _event_inspector, _performance_profiler

    _debug_metrics = DebugMetrics()
    _component_debugger = ComponentDebugger()
    _event_inspector = EventInspector()
    _performance_profiler = PerformanceProfiler()

    print("🔧 UCore debug utilities initialized")


def get_debug_metrics() -> DebugMetrics:
    """Get global debug metrics instance."""
    return _debug_metrics


def get_component_debugger() -> ComponentDebugger:
    """Get global component debugger instance."""
    return _component_debugger


def get_event_inspector() -> EventInspector:
    """Get global event inspector instance."""
    return _event_inspector


def get_performance_profiler() -> PerformanceProfiler:
    """Get global performance profiler instance."""
    return _performance_profiler


def save_all_debug_reports(directory: str = 'debug_reports'):
    """Save all debug reports to specified directory."""
    Path(directory).mkdir(exist_ok=True)

    # Save all reports
    if _component_debugger:
        _component_debugger.save_report(f'{directory}/component_debug.json')

    if _performance_profiler:
        _performance_profiler.save_performance_report(f'{directory}/performance.json')

    # Add metrics report if available
    if _debug_metrics:
        report = _debug_metrics.get_report()
        with open(f'{directory}/debug_metrics.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

    print(f"📁 All debug reports saved to {directory}/")


# Convenience functions
def debug_component(component_name: str, component: Any):
    """Start debugging a component."""
    if _component_debugger:
        _component_debugger.trace_component(component_name, component)


def inspect_event_bus(event_bus):
    """Start inspecting an event bus."""
    if _event_inspector:
        _event_inspector.attach_to_event_bus(event_bus)
        _event_inspector.start_inspecting()


def profile_method(component_name: str, method_name: str = None):
    """Profile a method's performance."""
    if _performance_profiler:
        return _performance_profiler.profile_method(component_name, method_name)
    return lambda func: func
