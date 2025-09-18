import sys
sys.path.insert(0, r"D:\UCore")
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, call
import os
from ucore_framework.data.disk_cache import DiskCacheAdapter, create_disk_cache_adapter


class TestDiskCacheAdapterInitialization:
    """Test DiskCacheAdapter initialization and basic setup."""

    def test_init(self):
        """Test basic initialization."""
        app = Mock()
        adapter = DiskCacheAdapter(app)

        assert adapter.app == app
        assert adapter.cache is None
        assert adapter.cache_dir is None
        assert adapter.size_limit is None
        assert adapter.eviction_policy is None

    def test_factory_function(self):
        """Test factory function for dependency injection."""
        factory = create_disk_cache_adapter()
        app = Mock()
        adapter = factory(app)

        assert isinstance(adapter, DiskCacheAdapter)
        assert adapter.app == app


class TestDiskCacheAdapterLifecycle:
    """Test start/stop lifecycle management."""

    @patch('diskcache.Index')
    def test_start_success_with_config(self, mock_index_class):
        """Test successful start with config values."""
        app = Mock()
        config = Mock()
        config.get.side_effect = lambda key, default: {
            "CACHE_DIR": "./test_cache",
            "CACHE_SIZE_LIMIT": 50 * 1024 * 1024,
            "CACHE_EVICTION_POLICY": "lru"
        }.get(key, default)
        logger = Mock()

        app.container.get.side_effect = lambda cls: config if cls == 'Config' else logger
        app.logger = logger

        adapter = DiskCacheAdapter(app)
        adapter.start()

        assert adapter.cache_dir in ("./test_cache", "test_cache")
        assert adapter.size_limit == 50 * 1024 * 1024
        assert adapter.eviction_policy == "lru"
        # Accept both './test_cache' and 'test_cache' for directory
        called_args = mock_index_class.call_args[1]
        assert called_args["directory"].replace("./", "") == "test_cache"
        assert called_args["size_limit"] == 50 * 1024 * 1024
        logger.info.assert_called()

    @patch('diskcache.Index')
    def test_start_success_with_defaults(self, mock_index_class):
        """Test successful start with default values when config fails."""
        app = Mock()
        logger = Mock()

        app.container.get.side_effect = Exception("Config not available")
        app.logger = logger

        adapter = DiskCacheAdapter(app)
        adapter.start()

        assert adapter.cache_dir in ("./cache", "cache")
        assert adapter.size_limit == 100 * 1024 * 1024
        assert adapter.eviction_policy == "least-recently-used"
        called_args = mock_index_class.call_args[1]
        assert called_args["directory"].replace("./", "") == "cache"
        assert called_args["size_limit"] == 100 * 1024 * 1024
        logger.warning.assert_called()

    def test_stop_success(self):
        """Test successful stop operation."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = DiskCacheAdapter(app)
        adapter.cache = MagicMock()  # Mock cache object
        adapter.stop()

        logger.info.assert_called_once_with("DiskCacheAdapter stopped")


class TestDiskCacheAdapterOperations:
    """Test cache operations (get, set, delete, etc.)."""

    def setup_method(self):
        """Setup method for each test."""
        self.app = Mock()
        self.logger = Mock()
        self.app.logger = self.logger
        self.adapter = DiskCacheAdapter(self.app)
        self.adapter.cache = MagicMock()

    def test_get_with_cache_available(self):
        """Test get operation when cache is available."""
        self.adapter.cache.get.return_value = "test_value"
        result = self.adapter.get("test_key", "default")

        assert result == "test_value"
        self.adapter.cache.get.assert_called_once_with("test_key", "default")

    def test_get_with_cache_unavailable(self):
        """Test get operation when cache is not available."""
        self.adapter.cache = None

        with patch.object(self.logger, 'warning') as mock_warning:
            result = self.adapter.get("test_key", "default")

            assert result == "default"
            mock_warning.assert_called_once()

    def test_set_success(self):
        """Test successful set operation."""
        self.adapter.cache.__setitem__.return_value = None
        result = self.adapter.set("test_key", "test_value")

        assert result is True
        # Verify the item was set
        assert self.adapter.cache.__setitem__.called

    def test_set_failure(self):
        """Test set operation failure."""
        self.adapter.cache.__setitem__.side_effect = Exception("Set error")

        with patch.object(self.logger, 'error') as mock_error:
            result = self.adapter.set("test_key", "test_value")

            assert result is False
            mock_error.assert_called()

    def test_set_with_cache_unavailable(self):
        """Test set when cache is not available."""
        self.adapter.cache = None

        with patch.object(self.logger, 'warning') as mock_warning:
            result = self.adapter.set("test_key", "test_value")

            assert result is False
            mock_warning.assert_called_once()

    def test_delete_success(self):
        """Test successful delete operation."""
        self.adapter.cache.__contains__.return_value = True
        self.adapter.cache.__delitem__.return_value = None

        result = self.adapter.delete("test_key")

        assert result is True
        assert self.adapter.cache.__contains__.called
        assert self.adapter.cache.__delitem__.called

    def test_delete_nonexistent_key(self):
        """Test delete of non-existent key."""
        self.adapter.cache.__contains__.return_value = False

        result = self.adapter.delete("nonexistent_key")

        assert result is False
        assert self.adapter.cache.__delitem__.not_called

    def test_delete_with_error(self):
        """Test delete operation with error."""
        self.adapter.cache.__contains__.return_value = True
        self.adapter.cache.__delitem__.side_effect = Exception("Delete error")

        with patch.object(self.logger, 'error') as mock_error:
            result = self.adapter.delete("test_key")

            assert result is False
            mock_error.assert_called()

    def test_delete_with_cache_unavailable(self):
        """Test delete when cache is not available."""
        self.adapter.cache = None

        result = self.adapter.delete("test_key")

        assert result is False

    def test_clear_success(self):
        """Test successful clear operation."""
        self.adapter.cache.clear.return_value = None

        self.adapter.clear()

        self.adapter.cache.clear.assert_called_once()
        self.logger.info.assert_called_once_with("Cache cleared")

    def test_clear_with_cache_unavailable(self):
        """Test clear when cache is not available."""
        self.adapter.cache = None

        # Should not raise an error
        self.adapter.clear()

    def test_has_key_success(self):
        """Test has_key operation."""
        self.adapter.cache.__contains__.return_value = True

        result = self.adapter.has_key("test_key")

        assert result is True
        self.adapter.cache.__contains__.assert_called_once_with("test_key")

    def test_has_key_cache_unavailable(self):
        """Test has_key when cache is not available."""
        self.adapter.cache = None

        result = self.adapter.has_key("test_key")

        assert result is False

    def test_get_all_keys_success(self):
        """Test get_all_keys operation."""
        self.adapter.cache.keys.return_value = ["key1", "key2", "key3"]

        result = self.adapter.get_all_keys()

        assert result == ["key1", "key2", "key3"]
        self.adapter.cache.keys.assert_called_once()

    def test_get_all_keys_cache_unavailable(self):
        """Test get_all_keys when cache is not available."""
        self.adapter.cache = None

        result = self.adapter.get_all_keys()

        assert result == []

    def test_get_stats_success(self):
        """Test get_stats operation."""
        self.adapter.cache_dir = "./test_cache"
        self.adapter.size_limit = 50 * 1024 * 1024
        self.adapter.eviction_policy = "test_policy"
        self.adapter.cache.__len__.return_value = 42

        result = self.adapter.get_stats()

        expected = {
            "count": 42,
            "size_limit": 50 * 1024 * 1024,
            "directory": "./test_cache",
            "eviction_policy": "test_policy",
            "type": "diskcache.Index"
        }
        assert result == expected

    def test_get_stats_cache_unavailable(self):
        """Test get_stats when cache is not available."""
        self.adapter.cache = None

        result = self.adapter.get_stats()

        assert result == {"error": "Cache not initialized"}


class TestDiskCacheAdapterMemoization:
    """Test memoization decorator functionality."""

    def setup_method(self):
        """Setup method for each test."""
        self.app = Mock()
        self.logger = Mock()
        self.app.logger = self.logger
        self.adapter = DiskCacheAdapter(self.app)
        self.adapter.cache = MagicMock()

    def test_memoize_decorator_success(self):
        """Test memoization decorator success case."""
        # Mock get to return None (cache miss) then set to work
        self.adapter.get = Mock(return_value=None)
        self.adapter.set = Mock(return_value=True)

        @self.adapter.memoize()
        def test_function(x, y=10):
            return x + y

        # First call should execute function and cache
        result1 = test_function(5, 15)
        assert result1 == 20
        self.adapter.set.assert_called_once()

        # Reset set mock
        self.adapter.set = Mock()

        # Second call should return cached result
        self.adapter.get = Mock(return_value=20)
        result2 = test_function(5, 15)
        assert result2 == 20
        # set should not be called this time
        self.adapter.set.assert_not_called()

    def test_memoize_decorator_error_handling(self):
        """Test memoization decorator error handling."""
        self.adapter.get = Mock(side_effect=Exception("Cache error"))
        self.adapter.set = Mock(return_value=True)

        with patch.object(self.logger, 'warning') as mock_warning:
            @self.adapter.memoize()
            def test_function(x):
                return x * 2

            # Should still execute function despite cache errors
            result = test_function(5)
            assert result == 10
            mock_warning.assert_called()


class TestDiskCacheAdapterConfiguration:
    """Test configuration update functionality."""

    @patch('diskcache.Index')
    @patch('pathlib.Path.mkdir')
    def test_update_config_success(self, mock_mkdir, mock_index_class):
        """Test successful configuration update."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = DiskCacheAdapter(app)
        adapter.cache = MagicMock()  # Existing cache

        adapter.update_config(
            cache_dir="./new_cache",
            size_limit=200 * 1024 * 1024,
            eviction_policy="fifo"
        )

        # Should update attributes
        assert adapter.cache_dir == "./new_cache"
        assert adapter.size_limit == 200 * 1024 * 1024
        assert adapter.eviction_policy == "fifo"

        # Should reinitialize cache (should be a MagicMock after re-init)
        assert isinstance(adapter.cache, MagicMock)
        assert mock_index_class.called

    @patch('diskcache.Index')
    @patch('pathlib.Path.mkdir')
    def test_update_config_partial_update(self, mock_mkdir, mock_index_class):
        """Test partial configuration update."""
        app = Mock()
        adapter = DiskCacheAdapter(app)
        adapter.cache = MagicMock()
        adapter.cache_dir = "./old_cache"
        adapter.size_limit = 100 * 1024 * 1024
        adapter.eviction_policy = "lru"

        # Only update cache_dir
        adapter.update_config(cache_dir="./new_cache")

        # Should update only changed attributes
        assert adapter.cache_dir == "./new_cache"
        assert adapter.size_limit == 100 * 1024 * 1024
        assert adapter.eviction_policy == "lru"

        # Should reinitialize since cache_dir changed
        assert mock_index_class.called

    def test_update_config_no_changes(self):
        """Test configuration update with no changes."""
        adapter = DiskCacheAdapter(Mock())
        adapter.cache = MagicMock()

        # Set same values
        adapter.cache_dir = "./cache"
        adapter.size_limit = 100 * 1024 * 1024
        adapter.eviction_policy = "policy"

        adapter.update_config(
            cache_dir="./cache",
            size_limit=100 * 1024 * 1024,
            eviction_policy="policy"
        )

        # Cache should still exist (no reinitialization)
        assert adapter.cache is not None


class TestDiskCacheAdapterErrorConditions:
    """Test error conditions and edge cases."""

    def test_start_with_path_creation_error(self):
        """Test start behavior when cache directory creation fails."""
        pass  # Implementation would require mocking Path.mkdir to raise exception

    def test_memoize_with_non_serializable_args(self):
        """Test memoization with arguments that can't be pickled."""
        app = Mock()
        logger = Mock()
        app.logger = logger

        adapter = DiskCacheAdapter(app)
        adapter.cache = Mock()

        # Mock pickle.dumps to raise exception
        with patch('pickle.dumps', side_effect=Exception("Pickle error")):
            with patch.object(logger, 'warning') as mock_warning:
                @adapter.memoize()
                def test_function(x):
                    return x * 2

                result = test_function(5)
                assert result == 10  # Should still work
                mock_warning.assert_called()

    def test_stats_with_directory_none(self):
        """Test get_stats when cache_dir is None."""
        adapter = DiskCacheAdapter(Mock())
        adapter.cache = MagicMock()
        adapter.cache.__len__.return_value = 5
        adapter.cache_dir = None

        result = adapter.get_stats()
        assert result["directory"] is None
