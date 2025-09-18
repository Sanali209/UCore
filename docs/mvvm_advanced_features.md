# ucore_framework MVVM Advanced Features

## Plugin-Based Data Providers

Register and use custom data providers at runtime:

```python
from ucore_framework.mvvm.data_provider import DataProviderPluginBase, InMemoryProvider

class CustomProviderPlugin(DataProviderPluginBase):
    def create_provider(self, **kwargs):
        return InMemoryProvider(kwargs.get("data", []))

plugin = CustomProviderPlugin()
provider = plugin.create_provider(data=["plugin", "data"])
items = provider.get_data()
```

## Async Data Loading

Support async data loading in ViewModel:

```python
from ucore_framework.mvvm.data_provider import AsyncMockProvider
import asyncio

class MyVM(ViewModelBase):
    def __init__(self):
        super().__init__()
        self.async_provider = AsyncMockProvider()
    async def load_async(self, data):
        items = await self.async_provider.get_data_async(data=data)
        self.set_property("items", ObservableList(items))

# Usage: asyncio.ensure_future(vm.load_async([...]))
```

## Grouping and Filtering

Dynamically group and filter data in ViewModel:

```python
from ucore_framework.mvvm.grouping_filter import GroupingFilterMixin

class MyVM(GroupingFilterMixin):
    def __init__(self, data):
        GroupingFilterMixin.__init__(self)
        self.data = data

vm = MyVM(["apple", "banana", "carrot"])
vm.set_group_func(lambda x: x[0])
vm.set_filter_func(lambda x: "a" in x)
grouped = vm.group_data(vm.data)
filtered = vm.filter_data(vm.data)
```

## Data Provisioning and Batching

Provide all or only visible data, and batch for large sets:

```python
from ucore_framework.mvvm.data_provisioning import DataProvisioningMixin

class MyVM(DataProvisioningMixin):
    def __init__(self, data):
        DataProvisioningMixin.__init__(self)
        self.data = data

vm = MyVM(list(range(10)))
vm.set_provision_mode("visible")
visible = vm.provide_data(vm.data, visible_indices=[1, 3, 5])
vm.set_batch_size(4)
batches = vm.provide_data_in_batches(vm.data)
```

## Transformation Pipelines

Chain, cache, and monitor data transformations:

```python
from ucore_framework.mvvm.transformation_pipeline import TransformationPipelineMixin

class MyVM(TransformationPipelineMixin):
    def __init__(self, data):
        TransformationPipelineMixin.__init__(self)
        self.data = data

vm = MyVM([1, 2, 3])
vm.add_transformation(lambda items: [x * 2 for x in items])
vm.add_transformation(lambda items: [x + 1 for x in items])
result = vm.transform(vm.data)
```

## Dependency Injection for MVVM Features

You can inject advanced MVVM features (grouping, filtering, transformation, provisioning) using the DI container.

### Using the Factory

```python
from ucore_framework.core.di import container
from ucore_framework.mvvm.base import AdvancedViewModelFactory

factory = AdvancedViewModelFactory(container)

class MyVM(ViewModelBase):
    def __init__(self, data_provisioning=None, transformation=None, grouping=None):
        # Use injected mixins/services as needed
        ...

vm = factory.create(MyVM)
```

### Using the Decorator

```python
from ucore_framework.mvvm.base import inject_mvvm_features

@inject_mvvm_features
class MyVM(ViewModelBase):
    def __init__(self, data_provisioning=None, transformation=None, grouping=None):
        # Use injected mixins/services as needed
        ...
```

## Monitoring and Logging

Integrate loguru for logging and tqdm for progress:

```python
from loguru import logger
from tqdm import tqdm

logger.info("Start loading")
for _ in tqdm(range(10), desc="Loading"):
    ...
logger.info("Done")
```

## Example Apps

- See `examples/mvvm_advanced_demo/main.py` for async, plugin, and event-driven demo.
- See `examples/mvvm_advanced_demo/tree_demo.py` for hierarchical TreeView demo.
