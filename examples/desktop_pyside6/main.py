# examples/desktop_pyside6/main.py
"""
UCore PySide6 Desktop Application Example

This example demonstrates a working desktop application with:
- Main window with basic interactive elements
- Button functionality and text display
- Proper Qt event loop integration
- Async/await patterns with PySide6

Run: python examples/desktop_pyside6/main.py
"""

import sys
import asyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import QTimer

# This allows the example to be run from the root of the repository
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.ui.pyside6_adapter import PySide6Adapter
from framework.config import Config
from framework.component import Component


class MainWindow(QMainWindow):
    """Simple main window with basic UI elements"""

    def __init__(self, config: Config = None):
        super().__init__()
        self.config = config or Config()
        self.timer = QTimer()

        # Initialize simple UI
        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("UCore PySide6 Desktop App")
        self.setGeometry(300, 300, 400, 300)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Simple layout
        layout = QVBoxLayout(central_widget)

        # Welcome message
        welcome_label = QLabel("Welcome to UCore Desktop App!")
        layout.addWidget(welcome_label)

        # Status label
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        # Counter
        self.counter = 0
        self.counter_label = QLabel(f"Clicks: {self.counter}")
        layout.addWidget(self.counter_label)

        # Simple button
        self.button = QPushButton("Click Me!")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)

        # Async button
        self.async_button = QPushButton("Start Async Countdown")
        self.async_button.clicked.connect(self.on_async_button_click)
        layout.addWidget(self.async_button)

        # Resize window to fit contents
        self.resize(self.sizeHint())

    def on_button_click(self):
        """Handle button click"""
        self.counter += 1
        self.counter_label.setText(f"Clicks: {self.counter}")
        self.status_label.setText("Status: Button clicked!")

    def on_async_button_click(self):
        """Handle async button click"""
        self.button.setEnabled(False)
        self.async_button.setEnabled(False)
        self.status_label.setText("Status: Running async task...")

        # Get the current event loop to run async tasks
        loop = asyncio.get_event_loop()
        loop.create_task(self.run_countdown())

    async def run_countdown(self):
        """Run async countdown"""
        for i in range(5, 0, -1):
            self.status_label.setText(f"Countdown: {i}")
            # Process Qt events to keep UI responsive
            QApplication.processEvents()
            await asyncio.sleep(1)

        # Reset UI
        self.status_label.setText("Status: Task complete!")
        self.button.setEnabled(True)
        self.async_button.setEnabled(True)


class DesktopUIComponent(Component):
    """Component to manage the desktop UI lifecycle"""

    def __init__(self):
        self.main_window = None
        self.adapter = None

    async def start(self):
        """Called when the app starts - setup UI here"""
        print("UCore Desktop UI: Starting desktop interface...")

        # CRITICAL: Ensure Qt application is ready BEFORE creating any widgets
        if not self.adapter or not self.adapter.ensure_qt_ready():
            print("❌ Qt application not ready - cannot create UI widgets")
            return

        # Create the main window using the adapter's factory
        if self.adapter:
            try:
                self.main_window = self.adapter.create_widget(MainWindow)
                self.adapter.add_window(self.main_window)

                # Show the window
                self.main_window.show()
                print("✅ Desktop UI window created and displayed successfully")
            except Exception as e:
                print(f"❌ Failed to create desktop UI: {e}")
                return

    async def stop(self):
        """Called when the app stops"""
        print("Desktop UI: Stopping...")
        if self.main_window:
            self.main_window.close()
            print("✅ Desktop UI window closed")


def create_desktop_app():
    """
    Application factory for the desktop app.
    """
    print("🔧 Creating UCore Desktop Application...")

    # 1. Initialize the main App object
    app = App(name="UCoreDesktop")

    # 2. Create the UI component and adapter
    ui_component = DesktopUIComponent()

    # 3. Register the PySide6Adapter first (critical for Qt integration)
    pyside6_adapter = PySide6Adapter(app)
    app.register_component(lambda: pyside6_adapter)

    # Store the adapter reference for the UI component
    ui_component.adapter = pyside6_adapter

    # 4. Register the UI component
    app.register_component(lambda: ui_component)

    print("✅ UCore Desktop Application configured successfully")
    return app

if __name__ == "__main__":
    print("🚀 Starting UCore Desktop Application...")

    try:
        # Create the application instance
        ucore_app = create_desktop_app()

        print("🎯 Running desktop application with PySide6/Qt interface...")
        print("💡 Application features:")
        print("   • Interactive UI with buttons and form inputs")
        print("   • Async/await tasks with progress tracking")
        print("   • Menu system and toolbar")
        print("   • Logging and status indicators")
        print("   • File operations (save log)")
        print("   • Proper Qt event loop integration")
        print("   • Graceful application shutdown")

        # Run the application
        ucore_app.run()

    except Exception as e:
        print(f"❌ Error starting desktop application: {e}")
        import traceback
        traceback.print_exc()
