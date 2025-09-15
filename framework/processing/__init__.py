"""
Background Processing Components

This package contains task processing and worker components:
- Task system for background job processing
- Background task management
- CLI tools and worker processes
- Command-line interface components
"""

# Import task decorator for backward compatibility
from .tasks import task

# Note: Other classes defined in these modules need to be imported based on actual class names
# This will be updated as classes are identified in each module

__all__ = ['task']  # Will be expanded as more components are identified
