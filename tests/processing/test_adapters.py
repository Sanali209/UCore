import pytest
from framework.processing.background import TaskQueueAdapter
from framework.processing.cli_worker import WorkerManager
from framework.processing.cpu_tasks import ConcurrentFuturesAdapter
from framework.core.app import App

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
    monkeypatch.setattr(adapter, "start", lambda: None)
    monkeypatch.setattr(adapter, "stop", lambda: None)
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
