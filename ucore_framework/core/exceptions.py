"""
Exception classes for UCore Framework.

Defines base and specialized exceptions for structured error handling
across the framework, supporting error codes and contextual information.

Classes:
    UCoreError: Base exception for all framework errors.
    ResourceError: Raised for resource management errors.
    ConfigurationError: Raised for configuration-related errors.
"""

from typing import Any, Dict, Optional

class UCoreError(Exception):
    """Base exception with structured context for all framework errors."""
    def __init__(self, message: str, code: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.context = context or {}

    def __str__(self):
        return f"{self.__class__.__name__}(code={self.code}, message={super().__str__()}, context={self.context})"

class ResourceError(UCoreError):
    """Raised for errors related to resource management (e.g., connection, initialization)."""
    pass

class ConfigurationError(UCoreError):
    """Raised for errors related to application configuration (e.g., missing value, invalid format)."""
    pass
