# Detailed Checklist for the Second Iteration (v0.3)

## Iteration Goals:

- Implement asynchronous support for desktop and web UIs.
- Create the foundation for a simulation module (Environment).
- Add basic support for database operations (Persistence).
- Improve developer experience (DX) with tools.

---

### 1. UI Integration (PySide6 & Flet)

| #   | Task                               | Status | Comments                                                                                                                            |
|-----|------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------|
| 1.1 | **PySide6 Adapter**: Research and implement asyncio integration with the Qt event loop. |   ✅   | Create an adapter component (`PySide6Adapter`) that manages the `QApplication` lifecycle and ensures the event loops work together. |
| 1.2 | Add DI support for PySide6 widgets and windows. |   ✅   | Allow injecting services from the DI container directly into UI classes.                                                            |
| 1.3 | **Flet Adapter**: Implement a component to run Flet applications. |   ✅   | Create a wrapper (`FletAdapter`) that integrates the launch of a Flet application into the main framework's lifecycle.        |
| 1.4 | Create a PySide6 desktop application example. |   ✅   | The example should demonstrate asynchronous interaction with a backend component (e.g., an async HTTP client or a background task). |
| 1.5 | Create a Flet web UI example.      |   ✅   | An example showing how a Flet UI can interact with framework services.                                                              |
| 1.6 | Write tests for the UI adapters.   |   ✅   | Tests should verify correct startup, shutdown, and event loop integration.                                                          |

---

### 2. Environment/Simulation Module (Base)

| #   | Task                               | Status | Comments                                                                                                                            |
|-----|------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------|
| 2.1 | Implement the base `EnvironmentEntity` class. |   ✅   | Must support a hierarchy (parent/child) and a list of attached controllers.                                                 |
| 2.2 | Implement the base `EntityController` class. |   ✅   | Must have methods integrated into the main loop (`update`, `start`, `stop`) and access to the parent `Entity`.                |
| 2.3 | Implement basic controllers: `Transform` and `BotAgent`. |   ✅   | `Transform` for position/rotation, `BotAgent` as a stub for AI with a simple `get_action()` method. |
| 2.4 | Create a simple simulation example. |   ✅   | For example, a console application where several `Entity` objects with `BotAgent` move randomly in 2D space.                      |
| 2.5 | Write Unit tests for `EnvironmentEntity` and `EntityController` logic. |   ✅   | Check correct addition/removal of child elements and controllers, and lifecycle method calls.                                 |

---

### 3. Persistence Layer (SQLAlchemy)

| #   | Task                               | Status | Comments                                                                                                                            |
|-----|------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------|
| 3.1 | Design and implement a base adapter for SQLAlchemy. |   ✅   | A `SQLAlchemyAdapter` component that manages the `engine` and `sessionmaker`, reading configuration from `Config`.            |
| 3.2 | Integrate session management with the DI container. |   ✅   | Implement a `Depends()` mechanism to get a `Session` in HTTP request handlers and other services.                           |
| 3.3 | Integrate the adapter with the application lifecycle. |   ✅   | Connect to the DB on start (`on_start`) and correctly close the connection pool on stop (`on_stop`).                          |
| 3.4 | Extend the example HTTP service to work with the DB. |   ✅   | Add CRUD operations for a simple model (e.g., `Todo` or `Item`) to demonstrate persistence.                                 |
| 3.5 | Write integration tests for the SQLAlchemy adapter. |   ✅   | Use an in-memory database (e.g., SQLite) to test session lifecycle and CRUD operations.                                     |

---

### 4. Tooling & Developer Experience (DX)

| #   | Task                               | Status | Comments                                                                                                                            |
|-----|------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------|
| 4.1 | (Carryover from v0.1) Set up CI/CD for documentation generation. |        | Use GitHub Actions (or similar) to automatically build and publish documentation (e.g., to GitHub Pages) on `main` updates. |
| 4.2 | Implement a basic CLI command generator. |        | Allow registering functions as CLI commands that can be run via `python app.py <command_name>`.                                   |
| 4.3 | Create a project initialization tool (`ucore init`). |        | Can use `cookiecutter` or write a simple script that creates the directory structure for a new framework-based project.       |

---

### 5. Documentation & Examples

| #   | Task                               | Status | Comments                                                                                                                            |
|-----|------------------------------------|--------|-------------------------------------------------------------------------------------------------------------------------------------|
| 5.1 | Write a guide on creating a desktop application (PySide6). |        | A step-by-step tutorial based on the created example.                                                                       |
| 5.2 | Write a guide on creating a web UI (Flet). |        |                                                                                                                                     |
| 5.3 | Write an introduction to the Environment module. |        | Explain the concepts of `Entity`, `Controller`, and how to use them.                                                          |
| 5.4 | Update documentation with a section on working with databases. |        | Describe how to configure `SQLAlchemyAdapter` and use DI for sessions.                                                      |
| 5.5 | Restructure the `examples/` directory for better navigation. |        | Create subdirectories for different types of examples (`api/`, `desktop-ui/`, `simulation/`).                               |
