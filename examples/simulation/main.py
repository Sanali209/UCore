# examples/simulation/main.py
import sys
import time
import math
import random

# This allows the example to be run from the root of the repository
sys.path.insert(0, 'd:/UCore')

from framework.app import App
from framework.simulation.entity import EnvironmentEntity
from framework.simulation.controllers import Transform, BotAgent

def run_simulation():
    """
    A simple console-based simulation runner.
    """
    print("--- Simple Simulation Example ---")

    # 1. Create entities
    agents = []
    for i in range(3):
        agent = EnvironmentEntity(name=f"Agent-{i}")
        agent.add_controller(Transform(x=random.uniform(-10, 10), y=random.uniform(-10, 10)))
        agent.add_controller(BotAgent())
        agents.append(agent)
        print(f"Created: {agent} at {agent.get_controller(Transform)}")

    # 2. Simulation loop
    print("\n--- Starting Simulation Loop (10 steps) ---")
    for step in range(10):
        print(f"\n[Step {step + 1}]")
        for agent in agents:
            transform = agent.get_controller(Transform)
            bot = agent.get_controller(BotAgent)
            
            # Get an action from the agent
            action = bot.get_action()
            print(f"  - {agent.name}: Action='{action}'")

            # Update transform based on action
            if action == 'move_forward':
                speed = 1.0
                transform.x += math.cos(math.radians(transform.rotation)) * speed
                transform.y += math.sin(math.radians(transform.rotation)) * speed
            elif action == 'turn_left':
                transform.rotation -= 15
            elif action == 'turn_right':
                transform.rotation += 15
            
            print(f"    New State: {transform}")
        
        # In a real app, this would be a controlled time step
        time.sleep(0.5)

    print("\n--- Simulation Finished ---")


if __name__ == "__main__":
    # This example does not use the full UCore App lifecycle,
    # as it's a simple, synchronous console script.
    # It directly demonstrates the simulation classes.
    run_simulation()
