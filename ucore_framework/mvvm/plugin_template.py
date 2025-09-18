from ucore_framework.core.plugins import PluginBase
from ucore_framework.mvvm.examples.simple_counter import CounterView, CounterViewModel

class MVVMWidgetPlugin(PluginBase):
    """Example plugin that registers an MVVM widget."""
    def __init__(self):
        super().__init__()
        self._viewmodel = CounterViewModel()
        self._view = CounterView()
        self._view.bind_viewmodel(self._viewmodel)

    def get_widget(self):
        """Return the main widget for integration into the host app."""
        return self._view

    def get_name(self):
        return "Counter MVVM Widget"
