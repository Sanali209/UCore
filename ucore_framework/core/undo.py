from UCoreFrameworck.core.component import Component
from typing import Callable, List, Optional
from loguru import logger

class UndoItem:
    def __init__(self, undo: Callable, redo: Callable, description: Optional[str] = None):
        self._undo = undo
        self._redo = redo
        self.description = description

    def do_undo(self):
        logger.info(f"Undo: {self.description or ''}")
        self._undo()

    def do_redo(self):
        logger.info(f"Redo: {self.description or ''}")
        self._redo()

class UndoSystem(Component):
    def __init__(self, name="undo_system"):
        super().__init__(name=name)
        self._undo_stack: List[UndoItem] = []
        self._redo_stack: List[UndoItem] = []

    def add_undo_item(self, undo: Callable, redo: Callable, description: Optional[str] = None):
        item = UndoItem(undo, redo, description)
        self._undo_stack.append(item)
        self._redo_stack.clear()
        logger.info(f"Added undo item: {description or ''}")

    def undo(self):
        if not self._undo_stack:
            logger.warning("Undo stack is empty")
            return
        item = self._undo_stack.pop()
        item.do_undo()
        self._redo_stack.append(item)
        # Optionally: self.emit_event("undo_performed", item)

    def redo(self):
        if not self._redo_stack:
            logger.warning("Redo stack is empty")
            return
        item = self._redo_stack.pop()
        item.do_redo()
        self._undo_stack.append(item)
        # Optionally: self.emit_event("redo_performed", item)

    def clear(self):
        self._undo_stack.clear()
        self._redo_stack.clear()
        logger.info("Undo/redo stacks cleared")

    @property
    def undo_stack(self):
        return list(self._undo_stack)

    @property
    def redo_stack(self):
        return list(self._redo_stack)
