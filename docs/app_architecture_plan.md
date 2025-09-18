# UCore App Architecture Plan (VSCode/Directory Opus Style)

## Integration & Refactoring Steps

1. **Plugin/Extension System**
   - Use `framework/core/plugins.py` and `desktop/plugins/api.py` for plugin/component registration.
   - Refactor all plugin loading/unloading to use `PluginRegistry`.
   - Document plugin discovery and hot-reload as future extension.

2. **File System Abstraction**
   - Use `resource/types/file.py` and `fs/adapter.py` for file system adapters.
   - Register all adapters in `FileSystemAdapterRegistry`.
   - Implement cloud/remote adapters as plugins if needed.

3. **Editor/Viewer Components**
   - Use MVVM base and PySide6 widgets for all editors/viewers.
   - Register new editors/viewers as plugins.
   - Add syntax highlighting and advanced previewers as plugins.

4. **Task/Process Management**
   - Use `processing/background.py`, `processing/tasks.py`, and `TaskRunner` for background tasks.
   - Integrate UI for task status/cancellation using MVVM.

5. **Event Bus & Messaging**
   - Use `resource/manager.py` and `desktop/event_bus.py` for event bus.
   - Ensure all UI, plugins, and core logic communicate via event bus.

6. **Settings & State Management**
   - Use `desktop/settings.py` and `core/settings.py` for settings.
   - Add MVVM dialogs for settings and workspace/session restore.

7. **Monitoring & Debugging**
   - Use `framework/monitoring/logging.py`, loguru, tqdm.
   - Add log viewer and error reporting UI as plugins.

8. **Documentation**
   - Update `docs/extension_api.md` and `docs/mvvm_usage_guide.md` with integration patterns and extension points.
   - Add architecture diagrams and plugin guides.

---

## Next Steps

- [ ] Refactor all new modules to use/extend UCore's plugin/component, event bus, resource, and background task systems.
- [ ] Register all plugins and adapters at startup.
- [ ] Remove duplicated logic and document integration points.
- [ ] Add missing extension points only where UCore does not provide functionality.
- [ ] Update documentation to reflect integration and extension patterns.
