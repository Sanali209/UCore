from ucore_framework.mvvm.base import ViewModelBase, ObservableList
from ucore_framework.mvvm.data_provider import InMemoryProvider, AsyncMockProvider, DataProviderPluginBase
from ucore_framework.mvvm.grouping_filter import GroupingFilterMixin
from ucore_framework.mvvm.data_provisioning import DataProvisioningMixin
from ucore_framework.mvvm.transformation_pipeline import TransformationPipelineMixin
from ucore_framework.mvvm.datatable import DataTemplate
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QPushButton
import sys
import asyncio
from loguru import logger
from tqdm import tqdm

class AdvancedListViewModel(ViewModelBase, GroupingFilterMixin, DataProvisioningMixin, TransformationPipelineMixin):
    def __init__(self, data):
        ViewModelBase.__init__(self)
        GroupingFilterMixin.__init__(self)
        DataProvisioningMixin.__init__(self)
        TransformationPipelineMixin.__init__(self)
        self.provider = InMemoryProvider(data)
        self.async_provider = AsyncMockProvider()
        self.set_property("items", ObservableList(self.provider.get_data()))
        self.set_property("loading", False)

    async def load_async(self, data):
        self.set_property("loading", True)
        logger.info("Async loading started")
        items = []
        for _ in tqdm(range(1), desc="Loading async data"):
            items = await self.async_provider.get_data_async(data=data)
        self.set_property("items", ObservableList(items))
        self.set_property("loading", False)
        logger.info("Async loading finished")

    def get_transformed_items(self):
        data = self.get_property("items")
        filtered = self.filter_data(data)
        grouped = self.group_data(filtered)
        flat = []
        for group, items in grouped.items():
            flat.append(f"Group: {group}")
            flat.extend(self.transform(items))
        return flat

# Example plugin for DataProvider
class CustomProviderPlugin(DataProviderPluginBase):
    def create_provider(self, **kwargs):
        return InMemoryProvider(kwargs.get("data", []))

def main():
    app = QApplication(sys.argv)
    DataTemplate.register(str, lambda data, ctx: QLabel(data))
    DataTemplate.register(int, lambda data, ctx: QLabel(f"Number: {data}"))

    data = ["apple", "banana", "carrot", 1, 2, 3, "avocado"]
    vm = AdvancedListViewModel(data)
    vm.set_filter_func(lambda x: isinstance(x, str))
    vm.set_group_func(lambda x: x[0] if isinstance(x, str) else "other")
    vm.add_transformation(lambda items: [item.upper() if isinstance(item, str) else item for item in items])

    # Plugin registration and usage
    plugin = CustomProviderPlugin()
    plugin_provider = plugin.create_provider(data=["plugin", "data", "demo"])
    plugin_items = plugin_provider.get_data()

    window = QWidget()
    layout = QVBoxLayout(window)

    # Button to trigger async loading
    def on_load_async():
        asyncio.ensure_future(vm.load_async(["async", "loaded", "data", 123]))

    load_btn = QPushButton("Load Async Data")
    load_btn.clicked.connect(on_load_async)
    layout.addWidget(load_btn)

    # Display plugin provider data
    for item in plugin_items:
        logger.info(f"Plugin item: {item}")
        widget = DataTemplate.resolve(item)
        layout.addWidget(widget)

    # Display transformed items
    for item in vm.get_transformed_items():
        logger.info(f"Transformed item: {item}")
        widget = DataTemplate.resolve(item)
        layout.addWidget(widget)

    window.setLayout(layout)
    window.setWindowTitle("MVVM Advanced Demo (Async, Plugin, Event-driven)")
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
