import pytest
from ucore_framework.monitoring.progress import ProgressManager, TqdmProgressVisualizer, LoguruProgressVisualizer, ProgressVisualizer

class DummyVisualizer(ProgressVisualizer):
    def __init__(self):
        self.updates = []

    def update_progress(self, progress, max_progress, message, description):
        self.updates.append((progress, max_progress, message, description))

def test_progress_manager_add_visualizer_and_step(monkeypatch):
    pm = ProgressManager(max_progress=5, description="Test Progress")
    dummy = DummyVisualizer()
    pm.add_visualizer(dummy)
    pm.step("Step 1")
    pm.step("Step 2")
    assert len(dummy.updates) == 2
    assert dummy.updates[0][2] == "Step 1"
    assert dummy.updates[1][2] == "Step 2"

def test_progress_manager_set_description():
    pm = ProgressManager(max_progress=3, description="Initial")
    pm.set_description("Updated")
    assert pm.description == "Updated"

def test_progress_manager_reset_and_update():
    pm = ProgressManager(max_progress=2, description="ResetTest")
    pm.step("First")
    pm.reset()
    assert pm.progress == 0
    pm.step("Second")
    assert pm.progress == 1

def test_progress_manager_set_progress():
    pm = ProgressManager(max_progress=4, description="SetProgress")
    pm.set_progress(2, "Halfway")
    assert pm.progress == 2

def test_tqdm_progress_visualizer(monkeypatch):
    # Patch tqdm to avoid actual progress bar in test output
    monkeypatch.setattr("UCoreFrameworck.monitoring.progress.tqdm", lambda *a, **k: None)
    vis = TqdmProgressVisualizer(max_progress=10, description="TQDM Test")
    vis.update_progress(5, 10, "Half", "TQDM Test")

def test_loguru_progress_visualizer(monkeypatch):
    # Patch loguru.logger to avoid actual logging in test output
    monkeypatch.setattr("UCoreFrameworck.monitoring.progress.logger", type("DummyLogger", (), {"info": lambda *a, **k: None})())
    vis = LoguruProgressVisualizer()
    vis.update_progress(3, 10, "Loguru", "Loguru Test")
