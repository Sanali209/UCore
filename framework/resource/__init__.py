"""
UCore Resource Provider
Provides unified resource management across the framework
"""

from .resource import Resource, ManagedResource, PooledResource, ObservableResource
from .manager import ResourceManager
from .pool import ResourcePool
from .exceptions import ResourceError, ResourcePoolExhaustedError, ResourceNotFoundError
from .events import ResourceEvent, ResourceCreatedEvent, ResourceDestroyedEvent

__version__ = "1.0.0"
__all__ = [
    # Base classes
    "Resource",
    "ManagedResource",
    "PooledResource",
    "ObservableResource",

    # Manager
    "ResourceManager",

    # Pooling
    "ResourcePool",

    # Exceptions
    "ResourceError",
    "ResourcePoolExhaustedError",
    "ResourceNotFoundError",

    # Events
    "ResourceEvent",
    "ResourceCreatedEvent",
    "ResourceDestroyedEvent",
]
