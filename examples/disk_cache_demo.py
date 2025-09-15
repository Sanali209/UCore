#!/usr/bin/env python3
"""
Disk Cache Demo - UCore Framework

This example demonstrates the DiskCacheAdapter component integration with modern UCore patterns:
- Component-based architecture
- Async startup patterns
- Proper error handling
- Real-world cache operations

Features:
🔄 Basic cache operations (set/get/delete/has_key)
⚡ Memoization decorator for function caching
📊 Cache statistics and inspection
🔧 Runtime configuration updates
🧹 Cache cleanup and lifecycle management
"""

import sys
import asyncio
import time
from pathlib import Path

# Add framework to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from framework import App
from framework.data.disk_cache import DiskCacheAdapter


class CacheDemo:
    """Demo class showing how to use the DiskCacheAdapter."""

    def __init__(self, cache_adapter: DiskCacheAdapter, app_config):
        self.cache = cache_adapter
        self.app_config = app_config

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

        if second_call_time > 0:
            speedup = first_call_time / second_call_time
            print(f"Cache speedup: {speedup:.1f}x faster on cached calls")
        else:
            print("Cache speedup: Instant cache hits! ⚡")

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
        self.cache.update_config(cache_dir="./new_cache")

        print("Cache directory updated!")
        stats = self.cache.get_stats()
        print(f"New cache stats: {stats}")

    def demonstrate_cleanup(self):
        """Demonstrate cache cleanup."""
        print("\n=== Cache Cleanup Demo ===")

        print("Adding some test data...")

        # Add more test data to demonstrate cleanup
        for i in range(10):
            self.cache.set(f"test_key_{i}", f"test_value_{i}")

        print("Getting all keys before cleanup:")
        keys_before = self.cache.get_all_keys()
        print(f"  Keys: {len(keys_before)}")

        print("Clearing cache...")
        self.cache.clear()

        print("Getting all keys after cleanup:")
        keys_after = self.cache.get_all_keys()
        print(f"  Keys: {len(keys_after)}")

        print("Cache cleanup complete!")


async def create_cache_demo():
    """Application factory for the cache demo."""
    print("🔄 Initializing Disk Cache Demo Application...")

    # 1. Initialize the main App object
    app = App(name="CacheDemo")

    # 2. Create and register the DiskCacheAdapter component
    cache_adapter = DiskCacheAdapter(app)
    app.register_component(lambda: cache_adapter)

    # Store reference for manual access (UCore framework pattern)
    app.cache_adapter = cache_adapter

    print("✅ DiskCacheAdapter component registered")

    # 3. Start the application (this will start all components)
    await app.start()

    # 4. Use the stored reference instead of trying to get from container
    cache_adapter = app.cache_adapter

    # 5. Create the demo with app instance for config access
    demo = CacheDemo(cache_adapter, app)

    print("✅ Cache demo application ready")

    return app, demo


async def main():
    """Async main function to run the cache demo."""
    print("🏗️  UCORE DISK CACHE DEMO")
    print("=" * 50)

    try:
        # Create demo app
        app, demo = await create_cache_demo()

        # Run demonstrations
        demo.demonstrate_basic_operations()
        demo.demonstrate_memoization()
        demo.demonstrate_stats()
        demo.demonstrate_all_keys()
        demo.demonstrate_config_update()
        demo.demonstrate_cleanup()

        print("\n" + "=" * 50)
        print("✅ DEMO COMPLETE!")
        print("🗂️  Cache directory: ./cache")
        print("💾 Persistent disk caching demonstrated")
        print("⚡ Memoization performance boost shown")
        print("🔧 Configuration management working")
        print("\n🏆 This demonstrates production-ready disk caching!")

    except Exception as e:
        print(f"💥 Demo failed with error: {e}")
        import traceback
        traceback.print_exc()

    finally:
        if 'app' in locals():
            await app.stop()
            print("✨ Cleanup complete")


if __name__ == "__main__":
    asyncio.run(main())
