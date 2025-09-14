# examples/basic_app/main.py
import sys
from aiohttp import web

# This allows the example to be run from the root of the repository
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.http import HttpServer
from framework.config import Config
from framework.observability import Observability

def create_app():
    """
    Application factory.
    """
    # 1. Initialize the main App object
    app = App(name="UCoreExample")

    # 2. Initialize and register core components
    # The HttpServer is created and then registered with the DI container
    # as a singleton instance. It's also registered with the app's
    # component lifecycle system.
    http_server = HttpServer(app)
    app.container.register_instance(http_server)
    app.register_component(lambda: http_server)

    # The Observability component provides /metrics and /health endpoints.
    # It depends on the HttpServer, which it will get from the DI container.
    observability = Observability(app)
    app.register_component(lambda: observability)

    # 3. Define application routes
    # This route uses the DI container to inject the `Config` object.
    @http_server.route("/", "GET")
    async def hello_handler(config: Config):
        app_name = config.get("APP_NAME", "UCoreExampleApp")
        return web.json_response({"message": f"Welcome to {app_name}!"})

    @http_server.route("/hello/{name}", "GET")
    async def hello_name_handler(request):
        name = request.match_info.get('name', "Anonymous")
        return web.json_response({"message": f"Hello, {name}!"})

    return app

if __name__ == "__main__":
    # Create the application instance
    ucore_app = create_app()
    
    # Run the application. This will start the asyncio event loop,
    # bootstrap all components, start the HTTP server, and wait for
    # a shutdown signal (like Ctrl+C).
    ucore_app.run()
