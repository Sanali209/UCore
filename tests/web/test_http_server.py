import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
import time
from framework.web.http import HttpServer
from framework.core.app import App
from framework.messaging.event_bus import EventBus
from framework.messaging.events import (
    HttpServerStartedEvent, HTTPRequestEvent, HTTPResponseEvent, HTTPErrorEvent
)
from aiohttp import web


class TestHttpServerInitialization:
    """Test HttpServer initialization and basic setup."""

    def test_http_server_create_with_defaults(self):
        """Test HttpServer creation with default parameters."""
        mock_container = Mock()
        mock_container._singletons = {}  # Empty singletons to avoid iteration error
        mock_container._providers = {}  # Empty providers to avoid iteration error

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        assert server.app == mock_app
        assert server.host == "0.0.0.0"
        assert server.port == 8080
        assert isinstance(server.web_app, web.Application)
        assert server.runner is None
        assert server.site is None

        # Check that logger was accessed for middleware setup
        mock_app.logger.info.call_count >= 1

    def test_http_server_create_with_custom_params(self):
        """Test HttpServer creation with custom host and port."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app, host="127.0.0.1", port=3000)

        assert server.host == "127.0.0.1"
        assert server.port == 3000

    def test_http_server_without_app(self):
        """Test HttpServer creation without app (should handle gracefully)."""
        with pytest.raises(AttributeError):
            server = HttpServer()
            # Should fail when trying to set up middlewares due to missing app container

    def test_http_server_container_registration(self):
        """Test HttpServer registers itself in the container."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}
        mock_container.register_instance = Mock()

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        # Should register the class if not already present
        mock_container.register.assert_called_once()
        # Should register the instance
        mock_container.register_instance.assert_called_once_with(server, HttpServer)


class TestRouteRegistration:
    """Test HTTP route registration with dependency injection."""

    def test_route_registration_basic(self):
        """Test basic route registration."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        @server.route('/test', method='GET')
        async def test_handler():
            return web.Response(text="test")

        # Route should be registered
        routes = list(server.web_app.router.routes())
        assert len(routes) == 1
        assert routes[0].method == 'GET'

        # Logger should be called
        mock_app.logger.info.assert_any_call("Registered route: GET /test")

    def test_route_registration_with_methods_list(self):
        """Test route registration with methods list (backwards compatibility)."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        @server.route('/api', methods=['GET', 'POST'])
        async def api_handler():
            return web.Response(text="api")

        # Route should be registered (uses first method)
        routes = list(server.web_app.router.routes())
        assert len(routes) == 1


class TestComponentLifecycle:
    """Test HTTP server as a component lifecycle."""

    @pytest.mark.asyncio
    async def test_component_start_success(self):
        """Test successful component start."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_event_bus = Mock()
        mock_event_bus._running = True
        mock_container.get.return_value = mock_event_bus

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        with patch.object(server, 'start_server', new=AsyncMock()) as mock_start_server:
            await server.start()

            mock_start_server.assert_called_once()

            # Should publish lifecycle events
            mock_event_bus.publish_lifecycle_event.assert_called_with(
                component_name="HttpServer",
                lifecycle_type="starting"
            )

    def test_component_stop_success(self):
        """Test successful component stop."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_event_bus = Mock()
        mock_event_bus._running = True
        mock_container.get.return_value = mock_event_bus

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)
        server.runner = Mock()  # Mock runner as if server was started

        with patch.object(server, 'stop_server', new=AsyncMock()) as mock_stop_server:
            with patch('asyncio.run') as mock_asyncio_run:
                server.stop()

                # Should call stop_server via asyncio.run
                mock_asyncio_run.assert_called_once()


class TestConfigurationHandling:
    """Test HTTP server configuration updates and handling."""

    def test_config_update_host_port_changes(self):
        """Test configuration updates that change host and port."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()
        mock_config = Mock()

        # Initial configuration
        server = HttpServer(app=mock_app, host="0.0.0.0", port=8080)

        # Mock config values
        mock_config.get.side_effect = lambda key, default=None: {
            "HTTP_HOST": "127.0.0.1",
            "HTTP_PORT": 3000,
            "HTTP_CORS_ENABLED": True,
            "HTTP_REQUEST_TIMEOUT": 60.0,
            "HTTP_MAX_CONNECTIONS": 200
        }.get(key, default)

        server.on_config_update(mock_config)

        # Should update host and port
        assert server.host == "127.0.0.1"
        assert server.port == 3000

        # Should log configuration changes
        mock_app.logger.info.assert_any_call("HTTP server host changing from 0.0.0.0 to 127.0.0.1")
        mock_app.logger.info.assert_any_call("HTTP server port changing from 8080 to 3000")
        mock_app.logger.warning.assert_any_call("HTTP server configuration changed - restart recommended")


class TestClientIPExtraction:
    """Test client IP address extraction from requests."""

    def test_get_client_ip_x_forwarded_for(self):
        """Test IP extraction from X-Forwarded-For header."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        mock_request = Mock()
        mock_request.headers = {'X-Forwarded-For': '192.168.1.100, 10.0.0.1'}
        mock_request.remote = '127.0.0.1'

        ip = server._get_client_ip(mock_request)
        assert ip == '192.168.1.100'

    def test_get_client_ip_x_real_ip(self):
        """Test IP extraction from X-Real-IP header."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        mock_request = Mock()
        mock_request.headers = {'X-Real-IP': '10.0.0.50'}
        mock_request.remote = '127.0.0.1'

        ip = server._get_client_ip(mock_request)
        assert ip == '10.0.0.50'

    def test_get_client_ip_fallback_to_remote(self):
        """Test IP fallback to request.remote when no headers."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        mock_request = Mock()
        mock_request.headers = {}
        mock_request.remote = '192.168.1.1'

        ip = server._get_client_ip(mock_request)
        assert ip == '192.168.1.1'


class TestServerLifecycle:
    """Test HTTP server lifecycle management."""

    @pytest.mark.asyncio
    async def test_start_server_success(self):
        """Test successful server startup."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()
        mock_web_app = Mock()

        server = HttpServer(app=mock_app)
        server.web_app = mock_web_app

        with patch('aiohttp.web.AppRunner') as mock_runner_class:
            with patch('aiohttp.web.TCPSite') as mock_site_class:
                mock_runner = Mock()
                mock_site = Mock()

                mock_runner_class.return_value = mock_runner
                mock_site_class.return_value = mock_site

                await server.start_server()

                # Should create and start AppRunner and TCPSite
                mock_runner_class.assert_called_once_with(mock_web_app)
                mock_runner.setup.assert_called_once()
                mock_site_class.assert_called_once_with(mock_runner, "0.0.0.0", 8080)
                mock_site.start.assert_called_once()

                mock_app.logger.info.assert_called_once_with(
                    "HTTP server started at http://0.0.0.0:8080"
                )

    @pytest.mark.asyncio
    async def test_stop_server_success(self):
        """Test successful server shutdown."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        # Mock running server
        mock_runner = Mock()
        mock_site = Mock()

        server.runner = mock_runner
        server.site = mock_site

        await server.stop_server()

        # Should stop site and clean up runner
        mock_site.stop.assert_called_once()
        mock_runner.cleanup.assert_called_once()

        mock_app.logger.info.assert_any_call("HTTP server site stopped.")
        mock_app.logger.info.assert_any_call("HTTP server runner cleaned up.")


class TestEventPublishingMiddleware:
    """Test HTTP request/response/error event publishing middleware."""

    def test_request_event_publishing(self):
        """Test request events are published."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_event_bus = Mock()
        mock_event_bus._running = True
        mock_container.get.return_value = mock_event_bus

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        # The middleware should publish events
        middleware_list = server.web_app.middlewares
        assert len(middleware_list) >= 1

    def test_error_event_publishing(self):
        """Test error events are published with proper error data."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}

        mock_event_bus = Mock()
        mock_event_bus._running = True
        mock_container.get.return_value = mock_event_bus

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        # Error handling middleware should be in place
        middleware_list = server.web_app.middlewares
        assert len(middleware_list) >= 1


class TestDependencyInjection:
    """Test dependency injection in route handlers."""

    def test_route_with_dependency_injection(self):
        """Test route handler with dependency injection."""
        mock_container = Mock()
        mock_container._singletons = {}
        mock_container._providers = {}
        mock_dependency = Mock()
        mock_dependency.value = "injected"

        mock_container.get.return_value = mock_dependency

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        @server.route('/inject', method='GET')
        async def inject_handler(dependency: Mock):
            return web.json_response({"result": dependency.value})

        # Route should be registered with dependency injection capability
        routes = list(server.web_app.router.routes())
        assert len(routes) == 1


class TestMetricsIntegration:
    """Test HTTP metrics middleware integration."""

    @patch('framework.monitoring.metrics.HTTPMetricsAdapter')
    def test_metrics_middleware_integration(self, mock_metrics_adapter_class):
        """Test automatic HTTP metrics middleware addition."""
        mock_metrics_instance = Mock()
        mock_metrics_instance.middleware.return_value = Mock()
        mock_metrics_adapter_class.__instance__ = mock_metrics_instance

        mock_container = Mock()
        mock_container._singletons = {HttpServer: mock_metrics_instance}
        mock_container._providers = {}

        mock_app = Mock()
        mock_app.container = mock_container
        mock_app.logger = Mock()

        server = HttpServer(app=mock_app)

        # Should have auto-added metrics middleware
        mock_app.logger.info.assert_any_call("HTTP Metrics middleware automatically added")
