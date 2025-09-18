import os
import pytest
from UCoreFrameworck.resource.secrets import EnvVarSecretsManager

def test_env_var_secrets_manager_set_get_rotate_audit(monkeypatch):
    manager = EnvVarSecretsManager()
    key = "TEST_SECRET_KEY"
    value = "supersecret"
    new_value = "newsupersecret"

    # Set secret
    manager.set_secret(key, value)
    assert os.environ[key] == value

    # Get secret
    assert manager.get_secret(key) == value

    # Rotate secret
    manager.rotate_secret(key, new_value)
    assert os.environ[key] == new_value

    # Audit log should contain all events
    audit = manager.audit(key)
    event_types = [e["event"] for e in audit["events"]]
    assert "set" in event_types
    assert "access" in event_types
    assert "rotate" in event_types

    # Clean up
    del os.environ[key]
