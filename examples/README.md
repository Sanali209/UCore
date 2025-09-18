# UCore Framework Example Apps

This directory contains sample applications demonstrating the main features of the UCore framework. Each subdirectory contains a minimal, real-world example for a specific feature area:

- **core**: Application/component system, dependency injection, configuration, plugins
- **data**: Database access, disk cache, MongoDB integration
- **desktop**: UI adapters (PySide6, Flet)
- **fs**: File system abstraction, annotation, indexing, vector DB
- **messaging**: Event bus, events, Redis integration
- **monitoring**: Logging, metrics, observability, progress tracking
- **processing**: Background tasks, CLI, CPU tasks, chains
- **resource**: Resource management, backend providers, secrets, unified registry
- **simulation**: Simulation systems, entities, actions, sensors
- **web**: HTTP server

Each sample app is located in a subdirectory named after the feature, e.g. `examples/core_demo/`, `examples/data_demo/`, etc.

## How to run

Each sample app contains a `main.py` file. Run with:

```bash
python main.py
