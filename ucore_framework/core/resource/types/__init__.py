"""
Resource Types
Concrete implementations of various resource types
"""

from .database import DatabaseResource
from .file import FileSystem, FileSystemProvider, LocalFileSystemProvider, InMemoryFileSystemProvider

# Try to import optional resource types
try:
    from .api import APIResource
    _api_available = True
except ImportError:
    _api_available = False
    APIResource = None

try:
    from .mongodb import MongoDBResource
    _mongodb_available = True
except ImportError:
    _mongodb_available = False
    MongoDBResource = None

__all__ = [
    "DatabaseResource",
    "FileSystem",
    "FileSystemProvider", 
    "LocalFileSystemProvider",
    "InMemoryFileSystemProvider",
]

# Add optional resource types if available
if _api_available:
    __all__.append("APIResource")
if _mongodb_available:
    __all__.append("MongoDBResource")
