# Web & HTTP Utilities

This section documents the web and HTTP utilities in UCore, including API resource types, HTTP helpers, and integration patterns.

---

## Overview

UCore provides utilities for building web-enabled applications and services, including:
- API resource types for RESTful endpoints
- HTTP helpers for requests and responses
- Integration with the event bus and resource manager

---

## Key Components

- **APIResource:**  
  Base class for defining RESTful API endpoints.

- **FileResource, DatabaseResource, MongoDBResource:**  
  Resource types for exposing files and databases over HTTP.

- **HTTP Utilities:**  
  Helpers for request parsing, response formatting, and error handling.

---

## Usage Example

```python
from ucore_framework.core.resource.types.api import APIResource

class UserAPI(APIResource):
    route = "/api/users"

    async def get(self, request):
        # Return list of users
        return await User.find({})

    async def post(self, request):
        data = await request.json()
        user = await User.new_record(**data)
        return user
```

---

## Integration Patterns

- Register API resources with the resource manager for automatic routing.
- Use event bus to trigger actions on HTTP events (e.g., after file upload).

---

## Extending Web Utilities

- Create new API resources by subclassing `APIResource`.
- Implement custom HTTP handlers for advanced use cases.
- Integrate with monitoring for API metrics and tracing.

---

See also:  
- [Core Framework](core.md)  
- [File System Resource Management](fs.md)
