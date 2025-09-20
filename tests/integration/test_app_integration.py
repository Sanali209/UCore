import pytest
from unittest.mock import AsyncMock, Mock, patch
from ucore_framework.core.app import App, Component

@pytest.mark.asyncio
@patch('ucore_framework.core.plugins.PluginManager.load_plugins')
@patch('ucore_framework.core.config.ConfigManager._load_from_files')
async def test_integrated_bootstrap_and_start(mock_config_load, mock_plugin_load):
    class MockComponent(Component):
        def __init__(self):
            super().__init__(name="mock")
        def start(self): pass

    mock_component = MockComponent()
    mock_component.start = AsyncMock()
    app = App("test_app")
    app.register_component(mock_component)
    import argparse
    args = argparse.Namespace(config=None, log_level="INFO", plugins_dir=None)
    app.bootstrap(args)
    await app.start()
    mock_config_load.assert_called()
    # plugins_dir is None, so load_plugins should not be called
    mock_plugin_load.assert_not_called()
    mock_component.start.assert_awaited_once()
