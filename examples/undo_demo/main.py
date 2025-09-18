"""
UCore Framework Example: Undo System

This example demonstrates:
- Usage of the undo/redo system from ucore_framework.core.undo

Usage:
    python -m examples.undo_demo.main

Requirements:
    pip install loguru

"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from ucore_framework.core.undo import UndoSystem
from loguru import logger

def main():
    logger.info("Undo system demo started")

    # Create an UndoSystem
    undo_system = UndoSystem()

    # Example state and actions
    state = {'value': 0}

    def increment():
        state['value'] += 1
        logger.info(f"Incremented value to {state['value']}")

    def decrement():
        state['value'] -= 1
        logger.info(f"Decremented value to {state['value']}")

    # Perform increment and add to undo stack
    increment()
    undo_system.add_undo_item(undo=decrement, redo=increment, description="Increment value")

    # Undo the action
    undo_system.undo()
    # Redo the action
    undo_system.redo()

    logger.success("Undo system demo completed")

if __name__ == "__main__":
    main()
