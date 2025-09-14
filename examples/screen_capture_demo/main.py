#!/usr/bin/env python3
"""
Screen Capture Demo for UCore Framework
========================================

This example demonstrates the ScreenCapturer controller which can capture screenshots
of the full screen or specific regions at configurable intervals.

Features demonstrated:
- Full screen capture
- Region-based capture
- Different capture frequencies
- Disk and memory storage options
- Real-time statistics

Installation Requirements:
pip install mss pyautogui Pillow

Usage:
python examples/screen_capture_demo/main.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Set up the module path to find the framework
current_dir = Path(__file__).resolve().parent
ucore_root = current_dir.parent

# Add the UCore root to sys.path if not already there
if str(ucore_root) not in sys.path:
    sys.path.insert(0, str(ucore_root))

# Now import the framework modules
from framework.app import App
from framework.simulation.entity import EnvironmentEntity
from framework.simulation.controllers import ScreenCapturer

class ScreenCaptureDemo(App):
    """Demo application showing ScreenCapturer functionality."""

    def __init__(self):
        super().__init__("ScreenCaptureDemo")

        # Create entities with different screen capture configurations
        self.full_screen_entity = EnvironmentEntity("FullScreenCapturer")
        self.region_entity = EnvironmentEntity("RegionCapturer")
        self.fast_capture_entity = EnvironmentEntity("FastCapturer")

        # Setup controllers with different configurations
        self.setup_controllers()

    def setup_controllers(self):
        """Initialize screen capture controllers with different settings."""

        # 1. Full screen capturer - captures entire screen every 2 seconds
        full_screen_controller = ScreenCapturer(
            capture_region=None,  # Full screen
            capture_interval=2.0,
            store_on_disk=True,
            storage_path="full_screen_captures",
            max_screenshots=50,
            format="PNG"
        )

        # 2. Region capturer - captures specific region every 1 second
        region_controller = ScreenCapturer(
            capture_region=(100, 100, 800, 600),  # x=100, y=100, w=800, h=600
            capture_interval=1.0,
            store_on_disk=False,  # Keep in memory only
            max_screenshots=100,
            format="JPEG",
            quality=90
        )

        # 3. Fast capturer - very frequent captures for monitoring
        fast_controller = ScreenCapturer(
            capture_region=None,
            capture_interval=0.5,  # 2 FPS
            store_on_disk=False,
            max_screenshots=200
        )

        # Attach controllers to entities
        self.full_screen_entity.add_controller(full_screen_controller)
        self.region_entity.add_controller(region_controller)
        self.fast_capture_entity.add_controller(fast_controller)

        # Store references for monitoring
        self.controllers = [full_screen_controller, region_controller, fast_controller]

async def run_simulation(app, duration_seconds=30):
    """Run the simulation for the specified duration."""
    print("🎥 Starting screen capture simulation...")
    print("=" * 60)

    start_time = asyncio.get_event_loop().time()
    stats_interval = 5.0  # Print stats every 5 seconds
    last_stats_time = start_time

    print("📊 Initial Status:")
    for i, controller in enumerate(app.controllers, 1):
        stats = controller.get_stats()
        print(f"  {i}. {controller.entity.name}: Initialized")

    # Main simulation loop
    while True:
        current_time = asyncio.get_event_loop().time()
        elapsed = current_time - start_time

        if elapsed >= duration_seconds:
            break

        # Update simulation (this triggers controller updates)
        delta_time = 0.1  # 10 FPS simulation
        for entity in [app.full_screen_entity, app.region_entity, app.fast_capture_entity]:
            for controller in entity.get_controllers():
                if hasattr(controller, 'update'):
                    controller.update(delta_time)

        # Print stats periodically
        if current_time - last_stats_time >= stats_interval:
            print(f"\n📊 Stats at {elapsed:.1f}s:")
            for i, controller in enumerate(app.controllers, 1):
                stats = controller.get_stats()
                print(f"  {i}. {controller.entity.name}:")
                print(f"     Captures: {stats['stored_captures']}/{stats['total_captures']}")
                print(f"     Method: {stats['capture_method']}")

                # Show recent captures
                latest = controller.get_latest_capture()
                if latest:
                    size_kb = latest['size'] / 1024
                    print(f"     Last: #{latest['id']} ({latest['width']}x{latest['height']}, {size_kb:.1f}KB)")

            last_stats_time = current_time

        await asyncio.sleep(delta_time)

    print(f"\n🎉 Simulation completed! Total duration: {elapsed:.1f}s")

async def main():
    """Main demo function."""
    print("🖼️ UCore Framework - Screen Capture Demo")
    print("=" * 50)

    try:
        # Check if required libraries are available
        try:
            import mss
            print("✅ MSS library available (recommended for performance)")
        except ImportError:
            try:
                import pyautogui
                print("⚠️ MSS not available, using PyAutoGUI (slower)")
            except ImportError:
                print("❌ Neither MSS nor PyAutoGUI available!")
                print("Please install with: pip install mss")
                return

    except Exception as e:
        print(f"❌ Screen capture libraries not available: {e}")
        return

    # Initialize and start the demo application
    app = ScreenCaptureDemo()

    print("\n🚀 Starting Screen Capture Demo...")

    try:
        # Register components and start
        app.register_component(lambda: app.full_screen_entity)
        app.register_component(lambda: app.region_entity)
        app.register_component(lambda: app.fast_capture_entity)

        # Start the application
        await app.start()

        print("\n🎮 Controls:")
        print("  • Full Screen: Captures entire screen every 2s, saves to disk")
        print("  • Region: Captures specific area every 1s, keeps in memory")
        print("  • Fast: Captures full screen every 0.5s for monitoring")
        print("=" * 60)

        # Run the main capture simulation
        await run_simulation(app, duration_seconds=20)

        # Final statistics
        print("\n🏆 FINAL STATISTICS:")
        total_captures_all = 0
        total_size_all = 0

        for i, controller in enumerate(app.controllers, 1):
            stats = controller.get_stats()
            captures = stats['total_captures']
            size_mb = stats['total_size_bytes'] / (1024 * 1024)

            total_captures_all += captures
            total_size_all += stats['total_size_bytes']

            print(f"  {controller.entity.name}:")
            print(f"    📸 Captures: {captures}")
            print(f"    💾 Size: {size_mb:.1f}MB")
            if stats['storage_path']:
                print(f"    📁 Storage: {stats['storage_path']}")

            # Show sample captures
            all_captures = controller.get_all_captures()
            if all_captures:
                print(f"    📊 First capture: {all_captures[0]['timestamp']}")
                print(f"    📊 Latest capture: {all_captures[-1]['timestamp']}")

        total_size_mb = total_size_all / (1024 * 1024)
        avg_capture_rate = total_captures_all / 20.0 if total_captures_all > 0 else 0

        print("\n📈 AGGREGATE RESULTS:")
        print(f"  🎯 Total Captures: {total_captures_all}")
        print(f"  💾 Total Size: {total_size_mb:.1f}MB")
        print(f"  🔄 Average Rate: {avg_capture_rate:.1f} FPS")
        print("\n💡 Usage Tips:")
        print("  • Access captures programmatically with get_latest_capture()")
        print("  • Enable/disable disk storage with store_on_disk parameter")
        print("  • Adjust capture frequency with set_capture_interval()")
        print("  • Change capture region dynamically with set_capture_region()")

        print("\n✨ Demo completed successfully!")

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        raise
    finally:
        # Clean up
        await app.stop()

if __name__ == "__main__":
    asyncio.run(main())
