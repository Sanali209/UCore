import pytest
from unittest.mock import patch, Mock
from ucore_framework.desktop.ui.pyside6_adapter import PySide6Adapter

@patch('ucore_framework.desktop.ui.pyside6_adapter.QApplication')
@patch('ucore_framework.desktop.ui.pyside6_adapter.qasync')
def test_get_event_loop_initialization(mock_qasync, mock_qapplication):
    mock_app = Mock()
    adapter = PySide6Adapter(mock_app)
    adapter.get_event_loop()
    mock_qapplication.assert_called_once()
    mock_qasync.QEventLoop.assert_called_once_with(mock_qapplication.return_value)
