"""
UCore Framework Example: Simulation Features

This example demonstrates:
- Simulation of entities, actions, and sensors using OOP
- Logging with loguru
- Progress visualization with tqdm

Usage:
    python -m examples.simulation_demo.main

Requirements:
    pip install loguru tqdm

Demonstrates simulation systems, entities, actions, and sensors.
"""

from loguru import logger
from tqdm import tqdm
import time

class Entity:
    def __init__(self, name):
        self.name = name
        self.state = 0

    def act(self):
        logger.info(f"{self.name} acts. State before: {self.state}")
        self.state += 1
        logger.info(f"{self.name} state after: {self.state}")

class Sensor:
    def __init__(self, entity):
        self.entity = entity

    def sense(self):
        logger.info(f"Sensor reads {self.entity.name} state: {self.entity.state}")
        return self.entity.state

def main():
    logger.info("Simulation demo started")
    entity = Entity("SimEntity")
    sensor = Sensor(entity)

    for i in tqdm(range(5), desc="Simulation Steps"):
        entity.act()
        sensed = sensor.sense()
        logger.debug(f"Step {i+1}: sensed state = {sensed}")
        time.sleep(0.2)

    logger.success("Simulation demo completed")

if __name__ == "__main__":
    main()
