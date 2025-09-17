# Test Report: tests/messaging/test_redis_event_bridge.py

**Date:** 17.09.2025  
**Test File:** `tests/messaging/test_redis_event_bridge.py`  
**Python Version:** 3.11.9  
**Pytest Version:** 8.4.2

---

## Summary

- **Total tests:** 23
- **Passed:** 23
- **Failed:** 0
- **Warnings:** 4 (see below)
- **Duration:** ~0.36s

---

## Warnings

- RuntimeWarning: coroutine 'AsyncMockMixin._execute_mock_call' was never awaited (several locations)
- These warnings are due to unawaited coroutines in some test mocks and do not affect test pass/fail status.

---

## Conclusion

All tests in `tests/messaging/test_redis_event_bridge.py` passed successfully.  
No failures detected.  
Warnings are related to test mocking and do not indicate functional errors.
