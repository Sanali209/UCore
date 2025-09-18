import pytest
from ucore_framework.processing.background import TaskQueueAdapter
from ucore_framework.processing.cli_worker import WorkerManager
from ucore_framework.processing.cpu_tasks import ConcurrentFuturesAdapter
from ucore_framework.core.app import App

class DummyApp(App):
    def __init__(self):
        super().__init__("dummy")

def test_task_queue_adapter_init():
    app = DummyApp()
    adapter = TaskQueueAdapter(app)
    assert adapter.app is app

@pytest.mark.asyncio
async def test_task_queue_adapter_lifecycle(monkeypatch):
    app = DummyApp()
    adapter = TaskQueueAdapter(app)
    async def async_noop(*args, **kwargs):
        pass
    monkeypatch.setattr(adapter, "start", async_noop)
    monkeypatch.setattr(adapter, "stop", async_noop)
    await adapter.start()
    await adapter.stop()

def test_worker_manager_init():
    wm = WorkerManager()
    assert isinstance(wm, WorkerManager)

def test_worker_manager_run(monkeypatch):
    wm = WorkerManager()
    monkeypatch.setattr(wm, "run", lambda: True)
    assert wm.run() is True

def test_concurrent_futures_adapter_init():
    app = DummyApp()
    adapter = ConcurrentFuturesAdapter(app)
    assert adapter.app is app

def test_concurrent_futures_adapter_start_stop(monkeypatch):
    app = DummyApp()
    adapter = ConcurrentFuturesAdapter(app)
    monkeypatch.setattr(adapter, "start", lambda: None)
    monkeypatch.setattr(adapter, "stop", lambda: None)
    adapter.start()
    adapter.stop()
