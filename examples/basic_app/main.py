#!/usr/bin/env python3
"""
Basic HTTP Server Example - Domain-Driven Structure

This example demonstrates the new domain-driven structure:
- Web domain (HttpServer)
- Core domain (App, Config)
- Monitoring domain (logging)
"""

import sys
sys.path.insert(0, 'd:/UCore')

from framework import App
from framework.web import HttpServer
from aiohttp import web

# Create your UCore application
app = App("BasicWebServer")
http_server = HttpServer(app, port=8080)  # Standard port
app.register_component(lambda: http_server)  # Register the component

# Simple endpoint
@http_server.route("/", "GET")
async def hello():
    return web.json_response({
        "message": "Hello from UCore Web Domain!",
        "framework_structure": "Domain-Driven Architecture",
        "domains": ["core", "web", "messaging", "data", "processing"],
        "status": "Ready"
    })

@http_server.route("/health", "GET")
async def health():
    return web.json_response({
        "status": "healthy",
        "timestamp": "2025-01-01T12:00:00Z",
        "domain": "web"
    })

if __name__ == "__main__":
    # Start server on port 8080
    print("🚀 Starting UCore Web Server (Domain-Driven Structure)")
    print("📊 Visit: http://localhost:8080")
    app.run()
