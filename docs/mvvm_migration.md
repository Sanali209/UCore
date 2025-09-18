# ucore_framework MVVM Migration Guide

## Overview

This guide helps migrate existing ucore_framework apps to use the new MVVM and PySide6 abstractions for modular, extensible, and testable UI code.

## Migration Steps

1. **Refactor Models**
   - Subclass `ModelBase` for your data models.
   - Move validation and business logic into models.

2. **Create ViewModels**
   - Subclass `ViewModelBase` for each UI component.
   - Move state, property management, and commands to ViewModel.
   - Use `set_property`/`get_property` for all bindable properties.
   - Implement commands by subclassing `Command`.

3. **Update Views**
   - Subclass `PySide6ViewBase` for each widget/view.
   - Move UI logic and widget setup to the view class.
   - Use `bind_property`, `bind_bidirectional`, and `bind_command` for all bindings.
   - Use `ObservableListModel` for list/table widgets.

4. **Integrate Event Bus (Optional)**
   - Use event bus for decoupled communication between ViewModels and other app parts.

5. **Update Plugins**
   - Register MVVM-based widgets using the plugin template.
   - Expose `get_widget()` and `get_name()` for integration.

6. **Testing**
   - Use the provided tests as a template for your ViewModels and commands.

## Example Refactor

**Before:**
```python
class MyWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.counter = 0
        # UI setup...
    def on_click(self):
        self.counter += 1
        self.label.setText(str(self.counter))
```

**After:**
```python
from ucore_framework.mvvm.base import ViewModelBase, Command
from ucore_framework.mvvm.pyside6 import PySide6ViewBase, bind_property, bind_command

class MyViewModel(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.set_property("counter", 0)
        self.increment_command = IncrementCommand(self)
class IncrementCommand(Command):
    def __init__(self, vm): self.vm = vm
    def execute(self, *a, **k): self.vm.set_property("counter", self.vm.get_property("counter")+1)
class MyView(PySide6ViewBase):
    def __init__(self):
        super().__init__()
        # UI setup...
    def on_viewmodel_bound(self, vm):
        bind_property(self.label, "text", vm, "counter")
        bind_command(self.button, "clicked", vm.increment_command)
```

## Tips

- Keep ViewModel logic UI-agnostic and testable.
- Use OOP and modular design for all MVVM components.
- Use loguru for logging and debugging.
