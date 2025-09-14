# examples/desktop_pyside6/simple_test.py
"""
Simple PySide6 test without UCore framework
"""
import sys
import asyncio
from PySide6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QLabel
from PySide6.QtCore import QTimer

class TestWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.counter = 0
        self.init_ui()

    def init_ui(self):
        """Initialize user interface"""
        self.setWindowTitle("Simple PySide6 Test")
        self.setGeometry(300, 300, 400, 300)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Simple layout
        layout = QVBoxLayout(central_widget)

        # Welcome message
        welcome_label = QLabel("Hello! This is a simple PySide6 test.")
        layout.addWidget(welcome_label)

        # Status label
        self.status_label = QLabel("Status: Ready")
        layout.addWidget(self.status_label)

        # Counter
        self.counter_label = QLabel(f"Clicks: {self.counter}")
        layout.addWidget(self.counter_label)

        # Simple button
        self.button = QPushButton("Click Me!")
        self.button.clicked.connect(self.on_button_click)
        layout.addWidget(self.button)

        # Async button
        self.async_button = QPushButton("Test Async")
        self.async_button.clicked.connect(self.test_async)
        layout.addWidget(self.async_button)

        self.resize(self.sizeHint())

    def on_button_click(self):
        self.counter += 1
        self.counter_label.setText(f"Clicks: {self.counter}")
        self.status_label.setText("Button clicked!")

    def test_async(self):
        print("Testing async functionality")
        self.status_label.setText("Async running!")

if __name__ == "__main__":
    print("Starting simple PySide6 test...")

    # Create Qt app
    app = QApplication(sys.argv)

    # Create window
    window = TestWindow()
    window.show()

    print("Window should be visible now")
    print("Close the window to exit")

    # Run event loop
    sys.exit(app.exec())
