# UCore Framework Guide

## Unified Resource Registration

UCore supports unified resource registration via the UnifiedResourceRegistry and UCoreResourceRegistry adapter.

### Example Usage

```python
from ucore_framework.resource.manager import ResourceManager, Resource
from ucore_framework.resource.ucore_registry import UCoreResourceRegistry
from ucore_framework.resource.unified_registry import UnifiedResourceRegistry

resource_manager = ResourceManager()
ucore_registry = UCoreResourceRegistry(resource_manager)
unified_registry = UnifiedResourceRegistry(ucore_registry, ucore_registry)

my_resource = Resource(name="example", resource_type="custom")
unified_registry.register(my_resource)
resources = unified_registry.find(name="example")
```

## BackendProvider Integration

BackendProvider supports policy-driven backend selection and can discover backends via UnifiedResourceRegistry.

### Example Usage

```python
from ucore_framework.resource.backend_provider import BackendProvider, ServiceBackend, RoundRobinPolicy
from ucore_framework.resource.unified_registry import UnifiedResourceRegistry

provider = BackendProvider(selection_policy=RoundRobinPolicy(), registry=unified_registry)
backend = ServiceBackend(name="db1", tags=["db"])
provider.register_backend(backend)
selected = provider.get_backend()
```

## Secrets Management

SecretsManager provides secure access to secrets for configuration and resources.

### Example Usage

```python
from ucore_framework.resource.secrets import EnvVarSecretsManager

secrets = EnvVarSecretsManager()
secrets.set_secret("MY_SECRET", "value")
assert secrets.get_secret("MY_SECRET") == "value"
secrets.rotate_secret("MY_SECRET", "newvalue")
audit = secrets.audit("MY_SECRET")
print(audit)
```

- Config loading uses SecretsManager for secret-like keys in environment variables.
- Audit logging is available for secret access and rotation.

## Progress and Logging

- All resource/module lifecycle operations use loguru for logging.
- ProgressManager supports tqdm/loguru visualizers and emits progress events to the event bus.

## Undo System Component

UCore provides an `UndoSystem` component for undo/redo functionality, suitable for editors, UI, and stateful operations.

### Usage Example

```python
from ucore_framework.core.undo import UndoSystem

undo_system = UndoSystem()
undo_system.add_undo_item(lambda: print("undo!"), lambda: print("redo!"), description="Sample action")
undo_system.undo()
undo_system.redo()
```

- Integrates with the component system for DI and event support.
- Uses loguru for logging all actions.
- Undo/redo stacks are accessible as properties.

## TimeMeasure Component

UCore provides a `TimeMeasure` component for profiling and timing code execution with lap/step support, logging, and plotting.

### Usage Example

```python
from ucore_framework.core.timemeasure import TimeMeasure

tm = TimeMeasure()
tm.start_timer("mytask", step=2)
# ... code ...
tm.lap("mytask")
# ... code ...
tm.lap("mytask")
tm.plot("mytask")
tm.export_laps("mytask", "laps.csv")
```

- Integrates with the component system for DI and event support.
- Uses loguru for logging all actions.
- Supports lap/step, plotting (matplotlib), and CSV export.
