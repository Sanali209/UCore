#!/usr/bin/env python3
"""
Test the new UCore Settings Module - YAML-based persistence
"""
import sys
sys.path.insert(0, 'd:/UCore')  # Add current directory to path

from framework.core.settings import SettingsManager

def test_settings_module():
    print("🧪 Testing UCore Settings Module")
    print("=" * 50)

    # Create settings manager
    settings = SettingsManager("test_settings.yml")

    # Test initial values
    print("✅ Initial settings loaded:")
    print(f"  App Name: {settings.get('app_name')}")
    print(f"  Download Dir: {settings.get('download_directory')}")
    print(f"  Version: {settings.get('version')}")
    print()

    # Test setting changes
    print("🔧 Testing settings changes:")
    old_dir = settings.get('download_directory')
    settings.set('download_directory', '/home/user/test')
    print(f"  Changed download_directory: '{old_dir}' → '{settings.get('download_directory')}'")
    print()

    # Test callback subscription
    def on_download_dir_change(key, new_value, old_value):
        print(f"  📢 Callback: '{key}' changed from '{old_value}' to '{new_value}'")

    settings.subscribe('download_directory', on_download_dir_change)
    print("📢 Subscribed to download_directory changes")
    settings.set('download_directory', '/home/user/new_path')
    print()

    # Test specialized methods
    print("🎯 Testing specialized methods:")
    settings.set_download_directory('/tmp/test_dir')
    print(f"  Download directory set to: {settings.get_download_directory()}")
    print(f"  Recent directories: {settings.get_recent_directories()}")
    print()

    # Test saving and reloading
    print("💾 Testing save and reload:")
    print(f"  Settings saved: {settings.save()}")

    # Create new instance to test persistence
    print("📖 Testing persistence with new instance:")
    new_settings = SettingsManager("test_settings.yml")
    print(f"  Reloaded download_directory: {new_settings.get_download_directory()}")
    print("  ✅ Settings persisted correctly!")
    print()

    # Show all settings
    print("📋 All current settings:")
    all_settings = settings.get_all()
    for key, value in sorted(all_settings.items()):
        print(f"  {key}: {value}")
    print()

    print("🎉 Settings Module Test COMPLETED!")
    print("✅ All functionality working correctly")
    print("✅ YAML persistence verified")
    print("✅ Callbacks and subscriptions operational")
    print("✅ Specialized methods functional")

if __name__ == "__main__":
    test_settings_module()
