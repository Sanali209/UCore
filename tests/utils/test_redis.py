import pytest
import fakeredis.aioredis
from typing import Generator

@pytest.fixture(scope="function")
def fake_redis_instance() -> Generator[fakeredis.aioredis.FakeRedis, None, None]:
    """
    Pytest fixture that provides a clean, in-memory Redis instance for each test.
    """
    redis = fakeredis.aioredis.FakeRedis()
    yield redis
    redis.flushall()
