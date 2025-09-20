"""
Secrets management utilities for UCore Framework.

This module provides:
- Abstract interface for secrets managers
- Environment variable-based secrets manager
- Enhanced secrets manager using OS keyring and encryption

Classes:
    SecretsManager: Abstract base class for secrets managers.
    EnvVarSecretsManager: Uses environment variables for secrets.
    EnhancedSecretsManager: Uses OS keyring and encryption.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict
from loguru import logger

class SecretsManager(ABC):
    """
    Abstract base class for secrets managers in UCore.

    Defines the interface for secure storage, retrieval, rotation,
    and auditing of secrets.
    """
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret value by key."""
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> None:
        """Set a secret value by key."""
        pass

    @abstractmethod
    def rotate_secret(self, key: str, new_value: str) -> None:
        """Rotate (replace) a secret value by key."""
        pass

    @abstractmethod
    def audit(self, key: str) -> Dict:
        """Return an audit log for a given secret key."""
        pass

class EnvVarSecretsManager(SecretsManager):
    """
    Secrets manager that uses environment variables for storage.

    Provides basic get/set/rotate/audit functionality for secrets,
    storing audit logs in memory.
    """
    _audit_log = []

    def get_secret(self, key: str) -> Optional[str]:
        """Retrieve a secret from environment variables."""
        value = os.environ.get(key)
        event = {"event": "access", "key": key}
        self._audit_log.append(event)
        logger.info(f"Secret accessed: {key}")
        return value

    def set_secret(self, key: str, value: str) -> None:
        """Set a secret in environment variables."""
        os.environ[key] = value
        event = {"event": "set", "key": key}
        self._audit_log.append(event)
        logger.info(f"Secret set: {key}")

    def rotate_secret(self, key: str, new_value: str) -> None:
        """Rotate (replace) a secret in environment variables."""
        old_value = os.environ.get(key)
        os.environ[key] = new_value
        event = {"event": "rotate", "key": key}
        self._audit_log.append(event)
        logger.info(f"Secret rotated: {key}")

    def audit(self, key: str) -> Dict:
        """Return an audit log for a given secret key."""
        events = [e for e in self._audit_log if e["key"] == key]
        logger.info(f"Secret audit requested: {key}")
        return {"key": key, "events": events}

# --- EnhancedSecretsManager: Encrypted secrets in OS keyring ---

import keyring
from cryptography.fernet import Fernet
from typing import Optional

class EnhancedSecretsManager:
    """
    Enhanced secrets manager using OS keyring and symmetric encryption.

    Stores secrets securely in the OS keyring, encrypting values with a
    master key. For single-machine use only; not suitable for distributed
    production deployments.

    Methods:
        get_secret(key): Retrieve and decrypt a secret.
        set_secret(key, value): Encrypt and store a secret.
    """
    _SERVICE_NAME = "ucore_framework"
    _MASTER_KEY_NAME = "ucore_master_key"

    def __init__(self):
        self.cipher = Fernet(self._get_or_create_master_key())

    def _get_or_create_master_key(self) -> bytes:
        """
        Retrieves the master encryption key from the keyring or creates a new one.

        WARNING: In a real distributed system, this key must be managed securely
        (e.g., via HashiCorp Vault, AWS KMS) and not stored this way.
        This implementation is for a single-machine context.
        """
        master_key = keyring.get_password(self._SERVICE_NAME, self._MASTER_KEY_NAME)
        if master_key:
            return master_key.encode()

        # Generate a new key if one doesn't exist
        new_key = Fernet.generate_key()
        keyring.set_password(self._SERVICE_NAME, self._MASTER_KEY_NAME, new_key.decode())
        return new_key

    def get_secret(self, key: str) -> Optional[str]:
        """
        Retrieves and decrypts a secret from the secure keyring.

        Args:
            key: Secret key name.

        Returns:
            Decrypted secret value, or None if not found or decryption fails.
        """
        encrypted_value = keyring.get_password(self._SERVICE_NAME, key)
        if encrypted_value:
            try:
                decrypted_bytes = self.cipher.decrypt(encrypted_value.encode())
                return decrypted_bytes.decode()
            except Exception:
                # Handle cases where decryption fails (e.g., master key changed)
                return None
        return None

    def set_secret(self, key: str, value: str) -> None:
        """
        Encrypts and stores a secret in the secure keyring.

        Args:
            key: Secret key name.
            value: Secret value to encrypt and store.
        """
        encrypted_value = self.cipher.encrypt(value.encode()).decode()
        keyring.set_password(self._SERVICE_NAME, key, encrypted_value)
