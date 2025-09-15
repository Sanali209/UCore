import os
from typing import Any, Optional, Callable
from pathlib import Path
import diskcache
from ..core.component import Component


class DiskCacheAdapter(Component):
    """
    Framework component for managing disk-based caching operations using diskcache.Index.
    Provides a high-performance persistent cache with automatic serialization and indexing.
    """

    def __init__(self, app):
        self.app = app
        self.cache = None
        self.cache_dir = None
        self.size_limit = None
        self.eviction_policy = None

    def start(self):
        """
        Initialize the disk cache with configuration values using Index.
        """
        try:
            config = self.app.container.get('Config')
            self.cache_dir = config.get("CACHE_DIR", "./cache")
            self.size_limit = config.get("CACHE_SIZE_LIMIT", 100 * 1024 * 1024)  # 100MB default
            self.eviction_policy = config.get("CACHE_EVICTION_POLICY", "least-recently-used")
        except Exception as e:
            self.app.logger.warning(f"Could not get config for DiskCacheAdapter: {e}, using defaults")
            self.cache_dir = "./cache"
            self.size_limit = 100 * 1024 * 1024
            self.eviction_policy = "least-recently-used"

        # Ensure cache directory exists
        cache_path = Path(self.cache_dir)
        cache_path.mkdir(parents=True, exist_ok=True)

        # Initialize diskcache.Index which provides better indexing capabilities
        self.cache = diskcache.Index(
            directory=str(cache_path),
            size_limit=self.size_limit
        )

        self.app.logger.info(f"DiskCacheAdapter started with Index cache dir: {self.cache_dir}, size limit: {self.size_limit}")

    def stop(self):
        """
        Close the disk cache cleanly.
        """
        if self.cache:
            # diskcache.Index objects don't have a close() method like Cache objects
            # Just log the shutdown
            self.app.logger.info("DiskCacheAdapter stopped")

    def get(self, key: str, default=None) -> Any:
        """
        Get a value from the cache.

        Args:
            key: Cache key
            default: Default value if key doesn't exist

        Returns:
            Cached value or default
        """
        if not self.cache:
            self.app.logger.warning("Cache not initialized, returning default")
            return default
        return self.cache.get(key, default)

    def set(self, key: str, value: Any) -> bool:
        """
        Set a value in the cache.

        Args:
            key: Cache key
            value: Value to cache

        Returns:
            True if successful, False otherwise
        """
        if not self.cache:
            self.app.logger.warning("Cache not initialized")
            return False
        try:
            self.cache[key] = value
            return True
        except Exception as e:
            self.app.logger.error(f"Error setting cache key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        Delete a key from the cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted, False otherwise
        """
        if not self.cache:
            return False
        try:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
        except Exception as e:
            self.app.logger.error(f"Error deleting cache key {key}: {e}")
            return False

    def clear(self):
        """Clear all items from the cache."""
        if self.cache:
            self.cache.clear()
            self.app.logger.info("Cache cleared")

    def has_key(self, key: str) -> bool:
        """
        Check if a key exists in the cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        if not self.cache:
            return False
        return key in self.cache

    def get_all_keys(self) -> list:
        """
        Get all keys in the cache.

        Returns:
            List of all cache keys
        """
        if not self.cache:
            return []
        return list(self.cache.keys())

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        if not self.cache:
            return {"error": "Cache not initialized"}

        return {
            "count": len(self.cache),
            "size_limit": self.size_limit,
            "directory": str(self.cache_dir),
            "eviction_policy": str(self.eviction_policy),
            "type": "diskcache.Index"
        }

    def memoize(self, ttl: Optional[float] = None) -> Callable:
        """
        Decorator for memoizing function results.

        Args:
            ttl: Time-to-live for cached results in seconds (Index doesn't support TTL, use expire method)

        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Create a cache key from function name and arguments
                import hashlib
                import pickle

                try:
                    # Serialize arguments to create a unique key
                    key_data = pickle.dumps((func.__name__, args, kwargs), protocol=pickle.HIGHEST_PROTOCOL)
                    key = hashlib.md5(key_data).hexdigest()

                    # Check cache first
                    result = self.get(key)
                    if result is not None:
                        return result

                    # Execute function and cache result
                    result = func(*args, **kwargs)
                    self.set(key, result)
                    return result

                except Exception as e:
                    self.app.logger.warning(f"Memoization error for {func.__name__}: {e}")
                    # Fall back to executing the function without caching
                    return func(*args, **kwargs)

            return wrapper
        return decorator

    def update_config(self, cache_dir=None, size_limit=None, eviction_policy=None):
        """
        Update cache configuration at runtime.

        Args:
            cache_dir: New cache directory
            size_limit: New size limit
            eviction_policy: New eviction policy
        """
        needs_reinit = False

        if cache_dir is not None and cache_dir != self.cache_dir:
            self.cache_dir = cache_dir
            needs_reinit = True

        if size_limit is not None and size_limit != self.size_limit:
            self.size_limit = size_limit
            needs_reinit = True

        if eviction_policy is not None and eviction_policy != self.eviction_policy:
            self.eviction_policy = eviction_policy
            needs_reinit = True

        if needs_reinit and self.cache:
            # Index objects don't have close() method like Cache objects
            # Just set to None and reinitialize
            self.cache = None

            # Reinitialize with new settings
            cache_path = Path(self.cache_dir)
            cache_path.mkdir(parents=True, exist_ok=True)

            self.cache = diskcache.Index(
                directory=str(cache_path),
                size_limit=self.size_limit
            )

            self.app.logger.info(f"DiskCacheAdapter reinitialized with Index and new configuration")


def create_disk_cache_adapter():
    """
    Factory function for dependency injection.
    """
    def factory(app):
        adapter = DiskCacheAdapter(app)
        return adapter
    return factory
