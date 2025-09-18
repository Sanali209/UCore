import pytest
import json
import logging
import sys
from unittest.mock import Mock, patch, MagicMock, call
from io import StringIO
from datetime import datetime

from ucore_framework.monitoring.logging import JsonFormatter, Logging


class TestJsonFormatter:
    """Test JsonFormatter for structured logging."""

    def setup_method(self):
        """Setup for each test."""
        self.formatter = JsonFormatter()
        self.formatter.datefmt = "%Y-%m-%d %H:%M:%S"

    def test_format_basic_log_record(self):
        """Test basic log record formatting."""
        record = Mock()
        record.name = "test.logger"
        record.levelname = "INFO"
        record.getMessage.return_value = "Test message"
        record.exc_info = None

        # Mock time formatting
        with patch.object(self.formatter, 'formatTime', return_value="2023-10-01 12:00:00"):
            result = self.formatter.format(record)

            parsed = json.loads(result)
            assert parsed["name"] == "test.logger"
            assert parsed["level"] == "INFO"
            assert parsed["message"] == "Test message"
            assert parsed["timestamp"] == "2023-10-01 12:00:00"
            assert "exc_info" not in parsed

    def test_format_with_exception_info(self):
        """Test log record formatting with exception information."""
        record = Mock()
        record.name = "error.logger"
        record.levelname = "ERROR"
        record.getMessage.return_value = "Error occurred"
        record.exc_info = ("traceback", "exception", "tb")

        with patch.object(self.formatter, 'formatTime', return_value="2023-10-01 12:00:00"), \
             patch.object(self.formatter, 'formatException', return_value="formatted traceback"):

            result = self.formatter.format(record)

            parsed = json.loads(result)
            assert parsed["level"] == "ERROR"
            assert parsed["message"] == "Error occurred"
            assert parsed["exc_info"] == "formatted traceback"

    def test_format_call_chains(self):
        """Test that formatter methods are called correctly."""
        record = Mock()
        record.name = "test"
        record.levelname = "DEBUG"
        record.getMessage.return_value = "debug message"
        record.exc_info = None

        with patch.object(self.formatter, 'formatTime') as mock_format_time, \
             patch.object(self.formatter, 'formatException') as mock_format_exception:

            mock_format_time.return_value = "formatted_time"
            mock_format_exception.return_value = "formatted_exception"

            result = self.formatter.format(record)

            # Should only call formatTime, not formatException
            mock_format_time.assert_called_once()
            mock_format_exception.assert_not_called()

    def test_format_json_structure(self):
        """Test that formatted output is valid JSON."""
        record = Mock()
        record.name = "test"
        record.levelname = "DEBUG"
        record.getMessage.return_value = "debug message"
        record.exc_info = None
        record.created = 0

        with patch.object(self.formatter, 'formatTime', return_value="2023-10-01 12:00:00"):
            result = self.formatter.format(record)

        # Should be valid JSON
        parsed = json.loads(result)
        assert isinstance(parsed, dict)
        assert set(parsed.keys()) == {"timestamp", "name", "level", "message"}

    def test_format_special_characters(self):
        """Test formatting with special characters in message."""
        record = Mock()
        record.name = "test"
        record.levelname = "DEBUG"
        record.getMessage.return_value = 'Message with "quotes" and \'apostrophes\''
        record.exc_info = None
        record.created = 0

        with patch.object(self.formatter, 'formatTime', return_value="2023-10-01 12:00:00"):
            result = self.formatter.format(record)

        parsed = json.loads(result)
        assert parsed["message"] == 'Message with "quotes" and \'apostrophes\''


class TestLoggingInitialization:
    """Test Logging class initialization and basic functionality."""

    def test_init(self):
        """Test Logging initialization."""
        logging_instance = Logging()

        assert logging_instance._loggers == {}
        assert logging_instance._global_level == "INFO"
        assert hasattr(logging_instance, 'get_logger')
        assert hasattr(logging_instance, 'set_global_level')

    def test_get_available_levels(self):
        """Test get_available_levels method."""
        logging_instance = Logging()

        levels = logging_instance.get_available_levels()

        expected_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        assert levels == expected_levels


class TestLoggingGetLogger:
    """Test the get_logger method functionality."""

    def setup_method(self):
        """Setup for each test."""
        self.logging_instance = Logging()
        self.test_name = "test.module"


    def test_get_logger_cached_logger(self):
        """Test retrieving cached logger."""
        # First create and cache logger
        with patch('logging.getLogger') as mock_get_logger, \
             patch('logging.StreamHandler') as mock_stream_handler:

            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Set up logger for first call
            mock_logger.handlers = []
            mock_logger.level = logging.INFO

            # First call - should create logger
            result1 = self.logging_instance.get_logger(self.test_name, "INFO")

            # Second call - should return cached logger
            result2 = self.logging_instance.get_logger(self.test_name, "DEBUG")

            # Should return same logger instance
            assert result1 == result2
            assert result1 == mock_logger

            # Should update level on cached logger
            mock_logger.setLevel.assert_any_call(logging.INFO)
            mock_logger.setLevel.assert_any_call(logging.DEBUG)
