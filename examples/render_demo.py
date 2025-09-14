#!/usr/bin/env python3
"""
RenderController Demo for UCore Framework
===========================================

This example demonstrates the RenderController which can visualize simulation
state in real-time using Pygame. Shows entities with transforms moving around
a 2D space with interactive camera controls.

Features demonstrated:
- Real-time entity rendering
- Interactive camera controls (arrow keys, zoom)
- Different entity types with custom colors
- Performance monitoring (FPS counter)
- Grid overlay and UI elements
- Automated entity simulation

Installation Requirements:
pip install pygame

Usage:
python examples/render_demo.py

Controls:
- Arrow Keys: Move camera
- Space: Reset camera to center
- G: Toggle coordinate grid
- F: Toggle FPS display
- S: Toggle stats overlay
- ESC or close window: Exit
"""

import asyncio
import math
import random
import sys
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
from framework.simulation.controllers import RenderController, Transform


class SimulationEntity(EnvironmentEntity):
    """An entity with a transform that moves around automatically."""

    def __init__(self, name: str, x: float = 0.0, y: float = 0.0, speed: float = 1.0):
        super().__init__(name)

        # Create and attach transform controller
        self.transform = Transform(x, y)
        self.add_controller(self.transform)

        # Movement settings
        self.speed = speed
        self.angle = random.random() * 2 * math.pi
        self.turn_speed = random.uniform(-0.5, 0.5)
        self.target_chase_time = 0
        self.chase_target = None

        # Visual properties
        self.radius = random.randint(8, 15)

    def update(self, delta_time: float):
        """Update entity movement."""
        # Random movement pattern
        self.angle += self.turn_speed * delta_time

        # Occasionally change direction
        if random.random() < 0.01:
            self.angle += random.uniform(-math.pi/2, math.pi/2)
            self.turn_speed = random.uniform(-0.5, 0.5)

        # Move in current direction
        dx = math.cos(self.angle) * self.speed * delta_time
        dy = math.sin(self.angle) * self.speed * delta_time

        # Bounce off edges (keep entities within reasonable bounds)
        margin = 100
        if abs(self.transform.x) > 300 or abs(self.transform.y) > 200:
            # Turn towards center
            angle_to_center = math.atan2(-self.transform.y, -self.transform.x)
            self.angle = angle_to_center + random.uniform(-math.pi/4, math.pi/4)

        self.transform.x += dx
        self.transform.y += dy


class EnhancedRenderController(RenderController):
    """Extended RenderController with custom entity rendering."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Add custom colors for simulation entities
        self.add_entity_color('SimulationEntity', (100, 200, 100))

        # Enhanced entity visual properties
        self.render_mode = 'circle'  # circle, rect, triangle
        self.show_movement_vectors = True
        self.trail_alpha = 0.3
        self.entity_trails = {}
        self.max_trail_length = 50

    def _render_entity_visual(self, entity, x: float, y: float):
        """Enhanced rendering with trails and different shapes."""
        if not self._screen or not self._pygame:
            return

        pygame = self._pygame

        # Calculate screen position with camera
        if hasattr(entity, 'transform') and entity.transform:
            screen_x = x + entity.transform.x * self.zoom - self.camera_x
            screen_y = y + entity.transform.y * self.zoom - self.camera_y
        else:
            screen_x = x - self.camera_x
            screen_y = y - self.camera_y

        # Get entity type and color
        entity_type = type(entity).__name__
        color = self.entity_colors.get(entity_type, self.entity_colors['default'])

        # Apply zoom to visual size
        visual_size = max(5, int(entity.radius * self.zoom if hasattr(entity, 'radius') else 10))

        # Render based on mode
        if self.render_mode == 'circle':
            pygame.draw.circle(self._screen, color, (int(screen_x), int(screen_y)), visual_size)

            # Add outline for visibility
            outline_color = (min(255, color[0] + 50), min(255, color[1] + 50), min(255, color[2] + 50))
            pygame.draw.circle(self._screen, outline_color, (int(screen_x), int(screen_y)), visual_size, 2)

        elif self.render_mode == 'rect':
            rect = pygame.Rect(screen_x - visual_size, screen_y - visual_size, visual_size * 2, visual_size * 2)
            pygame.draw.rect(self._screen, color, rect)

        elif self.render_mode == 'triangle':
            # Draw triangle
            points = [
                (screen_x, screen_y - visual_size),
                (screen_x - visual_size, screen_y + visual_size//2),
                (screen_x + visual_size, screen_y + visual_size//2)
            ]
            pygame.draw.polygon(self._screen, color, points)

        # Draw movement vector if available
        if self.show_movement_vectors and hasattr(entity, 'angle'):
            vector_length = visual_size * 2
            vector_x = screen_x + math.cos(entity.angle) * vector_length
            vector_y = screen_y + math.sin(entity.angle) * vector_length
            vector_color = (255, 100, 100)
            pygame.draw.line(self._screen, vector_color, (screen_x, screen_y), (vector_x, vector_y), 2)

        # Render entity label
        if self._font:
            label = entity.name or entity_type
            text_surface = self._font.render(label, True, (255, 255, 255))
            text_rect = text_surface.get_rect(center=(int(screen_x), int(screen_y + visual_size + 15)))
            self._screen.blit(text_surface, text_rect)

        # Store entity position for statistics
        self.entity_positions[id(entity)] = (screen_x, screen_y)

    def _handle_key_events(self, key):
        """Enhanced key handling."""
        super()._handle_key_events(key)

        pygame = self._pygame

        if key == pygame.K_ESCAPE:
            # Exit application
            if hasattr(self.entity, '_app'):
                self.entity._app.logger.info("🔄 Exit requested via ESC key")
                # Set a flag that can be checked by main loop


class RenderDemo(App):
    """Demo application showing RenderController functionality."""

    def __init__(self):
        super().__init__("RenderDemo")

        # Create simulation entities
        self.entities = []
        self.create_simulation_entities()

        # Create render controller
        self.renderer = EnhancedRenderController(
            width=1200,
            height=800,
            fps=60,
            background_color=(20, 20, 30),
            show_grid=True,
            grid_size=25,
            window_title="UCore Simulation Renderer - Moving Entities Demo"
        )

        # Attach renderer to app
        self.add_controller(self.renderer)

        # Demo state
        self.running = True
        self.frame_count = 0

    def create_simulation_entities(self):
        """Create a set of simulation entities with different behaviors."""
        # Create different types of entities
        entity_configs = [
            ("FastEntity", 50, 50, 3.0),
            ("SlowEntity", -50, 0, 1.0),
            ("MediumEntity", 0, -50, 2.0),
        ]

        # Create individual named entities
        for i in range(8):
            x = random.uniform(-200, 200)
            y = random.uniform(-150, 150)
            speed = random.uniform(1.0, 4.0)

            entity_name = f"Entity_{i+1}"
            entity = SimulationEntity(entity_name, x, y, speed)
            entity.radius = random.randint(8, 15)

            self.entities.append(entity)

        self.logger.info(f"🎯 Created {len(self.entities)} simulation entities")

    def update(self, delta_time: float):
        """Update all simulation entities."""
        self.frame_count += 1

        for entity in self.entities:
            entity.update(delta_time)

        super().update(delta_time)


async def main():
    """Main demo function."""
    print("🎨 UCore Framework - RenderController Demo")
    print("=" * 50)

    # Check if pygame is available
    try:
        import pygame
        print("✅ Pygame library available")
    except ImportError:
        print("❌ Pygame not available!")
        print("Please install with: pip install pygame")
        return

    # Initialize and start the demo application
    app = RenderDemo()

    print("\n🚀 Starting Rendering Demo...")

    try:
        # Start the application
        await app.astart()

        print("\n🎮 CONTROLS:")
        print("  • Arrow Keys: Pan camera around the scene")
        print("  • Space: Reset camera to origin")
        print("  • G: Toggle coordinate grid")
        print("  • F: Toggle FPS counter")
        print("  • S: Toggle statistics overlay")
        print("  • ESC: Exit the demo")
        print("=" * 60)

        # Main game loop
        running = True
        frame_time = 1.0 / 60  # 60 FPS
        last_time = asyncio.get_running_loop().time()

        print("🎯 SIMULATION RUNNING")
        print("Watch the entities move around the screen!")
        print("Use arrow keys to explore different parts of the simulation.")

        while running:
            current_time = asyncio.get_running_loop().time()
            delta_time = current_time - last_time
            last_time = current_time

            # Update game logic
            app.update(delta_time)

            # Check for exit condition
            if app.frame_count > 60 * 120:  # Exit after 2 minutes
                print("\n⏰ Demo completed (2 minute timeout)")
                running = False

            # Small delay to prevent CPU overload
            await asyncio.sleep(0.001)

        print("\n🛑 Demo completed!")

    except KeyboardInterrupt:
        print("\n🛑 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")
        raise
    finally:
        # Clean up
        if hasattr(app, 'astop'):
            await app.astop()
        print("✨ Cleanup complete")


if __name__ == "__main__":
    # Windows compatibility for subprocess
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    # Run the demo
    asyncio.run(main())
