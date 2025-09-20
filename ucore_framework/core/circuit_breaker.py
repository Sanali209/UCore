"""
Circuit breaker utilities for UCore Framework.

This module provides:
- CircuitBreakerManager: Singleton manager for named circuit breakers
- Integration with pybreaker for robust circuit breaking
- Easy access to the core CircuitBreakerError

Classes:
    CircuitBreakerManager: Manages named circuit breaker instances.

Usage:
    from ucore_framework.core.circuit_breaker import CircuitBreakerManager, BreakerError

    breaker = CircuitBreakerManager.get_breaker("redis_main")
    try:
        result = await breaker.call(some_function)
    except BreakerError:
        # handle circuit open
        ...

"""

import asyncio
import time
from pybreaker import CircuitBreaker, CircuitBreakerError
from typing import Dict, Callable, Any, Optional

class AsyncCircuitBreaker:
    """Async wrapper for CircuitBreaker with call method."""
    
    def __init__(self, fail_max: int = 3, reset_timeout: int = 30):
        self._breaker = CircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout)
        self._failure_count = 0
        self._max_failures = fail_max
        self._reset_timeout = reset_timeout
        self._last_failure_time: Optional[float] = None
    
    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """Call a function with circuit breaker protection."""
        current_time = time.time()
        
        # Check if enough time has passed to reset the circuit
        if (self._failure_count >= self._max_failures and 
            self._last_failure_time and 
            current_time - self._last_failure_time >= self._reset_timeout):
            # Reset the circuit (half-open state)
            self._failure_count = 0
            self._last_failure_time = None
        
        # Check if circuit is open
        if self._failure_count >= self._max_failures:
            raise CircuitBreakerError()
        
        try:
            # Call the function (handle both sync and async)
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                result = func(*args, **kwargs)
            
            # Reset failure count on success
            self._failure_count = 0
            self._last_failure_time = None
            return result
            
        except Exception as e:
            # Increment failure count and record time
            self._failure_count += 1
            self._last_failure_time = current_time
            raise
    
    @property
    def current_state(self):
        """Get current circuit breaker state."""
        if self._failure_count >= self._max_failures:
            return 'open'
        return 'closed'

class CircuitBreakerManager:
    """
    Singleton manager for named circuit breaker instances.

    Responsibilities:
        - Create and hold named circuit breakers for different resources/services
        - Provide easy access to circuit breakers by name
        - Configure failure threshold and reset timeout per breaker

    Example:
        breaker = CircuitBreakerManager.get_breaker("external_api", fail_max=5, reset_timeout=60)
        try:
            result = await breaker.call(some_function)
        except BreakerError:
            # handle circuit open
            ...
    """
    _breakers: Dict[str, AsyncCircuitBreaker] = {}

    @classmethod
    def get_breaker(cls, name: str, fail_max: int = 3, reset_timeout: int = 30) -> AsyncCircuitBreaker:
        """
        Get a circuit breaker by name, creating it if it doesn't exist.

        Args:
            name: Unique name for the circuit breaker (e.g., 'redis_main', 'external_api').
            fail_max: Number of failures before opening the circuit.
            reset_timeout: Seconds to wait before moving from 'open' to 'half-open'.

        Returns:
            AsyncCircuitBreaker: The named circuit breaker instance.
        """
        if name not in cls._breakers:
            cls._breakers[name] = AsyncCircuitBreaker(fail_max=fail_max, reset_timeout=reset_timeout)
        return cls._breakers[name]

# Expose the core error for easy importing
BreakerError = CircuitBreakerError
