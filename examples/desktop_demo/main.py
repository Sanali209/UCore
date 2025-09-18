"""
UCore Framework Example: Desktop Features

This example demonstrates:
- UI adapters for PySide6 and Flet
- How to show a real PySide6 window

Usage:
    python -m examples.desktop_demo.main

Requirements:
    pip install loguru PySide6 qasync

"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from ucore_framework.desktop.ui.pyside6_adapter import PySide6Adapter
from ucore_framework.desktop.ui.flet.flet_adapter import FletAdapter
from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout
import qasync
import asyncio

class MockApp:
    def __init__(self):
        self.container = {}
        self.logger = type("Logger", (), {"info": print, "warning": print, "error": print, "debug": print})()

def main():
    app = MockApp()

    # PySide6 UI Adapter demo
    pyside_adapter = PySide6Adapter(app)
    loop = pyside_adapter.get_event_loop()

    # Create a simple window
    window = QWidget()
    window.setWindowTitle("UCore PySide6 Demo")
    layout = QVBoxLayout()
    label = QLabel("Hello from PySide6Adapter!")
    layout.addWidget(label)
    window.setLayout(layout)
    window.show()
    pyside_adapter.add_window(window)

    # Start the Qt event loop using qasync
    loop.run_forever()

    # Flet UI Adapter demo (not shown)
    # def dummy_flet_app(page):
    #     pass
    # flet_adapter = FletAdapter(app, dummy_flet_app)
    # print("FletAdapter initialized:", flet_adapter)

if __name__ == "__main__":
    main()
