import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from ucore_framework.core.resource.types.api import APIResource
from ucore_framework.core.resource.exceptions import ResourceTimeoutError

@pytest.fixture
@patch('aiohttp.ClientSession')
def mock_session(mock_client_session):
    mock_session = AsyncMock()
    mock_client_session.return_value = mock_session
    return mock_session

@pytest.mark.asyncio
async def test_successful_get_request(mock_session):
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"data": "success"}
    mock_session.request.return_value = mock_response

    resource = APIResource(name="test_api", base_url="http://test.com")
    await resource._initialize()
    await resource._connect()
    response = await resource.get("/endpoint")
    mock_session.request.assert_called_with(method='GET', url='http://test.com/endpoint', headers=None, params=None, json=None, timeout=None)
    assert response['data'] == "success"

@pytest.mark.asyncio
async def test_retry_on_timeout(mock_session):
    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = {"data": "success"}
    mock_session.request.side_effect = [asyncio.TimeoutError(), mock_response]

    resource = APIResource(name="test_api", base_url="http://test.com", max_retries=1)
    await resource._initialize()
    await resource._connect()
    await resource.get("/endpoint")
    assert mock_session.request.call_count == 2
