# UCore Framework Comprehensive Guide

## Table of Contents
- [🎯 Overview](#-overview)
- [🚀 Quick Start](#-quick-start)
- [🏗️ Core Architecture](#️-core-architecture)
- [🔧 Component System](#-component-system)
- [⚙️ Dependency Injection](#️-dependency-injection)
- [🌐 HTTP Server & APIs](#-http-server--apis)
- [💾 Database Integration](#-database-integration)
- [⚙️ Configuration System](#️-configuration-system)
- [🎨 UI Frameworks](#-ui-frameworks)
- [🎮 Simulation Framework](#-simulation-framework)
- [🔧 CLI Tools](#-cli-tools)
- [📊 Observability & Metrics](#-observability--metrics)
- [🔌 Plugin System](#-plugin-system)
- [🎯 Background Tasks](#-background-tasks)
- [📝 Examples & Recipes](#-examples--recipes)

---

## 🎯 Overview

UCore is a comprehensive Python framework designed for building modern, scalable applications with:

- **🏗️ Component Architecture** - Modular, lifecycle-managed components
- **⚙️ Dependency Injection** - Clean, testable service management
- **🌐 HTTP Server** - Built-in async HTTP server with aiohttp
- **💾 Database Integration** - SQLAlchemy-based data persistence
- **🎨 UI Support** - Multiple UI frameworks (Flet, PySide6)
- **📊 Observability** - Metrics, logging, and monitoring
- **🔌 Extensible Plugins** - Plugin architecture for extensibility

### Key Features
- **Async-First Design** - Built for modern Python async patterns
- **Type-Safe Configuration** - Strong typing with Pydantic
- **Component Lifecycle** - Automatic startup/cleanup management
- **Rich Ecosystem** - Comprehensive tools and utilities
- **Production Ready** - Error handling, logging, metrics built-in

---

## 🚀 Quick Start

### 1. Installation

```bash
pip install -r requirements.txt
```

### 2. Your First UCore App

```python
from framework.app import App
from framework.component import Component

class HelloWorldComponent(Component):
    def start(self):
        self.app.logger.info("Hello from UCore!")

    def stop(self):
        self.app.logger.info("Goodbye from UCore!")

# Create and run the app
app = App(name="HelloWorldApp")
app.register_component(lambda: HelloWorldComponent())
app.run()
```

### 3. HTTP Server Example

```python
from framework.app import App
from framework.http import HttpServer

app = App(name="WebApp")

http_server = HttpServer(app)

@http_server.route("/api/hello", "GET")
def hello_endpoint(request):
    return {"message": "Hello, World!", "status": "success"}

app.register_component(lambda: http_server)
app.run()
```

---

## 🏗️ Core Architecture

### Application Structure

```
📦 UCore Framework
├── 🎯 App (Main Orchestrator)
├── 🔧 Components (Modular Services)
├── ⚙️ DI Container (Dependency Management)
├── 🌐 HTTP Server (API Layer)
├── 💾 Database (Data Persistence)
├── 🎨 UI Adapters (User Interface)
├── 📊 Observability (Monitoring)
└── 🔌 Plugins (Extensibility)
```

### Key Classes

```python
# Main application orchestrator
class App:
    def __init__(self, name: str, config_path: str = None)
    def register_component(self, component_factory: Callable)
    def run(self) -> None
    async def start(self) -> None  # Async startup
    async def stop(self) -> None   # Async shutdown

# Base class for all services
class Component:
    def __init__(self)
    def start(self) -> None    # Lifecycle: start
    def stop(self) -> None     # Lifecycle: stop

# Dependency injection container
class Container:
    def register(self, service_class, implementation=None, scope=Scope.SINGLETON)
    def get(self, service_type) -> object
```

---

## 🔧 Component System

Components are the building blocks of UCore applications. They follow a clear lifecycle pattern.

### Basic Component

```python
from framework.component import Component

class DatabaseComponent(Component):
    def __init__(self):
        self.connection = None

    def start(self):
        """Called when app starts"""
        self.connection = create_database_connection()
        self.app.logger.info("Database connected")

    def stop(self):
        """Called when app stops"""
        if self.connection:
            self.connection.close()
            self.app.logger.info("Database disconnected")
```

### Component Registration

```python
app = App("MyApp")

# Method 1: Lambda factory
app.register_component(lambda: DatabaseComponent())

# Method 2: Instance
db_comp = DatabaseComponent()
app.register_component(lambda: db_comp)

# Method 3: Class with custom args
def create_service(port=8080):
    return HttpService(port=port)

app.register_component(create_service)
```

### Advanced Component Patterns

```python
class AsyncComponent(Component):
    async def start(self):
        """Async startup - for connecting to external services"""
        self.client = await connect_to_external_service()
        self.app.logger.info("Service connected")

    async def stop(self):
        """Async shutdown"""
        if self.client:
            await self.client.disconnect()
            self.app.logger.info("Service disconnected")
```

---

## ⚙️ Dependency Injection

UCore provides a powerful DI container for managing service dependencies.

### Basic Usage

```python
from framework.di import Container, Scope

# Create container
container = Container()

# Register services
container.register(UserService)
container.register(DatabaseService, scope=Scope.SINGLETON)
container.register(CacheService, scope=Scope.TRANSIENT)

# Resolve services
user_service = container.get(UserService)
```

### Scopes

```python
# Singleton - One instance for entire application
container.register(DatabaseService, scope=Scope.SINGLETON)
db1 = container.get(DatabaseService)
db2 = container.get(DatabaseService)
assert db1 is db2  # Same instance

# Transient - New instance every time
container.register(UserService, scope=Scope.TRANSIENT)
user1 = container.get(UserService)
user2 = container.get(UserService)
assert user1 is not user2  # Different instances
```

### Constructor Injection

```python
class UserService:
    def __init__(self, database: DatabaseService, cache: CacheService):
        self.database = database
        self.cache = cache

class ApplicationService:
    def __init__(self, user_service: UserService):
        self.user_service = user_service

# Registration happens automatically
container.register(DatabaseService)
container.register(CacheService)
container.register(UserService)  # Dependencies resolved automatically

app_service = container.get(ApplicationService)
# Result: ApplicationService -> UserService -> DatabaseService & CacheService
```

---

## 🌐 HTTP Server & APIs

UCore includes a built-in HTTP server with automatic dependency injection.

### Basic HTTP Server

```python
from framework.app import App
from framework.http import HttpServer

app = App("APIServer")
http_server = HttpServer(app)

@http_server.route("/api/users", "GET")
def get_users(request):
    # Dependencies are automatically injected
    db = request.app.container.get(DatabaseService)
    users = db.get_all_users()
    return {"users": users}

@http_server.route("/api/users", "POST")
def create_user(request):
    # Access request data
    user_data = request.json()

    # Create user through service
    user_service = request.app.container.get(UserService)
    new_user = user_service.create_user(user_data)

    return {"user": new_user, "status": "created"}, 201

app.register_component(lambda: http_server)
app.run(port=8000)
```

### Advanced Routing

```python
# Multiple HTTP methods for same path
@http_server.route("/api/books/{id}", "GET")
def get_book(request):
    book_id = request.match_info['id']
    return {"book": get_book_by_id(book_id)}

@http_server.route("/api/books/{id}", "PUT")
def update_book(request):
    book_id = request.match_info['id']
    data = request.json()
    return {"book": update_book(book_id, data)}

@http_server.route("/api/books/{id}", "DELETE")
def delete_book(request):
    book_id = request.match_info['id']
    delete_book_by_id(book_id)
    return {"message": "Book deleted"}, 204
```

### Middleware Support

```python
# Custom middleware
def logging_middleware(request, response):
    request.app.logger.info(f"{request.method} {request.path}")
    return response

http_server.add_middleware(logging_middleware)
```

---

## 💾 Database Integration

UCore provides seamless database integration with SQLAlchemy.

### Database Setup

```python
from framework.app import App
from framework.db import SQLAlchemyAdapter

app = App("DatabaseApp")

# Database configuration through config
db_adapter = SQLAlchemyAdapter(app)
# Config loaded from environment or config file
# DATABASE_URL=/tmp/test.db

app.register_component(lambda: db_adapter)
```

### Model Definition

```python
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
```

### Database Operations

```python
from sqlalchemy.orm import sessionmaker

class UserService:
    def __init__(self, database_adapter: SQLAlchemyAdapter):
        self.session_local = database_adapter.SessionLocal

    def create_user(self, name: str, email: str):
        with self.session_local() as session:
            user = User(name=name, email=email)
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def get_user(self, user_id: int):
        with self.session_local() as session:
            return session.query(User).filter(User.id == user_id).first()

    def list_users(self):
        with self.session_local() as session:
            return session.query(User).all()
```

---

## ⚙️ Configuration System

UCore provides flexible configuration management from multiple sources.

### Configuration Sources

```python
from framework.config import Config

config = Config()

# Load from dictionary
config.load_from_dict({
    "app": {"name": "MyApp", "version": "1.0.0"},
    "database": {"url": "sqlite:///app.db"},
    "logger": {"level": "INFO"}
})

# Load from JSON file
config.load_from_file("/path/to/config.json")

# Load from environment variables
config.load_environment()  # UCORE_APP_NAME, UCORE_DATABASE_URL, etc.
```

### Configuration Usage

```python
# Access configuration values
app_name = config.get("app.name")
db_url = config.get("database.url")

# Access nested config
app_config = config.get("app")  # Returns dict
app_name = app_config["name"]

# Safe access with defaults
debug_mode = config.get("app.debug", default=False)
port = config.get("server.port", default=8080)
```

### Advanced Configuration Patterns

```python
# Runtime configuration updates
config.set("app.debug", True)
config.set("server.max_connections", 1000)

# Configuration validation
from typing import Dict, Any
from pydantic import BaseModel

class AppConfig(BaseModel):
    name: str
    version: str
    debug: bool = False
    port: int = 8080

app_config = AppConfig(**config.get("app"))
```

---

## 🎨 UI Frameworks

UCore supports multiple UI frameworks for desktop and web applications.

### Flet (Web/Desktop UI)

```python
from framework.app import App
from framework.ui.flet_adapter import FletAdapter

def create_flet_app():
    import flet as ft

    def main(page: ft.Page):
        page.title = "My Flet App"

        def button_clicked(e):
            page.add(ft.Text("Hello, World!"))

        page.add(ft.ElevatedButton("Say Hello", on_click=button_clicked))

    return main

app = App("FletApp")
flet_adapter = FletAdapter(app, target_func=create_flet_app())
app.register_component(lambda: flet_adapter)

# Run web server
app.run()  # Opens browser with Flet UI
```

### PySide6 (Desktop UI)

```python
from framework.app import App
from framework.ui.pyside6_adapter import PySide6Adapter

def create_pyside_app():
    from PySide6.QtWidgets import QApplication, QLabel, QPushButton, QVBoxLayout, QWidget

    def main():
        app = QApplication([])

        window = QWidget()
        window.setWindowTitle("My PySide6 App")

        layout = QVBoxLayout()
        label = QLabel("Hello, World!")
        button = QPushButton("Click Me")

        layout.addWidget(label)
        layout.addWidget(button)
        window.setLayout(layout)

        window.show()
        app.exec()

    return main

app = App("PySideApp")
pyside_adapter = PySide6Adapter(app, target_func=create_pyside_app())
app.register_component(lambda: pyside_adapter)

app.run()  # Launches desktop window
```

---

## 🎮 Simulation Framework

UCore includes a built-in simulation framework for game development and simulation.

### Basic Simulation

```python
from framework.simulation.entity import EnvironmentEntity
from framework.simulation.controllers import Transform

# Create simulation entity
entity = EnvironmentEntity(name="Player")

# Add transformation controller
transform = Transform(x=0, y=0, z=0)
entity.add_controller(transform)

# Update simulation
def game_loop(delta_time):
    entity.update(delta_time)

    # Access current position
    position = transform.get_position()
    print(f"Entity position: {position}")
```

---

## 🔧 CLI Tools

UCore provides powerful CLI tools for building command-line applications.

```python
from framework.app import App
from framework.cli import CLI

class MyCLI(CLI):
    def register_commands(self):
        @self.command("greet", "Greet a user")
        def greet(name: str, formal: bool = False):
            greeting = "Good day" if formal else "Hello"
            return f"{greeting}, {name}!"

        @self.command("create", "Create a new project")
        def create_project(name: str, template: str = "basic"):
            # Create project logic
            return f"Created project '{name}' using template '{template}'"

# Use CLI as main interface
app = App("CLITool")
cli = MyCLI(app)
app.register_component(lambda: cli)

# Run interactive CLI
cli.interactive()
```

---

## 📊 Observability & Metrics

Comprehensive monitoring and metrics collection.

### Metrics Collection

```python
from framework.metrics import MetricsManager

metrics = MetricsManager()

# Counter metrics
metrics.increment_counter("api_requests", tags={"method": "GET", "status": "200"})

# Gauge metrics
metrics.record_gauge("memory_usage", 75.5, tags={"unit": "MB"})

# Timer metrics
start_time = metrics.start_timer("db_query")
# ... database query
duration = metrics.end_timer(start_time, "db_query")

# Histogram metrics
metrics.record_histogram("response_time", 0.15, tags={"endpoint": "/api/users"})
```

### Logging Integration

```python
from framework.logging import LogManager

log_manager = LogManager()
logger = log_manager.get_logger("my_module")

# Configure different log levels
logger.debug("Detailed debug info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error occurred")

# Structured logging
logger.info("User login", extra={"user_id": 123, "ip": "192.168.1.1"})
```

---

## 🔌 Plugin System

Extend UCore applications through plugins.

### Creating a Plugin

```python
# plugins/my_plugin.py
from framework.plugins import Plugin

class MyPlugin(Plugin):
    def register(self, app):
        # Register services with app
        app.container.register(MyService)

        # Add routes
        http_server = app.container.get(HttpServer)
        @http_server.route("/my-plugin/greet", "GET")
        def greet(request):
            return {"message": "Hello from plugin!"}
```

### Loading Plugins

```python
from framework.plugins import PluginManager

plugin_manager = PluginManager()

# Load plugins from directory
plugins = plugin_manager.load_plugins("/path/to/plugins")

# Or specify individual plugins
plugin_manager.load_plugin("./plugins/my_plugin.py")
```

---

## 🎯 Background Tasks

Robust background task processing with Celery.

```python
from framework.background import TaskQueueAdapter
from framework.tasks import task

# Create background task adapter
bg_adapter = TaskQueueAdapter(app)
app.register_component(lambda: bg_adapter)

# Define background tasks
@task("send-email")
def send_email_task(user_email: str, subject: str, message: str):
    # Send email logic here
    print(f"Sending email to {user_email}: {subject}")

# Execute task
send_email_task.delay(
    user_email="user@example.com",
    subject="Welcome!",
    message="Welcome to our service"
)

# Schedule recurring tasks
@task("cleanup")
def cleanup_old_files():
    # Cleanup logic
    print("Cleaning up old files...")
```

---

## 📝 Examples & Recipes

### Complete API Server

```python
# Complete API application with database
from framework.app import App
from framework.http import HttpServer
from framework.db import SQLAlchemyAdapter
from framework.metrics import MetricsManager

app = App("APIServer")

# Database layer
db_adapter = SQLAlchemyAdapter(app)
app.register_component(lambda: db_adapter)

# HTTP server with routes
http_server = HttpServer(app)

@http_server.route("/api/health", "GET")
def health_check(request):
    return {"status": "healthy", "uptime": "24h"}

@http_server.route("/api/users", "GET")
def list_users(request):
    db = app.container.get(SQLAlchemyAdapter)
    users = db.get_users()
    return {"users": users}

@http_server.route("/api/users", "POST")
def create_user(request):
    data = request.json()
    db = app.container.get(SQLAlchemyAdapter)
    user = db.create_user(data)
    return {"user": user}, 201

app.register_component(lambda: http_server)

# Add metrics
metrics = MetricsManager()
app.register_component(lambda: metrics)

app.run(port=8000)
```

### Real-Time Chat Application

```python
# Real-time chat with WebSocket support
from framework.app import App
from framework.ui.flet_adapter import FletAdapter

def create_chat_app():
    import flet as ft
    import asyncio

    async def main(page: ft.Page):
        messages = ft.Column(scroll=ft.ScrollMode.AUTO)
        text_field = ft.TextField(hint_text="Type a message...")
        send_button = ft.ElevatedButton("Send")

        async def send_message(e):
            if not text_field.value:
                return

            # Add message to UI
            messages.controls.append(
                ft.Text(f"You: {text_field.value}")
            )
            text_field.value = ""
            page.update()

            # Process message in background
            # (could send to WebSocket, save to DB, etc.)

        send_button.on_click = send_message

        await page.add_async(
            ft.Text("Chat Application", style=ft.TextStyle(size=20)),
            messages,
            ft.Row([text_field, send_button])
        )

    return main

app = App("ChatApp")
flet_adapter = FletAdapter(app, target_func=create_chat_app())
app.register_component(lambda: flet_adapter)

app.run()
```

### Production Configuration

```python
# production_config.json
{
  "app": {
    "name": "ProductionApp",
    "version": "2.0.0",
    "debug": false
  },
  "server": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4
  },
  "database": {
    "url": "postgresql://user:pass@host:5432/db",
    "pool_size": 20,
    "max_overflow": 30
  },
  "logging": {
    "level": "WARNING",
    "file": "/var/log/application.log"
  },
  "cache": {
    "redis_url": "redis://localhost:6379/1",
    "ttl": 3600
  }
}

# Usage
app = App("ProductionApp", config_path="./production_config.json")
app.run()
```

---

This guide covers the core concepts and practical usage of the UCore Framework. Each section provides working examples that demonstrate real-world application development patterns.

For more advanced topics, see the detailed documentation in the `/docs` folder and examine the examples in the `/examples` directory.
