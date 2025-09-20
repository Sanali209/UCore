import pytest
import os
import yaml
from unittest.mock import patch, MagicMock
from ucore_framework.core.config import ConfigManager

@pytest.fixture
def tmp_config_file(tmp_path):
    def _create_config(data):
        config_path = tmp_path / "config.yml"
        with open(config_path, "w") as f:
            yaml.dump(data, f)
        return str(config_path)
    return _create_config

def test_load_from_yaml(tmp_config_file):
    config_path = tmp_config_file({"app_name": "TestApp"})
    config = ConfigManager(config_path)
    app_name = config.get("app_name")
    assert app_name == "TestApp"

@patch.dict(os.environ, {"UCORE_MAX_RESULTS": "50"})
def test_env_var_override(tmp_config_file):
    config_path = tmp_config_file({"max_results": 100})
    config = ConfigManager(config_path)
    max_results = config.get("max_results")
    assert max_results == 50

@patch('ucore_framework.core.config.EnhancedSecretsManager')
def test_secrets_manager_integration(mock_secrets_manager, tmp_config_file):
    mock_instance = mock_secrets_manager.return_value
    mock_instance.get_secret.return_value = "postgresql://user:pass@localhost:5432/db"
    config_path = tmp_config_file({"database_url_alias": "db_prod_url"})
    config = ConfigManager(config_path)
    db_url = config.get("database_url")
    mock_instance.get_secret.assert_called_once_with("db_prod_url")
    assert db_url == "postgresql://user:pass@localhost:5432/db"

def test_default_value_fallback():
    config = ConfigManager()
    log_level = config.get("log_level")
    assert log_level == "INFO"
