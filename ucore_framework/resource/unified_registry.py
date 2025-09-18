"""
Unified Resource Registry for UCore & SLM Integration

Defines IResourceRegistry interface and UnifiedResourceRegistry implementation.
Provides unified API for resource registration, discovery, monitoring, and orchestration.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

# DEPRECATED: Use ResourceManager for all resource registration, discovery, and monitoring.
# These interfaces remain only for legacy integration and will be removed in future versions.

# All new code should use ucore_framework.resource.manager.ResourceManager directly.
