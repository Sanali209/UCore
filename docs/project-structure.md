# Project Structure Guide

This document describes the structure of the UCore project and the purpose of each major directory and file.

---

## Root Directory

- **README.md** — Project overview, features, and quick start.
- **requirements.txt** — Python dependencies.
- **app_config.yml, config.yml, custom_settings.yml** — Configuration files for app and framework.
- **demo_laps.csv** — Example data for demos.
- **resource_manager.log** — Log file for resource manager.
- **site_packages_path.txt, sys_path_debug.txt, python_executable.txt, pytest_sys_path.txt** — Environment/debug info.

---

## ucore_framework/

Main framework source code, organized by domain.

- **core/** — Core app, component, DI, plugins, settings, undo system.
- **data/** — Database, disk cache, MongoDB adapters/ORM.
- **desktop/** — Desktop UI (PySide6), event bus, settings, tabbed window, plugins.
- **fs/** — File system adapters, models, resource types, vector DB extensions.
- **messaging/** — Event bus, Redis adapters, messaging bridges.
- **monitoring/** — Logging (loguru), metrics (Prometheus), observability, progress.
- **mvvm/** — MVVM base, PySide6 helpers, advanced features, plugin templates.
- **processing/** — Background tasks, CLI, worker management, CPU tasks.
- **resource/** — Resource manager, unified registry, backend provider, resource types (file, database).
- **simulation/** — Simulation components.
- **web/** — HTTP server, web adapters.

---

## examples/

Runnable demo apps for all major features.

- **core_demo/** — Core app and plugin demo.
- **data_demo/** — Database and disk cache demo.
- **debug_utilities_demo/** — Debugging and logging demo.
- **desktop_demo/** — PySide6 desktop UI demos (tabbed window, etc.).
- **disk_cache_demo/** — Disk cache usage.
- **fs_demo/** — File system resource demo.
- **messaging_demo/** — Messaging/event bus demo.
- **monitoring_demo/** — Monitoring/logging demo.
- **mvvm_advanced_demo/** — Advanced MVVM (tree, PySide6, plugins).
- **processing_demo/** — Background processing demo.
- **resource_demo/** — Resource manager demo.
- **simulation_demo/** — Simulation demo.
- **undo_demo/** — Undo/redo system demo.
- **web_demo/** — Web server demo.

---

## tests/

Unit and integration tests for all domains.

- **core/** — Core system tests.
- **data/** — Database and disk cache tests.
- **desktop/** — Desktop UI and adapter tests.
- **fs/** — File system and vector DB tests.
- **integration/** — Cross-domain integration tests.
- **messaging/** — Messaging/event bus tests.
- **monitoring/** — Logging and metrics tests.
- **mvvm/** — MVVM and PySide6 tests.
- **processing/** — Task and worker tests.
- **resource/** — Resource manager and registry tests.
- **web/** — Web server tests.

---

## docs/

Documentation and guides.

- **index.md** — Documentation index.
- **app_architecture_plan.md** — Architecture and integration plan.
- **extension_api.md** — Extension points and developer API.
- **mvvm_usage_guide.md** — MVVM usage and patterns.
- **mvvm_advanced_features.md, mvvm_pyside6.md, mvvm_migration.md** — Advanced MVVM guides.
- **project-structure.md** — This file.
- **project-structure-guide.md** — (Legacy) Older structure guide.
- **core.md, data.md, desktop.md, messaging.md, monitoring.md, processing.md, resource.md, web.md** — Domain-specific docs.
- **datatable_templates.md** — Data table templates and usage.

---

## ai/

AI-related scripts, reports, and integration requests.

---

## plugins/

Custom plugin implementations.

---

## Other

- **resource_manager.log** — Log file for resource manager.
- **test_cache/** — Temporary test data.

---

## Key Files

- **ucore_framework/desktop/ui/tabbed_window.py** — MVVM tabbed document/tool window.
- **ucore_framework/desktop/plugins/api.py** — Plugin API and registry.
- **ucore_framework/fs/adapter.py** — File system adapter interface and registry.
- **ucore_framework/processing/background_tasks.py** — Background task runner.
- **ucore_framework/desktop/event_bus.py** — Event bus for UI/plugins.
- **ucore_framework/desktop/settings.py** — Settings manager.
- **docs/app_architecture_plan.md** — Architecture and integration plan.
- **docs/extension_api.md** — Extension/developer API.

---

## Classes by File

### ucore_framework/desktop/ui/tabbed_window.py

- **DocumentTabViewModel** — ViewModel for a document tab (MVVM).
- **ToolTabViewModel** — ViewModel for a tool tab (MVVM).
- **TabbedWindow** — Main window with tabbed document and tool areas.

### ucore_framework/desktop/plugins/api.py

- **PluginBase** — Abstract base class for all plugins (editors, viewers, tools).
- **PluginRegistry** — Registry for dynamic plugin loading/unloading.

### ucore_framework/fs/adapter.py

- **FileSystemAdapter** — Abstract base class for file system adapters (local, remote, cloud, archive).
- **FileSystemAdapterRegistry** — Registry for pluggable file system adapters.

### ucore_framework/desktop/plugins/editor_text.py

- **TextEditorViewModel** — ViewModel for text editor content.
- **TextEditorWidget** — PySide6 widget for text editing.
- **TextEditorPlugin** — Plugin for text editor integration.

### ucore_framework/desktop/plugins/viewer_image.py

- **ImageViewerViewModel** — ViewModel for image viewer.
- **ImageViewerWidget** — PySide6 widget for image display.
- **ImageViewerPlugin** — Plugin for image viewer integration.

### ucore_framework/processing/background_tasks.py

- **Task** — Abstract base class for background tasks.
- **TaskRunner** — Runs background tasks with progress and logging.

### ucore_framework/desktop/event_bus.py

- **EventBus** — Simple event bus for decoupled messaging.

### ucore_framework/desktop/settings.py

- **SettingsManager** — Manages user/workspace settings and layout persistence.

---

For more details, see the documentation index (`docs/index.md`) and domain-specific guides.
