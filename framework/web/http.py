# framework/http.py
import asyncio
import inspect
import time
from aiohttp import web
from ..core.component import Component
from ..core.di import Depends
from ..messaging.events import HttpServerStartedEvent, HTTPRequestEvent, HTTPResponseEvent, HTTPErrorEvent
from typing import Dict, Any, Optional

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
                from ..monitoring.metrics import HTTPMetricsAdapter
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

        # Add event publishing middleware
        def event_publish_middleware():
            @web.middleware
            async def _middleware(request, handler):
                event_bus = self.get_event_bus()

                # Only publish events if event_bus exists and is running
                should_publish = event_bus and hasattr(event_bus, '_running') and event_bus._running

                start_time = time.time()

                try:
                    # Publish request event
                    if should_publish:
                        try:
                            client_ip = self._get_client_ip(request)

                            request_event = HTTPRequestEvent(
                                method=request.method,
                                path=str(request.path),
                                headers=dict(request.headers),
                                query_params=dict(request.query),
                                client_ip=client_ip
                            )
                            event_bus.publish(request_event)
                        except Exception:
                            # Silently ignore event publishing errors
                            pass

                    # Process the request
                    response = await handler(request)
                    response_time = time.time() - start_time

                    # Publish response event
                    if should_publish and isinstance(response, web.StreamResponse):
                        try:
                            response_event = HTTPResponseEvent(
                                method=request.method,
                                path=str(request.path),
                                status=response.status,
                                response_time=response_time,
                                response_size=getattr(response, '_body_length', 0)
                            )
                            event_bus.publish(response_event)

                            # Publish performance metric
                            event_bus.publish_performance_event(
                                metric_name="http_response_time",
                                value=response_time,
                                component_type="HttpServer",
                                tags={"method": request.method, "status": str(response.status)}
                            )
                        except Exception:
                            # Silently ignore event publishing errors
                            pass

                    return response

                except Exception as e:
                    response_time = time.time() - start_time

                    # Publish error event
                    if should_publish:
                        try:
                            status = getattr(e, 'status', 500)  # Handle web.HTTPException

                            error_event = HTTPErrorEvent(
                                method=request.method,
                                path=str(request.path),
                                status=status,
                                error_type=type(e).__name__,
                                error_message=str(e),
                                response_time=response_time
                            )
                            event_bus.publish(error_event)

                            # Publish error performance metric
                            event_bus.publish_performance_event(
                                metric_name="http_error_time",
                                value=response_time,
                                component_type="HttpServer",
                                tags={"method": request.method, "status": str(status)}
                            )
                        except Exception:
                            # Silently ignore event publishing errors
                            pass

                    raise

            return _middleware

        middlewares.append(event_publish_middleware())

        self.web_app = web.Application(middlewares=middlewares)
        self.app.logger.info("HTTP Event publishing middleware added")
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

    async def start(self):
        """
        Component lifecycle start method.
        """
        try:
            # Publish lifecycle event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_lifecycle_event(
                    component_name="HttpServer",
                    lifecycle_type="starting"
                )

            # Start the server
            await self.start_server()

            # Publish success event
            if event_bus:
                server_started_event = HttpServerStartedEvent(
                    host=self.host,
                    port=self.port,
                    route_count=len(self.web_app.router.routes())
                )
                event_bus.publish(server_started_event)

                # Log performance metric
                event_bus.publish_performance_event(
                    metric_name="server_startup_time",
                    value=time.time(),  # This could be actual startup time
                    component_type="HttpServer"
                )

        except Exception as e:
            # Publish error event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_error_event(
                    component_name="HttpServer",
                    error=e,
                    context={"operation": "start"}
                )
            raise

    def stop(self):
        """
        Component lifecycle stop method.
        """
        try:
            # Publish lifecycle event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_lifecycle_event(
                    component_name="HttpServer",
                    lifecycle_type="stopping",
                    success=True
                )

            # Stop the server
            if self.runner:
                asyncio.run(self.stop_server())

            # Publish success event
            if event_bus:
                event_bus.publish_lifecycle_event(
                    component_name="HttpServer",
                    lifecycle_type="stopped",
                    success=True
                )

        except Exception as e:
            # Publish error event
            event_bus = self.get_event_bus()
            if event_bus:
                event_bus.publish_error_event(
                    component_name="HttpServer",
                    error=e,
                    context={"operation": "stop"}
                )
            # Don't re-raise the error during shutdown



    def _get_client_ip(self, request) -> str:
        """
        Extract client IP address from request.
        """
        # Check for forwarded headers (common in proxy/load balancer setups)
        for header in ['X-Forwarded-For', 'X-Real-IP', 'CF-Connecting-IP']:
            forwarded = request.headers.get(header)
            if forwarded:
                # Take first IP if multiple are present
                return forwarded.split(',')[0].strip()

        # Fallback to aiohttp's remote address
        if hasattr(request, 'remote') and request.remote:
            return request.remote

        return "unknown"
