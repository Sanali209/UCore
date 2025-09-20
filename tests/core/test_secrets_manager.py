import pytest
from unittest.mock import patch, MagicMock
from ucore_framework.core.resource.secrets import EnhancedSecretsManager

@pytest.fixture
def mock_keyring():
    secrets = {}
    mock = MagicMock()
    def set_password(service, username, value):
        secrets[(service, username)] = value
    def get_password(service, username):
        return secrets.get((service, username))
    mock.set_password.side_effect = set_password
    mock.get_password.side_effect = get_password
    return mock

@patch("ucore_framework.core.resource.secrets.keyring", new_callable=lambda: MagicMock())
def test_set_and_get_secret(mock_keyring_mod, mock_keyring):
    mock_keyring_mod.get_password = mock_keyring.get_password
    mock_keyring_mod.set_password = mock_keyring.set_password
    manager = EnhancedSecretsManager()
    manager.set_secret("my_api_key", "12345")
    retrieved = manager.get_secret("my_api_key")
    assert retrieved == "12345"

@patch("ucore_framework.core.resource.secrets.keyring", new_callable=lambda: MagicMock())
def test_encryption_is_applied(mock_keyring_mod, mock_keyring):
    mock_keyring_mod.get_password = mock_keyring.get_password
    mock_keyring_mod.set_password = mock_keyring.set_password
    manager = EnhancedSecretsManager()
    manager.set_secret("my_api_key", "12345")
    # Check that the stored value is not the plain secret
    args, kwargs = mock_keyring.set_password.call_args
    stored_value = args[2]
    assert stored_value != "12345"
