"""
UCore Framework - Event System
A typed event system for in-process communication between components.
"""

from abc import ABC
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Type
import uuid


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
            import inspect

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
