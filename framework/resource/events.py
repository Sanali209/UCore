"""
Resource Provider Events
Event definitions for resource lifecycle management
"""

from typing import Any, Dict, Optional
from dataclasses import dataclass

@dataclass
class ResourceEvent:
    """Base event for all resource-related events"""
    resource_name: str
    resource_type: str
    timestamp: float

@dataclass
class ResourceCreatedEvent(ResourceEvent):
    """Event fired when a resource is created"""
    resource_id: str
    config: Optional[Dict[str, Any]] = None
    cleanup_duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

@dataclass
class ResourceDestroyedEvent(ResourceEvent):
    """Event fired when a resource is destroyed"""
    resource_id: str
    config: Optional[Dict[str, Any]] = None
    cleanup_duration: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

@dataclass
class ResourceHealthChangedEvent(ResourceEvent):
    """Event fired when resource health status changes"""
    health_status: str  # "healthy", "unhealthy", "degraded"
    previous_status: Optional[str] = None
    reason: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

@dataclass
class ResourcePoolEvent(ResourceEvent):
    """Base event for pool-related activities"""
    pool_name: str
    pool_size: int
    available_count: int

@dataclass
class ResourcePoolExhaustedEvent(ResourcePoolEvent):
    """Event fired when pool is exhausted"""
    waiters_count: int
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

@dataclass
class ResourceConnectionEvent(ResourceEvent):
    """Base event for connection-related activities"""
    connection_id: str
    connection_url: Optional[str] = None

@dataclass
class ResourceConnectionEstablishedEvent(ResourceConnectionEvent):
    """Event fired when a connection is established"""
    retry_count: int = 0
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

@dataclass
class ResourceConnectionLostEvent(ResourceConnectionEvent):
    """Event fired when a connection is lost"""
    disconnection_reason: Optional[str] = None
    reconnection_attempts: int = 0
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

@dataclass
class ResourcePerformanceEvent(ResourceEvent):
    """Event fired for performance metrics"""
    operation: str
    duration_ms: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

@dataclass
class ResourceErrorEvent(ResourceEvent):
    """Event fired when a resource operation fails"""
    operation: str
    error_type: str
    error_message: str
    stack_trace: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    data: Optional[dict] = None

# Event types registry for easy reference
EVENT_TYPES = {
    "resource_created": ResourceCreatedEvent,
    "resource_destroyed": ResourceDestroyedEvent,
    "resource_health_changed": ResourceHealthChangedEvent,
    "resource_pool_exhausted": ResourcePoolExhaustedEvent,
    "resource_connection_established": ResourceConnectionEstablishedEvent,
    "resource_connection_lost": ResourceConnectionLostEvent,
    "resource_performance": ResourcePerformanceEvent,
    "resource_error": ResourceErrorEvent,
}
