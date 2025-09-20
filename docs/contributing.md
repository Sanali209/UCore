# Contributing Guide

Thank you for your interest in contributing to UCore!  
This guide explains the process, coding standards, and best practices for contributing to the project.

---

## How to Contribute

1. **Fork the repository** and create your branch from `main`.
2. **Describe your changes** clearly in your pull request.
3. **Write tests** for new features and bug fixes.
4. **Follow the coding standards** and project conventions.
5. **Submit a pull request** and participate in code review.

---

## Coding Standards

- **OOP and Modularity:**  
  Use object-oriented design and keep code modular for extensibility.
- **Logging:**  
  Use `loguru` for all logging.
- **Progress Visualization:**  
  Use `tqdm` for progress bars in CLI/data tasks.
- **Docstrings:**  
  Document all modules, classes, and functions with clear docstrings.
- **Type Hints:**  
  Use Python type hints for function signatures and class attributes.
- **Testing:**  
  Use pytest for all tests. Write both unit and integration tests.

---

## Project Conventions

- **Directory Structure:**  
  Organize code by module (core, data, fs, monitoring, mvvm, web, desktop).
- **Configuration:**  
  Use YAML for config files and support environment variable overrides.
- **Plugins:**  
  Place new plugins in `ucore_framework/core/plugins.py` or `plugins/`.
- **Resource Management:**  
  Register new resources with the resource manager.

---

## Pull Request Checklist

- [ ] Code is modular and follows OOP principles
- [ ] All new code is tested
- [ ] Docstrings and type hints are present
- [ ] No linter or type errors
- [ ] Documentation is updated

---

## Getting Help

- Open an issue for questions, bugs, or feature requests.
- Join discussions in the repository for feedback and ideas.

---

See also:  
- [Testing](testing.md)  
- [Core Framework](core.md)
