import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from ucore_framework.core.timemeasure import TimeMeasure

def test_timemeasure_basic(monkeypatch):
    tm = TimeMeasure()
    tm.start_timer("foo", step=2)
    monkeypatch.setattr("time.time", lambda: 100.0)
    tm.lap("foo")
    monkeypatch.setattr("time.time", lambda: 101.0)
    tm.lap("foo")
    laps = tm.get_laps("foo")
    assert len(laps) == 1
    assert abs(laps[0].duration - 1.0) < 1e-6

def test_timemeasure_reset():
    tm = TimeMeasure()
    tm.start_timer("bar")
    tm.lap("bar")
    tm.reset_timer("bar")
    assert tm.get_laps("bar") == []

def test_timemeasure_export(tmp_path):
    tm = TimeMeasure()
    tm.start_timer("baz")
    tm.lap("baz")
    file_path = tmp_path / "laps.csv"
    tm.export_laps("baz", str(file_path))
    assert os.path.exists(file_path)
    with open(file_path) as f:
        lines = f.readlines()
    assert lines[0].startswith("Lap,Duration,Label")
