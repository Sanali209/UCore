"""
UCore Framework Example: Data Features

Demonstrates database access, disk cache, and MongoDB integration.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from ucore_framework.data.disk_cache import DiskCacheAdapter
from ucore_framework.data.mongo_adapter import MongoDBAdapter

class MockApp:
    def __init__(self):
        self.container = {}
        self.logger = type("Logger", (), {"info": print, "warning": print, "error": print, "debug": print})()

def main():
    app = MockApp()

    # Disk cache demo (DiskCacheAdapter)
    cache_adapter = DiskCacheAdapter(app)
    print("DiskCacheAdapter initialized:", cache_adapter)

    # MongoDB integration demo (MongoDBAdapter)
    mongo_adapter = MongoDBAdapter(app)
    print("MongoDBAdapter initialized:", mongo_adapter)

    print("In a real app, these adapters would be registered as components and started by the UCoreFrameworck.")

if __name__ == "__main__":
    main()
