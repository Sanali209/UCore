# tests/test_config.py
import unittest
import tempfile
import os
import yaml
from unittest.mock import patch

import sys
sys.path.insert(0, 'd:/UCore')

from framework.config import Config

class TestConfig(unittest.TestCase):

    def setUp(self):
        """Set up a new Config instance for each test."""
        self.config = Config(env_prefix="UCORE")

    def test_initialization(self):
        """Test that Config initializes with empty data."""
        self.assertEqual(self.config.data, {})

    def test_set_and_get_values(self):
        """Test setting and getting configuration values with dot notation."""
        self.config.set("app.name", "MyApp")
        self.config.set("app.debug", True)
        self.config.set("database.port", 5432)

        self.assertEqual(self.config.get("app.name"), "MyApp")
        self.assertTrue(self.config.get("app.debug"))
        self.assertEqual(self.config.get("database.port"), 5432)

    def test_get_with_default(self):
        """Test getting a value with a default."""
        self.assertIsNone(self.config.get("nonexistent.key"))
        self.assertEqual(self.config.get("nonexistent.key", "default"), "default")

    def test_load_from_valid_yaml(self):
        """Test loading configuration from a valid YAML file."""
        yaml_content = """
        app:
          name: "TestApp"
          version: "1.0"
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            filepath = f.name

        try:
            self.config.load_from_file(filepath)
            self.assertEqual(self.config.get("app.name"), "TestApp")
            self.assertEqual(self.config.get("app.version"), "1.0")
        finally:
            os.unlink(filepath)

    def test_load_from_nonexistent_file(self):
        """Test that loading from a nonexistent file does not raise an error."""
        self.config.load_from_file("/path/to/nonexistent/file.yaml")
        self.assertEqual(self.config.data, {})

    def test_load_from_invalid_yaml(self):
        """Test that loading from an invalid YAML file raises a RuntimeError."""
        invalid_yaml = "app: { name: Test"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            filepath = f.name

        try:
            with self.assertRaises(RuntimeError):
                self.config.load_from_file(filepath)
        finally:
            os.unlink(filepath)

    @patch.dict(os.environ, {
        "UCORE_APP_NAME": "EnvApp",
        "UCORE_DEBUG": "true",
        "UCORE_DATABASE_PORT": "5432",
        "UCORE_TIMEOUT": "12.5"
    })
    def test_load_from_env(self):
        """Test loading configuration from environment variables."""
        self.config.load_from_env()
        self.assertEqual(self.config.get("app.name"), "EnvApp")
        self.assertTrue(self.config.get("debug"))
        self.assertEqual(self.config.get("database.port"), 5432)
        self.assertEqual(self.config.get("timeout"), 12.5)

    @patch.dict(os.environ, {"UCORE_APP_NAME": "EnvOverride"})
    def test_env_overrides_yaml(self):
        """Test that environment variables override values from YAML files."""
        yaml_content = "app:\n  name: \"YamlApp\""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            filepath = f.name

        try:
            self.config.load_from_file(filepath)
            self.assertEqual(self.config.get("app.name"), "YamlApp")
            
            self.config.load_from_env()
            self.assertEqual(self.config.get("app.name"), "EnvOverride")
        finally:
            os.unlink(filepath)

    def test_save_to_file(self):
        """Test saving the configuration to a file."""
        self.config.set("app.name", "SavedApp")
        self.config.set("database.host", "localhost")

        with tempfile.NamedTemporaryFile(mode='w+', suffix='.yaml', delete=False) as f:
            filepath = f.name

        try:
            self.config.save_to_file(filepath)
            
            new_config = Config()
            new_config.load_from_file(filepath)
            
            self.assertEqual(new_config.get("app.name"), "SavedApp")
            self.assertEqual(new_config.get("database.host"), "localhost")
        finally:
            os.unlink(filepath)

if __name__ == '__main__':
    unittest.main()
