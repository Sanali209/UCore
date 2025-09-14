# framework/logging.py
import logging
import json
import sys

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record['exc_info'] = self.formatException(record.exc_info)
        return json.dumps(log_record)

class Logging:
    def __init__(self):
        self._loggers = {}
        self._global_level = "INFO"

    def get_logger(self, name: str, level: str = None):
        effective_level = level or self._global_level

        # Convert level string to numeric value with fallback to INFO
        try:
            numeric_level = getattr(logging, effective_level.upper(), logging.INFO)
            if not isinstance(numeric_level, int):
                numeric_level = logging.INFO
        except AttributeError:
            numeric_level = logging.INFO

        if name in self._loggers:
            logger = self._loggers[name]
            # Update level if it's cached and levels differ
            if logger.level != numeric_level:
                logger.setLevel(numeric_level)
            return logger

        logger = logging.getLogger(name)
        logger.setLevel(numeric_level)
        logger.propagate = False # Prevent duplicate logs in parent loggers

        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = JsonFormatter()
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        self._loggers[name] = logger
        return logger

    def set_global_level(self, level: str):
        """
        Set the global logging level for all existing and future loggers.
        Gracefully handles invalid level names.
        """
        original_level = self._global_level

        # Validate and set the global level with fallback
        try:
            test_numeric = getattr(logging, level.upper(), logging.INFO)
            if isinstance(test_numeric, int):
                self._global_level = level.upper()
            else:
                self._global_level = "INFO"
        except AttributeError:
            # Level not found, fallback to INFO and log warning
            print(f"Warning: Invalid log level '{level}', falling back to INFO")
            self._global_level = "INFO"

        # Update all existing loggers
        for logger in self._loggers.values():
            try:
                numeric_level = getattr(logging, self._global_level, logging.INFO)
                logger.setLevel(numeric_level)
                logger.info(f"Log level updated to {self._global_level}")
            except Exception:
                # If logging fails, set level silently
                logger.setLevel(logging.INFO)

    def get_available_levels(self):
        """
        Return available logging levels.
        """
        return ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
