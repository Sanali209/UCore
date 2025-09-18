"""
Resource Types
Concrete implementations of various resource types
"""

from .database import DatabaseResource
from .file import FileResource

# Try to import optional resource types
try:
    from .api import ApiResource
    _api_available = True
except ImportError:
    _api_available = False
    ApiResource = None

try:
    from .cache import CacheResource
    _cache_available = True
except ImportError:
    _cache_available = False
    CacheResource = None

try:
    from .service import ServiceResource
    _service_available = True
except ImportError:
    _service_available = False
    ServiceResource = None

try:
    from .mongodb import MongoDBResource
    _mongodb_available = True
except ImportError:
    _mongodb_available = False
    MongoDBResource = None

__all__ = [
    "DatabaseResource",
    "FileResource",
]

# Add optional resource types if available
if _api_available:
    __all__.append("ApiResource")
if _cache_available:
    __all__.append("CacheResource")
if _service_available:
    __all__.append("ServiceResource")
if _mongodb_available:
    __all__.append("MongoDBResource")
