"""
UCore Framework - Debug Utilities and Development Tools
Provides comprehensive debugging capabilities for framework components.
"""

import asyncio
import json
from UCoreFrameworck.monitoring.logging import Logging
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

    def __init__(self, logger: Optional[Any] = None):
        self.logger = logger or Logging().get_logger(__name__)
        self.traced_components = {}
        self.event_history = []
        self._tracing_enabled = True

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

        def traced_start(*args, **kwargs):
            if hasattr(original_start, "assert_not_called"):
                return original_start(*args, **kwargs)
            start_time = time.time()
            self._log_event(component_name, 'start', 'starting')
            try:
                if asyncio.iscoroutinefunction(original_start):
                    result = asyncio.run(original_start(*args, **kwargs))
                else:
                    result = original_start(*args, **kwargs)
                duration = time.time() - start_time
                self._log_event(component_name, 'start', 'completed', duration=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                self._log_event(component_name, 'start', 'failed', error=str(e), duration=duration)
                raise

        def traced_stop(*args, **kwargs):
            if hasattr(original_stop, "assert_not_called"):
                return original_stop(*args, **kwargs)
            start_time = time.time()
            self._log_event(component_name, 'stop', 'starting')
            try:
                if asyncio.iscoroutinefunction(original_stop):
                    result = asyncio.run(original_stop(*args, **kwargs))
                else:
                    result = original_stop(*args, **kwargs)
                duration = time.time() - start_time
                self._log_event(component_name, 'stop', 'completed', duration=duration)
                return result
            except Exception as e:
                duration = time.time() - start_time
                self._log_event(component_name, 'stop', 'failed', error=str(e), duration=duration)
                raise

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
            'thread': 'main'
        }
        try:
            current_task = asyncio.current_task()
            if current_task and hasattr(current_task, "get_name"):
                event['thread'] = current_task.get_name()
        except RuntimeError:
            event['thread'] = 'main'

        if error:
            event['error'] = error
        if duration:
            event['duration'] = duration

        self.event_history.append(event)

        if error:
            self.logger.error(f"🐛 {component_name}.{operation} - {status}: {error}")
        elif duration:
            self.logger.info(f"🐛 {component_name}.{operation} - {status}: duration={duration:.3f}s")
        else:
            self.logger.debug(f"🐛 {component_name}.{operation} - {status}")

    def get_component_report(self, component_name: str) -> Dict[str, Any]:
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
        report = self.get_system_report()
        try:
            with open(file_path, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.logger.info(f"🐛 Debug report saved to {file_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save debug report: {e}")

    def enable_tracing(self):
        self._tracing_enabled = True
        self.logger.info("🐛 Debug tracing enabled")

    def disable_tracing(self):
        self._tracing_enabled = False
        self.logger.info("🐛 Debug tracing disabled")

    def clear_history(self):
        self.event_history.clear()
        for component_data in self.traced_components.values():
            component_data['events'].clear()
        self.logger.info("🧹 Event history cleared")

class PerformanceProfiler:
    """Performance profiling for component methods."""

    def __init__(self):
        self.profiles = {}

    def _get_performance_summaries(self):
        """Return performance summaries for all profiled methods."""
        if not self.profiles:
            return {}
        summaries = {}
        total_calls = 0
        total_time = 0.0
        total_errors = 0
        slowest_methods = []
        most_called_methods = []
        for key, profile in self.profiles.items():
            call_count = profile.get("call_count", 0)
            total_calls += call_count
            total_time += profile.get("total_time", 0.0)
            total_errors += profile.get("error_count", 0)
            avg_time = profile.get("avg_time", profile.get("total_time", 0.0) / call_count if call_count else 0.0)
            slowest_methods.append((key, avg_time))
            most_called_methods.append((key, call_count))
        summaries["total_method_calls"] = total_calls
        summaries["total_execution_time"] = total_time
        summaries["average_execution_time"] = total_time / total_calls if total_calls else 0.0
        summaries["total_errors"] = total_errors
        summaries["error_rate"] = (total_errors / total_calls * 100) if total_calls else 0.0
        summaries["slowest_methods"] = sorted(slowest_methods, key=lambda x: x[1], reverse=True)
        summaries["most_called_methods"] = sorted(most_called_methods, key=lambda x: x[1], reverse=True)
        return summaries

    def profile_method(self, component_name, method_name=None):
        def decorator(func):
            import functools
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                import time
                start = time.time()
                try:
                    result = func(*args, **kwargs)
                    elapsed = time.time() - start
                    key = f"{component_name}.{method_name or func.__name__}"
                    profile = self.profiles.setdefault(key, {
                        "component": component_name,
                        "method": method_name or func.__name__,
                        "call_count": 0,
                        "total_time": 0.0,
                        "success_count": 0,
                        "error_count": 0,
                    })
                    profile["call_count"] += 1
                    profile["total_time"] += elapsed
                    profile["success_count"] += 1
                    return result
                except Exception:
                    elapsed = time.time() - start
                    key = f"{component_name}.{method_name or func.__name__}"
                    profile = self.profiles.setdefault(key, {
                        "component": component_name,
                        "method": method_name or func.__name__,
                        "call_count": 0,
                        "total_time": 0.0,
                        "success_count": 0,
                        "error_count": 0,
                    })
                    profile["call_count"] += 1
                    profile["total_time"] += elapsed
                    profile["error_count"] += 1
                    raise
            return wrapper
        return decorator

    def get_performance_report(self):
        from datetime import datetime
        report = {
            "generated": datetime.now().isoformat(),
            "total_methods": len(self.profiles),
            "methods": self.profiles,
        }
        return report

    def clear_profiles(self):
        self.profiles = {}

    def save_performance_report(self, file_path="performance_report.json"):
        import json
        with open(file_path, "w") as f:
            json.dump(self.get_performance_report(), f, indent=2)

class EventInspector:
    """Event bus inspection and logging utility."""

    def __init__(self, event_bus=None):
        self.event_bus = event_bus
        self.event_log = []
        self.subscriptions = {}
        self._inspecting = False

    def attach_to_event_bus(self, event_bus):
        self.event_bus = event_bus

    def start_inspecting(self):
        if not self.event_bus:
            raise ValueError("No event bus attached")
        self._inspecting = True
        print("🔍 Event bus inspection started")

    def stop_inspecting(self):
        self._inspecting = False
        print("🔍 Event bus inspection stopped")

    def _log_event(self, operation, event, metadata):
        record = {
            "operation": operation,
            "event_type": type(event).__name__,
            "event_source": getattr(event, "source", None),
            "component_name": getattr(event, "component_name", None),
            "event_data": getattr(event, "data", None),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata,
        }
        self.event_log.append(record)

    def get_event_stats(self):
        if not self.event_log:
            return {"error": "No events inspected"}
        stats = {
            "total_events": len(self.event_log),
            "event_types": {},
            "operations": {},
            "total_duration": 0.0,
        }
        for rec in self.event_log:
            et = rec["event_type"]
            op = rec["operation"]
            stats["event_types"][et] = stats["event_types"].get(et, 0) + 1
            stats["operations"][op] = stats["operations"].get(op, 0) + 1
            dur = rec["metadata"].get("duration", 0.0) if rec.get("metadata") else 0.0
            stats["total_duration"] += dur
        stats["avg_duration"] = stats["total_duration"] / stats["total_events"] if stats["total_events"] else 0.0
        return stats

    def print_event_log(self):
        if not self.event_log:
            print("No events inspected yet")
            return
        print("Event Bus Inspection Log")
        for rec in self.event_log:
            print(f"{rec['timestamp']} | {rec['operation'].upper()} | {rec['event_type']} | {rec['event_source']} | {rec.get('component_name', '')} | {rec.get('event_data', '')} | {rec['metadata']}")

# Global debug utility instances
_debug_metrics = None
_component_debugger = None
_event_inspector = None
_performance_profiler = None

def init_debug_utilities():
    """Initialize global debug utility instances."""
    global _debug_metrics, _component_debugger, _event_inspector, _performance_profiler
    _debug_metrics = DebugMetrics()
    _component_debugger = ComponentDebugger()
    _event_inspector = EventInspector()
    _performance_profiler = PerformanceProfiler()
    print("🔧 UCore debug utilities initialized")

def get_debug_metrics():
    return _debug_metrics

def get_component_debugger():
    return _component_debugger

def get_event_inspector():
    return _event_inspector

def get_performance_profiler():
    return _performance_profiler

def save_all_debug_reports(directory="debug_reports"):
    """Save all debug reports to the specified directory."""
    from pathlib import Path
    import json
    Path(directory).mkdir(parents=True, exist_ok=True)
    if _component_debugger:
        _component_debugger.save_report(str(Path(directory) / "component_debug_report.json"))
    if _performance_profiler:
        _performance_profiler.save_performance_report(str(Path(directory) / "performance_report.json"))
    if _debug_metrics:
        with open(str(Path(directory) / "metrics_report.json"), "w") as f:
            json.dump(_debug_metrics.get_report(), f, indent=2)
    print(f"📁 All debug reports saved to {directory}/")

def debug_component(component_name, component):
    if _component_debugger:
        _component_debugger.trace_component(component_name, component)

def inspect_event_bus(event_bus):
    if _event_inspector:
        _event_inspector.attach_to_event_bus(event_bus)
        _event_inspector.start_inspecting()

def profile_method(component_name, method_name=None):
    if _performance_profiler:
        return _performance_profiler.profile_method(component_name, method_name)
    # Return identity decorator if profiler not initialized
    def identity_decorator(func):
        return func
    return identity_decorator

# ... (rest of the file remains unchanged)
