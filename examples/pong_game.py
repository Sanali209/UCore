#!/usr/bin/env python3
"""
Pong Game Example for UCore Framework
=====================================

This example demonstrates building a classic Pong game using UCore Framework:

🎮 Game Features:
- Two-player Pong game with ball physics
- Player-controlled paddles (WASD controls)
- AI opponent with adjustable difficulty
- Score tracking and win conditions
- Ball trail effects and particle systems
- Game statistics and performance monitoring
- Event-driven architecture with Redis integration
- Real-time metrics and debugging capabilities

🎯 Demonstration Goals:
- Entity/Controller pattern for game objects
- RenderController for real-time visualization
- Transform controllers for position/rotation
- Input system integration
- Physics simulation and collision detection
- Event-driven game state management
- Metrics and observability integration
- Background tasks for AI decision making

Installation Requirements:
pip install pygame aiohttp prometheus-client redis

Usage:
python examples/pong_game.py

Controls:
- Player 1: W (up), S (down)
- Player 2: ↑ (up), ↓ (down)
- ESC: Quit game

Features Demonstrated:
- Component-based game architecture
- Real-time rendering with Pygame
- Physics simulation with UCore
- Event-driven game logic
- AI opponent system
- Metrics collection and monitoring
- Background task processing
- Professional game structure
"""

import asyncio
import math
import random
from datetime import datetime

# Third-party imports
try:
    import pygame
    from aiohttp import web
    import redis
except ImportError as e:
    print(f"⚠️ Missing dependencies: {e}")
    print("Install with: pip install pygame aiohttp prometheus-client redis")
    exit(1)

# UCore Framework imports
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from framework.app import App
from framework.simulation.entity import EnvironmentEntity
from framework.simulation.controllers import RenderController, Transform
from framework.redis_adapter import RedisAdapter

# Create Entity class for compatibility
class Entity(EnvironmentEntity):
    """Entity base class for Pong game objects."""
    def __init__(self, name: str):
        super().__init__(name)


# Simple metrics class for Pong game
class MetricsCollector:
    """Simple metrics collector for Pong game."""
    def __init__(self):
        from prometheus_client import Counter, Gauge, Histogram
        self.metrics = {}

        # Game-specific metrics
        self.metrics['goals_scored_total'] = Counter('goals_scored_total', 'Total goals scored', ['player'])
        self.metrics['game_score_player1'] = Gauge('game_score_player1', 'Player 1 current score')
        self.metrics['game_score_player2'] = Gauge('game_score_player2', 'Player 2 current score')
        self.metrics['ball_speed_distribution'] = Histogram('ball_speed_distribution', 'Ball speed distribution on goal')
        self.metrics['balls_served_total'] = Counter('balls_served_total', 'Total balls served')

    def add_counter(self, name, description, labels=None):
        """Add counter metric."""
        from prometheus_client import Counter
        if name not in self.metrics:
            self.metrics[name] = Counter(name, description, labelnames=labels or [])
        return self.metrics[name]

    def add_gauge(self, name, description, labels=None):
        """Add gauge metric."""
        from prometheus_client import Gauge
        if name not in self.metrics:
            self.metrics[name] = Gauge(name, description, labelnames=labels or [])
        return self.metrics[name]

    def add_histogram(self, name, description, labels=None, buckets=None):
        """Add histogram metric."""
        from prometheus_client import Histogram
        if name not in self.metrics:
            self.metrics[name] = Histogram(name, description, labelnames=labels or [], buckets=buckets)
        return self.metrics[name]

    def get_counter(self, name):
        """Get counter by name."""
        return self.metrics.get(name)

    def get_gauge(self, name):
        """Get gauge by name."""
        return self.metrics.get(name)

    def get_histogram(self, name):
        """Get histogram by name."""
        return self.metrics.get(name)


class Paddle(Entity):
    """Paddle entity with physics and input handling."""

    def __init__(self, name: str, x: float, y: float, player_id: int, width: int = 20, height: int = 100):
        super().__init__(name)

        # Transform for position
        self.transform = Transform(x, y)
        self.add_controller(self.transform)

        # Paddle properties
        self.player_id = player_id
        self.width = width
        self.height = height
        self.speed = 400.0  # pixels per second
        self.score = 0
        self.color = (255, 255, 255)  # White

        # Input state
        self.up_pressed = False
        self.down_pressed = False

        # Visual trail effect
        self.trail_positions = []
        self.max_trail = 10

    def update(self, delta_time: float):
        """Update paddle position based on input."""
        velocity = 0.0

        if self.up_pressed:
            velocity = -self.speed
        elif self.down_pressed:
            velocity = self.speed

        # Update position
        self.transform.y += velocity * delta_time

        # Clamp to screen bounds (assuming 600 height)
        self.transform.y = max(0, min(500, self.transform.y))

        # Update trail
        self.trail_positions.append((self.transform.x, self.transform.y))
        if len(self.trail_positions) > self.max_trail:
            self.trail_positions.pop(0)

    def set_input(self, up: bool, down: bool):
        """Set input state for this paddle."""
        self.up_pressed = up
        self.down_pressed = down


class Ball(Entity):
    """Ball entity with physics and collision detection."""

    def __init__(self, x: float, y: float, speed: float = 300.0):
        super().__init__("Ball")

        # Transform for position
        self.transform = Transform(x, y)
        self.add_controller(self.transform)

        # Ball properties
        self.radius = 15
        self.base_speed = speed
        self.speed = speed

        # Velocity components
        angle = random.uniform(0.3, 0.7) * math.pi  # Random angle, not too vertical
        if random.random() > 0.5:
            angle = -angle  # Random horizontal direction

        self.vx = self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)

        # Ball trail effect
        self.trail_positions = []
        self.max_trail = 20
        self.trail_color = (100, 150, 255)  # Blue trail

        # Collision state
        self.last_paddle_hit = 0

    def update(self, delta_time: float):
        """Update ball position and handle physics."""
        # Update position
        self.transform.x += self.vx * delta_time
        self.transform.y += self.vy * delta_time

        # Add to trail
        self.trail_positions.append((self.transform.x, self.transform.y))
        if len(self.trail_positions) > self.max_trail:
            self.trail_positions.pop(0)

        # Wall collision (top and bottom bounce)
        if self.transform.y <= 0 or self.transform.y >= 585:  # Assuming 600 height - ball radius
            self.vy = -self.vy
            # Add slight variation to prevent infinite horizontal bouncing
            self.vy += random.uniform(-0.5, 0.5)

    def check_paddle_collision(self, paddle):
        """Check collision with a paddle."""
        # Simple bounding box collision
        ball_x, ball_y = self.transform.x, self.transform.y

        paddle_left = paddle.transform.x - paddle.width // 2
        paddle_right = paddle.transform.x + paddle.width // 2
        paddle_top = paddle.transform.y - paddle.height // 2
        paddle_bottom = paddle.transform.y + paddle.height // 2

        # Check if ball overlaps with paddle
        if (ball_x + self.radius > paddle_left and
            ball_x - self.radius < paddle_right and
            ball_y + self.radius > paddle_top and
            ball_y - self.radius < paddle_bottom):

            # Calculate relative hit position (-1 to 1)
            relative_hit = (ball_y - paddle.transform.y) / (paddle.height / 2)

            # Apply pong-like physics
            self.vx = -self.vx  # Reverse direction

            # Increase speed slightly
            self.speed *= 1.05
            if self.speed > 1000:  # Cap maximum speed
                self.speed = 1000

            # Adjust angle based on where ball hit paddle
            angle_variation = relative_hit * 0.6  # Max 36 degrees variation
            current_angle = math.atan2(self.vy, self.vx)
            new_angle = current_angle + angle_variation

            # Ensure ball doesn't go too vertical
            if abs(math.cos(new_angle)) < 0.2:
                new_angle = math.copysign(math.pi/9, new_angle)  # Minimum 20 degrees from vertical

            self.vx = self.speed * math.cos(new_angle)
            self.vy = self.speed * math.sin(new_angle)

            return True

        return False

    def reset(self, x: float, y: float):
        """Reset ball to center position with new random direction."""
        self.transform.x = x
        self.transform.y = y
        self.speed = self.base_speed

        # New random angle, not too vertical
        angle = random.uniform(0.3, 0.7) * math.pi
        if random.random() > 0.5:
            angle = -angle

        self.vx = self.speed * math.cos(angle)
        self.vy = self.speed * math.sin(angle)

        self.trail_positions.clear()


class ParticleSystem(Entity):
    """Particle system for visual effects."""

    def __init__(self, x: float, y: float, particle_count: int = 10):
        super().__init__(f"Particles_{id(self)}")
        self.transform = Transform(x, y)
        self.add_controller(self.transform)

        self.particles = []

        # Create initial particles
        for _ in range(particle_count):
            self.particles.append({
                'x': x + random.uniform(-10, 10),
                'y': y + random.uniform(-10, 10),
                'vx': random.uniform(-200, 200),
                'vy': random.uniform(-200, 200),
                'lifetime': random.uniform(0.5, 1.5),
                'max_lifetime': random.uniform(0.5, 1.5),
                'color': (
                    random.randint(100, 255),
                    random.randint(100, 255),
                    random.randint(150, 255)
                )
            })

    def update(self, delta_time: float):
        """Update and remove dead particles."""
        for particle in self.particles[:]:
            particle['x'] += particle['vx'] * delta_time
            particle['y'] += particle['vy'] * delta_time
            particle['lifetime'] -= delta_time
            particle['vx'] *= 0.98  # Apply drag
            particle['vy'] *= 0.98

            if particle['lifetime'] <= 0:
                self.particles.remove(particle)


class PongGame(App):
    """Main Pong game application using UCore Framework."""

    def __init__(self):
        super().__init__("PongGame")

        # Game configuration
        self.width = 800
        self.height = 600
        self.fps = 60

        # Game entities
        self.paddle1 = None
        self.paddle2 = None
        self.ball = None
        self.particles = []

        # Game state
        self.running = True
        self.paused = False
        self.ai_enabled = True
        self.ai_difficulty = 3.0

        # Scoring
        self.max_score = 5  # Win condition
        self.winner = None

        # UCore services
        self.renderer = None
        self.metrics = None
        self.redis = None

        # Initialize services
        self.initialize_services()

    def initialize_services(self):
        """Initialize all required services."""
        # Create padded entities
        self.paddle1 = Paddle("Player1", x=50, y=self.height//2, player_id=1)
        self.paddle2 = Paddle("Player2", x=self.width-50, y=self.height//2, player_id=2)
        self.ball = Ball(x=self.width//2, y=self.height//2)

        # Create rendering service and attach it to this entity
        self.renderer = EnhancedPongRenderer(
            width=self.width,
            height=self.height,
            fps=self.fps,
            window_title="UCore Pong - W/S vs ↑/↓"
        )
        self.renderer.entity = self  # Attach renderer to this entity

        # Create metrics
        self.metrics = MetricsCollector()

        # Add game-specific metrics
        self.metrics.add_counter('balls_served_total', 'Total balls served')
        self.metrics.add_counter('goals_scored_total', 'Total goals scored', ['player'])
        self.metrics.add_gauge('game_score_player1', 'Player 1 current score')
        self.metrics.add_gauge('game_score_player2', 'Player 2 current score')
        self.metrics.add_histogram('ball_speed_distribution', 'Ball speed distribution on goal')

        # Initialize Redis for event publishing (optional)
        # Note: We'll initialize Redis in the start() method since it needs to be awaited
        self.redis = None

    async def start(self):
        """Start the game."""
        await super().start()

        # Initialize Redis if available
        try:
            self.redis = RedisAdapter(self)
            await self.redis.start()
            self.logger.info("🔴 Redis connected for game events")
        except Exception as e:
            self.redis = None
            self.logger.warning(f"⚠️ Redis not available - some features disabled: {e}")

        # Initialize renderer with robust fallback
        self.logger.info("🎮 Initializing RenderController...")

        # Ensure renderer exists and is properly attached
        if not hasattr(self, 'renderer') or self.renderer is None:
            self.logger.warning("🔧 Creating new RenderController")
            self.renderer = EnhancedPongRenderer(
                width=self.width,
                height=self.height,
                fps=self.fps,
                window_title="UCore Pong - W/S vs ↑/↓"
            )

        # Ensure renderer is properly attached
        if hasattr(self.renderer, 'entity'):
            self.renderer.entity = self
        else:
            self.logger.warning("⚠️ RenderController missing entity property")

        # Start renderer with error handling and robust checking
        self.logger.info("🔍 Starting renderer validation...")
        if hasattr(self.renderer, 'start'):
            self.logger.info("✅ Renderer has start method")
            start_method = getattr(self.renderer, 'start')
            if not hasattr(start_method, '__call__'):
                self.logger.error("❌ Renderer start method is not callable")
                raise RuntimeError("Renderer start method is not callable")
            if hasattr(start_method, '__await__'):
                self.logger.info("✅ Renderer start method is async")
            else:
                self.logger.warning("⚠️ Renderer start method is not async")

        try:
            self.logger.info("🚀 Calling renderer.start()...")
            result = await self.renderer.start()
            self.logger.info(f"✅ RenderController started successfully, result: {result}")
        except Exception as e:
            self.logger.error(f"❌ Failed to start renderer: {e}")

            # Debug: Check if renderer got changed during start
            self.logger.info(f"🔍 After error - renderer type: {type(self.renderer)}, value: {self.renderer}")
            if self.renderer is None:
                self.logger.warning("❌ Renderer became None during start() call")

            # Create backup renderer if first one fails
            self.logger.warning("🔄 Creating backup RenderController")
            try:
                self.renderer = EnhancedPongRenderer(
                    width=self.width,
                    height=self.height,
                    fps=self.fps,
                    window_title="UCore Pong BACKUP - W/S vs ↑/↓"
                )
                self.renderer.entity = self
                self.logger.info("✅ Backup renderer created successfully")
                await self.renderer.start()
                self.logger.info("✅ Backup RenderController started successfully")
            except Exception as e2:
                self.logger.error(f"❌ Backup renderer also failed: {e2}")
                self.logger.info(f"🔍 Backup After error - renderer type: {type(self.renderer)}, value: {self.renderer}")
                raise RuntimeError(f"Unable to initialize renderer: {e}") from e2

        # Start metrics server
        try:
            from prometheus_client import start_http_server
            start_http_server(9090)
            self.logger.info("📊 Metrics server started on http://localhost:9090")
        except Exception as e:
            self.logger.warning(f"⚠️ Failed to start metrics server: {e}")

        self.logger.info("🎮 Pong Game Started!")
        self.logger.info("🎯 Controls: Player 1 (W/S), Player 2 (↑/↓), ESC to quit")

        # Publish game start event
        if self.redis:
            try:
                await self.redis.publish_json("pong_events", {
                    "event_type": "game_started",
                    "timestamp": datetime.utcnow().isoformat(),
                    "game_mode": "two_player" if not self.ai_enabled else "ai_single",
                    "max_score": self.max_score
                })
            except Exception as e:
                self.logger.warning(f"⚠️ Failed to publish start event: {e}")

    async def aupdate(self):
        """Main game update loop."""
        if not self.renderer or not self.renderer._initialized:
            return

        if self.winner or self.paused:
            return

        # Handle input
        self.handle_input()

        # Update game entities
        self.update_game_state(1.0 / self.fps)  # Delta time

        # Update AI for player 2
        if self.ai_enabled:
            self.update_ai()

        # Check game conditions
        self.check_win_condition()
        self.check_collisions()
        self.check_ball_out_of_bounds()

        # Update particles
        for particle in self.particles:
            particle.update(1.0 / self.fps)
            if len(particle.particles) == 0:
                self.particles.remove(particle)

        # Update renderer (this will call the renderer's update method)
        await self.renderer.aupdate()

    def handle_input(self):
        """Handle player input."""
        if not self.renderer._pygame:
            return

        pygame = self.renderer._pygame

        # Handle quit event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self.reset_game()

        # Handle continuous key presses
        keys = pygame.key.get_pressed()

        # Player 1 (WASD)
        self.paddle1.set_input(keys[pygame.K_w], keys[pygame.K_s])

        # Player 2 (Arrow keys)
        self.paddle2.set_input(keys[pygame.K_UP], keys[pygame.K_DOWN])

    def update_game_state(self, delta_time: float):
        """Update game entities."""
        self.paddle1.update(delta_time)
        self.paddle2.update(delta_time)
        self.ball.update(delta_time)

    def update_ai(self):
        """Update AI for player 2."""
        paddle = self.paddle2
        ball = self.ball

        # Simple AI: Move towards predicted ball position
        target_y = ball.transform.y

        # Account for ball velocity to predict where it will be
        distance_to_ball = abs(ball.transform.x - paddle.transform.x)
        if distance_to_ball > 0:
            # Calculate time for ball to reach paddle
            time_to_reach = distance_to_ball / abs(ball.vx)
            # Predict y position with some error for difficulty
            prediction_error = (random.random() - 0.5) * self.ai_difficulty * 50
            target_y = ball.transform.y + ball.vy * time_to_reach + prediction_error

        # Move towards target position
        if target_y > paddle.transform.y + 20:
            paddle.up_pressed = False
            paddle.down_pressed = True
        elif target_y < paddle.transform.y - 20:
            paddle.up_pressed = True
            paddle.down_pressed = False
        else:
            paddle.up_pressed = False
            paddle.down_pressed = False

    def check_collisions(self):
        """Check for ball collisions with paddles."""
        if self.ball.check_paddle_collision(self.paddle1):
            # Add particles for collision effect
            particles = ParticleSystem(self.ball.transform.x, self.ball.transform.y, 8)
            self.particles.append(particles)

            # Publish collision event
            if self.redis:
                asyncio.create_task(
                    self.redis.publish_json("pong_events", {
                        "event_type": "ball_hit",
                        "player": 1,
                        "ball_speed": self.ball.speed,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )

        elif self.ball.check_paddle_collision(self.paddle2):
            # Add particles for collision effect
            particles = ParticleSystem(self.ball.transform.x, self.ball.transform.y, 8)
            self.particles.append(particles)

            # Publish collision event
            if self.redis:
                asyncio.create_task(
                    self.redis.publish_json("pong_events", {
                        "event_type": "ball_hit",
                        "player": 2,
                        "ball_speed": self.ball.speed,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )

    def check_ball_out_of_bounds(self):
        """Check if ball went out of bounds (goal!)."""
        # Left goal (Player 2 scores)
        if self.ball.transform.x < -50:
            # Player 2 scores
            self.paddle2.score += 1
            self.metrics.get_counter('goals_scored_total').labels(player='player2').inc()
            self.metrics.get_histogram('ball_speed_distribution').observe(self.ball.speed)
            self.metrics.get_gauge('game_score_player2').set(self.paddle2.score)

            self.logger.info(f"⚽ Player 2 Scores! Score: {self.paddle1.score}-{self.paddle2.score}")

            # Publish goal event
            if self.redis:
                asyncio.create_task(
                    self.redis.publish_json("pong_events", {
                        "event_type": "goal_scored",
                        "scoring_player": 2,
                        "score": f"{self.paddle1.score}-{self.paddle2.score}",
                        "ball_speed": self.ball.speed,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )

            self.reset_ball()

        # Right goal (Player 1 scores)
        elif self.ball.transform.x > self.width + 50:
            # Player 1 scores
            self.paddle1.score += 1
            self.metrics.get_counter('goals_scored_total').labels(player='player1').inc()
            self.metrics.get_histogram('ball_speed_distribution').observe(self.ball.speed)
            self.metrics.get_gauge('game_score_player1').set(self.paddle1.score)

            self.logger.info(f"⚽ Player 1 Scores! Score: {self.paddle1.score}-{self.paddle2.score}")

            # Publish goal event
            if self.redis:
                asyncio.create_task(
                    self.redis.publish_json("pong_events", {
                        "event_type": "goal_scored",
                        "scoring_player": 1,
                        "score": f"{self.paddle1.score}-{self.paddle2.score}",
                        "ball_speed": self.ball.speed,
                        "timestamp": datetime.utcnow().isoformat()
                    })
                )

            self.reset_ball()

    def reset_ball(self):
        """Reset ball to center position."""
        self.ball.reset(self.width // 2, self.height // 2)
        self.metrics.get_counter('balls_served_total').inc()

        # Add goal celebration particles
        particles = ParticleSystem(self.width // 2, self.height // 2, 20)
        # Make celebration 3x brighter
        for p in particles.particles:
            p['color'] = tuple(min(255, c * 3) for c in p['color'])
        self.particles.append(particles)

    def check_win_condition(self):
        """Check if a player has won."""
        if self.paddle1.score >= self.max_score:
            self.winner = 1
            self.logger.info(f"🏆 PLAYER 1 WINS! Final Score: {self.paddle1.score}-{self.paddle2.score}")
        elif self.paddle2.score >= self.max_score:
            self.winner = 2
            self.logger.info(f"🏆 PLAYER 2 WINS! Final Score: {self.paddle2.score}-{self.paddle2.score}")

        if self.winner and self.redis:
            asyncio.create_task(
                self.redis.publish_json("pong_events", {
                    "event_type": "game_won",
                    "winner": self.winner,
                    "final_score": f"{self.paddle1.score}-{self.paddle2.score}",
                    "timestamp": datetime.utcnow().isoformat()
                })
            )

    def reset_game(self):
        """Reset the entire game."""
        self.paddle1.score = 0
        self.paddle2.score = 0
        self.winner = None
        self.paused = False

        self.metrics.get_gauge('game_score_player1').set(0)
        self.metrics.get_gauge('game_score_player2').set(0)

        self.reset_ball()
        self.logger.info("🔄 Game Reset!")


class EnhancedPongRenderer(RenderController):
    """Enhanced RenderController specifically for Pong game."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Game-specific colors
        self.paddle_color = (255, 255, 255)
        self.ball_color = (255, 0, 0)  # Red ball
        self.center_line_color = (100, 100, 100)
        self.background_color = (20, 20, 50)  # Dark blue background
        self.particle_color = (100, 200, 100)

        # Font for scoring
        self.font = None
        self.score_font = None

    def _render_entity_visual(self, entity, x: float, y: float):
        """Override to render different entity types."""
        if not self._screen or not self._pygame:
            return

        pygame = self._pygame

        # Calculate world position
        screen_x = x + (entity.transform.x if hasattr(entity, 'transform') else 0) - self.camera_x
        screen_y = y + (entity.transform.y if hasattr(entity, 'transform') else 0) - self.camera_y

        # Render based on entity type
        if isinstance(entity, Paddle):
            # Render paddle as rectangle
            paddle_rect = pygame.Rect(
                screen_x - entity.width // 2,
                screen_y - entity.height // 2,
                entity.width,
                entity.height
            )
            pygame.draw.rect(self._screen, entity.color, paddle_rect)

            # Add border
            pygame.draw.rect(self._screen, (200, 200, 200), paddle_rect, 2)

            # Render paddle trail
            for i, (trail_x, trail_y) in enumerate(entity.trail_positions):
                alpha = (i + 1) / len(entity.trail_positions) * 0.3
                trail_color = (int(entity.color[0] * alpha), int(entity.color[1] * alpha), int(entity.color[2] * alpha))
                trail_rect = pygame.Rect(
                    x + trail_x - entity.width // 2,
                    y + trail_y - entity.height // 2,
                    entity.width,
                    entity.height
                )
                if alpha > 0.1:  # Only draw visible trail
                    pygame.draw.rect(self._screen, trail_color, trail_rect)

        elif isinstance(entity, Ball):
            # Render ball as circle
            pygame.draw.circle(self._screen, entity.ball_color or self.ball_color, (int(screen_x), int(screen_y)), entity.radius)

            # Add ball outline
            pygame.draw.circle(self._screen, (255, 255, 255), (int(screen_x), int(screen_y)), entity.radius, 2)

            # Render ball trail
            for i, (trail_x, trail_y) in enumerate(entity.trail_positions):
                if i % 3 == 0:  # Sparse trail for performance
                    alpha = (i + 1) / len(entity.trail_positions) * 0.6
                    trail_color = (int(255 * alpha), int(100 * alpha), int(100 * alpha))
                    trail_radius = int(entity.radius * (0.3 + alpha * 0.7))
                    pygame.draw.circle(self._screen, trail_color, (int(x + trail_x), int(y + trail_y)), trail_radius)

        elif isinstance(entity, ParticleSystem):
            # Render particles
            for particle in entity.particles:
                if particle['lifetime'] > 0:
                    alpha = particle['lifetime'] / particle['max_lifetime']
                    particle_color = tuple(int(c * alpha) for c in particle['color'])
                    pygame.draw.circle(self._screen, particle_color, (int(particle['x']), int(particle['y'])), 3)

    def _render_entities_from_simulation(self):
        """Render game entities from the Pong app."""
        if not self._pygame or not setattr:
            return

        # Get the main game app
        game_app = self.entity

        if not game_app:
            return

        # Render paddles
        if hasattr(game_app, 'paddle1'):
            self._render_entity_visual(game_app.paddle1, self.width // 2, self.height // 2)
        if hasattr(game_app, 'paddle2'):
            self._render_entity_visual(game_app.paddle2, self.width // 2, self.height // 2)
        if hasattr(game_app, 'ball'):
            self._render_entity_visual(game_app.ball, self.width // 2, self.height // 2)

        # Render particles
        if hasattr(game_app, 'particles'):
            for particle_system in game_app.particles:
                self._render_entity_visual(particle_system, self.width // 2, self.height // 2)

    def _draw_grid(self):
        """Override grid to draw Pong-specific elements."""
        pygame = self._pygame

        # Draw center line
        center_line_color = (100, 100, 100)
        line_segments = self.height // 40  # Number of line segments
        segment_height = self.height // line_segments

        for i in range(line_segments):
            if i % 2 == 0:  # Draw every other segment
                pygame.draw.rect(self._screen, center_line_color,
                                (self.width // 2 - 2, i * segment_height,
                                 4, segment_height - 5))

    def _render_overlays(self):
        """Render Pong-specific overlays."""
        if not self._screen or not hasattr(self, '_pygame'):
            return

        pygame = self._pygame
        game_app = self.entity

        # Initialize fonts if not done
        if not self.font:
            try:
                pygame.font.init()
                self.font = pygame.font.SysFont('Monospace', 24, bold=True)
                self.score_font = pygame.font.SysFont('Monospace', 48, bold=True)
            except:
                return

        # Render scores
        if game_app and hasattr(game_app, 'paddle1') and hasattr(game_app, 'paddle2'):
            score_text = self.score_font.render(
                f"{game_app.paddle1.score}  -  {game_app.paddle2.score}",
                True, (255, 255, 255)
            )
            self._screen.blit(score_text, (self.width // 2 - score_text.get_width() // 2, 20))

        # Render game status
        if game_app:
            if hasattr(game_app, 'paused') and game_app.paused:
                pause_text = self.font.render("PAUSED - Press SPACE to Resume", True, (255, 200, 0))
                self._screen.blit(pause_text, (self.width // 2 - pause_text.get_width() // 2, self.height // 2 - 50))

            if hasattr(game_app, 'winner') and game_app.winner:
                winner_text = self.score_font.render(
                    f"PLAYER {game_app.winner} WINS!",
                    True, (202, 225, 255)
                )
                self._screen.blit(winner_text, (self.width // 2 - winner_text.get_width() // 2, self.height // 2))

        # Render controls help
        y_offset = self.height - 120
        help_lines = [
            "Controls:",
            "Player 1: W (up), S (down)",
            "Player 2: ↑ (up), ↓ (down)",
            "SPACE: Pause/Resume, R: Reset Game, ESC: Quit"
        ]

        for line in help_lines:
            help_text = self.font.render(line, True, (150, 150, 150))
            self._screen.blit(help_text, (10, y_offset))
            y_offset += 20


def create_pong_demo():
    """Create and configure a Pong game demo."""
    print("🎮 UCore Framework - Pong Game Demo")
    print("=" * 50)

    app = PongGame()

    return app


async def main():
    """Main demo function."""
    try:
        # Create and start the game
        pong_app = create_pong_demo()
        await pong_app.start()

        print("\n🎯 GAME STARTED!")
        print("🎮 Controls:")
        print("  Player 1: W (up), S (down)")
        print("  Player 2: ↑ (up), ↓ (down)")
        print("  SPACE: Pause/Resume")
        print("  R: Reset Game")
        print("  ESC: Quit")
        print("\n📊 Monitoring:")
        print("  Metrics: http://localhost:9090")
        print("  Redis Events: Available if Redis is running")

        # Game loop
        last_time = asyncio.get_running_loop().time()

        while pong_app.running:
            current_time = asyncio.get_running_loop().time()
            delta_time = current_time - last_time
            last_time = current_time

            if delta_time > 0:
                await pong_app.aupdate()

            # Control loop frequency
            await asyncio.sleep(1.0 / 120.0)  # 120 Hz update rate

    except KeyboardInterrupt:
        print("\n🎮 GAME INTERRUPTED")
    except Exception as e:
        print(f"❌ GAME ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n🏁 CLEANING UP...")

        # Cleanup
        if 'pong_app' in locals():
            await pong_app.stop()

        print("✨ SHUTDOWN COMPLETE")


if __name__ == "__main__":
    print("🏗️ STARTING UCORE PONG GAME...")
    print("This demo showcases UCore's Entity/Controller architecture,")
    print("RenderController visualization, physics simulation,")
    print("metrics collection, and event-driven messaging!")

    # Check for optional dependencies
    try:
        import pygame
        pygame_available = True
    except ImportError:
        pygame_available = False

    try:
        import redis
        redis_available = True
    except ImportError:
        redis_available = False

    print("\n⚠️  DEPENDENCIES STATUS:")
    print(f"  Pygame: {'✅ Available' if pygame_available else '❌ Not available - install with pip install pygame'}")
    print(f"  Redis: {'✅ Available' if redis_available else '⚠️ Optional - for event streaming'}")

    if not pygame_available:
        print("\n❌ Pygame is required to run this game!")
        print("Install with: pip install pygame")
        exit(1)

    print("\n🚀 LAUNCHING GAME...")

    try:
        asyncio.run(main())
    except RuntimeError as e:
        print(f"❌ Asyncio Error: {e}")
        print("Try running with Python 3.7+ and the latest version of the framework.")
