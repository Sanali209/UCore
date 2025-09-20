"""
Resource Provider Exceptions
Custom exceptions for resource management
"""

from typing import Optional


class ResourceError(Exception):
    """Base exception for resource-related errors"""

    def __init__(self, message: str, resource_name: Optional[str] = None, resource_type: Optional[str] = None):
        self.resource_name = resource_name
        self.resource_type = resource_type
        super().__init__(f"{message} [Resource: {resource_name}, Type: {resource_type}]")


class ResourceNotFoundError(ResourceError):
    """Raised when a requested resource cannot be found"""

    def __init__(self, resource_name: str):
        super().__init__(f"Resource not found: {resource_name}", resource_name=resource_name)


class ResourcePoolExhaustedError(ResourceError):
    """Raised when resource pool has no available resources"""

    def __init__(self, resource_name: str, max_size: int):
        self.max_size = max_size
        super().__init__(
            f"Resource pool exhausted for {resource_name} (max size: {max_size})",
            resource_name=resource_name
        )


class ResourceConnectionError(ResourceError):
    """Raised when a resource connection fails"""

    def __init__(self, resource_name: str, connection_url: str = None):
        self.connection_url = connection_url
        message = f"Failed to connect to resource: {resource_name}"
        if connection_url:
            message += f" at {connection_url}"
        super().__init__(message, resource_name=resource_name)


class ResourceTimeoutError(ResourceError):
    """Raised when a resource operation times out"""

    def __init__(self, resource_name: str, operation: str, timeout: float):
        self.operation = operation
        self.timeout = timeout
        super().__init__(
            f"Resource operation '{operation}' timed out after {timeout}s for {resource_name}",
            resource_name=resource_name
        )


class ResourceConfigurationError(ResourceError):
    """Raised when resource configuration is invalid"""

    def __init__(self, resource_name: str, config_key: str, expected_type: str):
        self.config_key = config_key
        self.expected_type = expected_type
        super().__init__(
            f"Invalid configuration for {resource_name}: {config_key} should be {expected_type}",
            resource_name=resource_name
        )


class ResourceStateError(ResourceError):
    """Raised when resource is in an invalid state for an operation"""

    def __init__(self, resource_name: str, current_state: str, required_state: str):
        self.current_state = current_state
        self.required_state = required_state
        super().__init__(
            f"Resource {resource_name} is in state '{current_state}' but requires '{required_state}'",
            resource_name=resource_name
        )
