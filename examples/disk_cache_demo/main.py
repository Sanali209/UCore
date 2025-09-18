"""
UCore Framework Example: Disk Cache

This example demonstrates:
- Usage of the disk cache system from UCoreFrameworck.data.disk_cache

Usage:
    python -m examples.disk_cache_demo.main

Requirements:
    pip install loguru diskcache

"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from UCoreFrameworck.data.disk_cache import DiskCacheAdapter
from loguru import logger

class DummyApp:
    def __init__(self):
        self.logger = logger
        self.container = {}

def main():
    logger.info("Disk cache demo started")

    # Create a dummy app for the adapter
    app = DummyApp()
    cache = DiskCacheAdapter(app)
    cache.start()

    # Store a value
    cache.set("my_key", {"foo": "bar"})
    logger.info(f"Stored value for 'my_key': {cache.get('my_key')}")

    # Overwrite the value
    cache.set("my_key", {"foo": "baz"})
    logger.info(f"Overwritten value for 'my_key': {cache.get('my_key')}")

    # Delete the value
    cache.delete("my_key")
    logger.info(f"Deleted 'my_key', now: {cache.get('my_key')}")

    # Clear the cache
    cache.clear()
    logger.info("Cache cleared")

    logger.success("Disk cache demo completed")

if __name__ == "__main__":
    main()
