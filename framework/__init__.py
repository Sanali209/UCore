# UCore Framework
"""
UCore: Enterprise-Grade Framework for Python Applications

Domain-Driven Architecture organized by application use cases:

- Core: Fundamental framework components
- Web: HTTP servers and web applications
- Desktop: GUI desktop applications
- Messaging: Event-driven communication and message passing
- Data: Database operations, caching, and persistence
- Processing: Background tasks, workers, and CLI tools
- Monitoring: Metrics, observability, and logging
- Simulation: Testing and simulation environments
"""

__version__ = "1.0.0"
__author__ = "UCore Team"

# Legacy core exports (backward compatibility) - Direct imports for now
from .core.app import App
from .core.component import Component
from .core.di import Container, Scope
from .core.config import Config

# Domain-specific imports (new structure)
from . import core
from . import web
from . import desktop
from . import messaging
from . import data
from . import processing
from . import monitoring
# Simulation domain - optional import
try:
    from . import simulation
except ImportError:
    import sys
    sys.modules['framework.simulation'] = None

# Event system from messaging domain - Direct imports for now
from .messaging.event_bus import EventBus
from .messaging.events import (
    Event,
    ComponentStartedEvent, ComponentStoppedEvent,
    AppStartedEvent, AppStoppedEvent,
    ConfigUpdatedEvent, UserEvent, EventFilter
)

# Optional CPU tasks import to avoid circular imports
try:
    from . import cpu_tasks
    _cpu_tasks_available = True
except (ImportError, AttributeError):
    _cpu_tasks_available = False

__all__ = [
    '__version__',
    '__author__',
    # Legacy exports
    'App', 'Component', 'Config', 'Container', 'Scope',
    # New domain structure
    'core', 'web', 'desktop', 'messaging', 'data', 'processing', 'monitoring', 'simulation',
    # Supporting exports
    'Event', 'EventBus',
    'ComponentStartedEvent', 'ComponentStoppedEvent',
    'AppStartedEvent', 'AppStoppedEvent',
    'ConfigUpdatedEvent', 'UserEvent', 'EventFilter'
]

# Add optional exports if available
if _cpu_tasks_available:
    __all__.append('cpu_tasks')
