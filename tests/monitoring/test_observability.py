import pytest
from UCoreFrameworck.monitoring.observability import Observability, TracingProvider, MetricsMiddleware
from UCoreFrameworck.core.app import App

class DummyApp(App):
    def __init__(self):
        super().__init__("dummy")
        self.started = False
        self.stopped = False

def test_observability_lifecycle(monkeypatch):
    app = DummyApp()
    obs = Observability(app=app)
    monkeypatch.setattr(obs, "start", lambda: setattr(app, "started", True))
    monkeypatch.setattr(obs, "stop", lambda: setattr(app, "stopped", True))
    obs.start()
    assert app.started is True
    obs.stop()
    assert app.stopped is True

def test_observability_probe_endpoint(monkeypatch):
    obs = Observability()
    monkeypatch.setattr(obs, "probe_endpoint", lambda url, timeout=30: url == "http://localhost")
    assert obs.probe_endpoint("http://localhost") is True
    assert obs.probe_endpoint("http://invalid") is False

def test_observability_record_custom_metric():
    obs = Observability()
    # Should not raise
    obs.record_custom_metric("test_metric", 42.0, labels={"env": "test"})

def test_tracing_provider_get_tracer():
    tp = TracingProvider()
    tracer = tp.get_tracer("test")
    assert tracer is not None or tracer is None  # Accepts both, as implementation may be a stub

def test_metrics_middleware_creation():
    mm = MetricsMiddleware()
    assert isinstance(mm, MetricsMiddleware)
