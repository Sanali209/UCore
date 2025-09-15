import pytest
import os
import tempfile
import yaml
from unittest.mock import patch, mock_open
from framework.core.config import Config


class TestConfigInitialization:
    """Test Config class initialization and basic setup."""

    def test_config_create_with_defaults(self):
        """Test Config creation with default parameters."""
        config = Config()

        assert config.data == {}
        assert config.env_prefix == "UCORE"
        assert config.env_separator == "_"
        assert isinstance(config, Config)

    def test_config_create_with_custom_params(self):
        """Test Config creation with custom parameters."""
        config = Config(env_prefix="MYAPP", env_separator="-")

        assert config.env_prefix == "MYAPP"
        assert config.env_separator == "-"
        assert config.data == {}


class TestYamlFileLoading:
    """Test YAML file loading functionality."""

    def test_load_from_file_success(self):
        """Test successful loading from YAML file."""
        config = Config()

        # Create test YAML content
        yaml_content = """
database:
  host: localhost
  port: 27017
logging:
  level: INFO
  file: app.log
"""

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            config.load_from_file("test.yml")

        assert config.data["database"]["host"] == "localhost"
        assert config.data["database"]["port"] == 27017
        assert config.data["logging"]["level"] == "INFO"
        assert config.data["logging"]["file"] == "app.log"

    def test_load_from_file_not_found(self):
        """Test loading from non-existent file (should not raise error)."""
        config = Config()

        with patch("builtins.open", side_effect=FileNotFoundError):
            config.load_from_file("nonexistent.yml")

        # Should not have loaded any data
        assert config.data == {}

    def test_load_from_file_yaml_error(self):
        """Test handling of YAML parsing errors."""
        config = Config()

        # Mock yaml.safe_load to raise an error
        with patch("builtins.open", mock_open(read_data="invalid: yaml: content: [")):
            with patch("yaml.safe_load", side_effect=yaml.YAMLError("Parse error")):
                with pytest.raises(RuntimeError) as exc_info:
                    config.load_from_file("invalid.yml")

                assert "Error parsing YAML file" in str(exc_info.value)

    def test_load_from_file_general_error(self):
        """Test handling of general file reading errors."""
        config = Config()

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(RuntimeError) as exc_info:
                config.load_from_file("test.yml")

            assert "Error loading configuration" in str(exc_info.value)

    def test_load_from_file_empty(self):
        """Test loading from empty YAML file."""
        config = Config()

        with patch("builtins.open", mock_open(read_data="")):
            config.load_from_file("empty.yml")

        # Should not have loaded any data
        assert config.data == {}

    def test_load_from_file_none_content(self):
        """Test loading from YAML file with None content."""
        config = Config()

        with patch("builtins.open", mock_open(read_data=None)):
            with patch("yaml.safe_load", return_value=None):
                config.load_from_file("none.yml")

        # Should not have loaded any data
        assert config.data == {}


class TestEnvironmentVariableLoading:
    """Test environment variable loading functionality."""

    def test_load_from_env_simple_variables(self):
        """Test loading simple environment variables."""
        config = Config()

        env_vars = {
            "UCORE_DATABASE_HOST": "localhost",
            "UCORE_DATABASE_PORT": "27017",
            "UCORE_LOGGING_LEVEL": "INFO"
        }

        with patch.dict(os.environ, env_vars):
            config.load_from_env()

        assert config.data["database"]["host"] == "localhost"
        assert config.data["database"]["port"] == 27017
        assert config.data["logging"]["level"] == "INFO"

    def test_load_from_env_type_casting(self):
        """Test automatic type casting of environment variables."""
        config = Config()

        env_vars = {
            "UCORE_APP_DEBUG": "true",
            "UCORE_APP_PORT": "8080",
            "UCORE_DATABASE_TIMEOUT": "30.5",
            "UCORE_LOGGING_FILE": "app.log"
        }

        with patch.dict(os.environ, env_vars):
            config.load_from_env()

        assert config.data["app"]["debug"] is True  # bool
        assert config.data["app"]["port"] == 8080   # int
        assert config.data["database"]["timeout"] == 30.5  # float
        assert config.data["logging"]["file"] == "app.log"  # str

    def test_load_from_env_false_values(self):
        """Test boolean false values casting."""
        config = Config()

        env_vars = {
            "UCORE_APP_DEBUG": "false",
            "UCORE_APP_ENABLED": "False"
        }

        with patch.dict(os.environ, env_vars):
            config.load_from_env()

        assert config.data["app"]["debug"] is False
        assert config.data["app"]["enabled"] is False

    def test_load_from_env_custom_prefix(self):
        """Test environment loading with custom prefix."""
        config = Config(env_prefix="MYAPP")

        env_vars = {
            "MYAPP_SERVER_HOST": "api.example.com",
            "MYAPP_DATABASE_NAME": "myapp"
        }

        with patch.dict(os.environ, env_vars):
            config.load_from_env()

        assert config.data["server"]["host"] == "api.example.com"
        assert config.data["database"]["name"] == "myapp"

    def test_load_from_env_custom_separator(self):
        """Test environment loading with custom separator."""
        config = Config(env_separator="-")

        env_vars = {
            "UCORE-DATABASE-HOST": "db.example.com",
            "UCORE-APP-NAME": "MyApp"
        }

        with patch.dict(os.environ, env_vars):
            config.load_from_env()

        assert config.data["database"]["host"] == "db.example.com"
        assert config.data["app"]["name"] == "MyApp"

    def test_load_from_env_filters_prefix(self):
        """Test that only prefixed environment variables are loaded."""
        config = Config()

        env_vars = {
            "UCORE_DATABASE_HOST": "localhost",
            "OTHER_DATABASE_HOST": "remote",  # Should be ignored
            "UCORE_LOGGING_LEVEL": "INFO",
            "UNRELATED_VAR": "value"  # Should be ignored
        }

        with patch.dict(os.environ, env_vars):
            config.load_from_env()

        assert config.data["database"]["host"] == "localhost"
        assert config.data["logging"]["level"] == "INFO"
        assert "other" not in config.data
        assert "unrelated_var" not in config.data

    def test_load_from_env_empty(self):
        """Test loading when no environment variables are set."""
        config = Config()

        with patch.dict(os.environ, {}, clear=True):
            config.load_from_env()

        assert config.data == {}


class TestValueAccessAndModification:
    """Test configuration value access and modification."""

    def test_get_simple_value(self):
        """Test getting simple configuration value."""
        config = Config()
        config.data = {"database": {"host": "localhost"}}

        assert config.get("database.host") == "localhost"

    def test_get_nested_value(self):
        """Test getting nested configuration value."""
        config = Config()
        config.data = {
            "database": {
                "connection": {
                    "host": "localhost",
                    "port": 27017
                }
            }
        }

        assert config.get("database.connection.host") == "localhost"
        assert config.get("database.connection.port") == 27017

    def test_get_with_default(self):
        """Test getting value with default when key doesn't exist."""
        config = Config()
        config.data = {"database": {"host": "localhost"}}

        assert config.get("database.port", 5432) == 5432
        assert config.get("missing.key", "default_value") == "default_value"

    def test_get_nonexistent_key(self):
        """Test getting nonexistent key without default."""
        config = Config()
        config.data = {"database": {"host": "localhost"}}

        assert config.get("database.port") is None

    def test_get_type_error_handling(self):
        """Test handling of TypeError in key access."""
        config = Config()
        config.data = {"database": "not_a_dict"}

        # Should return default when dot notation fails on non-dict value
        assert config.get("database.host", "default") == "default"

    def test_set_simple_value(self):
        """Test setting simple configuration value."""
        config = Config()

        config.set("database.host", "localhost")

        assert config.data["database"]["host"] == "localhost"

    def test_set_nested_value(self):
        """Test setting nested configuration value."""
        config = Config()

        config.set("database.connection.host", "db.example.com")
        config.set("database.connection.port", 5432)

        expected = {
            "database": {
                "connection": {
                    "host": "db.example.com",
                    "port": 5432
                }
            }
        }
        assert config.data == expected

    def test_set_overwrite_value(self):
        """Test overwriting existing configuration value."""
        config = Config()
        config.data = {"database": {"host": "old_host"}}

        config.set("database.host", "new_host")

        assert config.data["database"]["host"] == "new_host"

    def test_set_create_nested_structure(self):
        """Test creating nested structure with set."""
        config = Config()

        config.set("app.logging.file.path", "/var/log/app.log")

        expected = {
            "app": {
                "logging": {
                    "file": {
                        "path": "/var/log/app.log"
                    }
                }
            }
        }
        assert config.data == expected

    def test_set_empty_key(self):
        """Test setting value with empty path."""
        config = Config()

        config.set("", "value")

        # Should treat empty string as top-level replacement
        assert config.data == "value"


class TestFileSaving:
    """Test configuration saving to file."""

    def test_save_to_file_success(self):
        """Test successful saving configuration to YAML file."""
        config = Config()
        config.data = {
            "database": {
                "host": "localhost",
                "port": 27017
            },
            "logging": {
                "level": "INFO"
            }
        }

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("yaml.dump") as mock_yaml_dump:
                config.save_to_file("config.yml")

                mock_file.assert_called_once_with("config.yml", "w")
                mock_yaml_dump.assert_called_once()

    def test_save_to_file_io_error(self):
        """Test error handling when saving file fails."""
        config = Config()
        config.data = {"test": "value"}

        with patch("builtins.open", side_effect=OSError("Permission denied")):
            with pytest.raises(RuntimeError) as exc_info:
                config.save_to_file("config.yml")

            assert "Error saving configuration" in str(exc_info.value)

    def test_save_to_file_yaml_error(self):
        """Test error handling when YAML serialization fails."""
        config = Config()
        config.data = {"test": object()}  # Object that might cause YAML issues

        with patch("builtins.open", mock_open()):
            with patch("yaml.dump", side_effect=yaml.YAMLError("Serialization error")):
                with pytest.raises(RuntimeError) as exc_info:
                    config.save_to_file("config.yml")

                assert "Error saving configuration" in str(exc_info.value)


class TestTypeCasting:
    """Test automatic type casting functionality."""

    def test_cast_boolean_true(self):
        """Test casting boolean true values."""
        assert Config._cast_value("true") is True
        assert Config._cast_value("True") is True
        assert Config._cast_value("TRUE") is True

    def test_cast_boolean_false(self):
        """Test casting boolean false values."""
        assert Config._cast_value("false") is False
        assert Config._cast_value("False") is False
        assert Config._cast_value("FALSE") is False

    def test_cast_integer(self):
        """Test casting integer values."""
        assert Config._cast_value("42") == 42
        assert Config._cast_value("0") == 0
        assert Config._cast_value("-10") == -10

    def test_cast_float(self):
        """Test casting float values."""
        assert Config._cast_value("3.14") == 3.14
        assert Config._cast_value("0.5") == 0.5
        assert Config._cast_value("-2.5") == -2.5

    def test_cast_string(self):
        """Test keeping string values as strings."""
        assert Config._cast_value("some_string") == "some_string"
        assert Config._cast_value("123abc") == "123abc"
        assert Config._cast_value("true_string") == "true_string"

    def test_cast_empty_string(self):
        """Test casting empty string."""
        assert Config._cast_value("") == ""

    def test_cast_none_value(self):
        """Test casting None-like values."""
        assert Config._cast_value("none") == "none"  # Should remain string
        assert Config._cast_value("null") == "null"  # Should remain string

    def test_cast_invalid_integer(self):
        """Test casting strings that look like numbers but aren't."""
        # These should remain as strings since they contain non-numeric chars
        assert Config._cast_value("123abc") == "123abc"
        assert Config._cast_value("12.34.56") == "12.34.56"


class TestIntegration:
    """Test integration of multiple config features."""

    def test_file_and_env_integration(self):
        """Test loading from both file and environment variables."""
        config = Config()

        # Setup file config
        yaml_content = """
database:
  host: file_host
  name: file_database
"""

        env_vars = {
            "UCORE_DATABASE_HOST": "env_host",  # Should override file
            "UCORE_DATABASE_PORT": "3306",      # Additional from env
            "UCORE_LOGGING_LEVEL": "DEBUG"
        }

        with patch("builtins.open", mock_open(read_data=yaml_content)):
            with patch.dict(os.environ, env_vars):
                config.load_from_file("config.yml")
                config.load_from_env()

        # File values
        assert config.data["database"]["name"] == "file_database"
        # Environment overrides
        assert config.data["database"]["host"] == "env_host"
        assert config.data["database"]["port"] == 3306
        assert config.data["logging"]["level"] == "DEBUG"

    def test_multiple_file_loads(self):
        """Test loading multiple configuration files."""
        config = Config()

        file1_content = """
app:
  name: MyApp
database:
  host: localhost
"""

        file2_content = """
database:
  port: 27017
logging:
  level: INFO
"""

        with patch("builtins.open", mock_open(read_data=file1_content)):
            config.load_from_file("file1.yml")

        with patch("builtins.open", mock_open(read_data=file2_content)):
            config.load_from_file("file2.yml")

        # Should have merged both files
        assert config.data["app"]["name"] == "MyApp"
        assert config.data["database"]["host"] == "localhost"
        assert config.data["database"]["port"] == 27017
        assert config.data["logging"]["level"] == "INFO"

    def test_get_set_integration(self):
        """Test integration of get and set operations."""
        config = Config()

        # Set some values
        config.set("app.name", "TestApp")
        config.set("database.host", "localhost")
        config.set("database.port", 27017)

        # Test getting values back
        assert config.get("app.name") == "TestApp"
        assert config.get("database.host") == "localhost"
        assert config.get("database.port") == 27017

        # Test modifying values
        config.set("database.port", 3306)
        assert config.get("database.port") == 3306


class TestNestedHelperMethods:
    """Test the internal helper methods."""

    def test_set_nested_single_level(self):
        """Test _set_nested with single level nesting."""
        config = Config()
        data = {}

        config._set_nested(data, ["database"], "value")

        assert data["database"] == "value"

    def test_set_nested_multiple_levels(self):
        """Test _set_nested with multiple levels of nesting."""
        config = Config()
        data = {}

        config._set_nested(data, ["app", "database", "host"], "localhost")

        assert data["app"]["database"]["host"] == "localhost"

    def test_set_nested_overwrite(self):
        """Test _set_nested overwriting existing values."""
        config = Config()
        data = {"database": {"host": "old_host"}}

        config._set_nested(data, ["database", "host"], "new_host")

        assert data["database"]["host"] == "new_host"

    def test_set_nested_expand_structure(self):
        """Test _set_nested expanding data structure."""
        config = Config()
        data = {}

        config._set_nested(data, ["a", "b", "c", "d"], "value")

        assert data["a"]["b"]["c"]["d"] == "value"
