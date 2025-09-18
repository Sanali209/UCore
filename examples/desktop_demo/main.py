"""
UCore Framework Example: Desktop Features

Demonstrates UI adapters for PySide6 and Flet.
"""

from framework.desktop.ui.pyside6_adapter import PySide6Adapter
from framework.desktop.ui.flet.flet_adapter import FletAdapter

class MockApp:
    def __init__(self):
        self.container = {}
        self.logger = type("Logger", (), {"info": print, "warning": print, "error": print, "debug": print})()

def main():
    app = MockApp()

    # PySide6 UI Adapter demo
    pyside_adapter = PySide6Adapter(app)
    print("PySide6Adapter initialized:", pyside_adapter)

    # Flet UI Adapter demo
    def dummy_flet_app(page):
        pass
    flet_adapter = FletAdapter(app, dummy_flet_app)
    print("FletAdapter initialized:", flet_adapter)

    print("In a real app, these adapters would be registered as components and started by the framework.")

if __name__ == "__main__":
    main()
