# UCore Domain-Driven Architecture Guide

## 🏗️ **Architecture Overview**

UCore has been reorganized into a **domain-driven architecture** where components are grouped by their primary application use case rather than technical layer. This makes the framework more intuitive and easier to navigate.

## 📁 **Domain Structure**

### **1. Core Domain** (`framework.core`)
**Purpose**: Fundamental building blocks of the framework

**Key Components**:
- `App`: Main application orchestrator with component lifecycle management
- `Component`: Base class for all framework components
- `Config`: Configuration management system
- `Container`: Dependency injection and service resolution
- `Plugin`: Plugin system for extensibility

**Usage**:
```python
from framework import App
from framework.core import Component, Config

app = App("MyApplication")
config = Config()
```

### **2. Web Domain** (`framework.web`)
**Purpose**: HTTP servers and web application functionality

**Key Components**:
- `HttpServer`: Production-ready HTTP server with Prometheus metrics
- Web routing and middleware
- Request/response handling
- REST API utilities

**Usage**:
```python
from framework.web import HttpServer

server = HttpServer(app)

@server.route("/api/data", "GET")
async def get_data():
    return {"data": "sample"}
```

### **3. Messaging Domain** (`framework.messaging`)
**Purpose**: Event-driven communication and message passing

**Key Components**:
- `EventBus`: Central event management and routing
- `RedisAdapter`: Redis-based messaging
- `Event`: Event system with type safety
- `EventBusRedisBridge`: Distributed event communication

**Usage**:
```python
from framework.messaging import EventBus, Event

class UserEvent(Event):
    def __init__(self, user_id: str):
        self.user_id = user_id

event_bus = EventBus()
event_bus.publish(UserEvent("123"))
```

### **4. Data Domain** (`framework.data`)
**Purpose**: Database operations, caching, and data persistence

**Key Components**:
- `Database`: SQLAlchemy adapter with transaction monitoring
- `DiskCache`: High-performance disk-based caching
- `Base`: SQLAlchemy declarative base for models

**Usage**:
```python
from framework.data import Database, Base
from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    name = Column(String)

db = Database(app)
session = db.get_session()
```

### **5. Desktop Domain** (`framework.desktop`)
**Purpose**: GUI desktop applications and user interfaces

**Key Components**:
- `PySide6Adapter`: Native Qt/PySide6 desktop interface
- `FletAdapter`: Web-based desktop interface
- Desktop UI components and widgets

**Usage**:
```python
from framework.desktop import PySide6Adapter

ui_adapter = PySide6Adapter(app)
app.register_component(lambda: ui_adapter)
```

### **6. Processing Domain** (`framework.processing`)
**Purpose**: Background task processing and worker management

**Key Components**:
- `task`: Task decorator for background processing
- `BackgroundProcessor`: Background task management
- `CLI`: Command-line interface components
- Worker processes and job queues

**Usage**:
```python
from framework.processing import task

@task()
def process_email(user_id: str):
    # Send email processing logic
    return f"Email sent to {user_id}"
```

### **7. Monitoring Domain** (`framework.monitoring`)
**Purpose**: Observability, logging, and system monitoring

**Key Components**:
- `logging`: Structured logging with correlation
- `metrics`: Prometheus metrics collection
- `observability`: Application tracing and monitoring
- Health checks and performance monitoring

**Usage**:
```python
from framework.monitoring import logging

logger = logging.get_logger("my-service")
logger.info("Service started", user_id="123")
```

### **8. Simulation Domain** (`framework.simulation`)
**Purpose**: Testing and simulation environments

**Key Components**:
- Component simulation frameworks
- Entity definitions
- Testing utilities
- Mock environments

## 🔄 **Migration Guide**

### **Before (Flat Structure)**:
```python
from framework.app import App
from framework.http import HttpServer
from framework.db import Database
from framework.event_bus import EventBus
```

### **After (Domain-Driven)**:
```python
from framework import App              # Core domain
from framework.web import HttpServer   # Web domain
from framework.data import Database    # Data domain
from framework.messaging import EventBus  # Messaging domain
```

## 🎯 **Benefits**

1. **Intuitive Organization**: Components are grouped by application use case
2. **Easier Discovery**: Find relevant components by domain
3. **Clearer Dependencies**: Domain boundaries reduce coupling
4. **Scalable Architecture**: Add new domains without disrupting existing code
5. **Better Documentation**: Each domain has clear purpose and scope

## 🚀 **Getting Started**

Choose the domains relevant to your application:

**Web API**:
```python
from framework import App
from framework.web import HttpServer
from framework.data import Database
```

**Desktop App**:
```python
from framework import App
from framework.desktop import PySide6Adapter
from framework.processing import task
```

**Microservice**:
```python
from framework import App
from framework.web import HttpServer
from framework.messaging import EventBus, RedisAdapter
from framework.monitoring import metrics
```

---

This domain-driven architecture makes UCore more intuitive and maintainable while preserving all existing functionality through backward compatibility.
