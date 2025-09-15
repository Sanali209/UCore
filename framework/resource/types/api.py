"""
API Resource
HTTP client resource with connection management, retry logic, and monitoring
"""

import asyncio
import logging
from typing import Any, Dict, Optional, Union, List
import aiohttp
import json
from urllib.parse import urljoin, urlparse

from ..resource import Resource, ResourceHealth, ResourceState
from ..exceptions import ResourceError, ResourceConnectionError, ResourceTimeoutError


logger = logging.getLogger(__name__)


class APIResource(Resource):
    """
    HTTP API client resource providing connection management and monitoring

    Provides async HTTP operations with connection pooling, retry logic,
    health monitoring, and comprehensive error handling.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        config: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Dict[str, str]] = None,
        connection_pool_size: int = 20,
        max_keepalive_connections: int = 10,
        ssl_verify: bool = True,
        user_agent: str = "UCore-APIResource/1.0",
    ):
        super().__init__(name, "api", config, timeout)

        self.base_url = base_url.rstrip('/')
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.default_headers = headers or {}
        self.auth = auth
        self.connection_pool_size = connection_pool_size
        self.max_keepalive_connections = max_keepalive_connections
        self.ssl_verify = ssl_verify
        self.user_agent = user_agent

        # Connection state
        self._session: Optional[aiohttp.ClientSession] = None
        self._connector: Optional[aiohttp.TCPConnector] = None

        # Statistics
        self._request_count = 0
        self._error_count = 0
        self._retry_count = 0
        self._last_request_time = 0.0

        self._validate_base_url()

    def _validate_base_url(self) -> None:
        """Validate base URL format"""
        try:
            parsed = urlparse(self.base_url)
            if not parsed.scheme or not parsed.netloc:
                raise ValueError("Invalid URL format")
            if parsed.scheme not in ['http', 'https']:
                raise ValueError("Only HTTP and HTTPS URLs are supported")
        except Exception as e:
            raise ValueError(f"Invalid base URL '{self.base_url}': {e}")

    async def _initialize(self) -> None:
        """Initialize API resource"""
        logger.info(f"Initializing API resource {self.name} for {self.base_url}")

        # Set up default headers
        self.default_headers.update({
            'User-Agent': self.user_agent,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        })

        # Add authentication if provided
        if self.auth:
            if 'bearer_token' in self.auth:
                self.default_headers['Authorization'] = f"Bearer {self.auth['bearer_token']}"
            elif 'username' in self.auth and 'password' in self.auth:
                import base64
                auth_string = f"{self.auth['username']}:{self.auth['password']}"
                encoded = base64.b64encode(auth_string.encode()).decode()
                self.default_headers['Authorization'] = f"Basic {encoded}"
            elif 'api_key' in self.auth:
                self.default_headers['X-API-Key'] = self.auth['api_key']

    async def _connect(self) -> None:
        """Establish HTTP session and test connectivity"""
        try:
            # Create connector with pooling configuration
            self._connector = aiohttp.TCPConnector(
                limit=self.connection_pool_size,
                limit_per_host=self.max_keepalive_connections,
                ttl_dns_cache=300,  # 5 minutes
                use_dns_cache=True,
                verify_ssl=self.ssl_verify,
            )

            # Create session with timeout and headers
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=self.timeout * 0.3,
                sock_read=self.timeout * 0.7,
            )

            self._session = aiohttp.ClientSession(
                connector=self._connector,
                timeout=timeout,
                headers=self.default_headers,
            )

            # Test connectivity with a simple HEAD request
            await self._test_connection()

            logger.info(f"API resource {self.name} connected to {self.base_url}")

        except Exception as e:
            # Cleanup on failure
            if self._session:
                await self._session.close()
            if self._connector:
                await self._connector.close()
            self._session = None
            self._connector = None

            raise ResourceConnectionError(self.name, self.base_url) from e

    async def _disconnect(self) -> None:
        """Close HTTP session and cleanup connections"""
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
        self._session = None
        self._connector = None

        logger.info(f"API resource {self.name} disconnected")

    async def _health_check(self) -> ResourceHealth:
        """Perform API health check"""
        if not self._session:
            return ResourceHealth.UNHEALTHY

        try:
            # Try to reach the API with a simple HEAD request to root
            start_time = asyncio.get_event_loop().time()
            async with self._session.head(self.base_url) as response:
                latency = asyncio.get_event_loop().time() - start_time
                self._last_request_time = start_time

                if response.status < 400:  # Consider 2xx and 3xx as healthy
                    return ResourceHealth.HEALTHY
                elif response.status >= 500:  # Server errors
                    return ResourceHealth.UNHEALTHY
                else:  # 4xx errors (client errors)
                    return ResourceHealth.DEGRADED

        except Exception as e:
            logger.warning(f"API health check failed for {self.name}: {e}")
            return ResourceHealth.UNHEALTHY

    async def _cleanup(self) -> None:
        """Cleanup API resource"""
        await self._disconnect()
        logger.info(f"API resource {self.name} cleaned up")

    def _build_url(self, path: str) -> str:
        """Build full URL from base URL and path"""
        if path.startswith('http'):
            return path  # Already a full URL
        elif path.startswith('/'):
            return urljoin(self.base_url + '/', path[1:])
        else:
            return urljoin(self.base_url + '/', path)

    async def _execute_request(
        self,
        method: str,
        path: str,
        data: Optional[Any] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Execute HTTP request with retry logic"""
        if not self.is_connected:
            from ..exceptions import ResourceStateError
            raise ResourceStateError(self.name, self.state.value, ResourceState.CONNECTED.value)

        url = self._build_url(path)
        request_headers = self.default_headers.copy()
        if headers:
            request_headers.update(headers)

        # Prepare request data
        json_data = None
        if data is not None:
            if isinstance(data, dict):
                json_data = data
            elif isinstance(data, str):
                json_data = json.loads(data)
            else:
                json_data = data

        last_exception = None
        for attempt in range(self.max_retries + 1):
            try:
                self._request_count += 1

                async with self._session.request(
                    method=method.upper(),
                    url=url,
                    json=json_data,
                    params=params,
                    headers=request_headers,
                    timeout=aiohttp.ClientTimeout(total=timeout or self.timeout),
                ) as response:

                    # Log successful request
                    logger.debug(f"API {method} {url} -> {response.status}")

                    # Parse response
                    try:
                        if response.headers.get('content-type', '').startswith('application/json'):
                            response_data = await response.json()
                        else:
                            response_data = await response.text()
                    except Exception:
                        response_data = await response.text()

                    result = {
                        'status': response.status,
                        'headers': dict(response.headers),
                        'data': response_data,
                        'url': str(response.url),
                        'attempts': attempt + 1,
                    }

                    return result

            except asyncio.TimeoutError as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"API request timeout (attempt {attempt + 1}/{self.max_retries + 1}): {url}")
                    await asyncio.sleep(self.retry_delay * (attempt + 1))  # Exponential backoff
                else:
                    self._error_count += 1
                    raise ResourceTimeoutError(self.name, f"{method} {path}", self.timeout) from e

            except Exception as e:
                last_exception = e
                if attempt < self.max_retries:
                    logger.warning(f"API request failed (attempt {attempt + 1}/{self.max_retries + 1}): {e}")
                    self._retry_count += 1
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    self._error_count += 1
                    raise ResourceError(f"API request failed after {self.max_retries + 1} attempts", self.name) from e

    # Public API methods
    async def get(self, path: str, params: Optional[Dict[str, str]] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform GET request"""
        return await self._execute_request('GET', path, params=params, headers=headers)

    async def post(self, path: str, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform POST request"""
        return await self._execute_request('POST', path, data=data, headers=headers)

    async def put(self, path: str, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform PUT request"""
        return await self._execute_request('PUT', path, data=data, headers=headers)

    async def patch(self, path: str, data: Optional[Any] = None, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform PATCH request"""
        return await self._execute_request('PATCH', path, data=data, headers=headers)

    async def delete(self, path: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform DELETE request"""
        return await self._execute_request('DELETE', path, headers=headers)

    async def head(self, path: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Perform HEAD request"""
        return await self._execute_request('HEAD', path, headers=headers)

    async def ping(self) -> bool:
        """Test API connectivity"""
        try:
            result = await self._execute_request('HEAD', '/')
            return result['status'] < 400
        except Exception:
            return False

    async def get_endpoint_info(self, path: str = "/") -> Dict[str, Any]:
        """Get information about an endpoint"""
        try:
            result = await self.head(path)
            return {
                'available': True,
                'status': result['status'],
                'headers': result['headers'],
                'endpoint': result['url'],
            }
        except Exception as e:
            return {
                'available': False,
                'error': str(e),
                'endpoint': self._build_url(path),
            }

    def get_stats(self) -> Dict[str, Any]:
        """Get API resource statistics"""
        stats = super().get_stats()
        stats.update({
            'base_url': self.base_url,
            'is_connected': self.is_connected,
            'requests_total': self._request_count,
            'errors_total': self._error_count,
            'retries_total': self._retry_count,
            'max_retries': self.max_retries,
            'connection_pool_size': self.connection_pool_size,
            'last_request': self._last_request_time,
            'auth_method': self._get_auth_method(),
        })
        return stats

    def _get_auth_method(self) -> str:
        """Get authentication method description"""
        if not self.auth:
            return "none"
        elif 'bearer_token' in self.auth:
            return "bearer_token"
        elif 'username' in self.auth:
            return "basic_auth"
        elif 'api_key' in self.auth:
            return "api_key"
        else:
            return "custom"

    async def _test_connection(self) -> None:
        """Test connection to API"""
        await self._execute_request('HEAD', '/')

    def __str__(self) -> str:
        """String representation"""
        return f"APIResource(name='{self.name}', url='{self.base_url}', connected={self.is_connected})"
