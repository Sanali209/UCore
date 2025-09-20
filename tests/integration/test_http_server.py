import pytest
from aiohttp import web
from ucore_framework.web.http import HttpServer

class TestService:
    def get_value(self):
        return "ok"

@pytest.fixture
async def aiohttp_client(aiohttp_client):
    # Set up UCore App and HttpServer
    app = web.Application()
    http_server = HttpServer(app=app)

    # Register TestService in DI container if available
    if hasattr(http_server, "container"):
        http_server.container.register(TestService)

    # Handler with DI
    async def get_data(service: TestService):
        return web.json_response({"data": service.get_value()})

    http_server.route("/test", "GET")(get_data)

    return await aiohttp_client(app)

@pytest.mark.asyncio
async def test_get_endpoint_success(aiohttp_client):
    resp = await aiohttp_client.get("/test")
    assert resp.status == 200
    data = await resp.json()
    assert data == {"data": "ok"}

@pytest.mark.asyncio
async def test_endpoint_not_found(aiohttp_client):
    resp = await aiohttp_client.get("/nonexistent")
    assert resp.status == 404
