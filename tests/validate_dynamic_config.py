#!/usr/bin/env python3
"""
Simple validation script for dynamic configuration functionality.
This script tests the core dynamic configuration features without GUI components.
"""

import sys
import tempfile
import os

# Add framework to path
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.config import Config
from framework.cpu_tasks import ConcurrentFuturesAdapter
from framework.logging import Logging

def test_dynamic_config():
    """Test dynamic configuration functionality"""
    print("🚀 Testing Dynamic Configuration Framework")
    print("=" * 50)

    # Test 1: Configuration persistence
    print("\n1. Testing configuration persistence...")
    config = Config()
    config.set("TEST_WORKERS", 6)
    config.set("TEST_TIMEOUT", 45.5)

    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
        tmp_path = tmp.name

    try:
        config.save_to_file(tmp_path)

        new_config = Config()
        new_config.load_from_file(tmp_path)

        assert new_config.get("TEST_WORKERS") == 6
        assert new_config.get("TEST_TIMEOUT") == 45.5
        print("✅ Configuration persistence works!")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Test 2: App reload configuration
    print("\n2. Testing App configuration reload...")
    app = App("TestApp")

    # Create config file
    test_config = {
        "APP_WORKERS": 8,
        "APP_LEVEL": "DEBUG"
    }
    import yaml
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False) as tmp:
        yaml.dump(test_config, tmp)
        tmp_path = tmp.name

    try:
        app.reload_config(tmp_path)
        assert app.container.get(Config).get("APP_WORKERS") == 8
        print("✅ App configuration reload works!")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    # Test 3: Concurrent adapter updates
    print("\n3. Testing concurrent adapter dynamic updates...")
    concurrent_adapter = ConcurrentFuturesAdapter(app)

    # Test configuration update
    app.container.get(Config).set("CONCURRENT_WORKERS", 10)
    app.container.get(Config).set("CONCURRENT_TIMEOUT", 60.0)

    concurrent_adapter.on_config_update(app.container.get(Config))

    assert concurrent_adapter.max_workers == 10
    assert concurrent_adapter.timeout == 60.0
    print("✅ Concurrent adapter dynamic updates work!")

    # Test 4: Logging dynamic updates
    print("\n4. Testing dynamic logging level changes...")
    logging_instance = Logging()
    logger1 = logging_instance.get_logger("test1")
    logger2 = logging_instance.get_logger("test2")

    # Change global level
    logging_instance.set_global_level("WARNING")

    # Verify levels updated
    assert logger1.level == 30  # WARNING = 30
    assert logger2.level == 30
    print("✅ Dynamic logging level updates work!")

    # Test 5: App log level update
    print("\n5. Testing App log level updates...")
    app.update_log_level("ERROR")

    # Should not crash and update successfully
    logging_inst = app.container.get(Logging)
    logger = logging_inst.get_logger("app_test")
    assert logger.level == 40  # ERROR = 40
    print("✅ App log level updates work!")

    print("\n" + "=" * 50)
    print("🎉 ALL DYNAMIC CONFIGURATION TESTS PASSED!")
    print("=" * 50)

    # Cleanup
    concurrent_adapter.stop()

    return True

if __name__ == "__main__":
    try:
        test_dynamic_config()
        print("\n✅ Framework dynamic configuration is fully functional!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
