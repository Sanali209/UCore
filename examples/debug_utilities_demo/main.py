"""
UCore Framework Example: Debug Utilities

This example demonstrates:
- Usage of framework/debug_utilities.py for debugging and diagnostics

Usage:
    python -m examples.debug_utilities_demo.main

Requirements:
    pip install loguru

"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from framework import debug_utilities
from loguru import logger

def main():
    logger.info("Debug utilities demo started")

    # Initialize debug utilities
    debug_utilities.init_debug_utilities()

    # Get and print debug metrics report
    metrics = debug_utilities.get_debug_metrics()
    if metrics:
        logger.info("Debug metrics report:")
        logger.info(metrics.get_report())

    # Get and print component debugger system report
    component_debugger = debug_utilities.get_component_debugger()
    if component_debugger:
        logger.info("Component debugger system report:")
        logger.info(component_debugger.get_system_report())

    # Get and print performance profiler report
    profiler = debug_utilities.get_performance_profiler()
    if profiler:
        logger.info("Performance profiler report:")
        logger.info(profiler.get_performance_report())

    logger.success("Debug utilities demo completed")

if __name__ == "__main__":
    main()
