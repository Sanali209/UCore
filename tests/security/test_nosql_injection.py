import pytest
import httpx

@pytest.fixture(scope="session")
def app_base_url():
    # This fixture should start the UCore app in a test environment and return its base URL
    # For demonstration, assume it's already running at this address
    return "http://127.0.0.1:8888"

@pytest.mark.asyncio
async def test_where_operator_is_blocked(app_base_url):
    async with httpx.AsyncClient(base_url=app_base_url) as client:
        payload = {
            "username": {"$ne": None},
            "password": {"$ne": None},
            "$where": "sleep(5000)"
        }
        resp = await client.post("/api/login", json=payload)
        assert resp.status_code in (404, 422)
        assert "$where" not in resp.text

@pytest.mark.asyncio
async def test_regex_with_safe_operators(app_base_url):
    async with httpx.AsyncClient(base_url=app_base_url) as client:
        payload = {
            "username": {"$regex": ".*"}
        }
        resp = await client.post("/api/login", json=payload)
        assert resp.status_code in (200, 404)
