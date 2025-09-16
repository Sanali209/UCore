"""
UCore Framework - Event System
A typed event system for in-process communication between components.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Type
import uuid
import inspect  # Moved to module level for patching


@dataclass
class Event(ABC):
    """
    Base class for all events in the system.

    Events are immutable data structures that represent something that
    happened in the application. They contain metadata and event-specific data.
    """
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    source: str = field(default="")
    data: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate event after initialization"""
        if not self.source:
            # Auto-detect source module using call stack
            self.source = self._detect_source()

    def _detect_source(self) -> str:
        """Detect source module from call stack"""
        try:
            # Skip current frame and this method
            frame = inspect.currentframe()
            try:
                # Go up the stack to find meaningful source
                frame = frame.f_back.f_back  # Skip __post_init__ and __init__

                while frame:
                    frame_info = inspect.getframeinfo(frame)
                    if frame_info.filename != __file__:
                        # Extract module name from filename
                        import os
                        module_name = os.path.splitext(os.path.basename(frame_info.filename))[0]
                        if module_name and module_name != "__main__":
                            return module_name
                    frame = frame.f_back
            finally:
                del frame
        except Exception:
            pass
        return "unknown"


# Framework lifecycle events
@dataclass
class ComponentStartedEvent(Event):
    """Published when a component has been started"""
    component_name: str = field(default="")
    component_type: Type = field(default=str)


@dataclass
class ComponentStoppedEvent(Event):
    """Published when a component has been stopped"""
    component_name: str = field(default="")
    component_type: Type = field(default=str)
    reason: str = ""


@dataclass
class ComponentErrorEvent(Event):
    """Published when a component encounters an error"""
    component_name: str = field(default="")
    error_type: str = field(default="")
    error_message: str = field(default="")
    traceback: str = field(default="")
    context: Dict[str, Any] = field(default_factory=dict)


# HTTP Server Events
@dataclass
class HttpServerStartedEvent(Event):
    """Published when HTTP server starts"""
    host: str = field(default="")
    port: int = field(default=8080)
    route_count: int = field(default=0)


@dataclass
class HTTPRequestEvent(Event):
    """Published when HTTP request is received"""
    method: str = field(default="")
    path: str = field(default="")
    headers: Dict[str, str] = field(default_factory=dict)
    query_params: Dict[str, str] = field(default_factory=dict)
    client_ip: str = field(default="")


@dataclass
class HTTPResponseEvent(Event):
    """Published when HTTP response is sent"""
    method: str = field(default="")
    path: str = field(default="")
    status: int = field(default=200)
    response_time: float = field(default=0.0)
    response_size: int = field(default=0)


@dataclass
class HTTPErrorEvent(Event):
    """Published when HTTP request results in an error"""
    method: str = field(default="")
    path: str = field(default="")
    status: int = field(default=500)
    error_type: str = field(default="")
    error_message: str = field(default="")
    response_time: float = field(default=0.0)


# Database Events
@dataclass
class DBConnectionEvent(Event):
    """Published when database connection is opened/closed"""
    database_url: str = field(default="")
    connection_status: str = field(default="")  # 'success', 'error', 'closed'
    connection_time: float = field(default=0.0)


@dataclass
class DBQueryEvent(Event):
    """Published when database query is executed"""
    query_type: str = field(default="")  # 'SELECT', 'INSERT', 'UPDATE', 'DELETE'
    query_pattern: str = field(default="")  # Sanitized query template
    execution_time: float = field(default=0.0)
    row_count: int = field(default=0)
    transaction_id: str = field(default="")


@dataclass
class DBTransactionEvent(Event):
    """Published when database transaction occurs"""
    operation: str = field(default="")  # 'begin', 'commit', 'rollback'
    transaction_id: str = field(default="")
    duration: float = field(default=0.0)
    query_count: int = field(default=0)


@dataclass
class DBPoolEvent(Event):
    """Published when connection pool status changes"""
    pool_size: int = field(default=0)
    active_connections: int = field(default=0)
    idle_connections: int = field(default=0)
    pending_connections: int = field(default=0)


@dataclass
class AppStartedEvent(Event):
    """Published when the application has started"""
    app_name: str = field(default="")
    component_count: int = field(default=0)


@dataclass
class AppStoppedEvent(Event):
    """Published when the application is stopping"""
    app_name: str = field(default="")
    stop_reason: str = "normal"


@dataclass
class ConfigUpdatedEvent(Event):
    """Published when application configuration is updated"""
    updated_keys: list = field(default_factory=list)
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)


# User-defined event support
@dataclass
class UserEvent(Event):
    """Base class for user-defined events"""
    event_type: str = field(default="")
    payload: Dict[str, Any] = field(default_factory=dict)


# Event routing and filtering
@dataclass
class EventFilter:
    """Filter for selective event subscription"""
    event_types: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    data_patterns: Dict[str, Any] = field(default_factory=dict)

    def matches(self, event: Event) -> bool:
        """Check if an event matches this filter"""
        # Event type filtering
        if self.event_types and type(event) not in self.event_types:
            return False

        # Source filtering
        if self.sources and event.source not in self.sources:
            return False

        # Data pattern filtering
        if self.data_patterns:
            for key, expected_value in self.data_patterns.items():
                if key not in event.data:
                    return False
                if event.data[key] != expected_value:
                    return False

        return True
