# Testing Strategy & Best Practices

This section documents the testing approach for UCore, including test adapters, recommended tools, and best practices for unit, integration, and end-to-end tests.

---

## Overview

UCore is designed for testability and includes:
- Test adapters for MongoDB ORM and resources
- Mockable components and dependency injection
- Pytest-based test suite
- Support for async and sync tests

---

## Test Structure

- **Unit tests:**  
  Located in `tests/core/`, `tests/data/`, `tests/fs/`, etc.  
  Test individual modules and classes in isolation.

- **Integration tests:**  
  Located in `tests/integration/`  
  Test interactions between components (e.g., ORM + MongoDB, event bus + plugins).

- **End-to-end (e2e) tests:**  
  Located in `tests/e2e/`  
  Test full workflows and user scenarios.

- **Performance and security tests:**  
  Located in `tests/performance/`, `tests/security/`

---

## Test Adapters

- **TestableMongoRecord:**  
  Use for mocking and patching MongoDB operations in unit tests.

```python
from ucore_framework.data.mongo_test_adapter import TestableMongoRecord

class TestUser(TestableMongoRecord):
    collection_name = "test_users"
```

- **Mocked Resources:**  
  Use dependency injection to provide mock resources to components.

---

## Running Tests

- Run all tests:
  ```sh
  pytest
  ```

- Run a specific test file:
  ```sh
  pytest tests/core/test_event_bus.py
  ```

- Run async tests with pytest-asyncio:
  ```python
  @pytest.mark.asyncio
  async def test_async_feature():
      ...
  ```

---

## Best Practices

- Use test adapters and mocks to isolate units under test.
- Write tests for all new features and bug fixes.
- Use fixtures for setup and teardown.
- Test both success and failure scenarios.
- Measure code coverage and aim for high coverage on core modules.

---

See also:  
- [Core Framework](core.md)  
- [Data Layer & MongoDB ORM](data.md)  
- [Examples](examples.md)
