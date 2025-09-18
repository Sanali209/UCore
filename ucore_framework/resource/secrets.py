"""
SecretsManager interface and EnvVarSecretsManager implementation.

Provides secure access to secrets for resources and configuration.
"""

import os
from abc import ABC, abstractmethod
from typing import Optional, Dict
from loguru import logger

class SecretsManager(ABC):
    @abstractmethod
    def get_secret(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set_secret(self, key: str, value: str) -> None:
        pass

    @abstractmethod
    def rotate_secret(self, key: str, new_value: str) -> None:
        pass

    @abstractmethod
    def audit(self, key: str) -> Dict:
        pass

class EnvVarSecretsManager(SecretsManager):
    _audit_log = []

    def get_secret(self, key: str) -> Optional[str]:
        value = os.environ.get(key)
        event = {"event": "access", "key": key}
        self._audit_log.append(event)
        logger.info(f"Secret accessed: {key}")
        return value

    def set_secret(self, key: str, value: str) -> None:
        os.environ[key] = value
        event = {"event": "set", "key": key}
        self._audit_log.append(event)
        logger.info(f"Secret set: {key}")

    def rotate_secret(self, key: str, new_value: str) -> None:
        old_value = os.environ.get(key)
        os.environ[key] = new_value
        event = {"event": "rotate", "key": key}
        self._audit_log.append(event)
        logger.info(f"Secret rotated: {key}")

    def audit(self, key: str) -> Dict:
        events = [e for e in self._audit_log if e["key"] == key]
        logger.info(f"Secret audit requested: {key}")
        return {"key": key, "events": events}
