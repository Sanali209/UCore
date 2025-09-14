# framework/simulation/controllers.py
import random
import time
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any, List
from io import BytesIO

from .controller import EntityController

# Exports for easy importing
__all__ = [
    'ScreenCapturer',
    'RenderController',
    'Transform',
    'BotAgent'
]

class ScreenCapturer(EntityController):
    """
    A controller that captures screenshots of the screen or specific regions
    at configurable intervals using mss and pyautogui libraries.

    Features:
    - Full screen capture
    - Region-based capture with configurable coordinates
    - Configurable capture frequency
    - Image storage in memory or to disk
    - Base64 encoded output for server communication
    - Performance monitoring and frame rate control
    """

    def __init__(
        self,
        capture_region: Optional[Tuple[int, int, int, int]] = None,
        capture_interval: float = 1.0,  # seconds between captures
        store_on_disk: bool = False,
        storage_path: str = "screenshots",
        max_screenshots: int = 100,
        format: str = "PNG",
        quality: int = 85
    ):
        """
        Initialize the screen capturer.

        Args:
            capture_region: (x, y, width, height) region to capture. None for full screen.
            capture_interval: Time between captures in seconds
            store_on_disk: Whether to save screenshots to disk
            storage_path: Path to save screenshots if store_on_disk=True
            max_screenshots: Maximum number of screenshots to keep in memory
            format: Image format (PNG, JPEG, etc.)
            quality: Image quality for formats that support it (1-100)
        """
        super().__init__()

        # Capture configuration
        self.capture_region = capture_region
        self.capture_interval = capture_interval
        self.store_on_disk = store_on_disk
        self.storage_path = Path(storage_path)
        self.format = format.upper()
        self.quality = quality

        # State tracking
        self.captures: List[Dict[str, Any]] = []
        self.max_screenshots = max_screenshots
        self.last_capture_time = 0
        self.capture_count = 0

        # Screen capture libraries
        self._mss = None
        self._pyautogui = None
        self._initialized = False

    def start(self):
        """Initialize screen capture libraries and create storage directory if needed."""
        super().start()

        try:
            # Try to import mss first (faster)
            from mss import mss
            self._mss = mss()
            self.entity.logger.info("🖼️ ScreenCapturer initialized with MSS library")
        except ImportError:
            try:
                # Fall back to pyautogui
                import pyautogui
                self._pyautogui = pyautogui
                self.entity.logger.info("🖼️ ScreenCapturer initialized with PyAutoGUI library")
            except ImportError:
                raise RuntimeError(
                    "ScreenCapturer requires either 'mss' or 'pyautogui' library. "
                    "Install with: pip install mss or pip install pyautogui"
                )

        if self.store_on_disk and self.storage_path:
            self.storage_path.mkdir(parents=True, exist_ok=True)
            self.entity.logger.info(f"📁 ScreenCapturer storage: {self.storage_path.absolute()}")

        self._initialized = True
        self.entity.logger.info(f"🎥 ScreenCapturer started - interval: {self.capture_interval}s, region: {self.capture_region}")

    def stop(self):
        """Clean up resources."""
        if self._mss:
            self._mss.close()

        if self.store_on_disk and self.storage_path.exists():
            # Optional: cleanup old screenshots
            pass

        self._initialized = False
        self.entity.logger.info("🛑 ScreenCapturer stopped")
        super().stop()

    def update(self, delta_time: float):
        """Check if it's time to capture a screenshot and do so if needed."""
        if not self._initialized:
            return

        current_time = time.time()
        if current_time - self.last_capture_time >= self.capture_interval:
            self._capture_screenshot()
            self.last_capture_time = current_time

    def _capture_screenshot(self):
        """Capture a screenshot using the configured method."""
        try:
            if self._mss:
                screenshot_data = self._capture_with_mss()
            elif self._pyautogui:
                screenshot_data = self._capture_with_pyautogui()
            else:
                return

            if screenshot_data:
                self._store_capture(screenshot_data)

        except Exception as e:
            self.entity.logger.error(f"❌ Screenshot capture failed: {e}")

    def _capture_with_mss(self):
        """Capture screenshot using MSS library."""
        with self._mss as sct:
            if self.capture_region:
                # Region capture
                x, y, width, height = self.capture_region
                monitor = {
                    "top": y,
                    "left": x,
                    "width": width,
                    "height": height
                }
                screenshot = sct.grab(monitor)
            else:
                # Full screen capture (use first monitor)
                screenshot = sct.grab(sct.monitors[0])

            # Convert to PIL Image for consistent processing
            from PIL import Image
            img = Image.frombytes("RGB", (screenshot.width, screenshot.height), screenshot.bgra, "raw", "BGRX")
            return img

    def _capture_with_pyautogui(self):
        """Capture screenshot using PyAutoGUI library."""
        if self.capture_region:
            # Region capture
            x, y, width, height = self.capture_region
            screenshot = self._pyautogui.screenshot(region=(x, y, width, height))
        else:
            # Full screen capture
            screenshot = self._pyautogui.screenshot()

        return screenshot

    def _store_capture(self, image):
        """Store the captured screenshot with metadata."""
        self.capture_count += 1

        # Prepare metadata
        timestamp = datetime.now()
        filename = f"screenshot_{self.capture_count:06d}_{timestamp.strftime('%Y%m%d_%H%M%S')}.{self.format.lower()}"

        # Convert to base64 for storage
        buffer = BytesIO()
        if self.format == "JPEG":
            image.save(buffer, format=self.format, quality=self.quality)
        else:
            image.save(buffer, format=self.format)

        image_data = buffer.getvalue()
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Create capture record
        capture = {
            'id': self.capture_count,
            'timestamp': timestamp.isoformat(),
            'format': self.format,
            'size': len(image_data),
            'width': image.width,
            'height': image.height,
            'region': self.capture_region,
            'base64_data': image_base64
        }

        # Store in memory
        self.captures.append(capture)

        # Keep only the most recent screenshots
        if len(self.captures) > self.max_screenshots:
            removed = self.captures.pop(0)
            if self.store_on_disk and removed.get('file_path'):
                Path(removed['file_path']).unlink(missing_ok=True)

        # Optionally save to disk
        if self.store_on_disk and self.storage_path:
            file_path = self.storage_path / filename
            image.save(file_path, quality=self.quality)
            capture['file_path'] = str(file_path)
            self.entity.logger.debug(f"💾 Screenshot saved: {file_path}")

        self.entity.logger.debug(f"📸 Screenshot captured: #{self.capture_count} ({image.width}x{image.height})")

    def get_latest_capture(self) -> Optional[Dict[str, Any]]:
        """Get the most recent screenshot capture."""
        return self.captures[-1] if self.captures else None

    def get_all_captures(self) -> List[Dict[str, Any]]:
        """Get all stored screenshot captures."""
        return self.captures.copy()

    def clear_captures(self):
        """Clear all stored screenshots from memory and disk."""
        if self.store_on_disk:
            for capture in self.captures:
                if capture.get('file_path'):
                    Path(capture['file_path']).unlink(missing_ok=True)

        self.captures.clear()
        self.capture_count = 0
        self.entity.logger.info("🗑️ All screenshots cleared")

    def set_capture_region(self, region: Optional[Tuple[int, int, int, int]]):
        """Change the capture region at runtime."""
        self.capture_region = region
        self.entity.logger.info(f"🎯 Capture region changed to: {region}")

    def set_capture_interval(self, interval: float):
        """Change the capture interval at runtime."""
        self.capture_interval = interval
        self.last_capture_time = time.time()  # Reset timer
        self.entity.logger.info(f"📏 Capture interval changed to: {interval:.2f}s")

    def get_stats(self) -> Dict[str, Any]:
        """Get capture statistics."""
        total_size = sum(capture['size'] for capture in self.captures)
        avg_size = total_size / len(self.captures) if self.captures else 0

        oldest_timestamp = min((c['timestamp'] for c in self.captures), default=None)
        newest_timestamp = max((c['timestamp'] for c in self.captures), default=None)

        return {
            'total_captures': self.capture_count,
            'stored_captures': len(self.captures),
            'total_size_bytes': total_size,
            'average_size_bytes': avg_size,
            'oldest_capture': oldest_timestamp,
            'newest_capture': newest_timestamp,
            'capture_method': 'MSS' if self._mss else 'PyAutoGUI' if self._pyautogui else 'None',
            'storage_path': str(self.storage_path) if self.store_on_disk else None
        }

    def __repr__(self):
        return f"<ScreenCapturer(count={self.capture_count}, region={self.capture_region}, interval={self.capture_interval}s)>"

class RenderController(EntityController):
    """
    A controller that renders/visualizes simulation state using Pygame.
    Provides real-time visualization of entities, their properties, and interactions.

    Features:
    - Real-time 2D rendering of entities
    - Customizable entity visualization (colors, shapes, sizes)
    - Interactive visualization controls
    - Performance monitoring and statistics overlay
    - Save/load visual state
    - Flexible camera/viewport controls
    - Entity property visualization
    """

    def __init__(
        self,
        width: int = 800,
        height: int = 600,
        fps: int = 60,
        background_color: Tuple[int, int, int] = (25, 25, 25),
        show_grid: bool = True,
        grid_size: int = 20,
        window_title: str = "UCore Simulation Renderer"
    ):
        """
        Initialize the pygame renderer.

        Args:
            width: Window width in pixels
            height: Window height in pixels
            fps: Target frames per second
            background_color: RGB background color tuple
            show_grid: Whether to show coordinate grid
            grid_size: Size of grid squares in pixels
            window_title: Window title
        """
        super().__init__()

        # Window configuration
        self.width = width
        self.height = height
        self.fps = fps
        self.background_color = background_color
        self.window_title = window_title

        # Grid configuration
        self.show_grid = show_grid
        self.grid_size = grid_size

        # Pygame state
        self._pygame = None
        self._screen = None
        self._clock = None
        self._font = None
        self._initialized = False

        # Camera/viewport settings
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0

        # Rendering configuration
        self.entity_colors = {
            'default': (100, 150, 255),
            'Transform': (255, 100, 100),
            'BotAgent': (100, 255, 100),
            'ScreenCapturer': (255, 255, 100)
        }

        # Performance tracking
        self.frame_count = 0
        self.last_fps = 0
        self.show_fps = True
        self.show_stats = True

        # Entity visual cache
        self.entity_positions: Dict[int, Tuple[float, float]] = {}

    def start(self):
        """Initialize Pygame and create the rendering window."""
        super().start()

        try:
            # Import pygame
            import pygame
            self._pygame = pygame

            # Initialize pygame
            pygame.init()

            # Create window
            self._screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(self.window_title)

            # Create clock for FPS control
            self._clock = pygame.time.Clock()

            # Initialize fonts (with fallback)
            try:
                pygame.font.init()
                self._font = pygame.font.SysFont('Monospace', 14, bold=True)
            except:
                # Fallback font
                self._font = pygame.font.Font(None, 24)

            self._initialized = True
            self.entity.logger.info("🎨 RenderController initialized with Pygame")
            self.entity.logger.info(f"🖥️ Window: {self.width}x{self.height} @ {self.fps} FPS")

        except ImportError:
            raise RuntimeError(
                "RenderController requires pygame. Install with: pip install pygame"
            )
        except Exception as e:
            self.entity.logger.error(f"❌ RenderController initialization failed: {e}")
            self._cleanup_pygame()
            raise

    def stop(self):
        """Clean up Pygame resources."""
        self._cleanup_pygame()
        self._initialized = False
        self.entity.logger.info("🛑 RenderController stopped")
        super().stop()

    def _cleanup_pygame(self):
        """Clean up pygame resources."""
        if self._pygame:
            pygame = self._pygame
            pygame.quit()

        self._pygame = None
        self._screen = None
        self._clock = None
        self._font = None

    def update(self, delta_time: float):
        """Update the renderer and handle events."""
        if not self._initialized:
            return

        try:
            # Handle events
            self._handle_events()

            # Update FPS counter
            self.frame_count += 1

            # Render frame
            self._render_frame()

            # Control frame rate
            self._clock.tick(self.fps)

        except Exception as e:
            self.entity.logger.error(f"❌ RenderController update failed: {e}")

    def _handle_events(self):
        """Handle Pygame events."""
        if not self._pygame:
            return

        pygame = self._pygame
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                # Signal to exit (handle in main loop)
                self.entity.logger.info("🔄 Window close requested")
            elif event.type == pygame.KEYDOWN:
                self._handle_key_events(event.key)

        # Check for continuous key presses
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.camera_x -= 5
        if keys[pygame.K_RIGHT]:
            self.camera_x += 5
        if keys[pygame.K_UP]:
            self.camera_y -= 5
        if keys[pygame.K_DOWN]:
            self.camera_y += 5

    def _handle_key_events(self, key):
        """Handle discrete key events."""
        if not self._pygame:
            return

        pygame = self._pygame

        if key == pygame.K_SPACE:
            # Reset camera position
            self.camera_x = 0
            self.camera_y = 0
            self.zoom = 1.0
            self.entity.logger.info("📍 Camera reset to origin")
        elif key == pygame.K_g:
            # Toggle grid
            self.show_grid = not self.show_grid
            status = "enabled" if self.show_grid else "disabled"
            self.entity.logger.info(f"🎯 Grid {status}")
        elif key == pygame.K_f:
            # Toggle FPS display
            self.show_fps = not self.show_fps
        elif key == pygame.K_s:
            # Toggle stats overlay
            self.show_stats = not self.show_stats

    def _render_frame(self):
        """Render a complete frame."""
        if not self._screen or not self._pygame:
            return

        pygame = self._pygame

        # Clear screen
        self._screen.fill(self.background_color)

        # Draw grid
        if self.show_grid:
            self._draw_grid()

        # Render all entities in the simulation
        if hasattr(self.entity, '_simulation'):  # If this is attached to a simulation manager
            self._render_entities_from_simulation()
        else:
            # Render this entity and its children
            self._render_entity_tree()

        # Render UI overlays
        self._render_overlays()

        # Update display
        pygame.display.flip()

    def _draw_grid(self):
        """Draw a coordinate grid."""
        if not self._screen:
            return

        grid_color = (50, 50, 50)

        # Vertical lines
        for x in range(0, self.width, self.grid_size):
            pygame = self._pygame
            pygame.draw.line(self._screen, grid_color, (x, 0), (x, self.height))

        # Horizontal lines
        for y in range(0, self.height, self.grid_size):
            pygame.draw.line(self._screen, grid_color, (0, y), (self.width, y))

        # Axis lines (make them thicker)
        axis_color = (80, 80, 80)

        # Center X and Y axes (adjusted for camera)
        center_x = self.width // 2 - self.camera_x
        center_y = self.height // 2 - self.camera_y

        pygame.draw.line(self._screen, axis_color, (0, center_y), (self.width, center_y), 2)
        pygame.draw.line(self._screen, axis_color, (center_x, 0), (center_x, self.height), 2)

    def _render_entities_from_simulation(self):
        """Render entities from a simulation manager."""
        # This would render entities from a simulation context
        # For now, just show a placeholder
        pass

    def _render_entity_tree(self):
        """Render the entity tree starting from the attached entity."""
        # Get the root entity (simulation manager if available)
        root_entity = self.entity

        # For now, render a simple visual representation
        self._render_entity_visual(root_entity, self.width // 2, self.height // 2)

    def _render_entity_visual(self, entity, x: float, y: float):
        """Render a visual representation of an entity."""
        if not self._screen:
            return

        # Get entity type and color
        entity_type = type(entity).__name__
        color = self.entity_colors.get(entity_type, self.entity_colors['default'])

        # Render based on entity type
        if hasattr(entity, 'x') and hasattr(entity, 'y'):
            # Entity with transform
            screen_x = x + entity.x * self.zoom + self.grid_size
            screen_y = y + entity.y * self.zoom + self.grid_size

            # Draw entity as a circle
            radius = max(5, min(20, self.grid_size // 3))
            pygame = self._pygame
            pygame.draw.circle(self._screen, color, (int(screen_x), int(screen_y)), radius)

            # Draw entity type label
            if self._font:
                label = f"{entity_type}"
                text_surface = self._font.render(label, True, (255, 255, 255))
                text_rect = text_surface.get_rect(center=(int(screen_x), int(screen_y + radius + 15)))
                self._screen.blit(text_surface, text_rect)

        # Store entity position for statistics
        self.entity_positions[id(entity)] = (x, y)

    def _render_overlays(self):
        """Render UI overlays (FPS, stats, etc.)."""
        if not self._screen or not self._font:
            return

        pygame = self._pygame

        # Render FPS
        if self.show_fps:
            if self.frame_count % 10 == 0:  # Update every 10 frames
                self.last_fps = self._clock.get_fps()

            fps_text = self._font.render(f"FPS: {self.last_fps:.1f}", True, (255, 255, 255))
            self._screen.blit(fps_text, (10, 10))

        # Render stats
        if self.show_stats:
            y_offset = 40

            # Entity count
            entity_count = len(self.entity_positions)
            count_text = self._font.render(f"Entities: {entity_count}", True, (200, 200, 200))
            self._screen.blit(count_text, (10, y_offset))

            # Camera position
            y_offset += 20
            camera_text = self._font.render(
                f"Camera: ({self.camera_x}, {self.camera_y}) Z:{self.zoom:.1f}",
                True, (200, 200, 200)
            )
            self._screen.blit(camera_text, (10, y_offset))

            # Instructions
            y_offset = self.height - 100
            instructions = [
                "Arrow Keys: Move camera",
                "Space: Reset view",
                "G: Toggle grid",
                "F: Toggle FPS",
                "S: Toggle stats"
            ]

            for instruction in instructions:
                instr_text = self._font.render(instruction, True, (150, 150, 150))
                self._screen.blit(instr_text, (10, y_offset))
                y_offset += 15

    def get_window_dimensions(self) -> Tuple[int, int]:
        """Get the window dimensions."""
        return (self.width, self.height)

    def set_camera(self, x: float, y: float, zoom: float = None):
        """Set camera position and optionally zoom level."""
        self.camera_x = x
        self.camera_y = y
        if zoom is not None:
            self.zoom = zoom

    def reset_view(self):
        """Reset camera to default position."""
        self.camera_x = 0
        self.camera_y = 0
        self.zoom = 1.0

    def add_entity_color(self, entity_type: str, color: Tuple[int, int, int]):
        """Add custom color mapping for entity types."""
        self.entity_colors[entity_type] = color

    def get_entity_color(self, entity_type: str) -> Tuple[int, int, int]:
        """Get color for entity type."""
        return self.entity_colors.get(entity_type, self.entity_colors['default'])

    def get_render_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics."""
        return {
            'frame_count': self.frame_count,
            'fps': self.last_fps,
            'resolution': (self.width, self.height),
            'entity_count': len(self.entity_positions),
            'camera_position': (self.camera_x, self.camera_y),
            'zoom': self.zoom,
            'show_grid': self.show_grid,
            'show_fps': self.show_fps,
            'show_stats': self.show_stats
        }

    def save_screenshot(self, filename: str):
        """Save current screen as an image."""
        if self._pygame and self._screen:
            pygame.image.save(self._screen, filename)
            self.entity.logger.info(f"📸 Screenshot saved: {filename}")

    def __repr__(self):
        return f"<RenderController({self.width}x{self.height}, fps={self.fps})>"

class Transform(EntityController):
    """
    Manages an entity's position and rotation in 2D space.
    """
    def __init__(self, x: float = 0.0, y: float = 0.0, rotation: float = 0.0):
        super().__init__()
        self.x = x
        self.y = y
        self.rotation = rotation

    def __repr__(self):
        return f"<Transform(x={self.x}, y={self.y}, rot={self.rotation})>"

class BotAgent(EntityController):
    """
    A simple AI agent that can perform actions.
    This is a basic placeholder for more complex AI behaviors.
    """
    def __init__(self, action_space: list = None):
        super().__init__()
        self.action_space = action_space or ['move_forward', 'turn_left', 'turn_right', 'idle']

    def get_action(self) -> str:
        """
        Returns a random action from the available action space.
        """
        return random.choice(self.action_space)

    def update(self, delta_time: float):
        """
        Example of how an agent might decide on an action periodically.
        In a real scenario, this would be driven by more complex logic.
        """
        # For demonstration, we're not doing anything in the update loop.
        # The action would be requested by another system (e.g., a simulation runner).
        pass

    def __repr__(self):
        return f"<BotAgent(actions={len(self.action_space)})>"
