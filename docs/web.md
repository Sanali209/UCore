# Web Domain Guide

## Purpose

The web domain provides HTTP server capabilities for UCore, including routing, middleware, async endpoints, and integration with other domains.

---

## Main Classes & Components

- `HttpServer`: Async HTTP server with routing and middleware support.
- `Route`: Decorator for defining HTTP endpoints.
- Middleware: Customizable request/response processing.

---

## Usage Example

```python
from UCoreFrameworck.web.http import HttpServer

app = App("WebApp")
http_server = HttpServer(app)

@http_server.route("/ping", "GET")
async def ping():
    return {"status": "ok"}

if __name__ == "__main__":
    app.run()
```

---

## Middleware Example

```python
@http_server.middleware
async def log_request(request, call_next):
    print(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    return response
```

---

## Extensibility & OOP

- Add custom middleware for cross-cutting concerns.
- Subclass HttpServer for advanced server logic.

---

## Integration Points

- Integrates with resource, data, and monitoring domains.
- Exposes health and metrics endpoints.

---

## See Also

- [Project Structure Guide](project-structure-guide.md)
- [UCore Framework Guide](ucore-UCoreFrameworck-guide.md)
