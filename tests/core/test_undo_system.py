import pytest
from ucore_framework.core.undo import UndoSystem

def test_undo_redo_basic():
    result = []

    def do_undo():
        result.append("undo")

    def do_redo():
        result.append("redo")

    undo_system = UndoSystem()
    undo_system.add_undo_item(do_undo, do_redo, description="Test action")

    undo_system.undo()
    assert result == ["undo"]
    undo_system.redo()
    assert result == ["undo", "redo"]

def test_undo_stack_clear():
    undo_system = UndoSystem()
    undo_system.add_undo_item(lambda: None, lambda: None)
    undo_system.clear()
    assert len(undo_system.undo_stack) == 0
    assert len(undo_system.redo_stack) == 0

def test_undo_redo_empty():
    undo_system = UndoSystem()
    # Should not raise
    undo_system.undo()
    undo_system.redo()
