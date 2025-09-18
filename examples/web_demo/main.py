"""
UCore Framework Example: Web Features

This example demonstrates:
- HTTP server setup using UCoreFrameworck.core.app.App and UCoreFrameworck.web.http.HttpServer
- Dependency injection and route registration
- Logging with the framework logger

Usage:
    python -m examples.web_demo.main

Requirements:
    pip install aiohttp loguru

Demonstrates HTTP server functionality.
"""

from ucore_framework.web.http import HttpServer
from ucore_framework.core.app import App
from aiohttp import web
import asyncio

def main():
    app = App("WebDemoApp")
    server = HttpServer(app=app, host="127.0.0.1", port=8081)

    @server.route("/", method="GET")
    async def hello(request):
        return web.Response(text="Hello, UCore Web!", content_type="text/plain")

    app.register_component(server)

    async def run_server():
        await server.start_server()
        app.logger.info("HTTP server running at http://127.0.0.1:8081. Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            app.logger.info("Shutting down HTTP server...")
            await server.stop_server()
            app.logger.success("HTTP server stopped.")

    asyncio.run(run_server())

if __name__ == "__main__":
    main()
