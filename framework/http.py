# framework/http.py
import asyncio
import inspect
from aiohttp import web
from .component import Component
from .di import Depends

class HttpServer(Component):
    """
    An HTTP server component using aiohttp that supports dependency injection.
    """
    def __init__(self, app=None, host: str = "0.0.0.0", port: int = 8080):
        self.app = app
        self.host = host
        self.port = port

        # Check for metrics adapter and automatically add middleware
        middlewares = []
        if self.app and hasattr(self.app, 'container'):
            try:
                from .metrics import HTTPMetricsAdapter
                metrics_adapter_instance = None

                # Try to get metrics adapter from container if it exists
                if hasattr(self.app.container, '_singletons'):
                    for key, instance in self.app.container._singletons.items():
                        if isinstance(instance, HTTPMetricsAdapter):
                            metrics_adapter_instance = instance
                            break

                if metrics_adapter_instance:
                    middlewares.append(metrics_adapter_instance.middleware())
                    self.app.logger.info("HTTP Metrics middleware automatically added")
            except ImportError:
                pass  # Metrics not available, continue without

        self.web_app = web.Application(middlewares=middlewares)
        self.runner = None
        self.site = None

        # Register this instance of HttpServer in the container (only if app exists)
        if self.app and hasattr(self.app, 'container'):
            # Register instance for dependency injection, but don't try to replace the class registration
            if HttpServer not in self.app.container._providers:
                # Only register the class if it's not already registered
                self.app.container.register(HttpServer)
            # Always register the instance separately
            self.app.container.register_instance(self, HttpServer)

    def route(self, path: str, method: str = None, methods: list = None):
        """
        A decorator to register a route with dependency injection for the handler.
        """
        # Handle backwards compatibility - if methods is provided, use it
        if methods:
            method = methods[0] if isinstance(methods, list) and methods else (methods if isinstance(methods, str) else method)

        def decorator(handler):
            async def wrapped_handler(request):
                handler_params = inspect.signature(handler).parameters
                dependencies = {}
                to_cleanup = []

                try:
                    for name, param in handler_params.items():
                        # Check for request-time dependencies marked with Depends()
                        if hasattr(param.default, '_is_dependency_marker'):
                            provider_func = param.default
                            resolved_dependency = provider_func()

                            # If the dependency is an async context manager (like an async session), enter it.
                            if hasattr(resolved_dependency, '__aenter__'):
                                dependencies[name] = await resolved_dependency.__aenter__()
                                to_cleanup.append(resolved_dependency)
                            else:
                                dependencies[name] = resolved_dependency

                        # Handle standard, container-managed dependencies
                        elif param.annotation is not inspect.Parameter.empty:
                            try:
                                dependencies[name] = self.app.container.get(param.annotation)
                            except Exception as e:
                                self.app.logger.warning(f"Could not resolve dependency for {name}: {e}")

                    # Add the request object itself if requested
                    if 'request' in handler_params:
                        dependencies['request'] = request

                    return await handler(**dependencies)

                finally:
                    # Clean up any async context managers that were opened
                    for resource in to_cleanup:
                        await resource.__aexit__(None, None, None)

            self.web_app.router.add_route(method, path, wrapped_handler)
            self.app.logger.info(f"Registered route: {method.upper()} {path}")
            return handler
        return decorator

    async def start_server(self):
        self.runner = web.AppRunner(self.web_app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        self.app.logger.info(f"HTTP server started at http://{self.host}:{self.port}")

    async def stop_server(self):
        if self.site:
            await self.site.stop()
            self.app.logger.info("HTTP server site stopped.")
        if self.runner:
            await self.runner.cleanup()
            self.app.logger.info("HTTP server runner cleaned up.")

    def on_config_update(self, config):
        """
        Handle dynamic configuration updates for HTTP server.
        """
        # Get updated server settings
        new_host = config.get("HTTP_HOST")
        new_port = config.get("HTTP_PORT")
        new_cors_enabled = config.get("HTTP_CORS_ENABLED", False)
        new_request_timeout = config.get("HTTP_REQUEST_TIMEOUT", 30.0)
        new_max_connections = config.get("HTTP_MAX_CONNECTIONS", 100)

        # Check for server configuration changes
        config_changed = False

        if new_host and new_host != self.host:
            self.app.logger.info(f"HTTP server host changing from {self.host} to {new_host}")
            self.host = new_host
            config_changed = True

        if new_port and new_port != self.port:
            self.app.logger.info(f"HTTP server port changing from {self.port} to {new_port}")
            self.port = new_port
            config_changed = True

        if config_changed:
            self.app.logger.warning("HTTP server configuration changed - restart recommended")
            # Note: In a real implementation, you might want to implement
            # graceful server restart or signal the application for restart
            # For now, we'll log the change and note the limitation

        # Log other configuration updates
        self.app.logger.info(f"HTTP config - CORS: {new_cors_enabled}, Timeout: {new_request_timeout}s, MaxConn: {new_max_connections}")

    def start(self):
        """
        Component lifecycle start method.
        """
        # We run the server in a background task.
        asyncio.create_task(self.start_server())

    def stop(self):
        """
        Component lifecycle stop method.
        """
        # The stop needs to be async, but the component interface is sync.
        # This is a common challenge. For now, we'll run it synchronously.
        if self.runner:
            asyncio.run(self.stop_server())
