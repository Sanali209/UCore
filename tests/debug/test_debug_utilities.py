import pytest
from unittest.mock import Mock
from ucore_framework.debug_utilities import ComponentDebugger, PerformanceProfiler

def test_component_debugger_tracing():
    class MyComponent:
        def start(self):
            pass

    my_component = MyComponent()
    debugger = ComponentDebugger()
    debugger.trace_component("my_comp", my_component)
    my_component.start()
    history = debugger.event_history
    assert len(history) == 2
    assert history[0]["operation"] == "start"
    assert history[0]["status"] == "starting"
    assert history[1]["operation"] == "start"
    assert history[1]["status"] == "completed"

def test_performance_profiler_decorator():
    profiler = PerformanceProfiler()

    @profiler.profile_method("test_component")
    def my_func():
        pass

    my_func()
    my_func()
    profiles = profiler.profiles
    assert "test_component.my_func" in profiles
    assert profiles["test_component.my_func"]["call_count"] == 2
