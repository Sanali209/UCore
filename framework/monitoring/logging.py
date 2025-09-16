import json
import logging
from loguru import logger as loguru_logger

class JsonFormatter(logging.Formatter):
    """
    Formatter for structured JSON logs.
    """
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt) if hasattr(self, "datefmt") and self.datefmt else self.formatTime(record),
            "name": record.name,
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if record.exc_info:
            log_record["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

class LoggerWrapper:
    def __init__(self, logger, name):
        self._logger = logger
        self._name = name

    def getChild(self, suffix):
        # Return a new LoggerWrapper with the child name
        child_name = f"{self._name}.{suffix}" if self._name else suffix
        return LoggerWrapper(self._logger, child_name)

    def __getattr__(self, attr):
        return getattr(self._logger, attr)

class Logging:
    def __init__(self):
        self._global_level = "INFO"
        self._loggers = {}

    def get_logger(self, name: str = None, level: str = None):
        """
        Returns a loguru logger with the specified name and level.
        """
        # loguru does not use named loggers, but we can bind context
        bound_logger = loguru_logger.bind(logger_name=name) if name else loguru_logger
        effective_level = (level or self._global_level).upper()
        loguru_logger.remove()
        loguru_logger.add(lambda msg: print(msg, end=""), level=effective_level, serialize=True)
        return LoggerWrapper(bound_logger, name)

    def set_global_level(self, level: str):
        """
        Set the global logging level for all loggers.
        """
        self._global_level = level.upper()
        loguru_logger.remove()
        loguru_logger.add(lambda msg: print(msg, end=""), level=self._global_level, serialize=True)

    def get_available_levels(self):
        """
        Return available logging levels.
        """
        return ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
