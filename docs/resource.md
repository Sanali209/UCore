# Resource Domain Guide

## Purpose

The resource domain provides unified orchestration and management of resources in UCore, including connection pooling, health monitoring, and resource lifecycle management.

---

## Main Classes & Components

- `ResourceManager`: Central manager for all resources.
- `Resource`: Base class for resources.
- `ManagedResource`: Resources with explicit lifecycle management.
- `PooledResource`: Connection/resource pooling.
- `ObservableResource`: Resources with health/status monitoring.
- Resource types: API, Database, File, MongoDB, etc.

---

## Usage Example

```python
from ucore_framework.resource.manager import ResourceManager
from ucore_framework.resource.resource import Resource

class MyResource(Resource):
    def connect(self):
        print("Connected!")

manager = ResourceManager(app)
manager.register_resource(MyResource())
```

---

## Pooling Example

```python
from ucore_framework.resource.pool import PooledResource

class MyPool(PooledResource):
    ...
```

---

## Extensibility & OOP

- Subclass resource types for custom integrations.
- Add health checks and pooling logic as needed.

---

## Integration Points

- Used by data, processing, and web domains for resource access.
- Integrates with monitoring for health and metrics.

---

## See Also

- [Project Structure Guide](project-structure-guide.md)
- [UCore Framework Guide](ucore-ucore_framework-guide.md)
