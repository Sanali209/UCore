# 🚀 **UCore Framework Guide - Version 1.0.0**

## 📖 **Framework Overview**

UCore is an **enterprise-grade, component-based framework** for building sophisticated Python applications with integrated observability, asynchronous processing, and extensibility features. Built for production use with modern Python best practices.

**Core Philosophy:** *Component-first architecture with dependency injection, comprehensive monitoring, and plugin extensibility for scalable applications.*

---

## 🏗️ **Architecture Overview**

### **Core Principles**
- **Component-Based Design** - Everything is a component with lifecycle management
- **Dependency Injection** - Type-safe service resolution and scoping
- **Event-Driven Architecture** - Comprehensive event system for component communication
- **Observability First** - Built-in monitoring, metrics, and logging
- **Extensibility** - Plugin system for feature extension
- **Cross-Platform** - Works on server, desktop, web, and mobile platforms

### **Key Features**
- ✅ **Async Architecture** - Built for high-performance async/await patterns
- ✅ **Multi-Platform UI** - Flet (web) and PySide6 (desktop) support
- ✅ **Professional Monitoring** - Prometheus metrics and OpenTelemetry observability
- ✅ **Background Processing** - Redis/Celery integration for task management
- ✅ **Database Integration** - SQLAlchemy-based data management
- ✅ **Configuration Management** - YAML-based config with environment variable support
- ✅ **Plugin System** - Dynamic extensibility through plugins
- ✅ **Simulation & Testing** - Built-in simulation framework for testing

---

## 📦 **Core Components**

### **1. Application Architecture**

#### **App Class** (`framework/app.py`)
Central orchestration engine managing:
- **Component Lifecycle** - Automatic startup/shutdown of all components
- **Dependency Injection** - Container management and service resolution
- **Configuration Management** - YAML configs with environment variable overrides
- **Event System** - Built-in event publishing for application lifecycle
- **Plugin Loading** - Dynamic plugin discovery and registration
- **Signal Handling** - Graceful shutdown on SIGINT/SIGTERM
- **CLI Integration** - Argument parsing and bootstrap configuration

```python
# Correct imports for current framework
from framework.app import App
from framework.core.component import Component

app = App("MyApp")
app.register_component(lambda: MyComponent(app))  # Lambda wrapper required
await app.start()  # Async startup pattern
```

#### **Component System** (`framework/core/component.py`)
Base class for all framework components providing:
- **Lifecycle Management** - Standard `start()` and `stop()` methods
- **Dependency Injection** - Access to the DI container through `app.container`
- **Error Handling** - Structured error publishing through EventBus
- **Event Publishing** - Component lifecycle event publishing
- **Configuration Updates** - Dynamic configuration change notifications

```python
from framework.core.component import Component
from framework.monitoring.metrics import HTTPMetricsAdapter

class MyComponent(Component):
    def __init__(self, app):
        self.app = app  # App passed by factory function
        self.metrics = app.container.get(HTTPMetricsAdapter)

    async def start(self):
        # Component initialization logic
        pass

    async def stop(self):
        # Component cleanup logic
        pass

    def on_config_update(self, config):
        # Handle configuration changes
        pass
```

### **2. Dependency Injection**

#### **Container System** (`framework/di.py`)
Advanced dependency injection container with:
- **Multiple Scopes** - Singleton, Transient, and Scoped resolution
- **Type Safety** - Interface-based service registration
- **Circular Dependency Detection** - Automatic detection and error reporting
- **Provider Override** - Runtime service replacement for testing
- **Instance Registration** - Pre-created object injection

```python
from framework.core.di import Container, Scope

# Register services
container.register(DatabaseService, scope=Scope.SINGLETON)
container.register_instance(my_config, DatabaseConfig)

# Resolve dependencies
service = container.get(DatabaseService)
```

---

## 🌐 **Web & HTTP Services**

### **HTTP Server Component** (`framework/web/http.py`)
Production-ready HTTP server with:
- **Async Processing** - aiohttp-based high-performance server
- **Route Decorators** - Type-safe route registration with DI
- **Automatic Metrics** - Integrated Prometheus metrics collection
- **Event Integration** - Comprehensive request/response event publishing
- **Error Handling** - Structured HTTP error event creation
- **Middleware Support** - Custom middleware chains
- **Configuration Integration** - Runtime server configuration updates

```python
from framework.app import App
from framework.web.http import HttpServer

# Create app and register HTTP server
app = App("MyWebApp")
http_server = HttpServer(app, host="0.0.0.0", port=8080)

@http_server.route("/api/data", "GET")
async def get_data():
    # Direct dependency injection in route handlers
    return {"data": "Hello World", "status": "success"}

# Register and start
app.register_component(lambda: http_server)
await app.start()  # Server starts automatically
```

### **Metrics & Monitoring** (`framework/monitoring/metrics.py`)
Enterprise-grade observability system:
- **Prometheus Integration** - Counter, Histogram, Gauge metrics
- **Automatic HTTP Metrics** - Request duration, status codes, response sizes
- **Error Tracking** - HTTP error metrics with type classification
- **Performance Analysis** - Latency distribution and throughput monitoring
- **Business Metrics** - Custom metric decorators for business logic
- **Realtime Dashboards** - Prometheus-compatible metrics endpoint

```python
from framework.monitoring.metrics import HTTPMetricsAdapter

# Create app with metrics
app = App("MetricsApp")
metrics_adapter = HTTPMetricsAdapter(app)

@http_server.route("/metrics", "GET")
async def get_metrics():
    return {"metrics_endpoint": "available"}
```

---

## 🗄️ **Database Operations**

### **SQLAlchemy Integration** (`framework/db.py`)
Comprehensive database management with:
- **Async SQLAlchemy** - Full async database operations
- **Connection Pooling** - Efficient connection management
- **Session Monitoring** - Transaction lifecycle tracking
- **Performance Metrics** - Query duration and connection monitoring
- **Error Publishing** - Database error event creation
- **Transaction Context** - Monitored transaction boundaries

```python
from framework.data.db import SQLAlchemyAdapter

db_adapter = SQLAlchemyAdapter(app)

# Get monitored session
async with db_adapter.get_session() as session:
    result = await session.execute("SELECT * FROM users")
    # Session lifecycle events are automatically published
```

---

## 🔄 **Background Processing**

### **Task Management** (`framework/background.py`, `framework/tasks.py`)
Distributed task processing with:
- **Celery Integration** - Asynchronous task processing
- **Redis Backend** - Result storage and broker communication
- **Task Monitoring** - Execution status, duration, and error tracking
- **Retry Logic** - Automatic retry on task failure
- **Worker Management** - Distributed worker coordination

### **CPU Task Processing** (`framework/cpu_tasks.py`)
Concurrent CPU-intensive operations:
- **Thread Pool** - Offloaded CPU tasks from async loop
- **Progress Tracking** - Task execution progress monitoring
- **Resource Management** - CPU usage optimization
- **Result Caching** - Task result memoization

---

## 🚀 **Event-Driven Architecture**

### **Event System** (`framework/events.py`, `framework/event_bus.py`)
Sophisticated event delivery system:
- **Type-Safe Events** - Dataclass-based event definitions
- **Publish/Subscribe** - Component-to-component communication
- **Event Filtering** - Selective event subscription
- **Cross-Component Events** - Framework-wide event distribution
- **Error Events** - Structured error event publishing
- **Lifecycle Events** - Component startup/shutdown notification

```python
from framework.messaging.event_bus import EventBus
from framework.messaging.events import ComponentStartedEvent

# Publish custom events
event_bus.publish(ComponentStartedEvent(component_name="MyService"))
```

### **Redis Event Bridge** (`framework/redis_adapter.py`)
Inter-instance communication:
- **Redis Pub/Sub** - Distributed event communication
- **JSON Serialization** - Cross-platform event compatibility
- **Channel Naming** - Organized event routing
- **Message Queues** - Event buffering and processing

---

## 🎨 **User Interface Systems**

### **Cross-Platform UI** (`framework/desktop/ui/flet_adapter.py`, `framework/desktop/ui/pyside6_adapter.py`)

#### **FletAdapter** - Web/Browser Applications
- **Cross-Platform Web Apps** - Create web apps that run on any device
- **Modern UI Components** - Rich component library
- **Real-time Updates** - Live UI updates and interactive widgets
- **Responsive Design** - Automatic responsive layouts
- **State Management** - Integrated state synchronization
- **Deployment Options** - Self-hosted or cloud deployment
- **Task Tracker Example** - Complete CRUD application with persistent data

```python
from framework.app import App
from framework.desktop.ui.flet_adapter import FletAdapter

def flet_main(page):
    # Your Flet UI logic here
    pass

app = App("FletApp")
flet_adapter = FletAdapter(app, target_func=flet_main)
app.register_component(lambda: flet_adapter)
await app.start()  # Launches web server on port 8085
```

#### **PySide6Adapter** - Desktop Applications
- **Native Desktop Apps** - Professional-quality desktop applications
- **Qt Integration** - Full Qt5/Qt6 widget system access
- **Cross-Platform Desktop** - Windows, macOS, Linux support
- **Event Loop Integration** - Seamless GUI and async integration
- **Resource Management** - Memory and resource optimization

---

## 📊 **Observability & Monitoring**

### **Logging System** (`framework/logging.py`)
Structured logging with:
- **Multiple Output** - Console, file, rotating file outputs
- **Structured Data** - JSON-formatted log entries
- **Performance Logging** - Execution time tracking
- **Error Correlation** - Error ID generation for tracing
- **Log Levels** - Dynamic log level adjustment

### **Detailed Metrics** (`framework/metrics.py`)
Complete monitoring stack:
- **HTTP Metrics** - Request counts, durations, status codes
- **System Metrics** - CPU, memory, disk usage
- **Application Metrics** - Custom business metrics
- **Error Metrics** - Error rates and categorization
- **Performance Histograms** - Response time distributions

---

## 🔧 **Configuration Management**

### **Configuration System** (`framework/config.py`, `framework/settings.py`)
Advanced configuration management:
- **YAML Configuration** - Hierarchical configuration files
- **Environment Variables** - Runtime configuration override
- **Hot Reload** - Configuration changes without restart
- **Validation** - Configuration schema validation
- **Multi-Source** - File, environment, and programmatic config

```python
# Configuration file (config.yml)
app:
  name: MyApp
  http:
    host: "0.0.0.0"
    port: 8080

database:
  url: "postgresql://user:pass@localhost/db"
```

---

## 🎯 **Plugin System & Extensibility**

### **Plugin Architecture** (`framework/plugins.py`)
Dynamic extensibility through:
- **Plugin Discovery** - Automatic plugin loading from directories
- **Registration System** - Ordered plugin initialization
- **Dependency Management** - Plugin dependencies and requirements
- **Error Isolation** - Plugin failure isolation
- **Hot Loading** - Runtime plugin loading and unloading

```python
from ucore import Plugin

class MyPlugin(Plugin):
    def register(self, app):
        # Plugin registration logic
        pass
```

---

## 🎮 **Simulation & Testing Framework**

### **Built-in Simulation** (`framework/simulation/`)
Comprehensive testing support:
- **Entity Simulation** - Mock data generation and simulation
- **Controller Management** - Simulation lifecycle management
- **Scenario Testing** - Complex interaction testing
- **Performance Simulation** - Load testing and profiling
- **Integration Testing** - Component integration validation

---

## 📚 **Cache System**

### **Disk Cache Integration** (`framework/disk_cache.py`)
High-performance caching with:
- **Disk-Based Storage** - Persistent, high-volume caching
- **Memory Management** - LRU eviction and size limits
- **Indexing Support** - Fast lookup and query capabilities
- **Expiration Policies** - Time-based and size-based eviction
- **Multi-Level Caching** - Configurable cache hierarchies

---

## 🏆 **Advanced Features**

### **Resource Management**
- **Connection Pools** - Efficient database connection reuse
- **Thread Pools** - CPU task offloading with resource limits
- **Memory Pools** - Optimized memory usage patterns
- **File Handles** - Automatic cleanup and resource management

### **Security Features**
- **Credential Management** - Secure configuration handling
- **Access Control** - Component-level access patterns
- **Audit Logging** - Comprehensive operation logging
- **Security Events** - Security-relevant event tracking

### **Performance Optimization**
- **Async-First Design** - High-performance async patterns throughout
- **Connection Reuse** - Multiple connection types (HTTP, DB, Redis)
- **Resource Pooling** - Efficient resource utilization
- **Lazy Loading** - On-demand resource initialization

---

## 🚀 **Getting Started**

### **Quick Start - HTTP API**
```python
from framework.app import App
from framework.web.http import HttpServer

# Create application
app = App("MyAPI")

# Create HTTP server
http_server = HttpServer(app, host="0.0.0.0", port=8080)

# Add routes
@http_server.route("/api/health", "GET")
async def health_check():
    return {"status": "healthy", "service": "MyAPI"}

@http_server.route("/api/data", "GET")
async def get_data():
    return {"data": "Hello World", "timestamp": "2025-09-15"}

# Register and start
app.register_component(lambda: http_server)
await app.start()  # Starts HTTP server on port 8080
```

### **Quick Start - UI Application (Flet)**
```python
from framework.app import App
from framework.desktop.ui.flet_adapter import FletAdapter
import flet as ft

def flet_main(page: ft.Page):
    page.title = "My App"
    page.add(ft.Text("Hello from UCore + Flet!"))

app = App("MyUI")
flet_adapter = FletAdapter(app, target_func=flet_main)
app.register_component(lambda: flet_adapter)
await app.start()  # Opens web browser to http://localhost:8085
```

### **Advanced Example with Database & Redis**
```python
from framework.app import App
from framework.web.http import HttpServer
from framework.data.db import SQLAlchemyAdapter
from framework.messaging.redis_adapter import RedisAdapter
from framework.monitoring.metrics import HTTPMetricsAdapter

app = App("FullStackApp")

# Register components
http_server = HttpServer(app, host="0.0.0.0", port=8080)
db_adapter = SQLAlchemyAdapter(app)
redis_adapter = RedisAdapter(app)
metrics_adapter = HTTPMetricsAdapter(app)

app.register_component(lambda: http_server)
app.register_component(lambda: db_adapter)
app.register_component(lambda: redis_adapter)
app.register_component(lambda: metrics_adapter)

# Add routes with database access
@http_server.route("/api/users", "GET")
async def get_users():
    async with db_adapter.get_session() as session:
        # Your database queries here
        return {"users": []}

# Configure Redis pub/sub
await redis_adapter.subscribe('notifications')

# Start application
await app.start()
```

---

## 📋 **Architecture Patterns**

### **Recommended Application Structure**
```
/my-ucore-app/
├── app.py                 # Main application entry point
├── config.yml            # Application configuration
├── plugins/              # Custom plugins directory
│   ├── __init__.py
│   └── analytics_plugin.py
├── components/           # Custom component implementations
│   ├── __init__.py
│   ├── api_service.py
│   └── background_worker.py
├── models/               # Database models
│   └── user.py
├── routers/              # HTTP route handlers
│   └── api.py
└── tests/               # Test suites
    ├── test_app.py
    └── test_components.py
```

### **Best Practices**
- **Component Design** - Keep components focused and testable
- **Error Handling** - Use event publishing for error propagation
- **Configuration Management** - Externalize all configuration
- **Testing Strategy** - Use simulation framework for component testing
- **Monitoring Setup** - Enable all observability features in production

---

## 🔧 **Deployment & Operations**

### **Production Deployment**
```bash
# Development
python app.py --config config.yml --log-level DEBUG

# Production with plugins
python app.py --config production.yml --plugins-dir ./plugins --log-level INFO

# With process manager (systemd/pm2)
[Service]
ExecStart=/usr/bin/python3 /path/to/app.py --config prod.yml
WorkingDirectory=/path/to/my-app
Restart=always
```

### **Environment Variables**
```bash
export DATABASE_URL="postgresql://user:pass@host:5432/db"
export REDIS_URL="redis://localhost:6379/0"
export LOG_LEVEL="INFO"
export METRICS_ENABLED="true"
export HTTP_HOST="0.0.0.0"
export HTTP_PORT="8080"
```

### **Health Checks**
- **HTTP Health Endpoint** - Built-in `/health` endpoint
- **Metrics Endpoint** - Prometheus `/metrics` integration
- **Component Health** - Individual component health checks
- **Database Health** - Connection status and performance metrics

---

## � **Migration Guide**

### **From Traditional Frameworks**
```python
# Traditional Flask/FastAPI
from flask import Flask
app = Flask(__name__)

# UCore equivalent
from ucore import App, HttpServer

app = App("MyApp")
app.register_component(HttpServer(app))

@app.http.route("/endpoint")
async def handle_request():
    return {"data": "Hello World"}
```

---

## 📝 **API Reference**

### **Core Classes**
- `App` - Main application orchestrator
- `Component` - Base component class
- `Container` - Dependency injection container
- `EventBus` - Event publishing system
- `Config` - Configuration management

### **Component Classes**
- `HttpServer` - HTTP server component
- `SQLAlchemyAdapter` - Database adapter
- `RedisAdapter` - Redis client
- `MetricsAdapter` - Monitoring system
- `DiskCacheAdapter` - Caching system

### **Key Functions**
- `app.run()` - Start application with CLI handling
- `app.register_component()` - Register component instance/class/factory
- `event_bus.publish()` - Publish events to subscribers
- `container.get()` - Resolve services from DI container

---

## 🌟 **Performance Characteristics**

| Metric | Performance | Details |
|--------|------------|---------|
| **HTTP Throughput** | ⚡ **High** | aiohttp-based async processing |
| **Database Ops** | ⚡ **High** | Async SQLAlchemy with connection pooling |
| **Memory Usage** | 🟢 **Optimized** | Component-based with cleanup |
| **CPU Efficiency** | ⚡ **High** | Async patterns with selective threading |
| **Scalability** | 🚀 **Excellent** | Designed for horizontal scaling |
| **Observability** | 📊 **Complete** | Full monitoring and metrics integration |

---

## 🎉 **UCore Success Stories**

✓ **Web APIs** - High-performance REST APIs with monitoring
✓ **Data Processing** - ETL pipelines with progress tracking
✓ **Real-time Apps** - Live user interfaces with state synchronization
✓ **Microservices** - Event-driven distributed architectures
✓ **Desktop Apps** - Cross-platform GUI applications
✓ **Background Jobs** - Distributed task processing systems

---

## 📞 **Support & Community**

- **Documentation** - Comprehensive framework documentation
- **Examples** - Working example applications in `/examples`
- **Testing** - Complete test suite with examples
- **Contributing** - Open contribution model
- **Enterprise Support** - Professional support available

---

## 🎯 **Summary**

**UCore Framework** is the **ultimate enterprise-grade Python application framework** providing:

- ✅ **Complete Architecture** - Component-based with async-first design
- ✅ **Production Ready** - Observability, monitoring, and error handling
- ✅ **Highly Extensible** - Plugin system and component overriding
- ✅ **Multi-Platform** - Works on web, desktop, and server platforms
- ✅ **Developer Friendly** - Comprehensive tooling and documentation
- ✅ **Performance Focused** - Optimized for high-throughput applications

**Perfect for building sophisticated applications that require reliability, observability, and scalability!** 🚀

---

*Framework Version: 1.0.0 | Documentation Date: September 2025*
