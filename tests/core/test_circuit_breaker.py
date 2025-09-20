import pytest
import asyncio
import time
from ucore_framework.core.circuit_breaker import CircuitBreakerManager, BreakerError

async def failing_operation():
    raise Exception("fail")

async def successful_operation():
    return True

@pytest.mark.asyncio
async def test_breaker_opens_after_failures():
    breaker = CircuitBreakerManager.get_breaker("test_breaker", fail_max=2)
    # First two calls fail, third should raise BreakerError immediately
    for _ in range(2):
        with pytest.raises(Exception):
            await breaker.call(failing_operation)
    with pytest.raises(BreakerError):
        await breaker.call(failing_operation)

@pytest.mark.asyncio
async def test_breaker_resets_after_timeout():
    breaker = CircuitBreakerManager.get_breaker("test_breaker2", fail_max=1, reset_timeout=0.1)
    with pytest.raises(Exception):
        await breaker.call(failing_operation)
    await asyncio.sleep(0.2)
    # First call after timeout should succeed (half-open), second should also succeed (closed)
    assert await breaker.call(successful_operation) is True
    assert await breaker.call(successful_operation) is True
