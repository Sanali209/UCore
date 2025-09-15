# tests/test_http.py
import unittest
import asyncio
import sys
from aiohttp import web, ClientSession
from unittest.mock import MagicMock

sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.web.http import HttpServer
from framework.core.config import Config
from framework.core.di import Scope

class TestHttpServer(unittest.IsolatedAsyncioTestCase):

    async def test_http_server_and_route(self):
        """
        Tests that the HttpServer can be started and a route can be accessed.
        """
        app = App("HttpTestApp")
        
        # The HttpServer is now a component that will be automatically managed
        app.container.register(HttpServer, scope=Scope.SINGLETON)
        app.register_component(HttpServer)

        # Configure a different port for the http server
        config = app.container.get(Config)
        config.set("http.port", 8081)

        http_server = app.container.get(HttpServer)

        @http_server.route("/test", methods=["GET"])
        async def test_handler(request):
            return web.json_response({"status": "ok"})

        async def run_test_client():
            # Give the server a moment to start
            await asyncio.sleep(0.1)
            try:
                async with ClientSession() as session:
                    async with session.get("http://localhost:8081/test") as response:
                        self.assertEqual(response.status, 200)
                        data = await response.json()
                        self.assertEqual(data, {"status": "ok"})
            finally:
                # Stop the app
                await app.stop()

        # Run the app and the test client concurrently
        app_task = asyncio.create_task(app.start())
        client_task = asyncio.create_task(run_test_client())

        await asyncio.gather(app_task, client_task)

if __name__ == '__main__':
    unittest.main()
