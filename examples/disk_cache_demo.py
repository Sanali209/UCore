#!/usr/bin/env python3
"""
Example demonstrating the DiskCacheAdapter component integration.

This example shows how to:
1. Register and use the DiskCacheAdapter component
2. Configure cache settings
3. Perform basic cache operations
4. Use the memoization decorator
"""

import sys
import time
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework.app import App
from framework.disk_cache import DiskCacheAdapter
from framework.config import Config
from framework.logging import Logging


class CacheDemo:
    """Demo class showing how to use the DiskCacheAdapter."""

    def __init__(self, cache_adapter: DiskCacheAdapter, config: Config):
        self.cache = cache_adapter
        self.config = config

    def demonstrate_basic_operations(self):
        """Demonstrate basic cache operations."""
        print("=== Basic Cache Operations ===")

        # Set some values
        print("Setting cache values...")
        self.cache.set("user_profile", {"name": "John Doe", "email": "john@example.com"})
        self.cache.set("app_version", "1.2.3")
        self.cache.set("settings", {"theme": "dark", "language": "en"})

        # Get values
        print("Getting cache values...")
        profile = self.cache.get("user_profile")
        version = self.cache.get("app_version")
        settings = self.cache.get("settings")

        print(f"User Profile: {profile}")
        print(f"App Version: {version}")
        print(f"Settings: {settings}")

        # Check if keys exist
        print(f"Has 'user_profile': {self.cache.has_key('user_profile')}")
        print(f"Has 'nonexistent': {self.cache.has_key('nonexistent')}")

        # Delete a key
        print("Deleting 'app_version'...")
        deleted = self.cache.delete("app_version")
        print(f"Deletion successful: {deleted}")
        print(f"Has 'app_version' after deletion: {self.cache.has_key('app_version')}")

    def demonstrate_memoization(self):
        """Demonstrate the memoization decorator."""
        print("\n=== Memoization Demo ===")

        @self.cache.memoize()
        def expensive_calculation(x, y):
            """Simulate an expensive calculation."""
            print(f"  Performing expensive calculation for {x}, {y}...")
            time.sleep(0.5)  # Simulate work
            return x + y * 2

        # First call - should execute
        start_time = time.time()
        result1 = expensive_calculation(3, 4)
        first_call_time = time.time() - start_time
        print(".03f")

        # Second call with same arguments - should use cache
        start_time = time.time()
        result2 = expensive_calculation(3, 4)
        second_call_time = time.time() - start_time
        print(".03f")

        # Third call with different arguments - should execute
        start_time = time.time()
        result3 = expensive_calculation(5, 6)
        third_call_time = time.time() - start_time
        print(".03f")

        print(f"Cache speedup: {first_call_time / second_call_time:.1f}x faster on cached calls")

    def demonstrate_stats(self):
        """Show cache statistics."""
        print("\n=== Cache Statistics ===")
        stats = self.cache.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    def demonstrate_all_keys(self):
        """List all keys in the cache."""
        print("\n=== All Cache Keys ===")
        keys = self.cache.get_all_keys()
        for key in keys:
            print(f"  {key}")

    def demonstrate_config_update(self):
        """Demonstrate runtime configuration changes."""
        print("\n=== Configuration Update Demo ===")

        print("Updating cache directory to './new_cache'")
        self.config.set("CACHE_DIR", "./new_cache")
        self.cache.update_config(cache_dir="./new_cache")

        print("Cache directory updated!")
        stats = self.cache.get_stats()
        print(f"New cache stats: {stats}")


def create_cache_demo():
    """Application factory for the cache demo."""
    # 1. Initialize the main App object
    app = App(name="CacheDemo")

    # 2. Register the DiskCacheAdapter for caching
    disk_cache_adapter = DiskCacheAdapter(app)
    app.register_component(lambda: disk_cache_adapter)

    # 3. Register the adapter for dependency injection
    app.container.register(DiskCacheAdapter, disk_cache_adapter)

    # 4. Get dependencies manually
    config = app.container.get(Config)
    cache_adapter = app.container.get(DiskCacheAdapter)

    # 5. Start the cache component manually
    cache_adapter.start()

    # 6. Configure cache settings
    config.set("CACHE_DIR", "./demo_cache")
    config.set("CACHE_SIZE_LIMIT", 50 * 1024 * 1024)  # 50MB

    # 7. Create and configure the demo class
    demo = CacheDemo(cache_adapter, config)

    return app, demo


def main():
    """Main function to run the cache demo."""
    print("DiskCacheAdapter Demo")
    print("=" * 40)

    # Create demo app
    app, demo = create_cache_demo()

    try:
        # Run basic operations
        demo.demonstrate_basic_operations()

        # Demonstrate memoization
        demo.demonstrate_memoization()

        # Show cache stats
        demo.demonstrate_stats()

        # List all keys
        demo.demonstrate_all_keys()

        # Configuration update
        demo.demonstrate_config_update()

        print("\n=== Demo Complete ===")
        print("Cache files created in ./demo_cache directory")
        print("You can inspect cache contents directly or run this demo again!")

    except Exception as e:
        print(f"Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Clean up - framework will handle component shutdown
        pass


if __name__ == "__main__":
    main()
