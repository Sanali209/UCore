"""
Core Event Types for UCore Framework

This module defines all standard event types used throughout the framework,
providing a centralized registry of events for better type safety and discoverability.
"""

from typing import Any, Dict, Optional, List, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from abc import ABC
import uuid
import inspect


class EventPriority(Enum):
    """Priority levels for events."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


class EventCategory(Enum):
    """Categories of events in the system."""
    SYSTEM = "system"
    APPLICATION = "application"
    COMPONENT = "component"
    USER = "user"
    DATA = "data"
    RESOURCE = "resource"
    PLUGIN = "plugin"
    UI = "ui"
    PROCESSING = "processing"
    MONITORING = "monitoring"


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
            if frame:
                frame = frame.f_back
            if frame:
                frame = frame.f_back # Skip __post_init__ and __init__
            
            try:
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


@dataclass
class CoreEvent(Event):
    """Base class for all core framework events."""
    category: EventCategory = EventCategory.SYSTEM
    priority: EventPriority = EventPriority.NORMAL
    timestamp: datetime = field(default_factory=datetime.now)
    source_component: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# SYSTEM EVENTS
# ============================================================================

@dataclass
class SystemStartedEvent(CoreEvent):
    """Fired when the system starts up."""
    category: EventCategory = EventCategory.SYSTEM
    priority: EventPriority = EventPriority.HIGH


@dataclass
class SystemShutdownEvent(CoreEvent):
    """Fired when the system is shutting down."""
    category: EventCategory = EventCategory.SYSTEM
    priority: EventPriority = EventPriority.HIGH
    reason: Optional[str] = None


@dataclass
class SystemErrorEvent(CoreEvent):
    """Fired when a system-level error occurs."""
    category: EventCategory = EventCategory.SYSTEM
    priority: EventPriority = EventPriority.CRITICAL
    error_type: str = ""
    error_message: str = ""
    stack_trace: Optional[str] = None


@dataclass
class ConfigurationChangedEvent(CoreEvent):
    """Fired when system configuration changes."""
    category: EventCategory = EventCategory.SYSTEM
    changed_keys: List[str] = field(default_factory=list)
    old_values: Dict[str, Any] = field(default_factory=dict)
    new_values: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# APPLICATION EVENTS
# ============================================================================

@dataclass
class AppStartedEvent(CoreEvent):
    """Fired when the application has fully started."""
    category: EventCategory = EventCategory.APPLICATION
    priority: EventPriority = EventPriority.HIGH
    app_name: str = ""
    version: str = ""


@dataclass
class AppStoppedEvent(CoreEvent):
    """Fired when the application is stopping."""
    category: EventCategory = EventCategory.APPLICATION
    priority: EventPriority = EventPriority.HIGH
    exit_code: int = 0
    reason: Optional[str] = None


@dataclass
class AppStateChangedEvent(CoreEvent):
    """Fired when application state changes."""
    category: EventCategory = EventCategory.APPLICATION
    old_state: str = ""
    new_state: str = ""
    reason: Optional[str] = None


# ============================================================================
# COMPONENT EVENTS
# ============================================================================

@dataclass
class ComponentStartedEvent(CoreEvent):
    """Fired when a component starts."""
    category: EventCategory = EventCategory.COMPONENT
    component_name: str = ""
    component_type: str = ""


@dataclass
class ComponentStoppedEvent(CoreEvent):
    """Fired when a component stops."""
    category: EventCategory = EventCategory.COMPONENT
    component_name: str = ""
    component_type: str = ""
    reason: Optional[str] = None


@dataclass
class ComponentErrorEvent(CoreEvent):
    """Fired when a component encounters an error."""
    category: EventCategory = EventCategory.COMPONENT
    priority: EventPriority = EventPriority.HIGH
    component_name: str = ""
    component_type: str = ""
    error_type: str = ""
    error_message: str = ""


@dataclass
class ComponentHealthChangedEvent(CoreEvent):
    """Fired when component health status changes."""
    category: EventCategory = EventCategory.COMPONENT
    component_name: str = ""
    old_status: str = ""
    new_status: str = ""
    health_details: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PLUGIN EVENTS
# ============================================================================

@dataclass
class PluginLoadedEvent(CoreEvent):
    """Fired when a plugin is loaded."""
    category: EventCategory = EventCategory.PLUGIN
    plugin_name: str = ""
    plugin_type: str = ""
    plugin_version: str = ""


@dataclass
class PluginUnloadedEvent(CoreEvent):
    """Fired when a plugin is unloaded."""
    category: EventCategory = EventCategory.PLUGIN
    plugin_name: str = ""
    plugin_type: str = ""
    reason: Optional[str] = None


@dataclass
class PluginErrorEvent(CoreEvent):
    """Fired when a plugin encounters an error."""
    category: EventCategory = EventCategory.PLUGIN
    priority: EventPriority = EventPriority.HIGH
    plugin_name: str = ""
    plugin_type: str = ""
    error_type: str = ""
    error_message: str = ""


@dataclass
class PluginEnabledEvent(CoreEvent):
    """Fired when a plugin is enabled."""
    category: EventCategory = EventCategory.PLUGIN
    plugin_name: str = ""


@dataclass
class PluginDisabledEvent(CoreEvent):
    """Fired when a plugin is disabled."""
    category: EventCategory = EventCategory.PLUGIN
    plugin_name: str = ""


# ============================================================================
# RESOURCE EVENTS
# ============================================================================

@dataclass
class ResourceCreatedEvent(CoreEvent):
    """Fired when a resource is created."""
    category: EventCategory = EventCategory.RESOURCE
    resource_type: str = ""
    resource_id: str = ""
    resource_name: Optional[str] = None


@dataclass
class ResourceDeletedEvent(CoreEvent):
    """Fired when a resource is deleted."""
    category: EventCategory = EventCategory.RESOURCE
    resource_type: str = ""
    resource_id: str = ""
    resource_name: Optional[str] = None


@dataclass
class ResourceModifiedEvent(CoreEvent):
    """Fired when a resource is modified."""
    category: EventCategory = EventCategory.RESOURCE
    resource_type: str = ""
    resource_id: str = ""
    resource_name: Optional[str] = None
    changed_fields: List[str] = field(default_factory=list)


@dataclass
class ResourceAccessedEvent(CoreEvent):
    """Fired when a resource is accessed."""
    category: EventCategory = EventCategory.RESOURCE
    resource_type: str = ""
    resource_id: str = ""
    access_type: str = ""  # read, write, execute, etc.
    user_id: Optional[str] = None


@dataclass
class ResourceConnectionEvent(CoreEvent):
    """Fired when connecting to external resources."""
    category: EventCategory = EventCategory.RESOURCE
    resource_type: str = ""
    connection_status: str = ""  # connected, disconnected, failed
    endpoint: Optional[str] = None


# ============================================================================
# DATA EVENTS
# ============================================================================

@dataclass
class DataChangedEvent(CoreEvent):
    """Fired when data changes."""
    category: EventCategory = EventCategory.DATA
    data_type: str = ""
    data_id: Optional[str] = None
    operation: str = ""  # create, update, delete
    affected_records: int = 0


@dataclass
class DatabaseConnectionEvent(CoreEvent):
    """Fired when database connection status changes."""
    category: EventCategory = EventCategory.DATA
    database_name: str = ""
    connection_status: str = ""  # connected, disconnected, error
    connection_pool_size: Optional[int] = None


@dataclass
class CacheEvent(CoreEvent):
    """Fired for cache operations."""
    category: EventCategory = EventCategory.DATA
    cache_name: str = ""
    operation: str = ""  # hit, miss, set, evict, clear
    key: Optional[str] = None
    size: Optional[int] = None


@dataclass
class DataValidationEvent(CoreEvent):
    """Fired when data validation occurs."""
    category: EventCategory = EventCategory.DATA
    data_type: str = ""
    validation_result: str = ""  # passed, failed
    errors: List[str] = field(default_factory=list)


# ============================================================================
# UI EVENTS
# ============================================================================

@dataclass
class UIActionEvent(CoreEvent):
    """Fired when user performs UI actions."""
    category: EventCategory = EventCategory.UI
    action_type: str = ""
    component_id: Optional[str] = None
    user_id: Optional[str] = None
    action_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ViewChangedEvent(CoreEvent):
    """Fired when the view changes."""
    category: EventCategory = EventCategory.UI
    old_view: Optional[str] = None
    new_view: str = ""
    navigation_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIErrorEvent(CoreEvent):
    """Fired when UI encounters an error."""
    category: EventCategory = EventCategory.UI
    priority: EventPriority = EventPriority.HIGH
    error_type: str = ""
    error_message: str = ""
    component_id: Optional[str] = None


@dataclass
class WindowEvent(CoreEvent):
    """Fired for window operations."""
    category: EventCategory = EventCategory.UI
    window_id: str = ""
    event_type: str = ""  # opened, closed, minimized, maximized, focused
    window_properties: Dict[str, Any] = field(default_factory=dict)


# ============================================================================
# PROCESSING EVENTS
# ============================================================================

@dataclass
class TaskStartedEvent(CoreEvent):
    """Fired when a task starts."""
    category: EventCategory = EventCategory.PROCESSING
    task_id: str = ""
    task_type: str = ""
    task_name: Optional[str] = None
    estimated_duration: Optional[float] = None


@dataclass
class TaskCompletedEvent(CoreEvent):
    """Fired when a task completes."""
    category: EventCategory = EventCategory.PROCESSING
    task_id: str = ""
    task_type: str = ""
    task_name: Optional[str] = None
    duration: float = 0.0
    result: Optional[Any] = None


@dataclass
class TaskFailedEvent(CoreEvent):
    """Fired when a task fails."""
    category: EventCategory = EventCategory.PROCESSING
    priority: EventPriority = EventPriority.HIGH
    task_id: str = ""
    task_type: str = ""
    task_name: Optional[str] = None
    error_type: str = ""
    error_message: str = ""
    retry_count: int = 0


@dataclass
class TaskProgressEvent(CoreEvent):
    """Fired to report task progress."""
    category: EventCategory = EventCategory.PROCESSING
    task_id: str = ""
    progress_percent: float = 0.0
    current_step: Optional[str] = None
    estimated_remaining: Optional[float] = None


@dataclass
class QueueEvent(CoreEvent):
    """Fired for queue operations."""
    category: EventCategory = EventCategory.PROCESSING
    queue_name: str = ""
    operation: str = ""  # enqueue, dequeue, clear
    queue_size: int = 0
    item_count: int = 0


# ============================================================================
# MONITORING EVENTS
# ============================================================================

@dataclass
class MetricEvent(CoreEvent):
    """Fired when metrics are collected."""
    category: EventCategory = EventCategory.MONITORING
    metric_name: str = ""
    metric_value: Union[int, float] = 0
    metric_type: str = ""  # counter, gauge, histogram
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceEvent(CoreEvent):
    """Fired for performance measurements."""
    category: EventCategory = EventCategory.MONITORING
    operation_name: str = ""
    duration: float = 0.0
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    operation_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertEvent(CoreEvent):
    """Fired when an alert condition is met."""
    category: EventCategory = EventCategory.MONITORING
    priority: EventPriority = EventPriority.HIGH
    alert_type: str = ""
    alert_message: str = ""
    severity: str = ""  # info, warning, critical
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None


@dataclass
class LogEvent(CoreEvent):
    """Fired for log messages."""
    category: EventCategory = EventCategory.MONITORING
    log_level: str = ""
    log_message: str = ""
    logger_name: str = ""
    exception_info: Optional[str] = None


# ============================================================================
# USER EVENTS
# ============================================================================

@dataclass
class UserLoginEvent(CoreEvent):
    """Fired when user logs in."""
    category: EventCategory = EventCategory.USER
    user_id: str = ""
    username: Optional[str] = None
    login_method: str = ""
    ip_address: Optional[str] = None


@dataclass
class UserLogoutEvent(CoreEvent):
    """Fired when user logs out."""
    category: EventCategory = EventCategory.USER
    user_id: str = ""
    username: Optional[str] = None
    session_duration: Optional[float] = None


@dataclass
class UserActionEvent(CoreEvent):
    """Fired when user performs an action."""
    category: EventCategory = EventCategory.USER
    user_id: str = ""
    action_type: str = ""
    action_data: Dict[str, Any] = field(default_factory=dict)
    ip_address: Optional[str] = None


@dataclass
class UserPreferenceChangedEvent(CoreEvent):
    """Fired when user preferences change."""
    category: EventCategory = EventCategory.USER
    user_id: str = ""
    preference_key: str = ""
    old_value: Optional[Any] = None
    new_value: Any = None


# ============================================================================
# HTTP/WEB EVENTS
# ============================================================================

@dataclass
class HttpServerStartedEvent(CoreEvent):
    """Fired when HTTP server starts."""
    category: EventCategory = EventCategory.SYSTEM
    priority: EventPriority = EventPriority.HIGH
    host: str = ""
    port: int = 0
    route_count: int = 0


@dataclass
class HTTPRequestEvent(CoreEvent):
    """Fired when HTTP request is received."""
    category: EventCategory = EventCategory.SYSTEM
    method: str = ""
    path: str = ""
    headers: Dict[str, Any] = field(default_factory=dict)
    query_params: Dict[str, Any] = field(default_factory=dict)
    client_ip: str = ""


@dataclass
class HTTPResponseEvent(CoreEvent):
    """Fired when HTTP response is sent."""
    category: EventCategory = EventCategory.SYSTEM
    method: str = ""
    path: str = ""
    status: int = 200
    response_time: float = 0.0
    response_size: int = 0


@dataclass
class HTTPErrorEvent(CoreEvent):
    """Fired when HTTP error occurs."""
    category: EventCategory = EventCategory.SYSTEM
    priority: EventPriority = EventPriority.HIGH
    method: str = ""
    path: str = ""
    status: int = 500
    error_type: str = ""
    error_message: str = ""
    response_time: float = 0.0


# ============================================================================
# EVENT UTILITIES
# ============================================================================

def create_event(event_type: str, **kwargs) -> CoreEvent:
    """
    Factory function to create events by type name.
    
    Args:
        event_type: Name of the event type
        **kwargs: Event data
        
    Returns:
        Event instance
    """
    # Map of event type names to classes
    event_types = {
        'system_started': SystemStartedEvent,
        'system_shutdown': SystemShutdownEvent,
        'system_error': SystemErrorEvent,
        'configuration_changed': ConfigurationChangedEvent,
        'app_started': AppStartedEvent,
        'app_stopped': AppStoppedEvent,
        'app_state_changed': AppStateChangedEvent,
        'component_started': ComponentStartedEvent,
        'component_stopped': ComponentStoppedEvent,
        'component_error': ComponentErrorEvent,
        'component_health_changed': ComponentHealthChangedEvent,
        'plugin_loaded': PluginLoadedEvent,
        'plugin_unloaded': PluginUnloadedEvent,
        'plugin_error': PluginErrorEvent,
        'plugin_enabled': PluginEnabledEvent,
        'plugin_disabled': PluginDisabledEvent,
        'resource_created': ResourceCreatedEvent,
        'resource_deleted': ResourceDeletedEvent,
        'resource_modified': ResourceModifiedEvent,
        'resource_accessed': ResourceAccessedEvent,
        'resource_connection': ResourceConnectionEvent,
        'data_changed': DataChangedEvent,
        'database_connection': DatabaseConnectionEvent,
        'cache': CacheEvent,
        'data_validation': DataValidationEvent,
        'ui_action': UIActionEvent,
        'view_changed': ViewChangedEvent,
        'ui_error': UIErrorEvent,
        'window': WindowEvent,
        'task_started': TaskStartedEvent,
        'task_completed': TaskCompletedEvent,
        'task_failed': TaskFailedEvent,
        'task_progress': TaskProgressEvent,
        'queue': QueueEvent,
        'metric': MetricEvent,
        'performance': PerformanceEvent,
        'alert': AlertEvent,
        'log': LogEvent,
        'user_login': UserLoginEvent,
        'user_logout': UserLogoutEvent,
        'user_action': UserActionEvent,
        'user_preference_changed': UserPreferenceChangedEvent,
    }
    
    event_class = event_types.get(event_type)
    if event_class:
        return event_class(**kwargs)
    else:
        # Fall back to generic CoreEvent
        return CoreEvent(**kwargs)


def get_event_types() -> List[str]:
    """Get a list of all available event type names."""
    return [
        'system_started', 'system_shutdown', 'system_error', 'configuration_changed',
        'app_started', 'app_stopped', 'app_state_changed',
        'component_started', 'component_stopped', 'component_error', 'component_health_changed',
        'plugin_loaded', 'plugin_unloaded', 'plugin_error', 'plugin_enabled', 'plugin_disabled',
        'resource_created', 'resource_deleted', 'resource_modified', 'resource_accessed', 'resource_connection',
        'data_changed', 'database_connection', 'cache', 'data_validation',
        'ui_action', 'view_changed', 'ui_error', 'window',
        'task_started', 'task_completed', 'task_failed', 'task_progress', 'queue',
        'metric', 'performance', 'alert', 'log',
        'user_login', 'user_logout', 'user_action', 'user_preference_changed'
    ]


def get_events_by_category(category: EventCategory) -> List[str]:
    """Get all event types for a specific category."""
    category_events = {
        EventCategory.SYSTEM: ['system_started', 'system_shutdown', 'system_error', 'configuration_changed'],
        EventCategory.APPLICATION: ['app_started', 'app_stopped', 'app_state_changed'],
        EventCategory.COMPONENT: ['component_started', 'component_stopped', 'component_error', 'component_health_changed'],
        EventCategory.PLUGIN: ['plugin_loaded', 'plugin_unloaded', 'plugin_error', 'plugin_enabled', 'plugin_disabled'],
        EventCategory.RESOURCE: ['resource_created', 'resource_deleted', 'resource_modified', 'resource_accessed', 'resource_connection'],
        EventCategory.DATA: ['data_changed', 'database_connection', 'cache', 'data_validation'],
        EventCategory.UI: ['ui_action', 'view_changed', 'ui_error', 'window'],
        EventCategory.PROCESSING: ['task_started', 'task_completed', 'task_failed', 'task_progress', 'queue'],
        EventCategory.MONITORING: ['metric', 'performance', 'alert', 'log'],
        EventCategory.USER: ['user_login', 'user_logout', 'user_action', 'user_preference_changed']
    }
    return category_events.get(category, [])
