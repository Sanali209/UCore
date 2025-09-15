"""
Web Framework Components

This package contains HTTP server and web application components:
- HttpServer: Production-ready HTTP server with Prometheus metrics
- Web routes and middleware support
- Request/response handling
- API building utilities
"""

from .http import HttpServer

__all__ = ['HttpServer']
