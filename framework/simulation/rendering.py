"""
Enhanced Rendering System for UCore Simulation Framework
========================================================

Advanced rendering capabilities providing computer vision overlays,
real-time monitoring dashboards, performance visualization, and debug tools.

Rendering Components:
- OpenCVRenderer: Computer vision overlay rendering and annotations
- SimulationDashboard: Real-time metrics and status monitoring UI
- PerformanceVisualizer: Frame rates, latency graphs, bottleneck analysis
- DebugRenderer: Developer introspection and debugging visualization
- SceneRenderer: Unified scene management and rendering coordination
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable, Tuple, Type
from dataclasses import dataclass, field
from enum import Enum
import time
import math
import threading
from queue import Queue
import numpy as np
import cv2

from .entity import EnvironmentEntity
from .sensors import SensorData
from .io_modules import IOData, ProcessingResult
from .controllers import Transform, RenderController


class RenderLayer(Enum):
    """Rendering layer order for overlay management."""
    BACKGROUND = 0
    SCENE = 1
    ENTITIES = 2
    SENSORS = 3
    COMPUTER_VISION = 4
    DEBUG = 5
    UI_OVERLAY = 6
    PERFORMANCE_MONITOR = 7


class RenderFormat(Enum):
    """Supported rendering output formats."""
    PYGAME_SURFACE = "pygame_surface"
    OPENCV_FRAME = "opencv_frame"
    NUMPY_ARRAY = "numpy_array"
    BASE64_JPEG = "base64_jpeg"
    WINDOW_DISPLAY = "window_display"


class VisualizationMode(Enum):
    """Different visualization modes for debugging."""
    NORMAL = "normal"
    WIREFRAME = "wireframe"
    COLLISION_BOXES = "collision_boxes"
    SENSORS = "sensors"
    PERFORMANCE = "performance"
    HEATMAP = "heatmap"
    PATHFINDING = "pathfinding"
    STATE_DEBUG = "state_debug"


@dataclass
class RenderFrame:
    """Container for frame rendering data."""
    frame_data: Any
    format: RenderFormat
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    layers: Dict[RenderLayer, Any] = field(default_factory=dict)

    def add_layer(self, layer: RenderLayer, data: Any):
        """Add a rendering layer to the frame."""
        self.layers[layer] = data

    def get_layer(self, layer: RenderLayer) -> Any:
        """Get rendering data for a specific layer."""
        return self.layers.get(layer)


class OpenCVRenderer:
    """
    Computer vision-enhanced renderer using OpenCV.

    Provides advanced rendering capabilities with computer vision overlays:
    - Object detection bounding boxes and labels
    - Facial landmark visualization
    - Text overlay rendering
    - Gesture trail effects
    - Color analysis visualizations
    """

    def __init__(self, width: int = 1280, height: int = 720, fps: int = 30):
        self.width = width
        self.height = height
        self.fps = fps

        # Rendering configuration
        self.output_format = RenderFormat.OPENCV_FRAME
        self.background_color = (0, 0, 0)  # Black background

        # Visualization settings
        self.show_bounding_boxes = True
        self.show_labels = True
        self.show_landmarks = True
        self.show_trajectories = True
        self.annotation_color = (0, 255, 0)  # Green annotations
        self.text_color = (255, 255, 255)  # White text
        self.font_scale = 0.7
        self.thickness = 2

        # Performance tracking
        self.frame_count = 0
        self.render_times: List[float] = []
        self.max_timing_history = 100

        # OpenCV window (if used)
        self.window_name = "UCore Simulation - OpenCV Renderer"
        self.window_created = False

    def create_frame(self) -> RenderFrame:
        """Create a new blank frame."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (self.width, self.height), self.background_color, -1)

        return RenderFrame(
            frame_data=frame,
            format=self.output_format,
            metadata={"width": self.width, "height": self.height, "fps": self.fps}
        )

    def render_object_detection(self, frame: RenderFrame, detections: List[Dict[str, Any]]):
        """Render object detection results as overlays."""
        if not self.show_bounding_boxes:
            return

        for detection in detections:
            bbox = detection.get('bbox', [])
            name = detection.get('name', 'unknown')
            confidence = detection.get('confidence', 0.0)

            if len(bbox) >= 4:
                x1, y1, x2, y2 = map(int, bbox[:4])

                # Draw bounding box
                cv2.rectangle(frame.frame_data, (x1, y1), (x2, y2), self.annotation_color, self.thickness)

                # Draw label if enabled
                if self.show_labels:
                    label = f"{name}: {confidence:.2f}"
                    self._draw_text_with_background(frame.frame_data, label, (x1, max(y1-5, 10)))

    def render_face_analysis(self, frame: RenderFrame, faces: List[Dict[str, Any]]):
        """Render facial analysis results."""
        if not self.show_bounding_boxes:
            return

        for face in faces:
            bbox = face.get('bbox', [])
            emotions = face.get('emotions', {})
            age_range = face.get('age_range', '')
            gender = face.get('gender', '')

            if len(bbox) >= 4:
                x1, y1, x2, y2 = map(int, bbox[:4])

                # Draw face bounding box
                cv2.rectangle(frame.frame_data, (x1, y1), (x2, y2), (255, 0, 0), self.thickness)  # Red for faces

                # Draw facial landmarks if available
                if self.show_landmarks:
                    landmarks = face.get('landmarks', {})
                    self._draw_landmarks(frame.frame_data, landmarks)

                # Draw emotion overlay
                if emotions:
                    best_emotion = max(emotions.items(), key=lambda x: x[1])
                    emotion_text = f"{best_emotion[0]}: {best_emotion[1]:.2f}"

                    # Position below face box
                    text_x, text_y = x1, y2 + 20
                    self._draw_text_with_background(frame.frame_data, emotion_text, (text_x, text_y))

                    # Additional info
                    info_text = f"{age_range}, {gender}"
                    self._draw_text_with_background(frame.frame_data, info_text, (text_x, text_y + 25))

    def render_gesture_trails(self, frame: RenderFrame, gesture_data: List[Tuple[int, int, float]]):
        """Render gesture trails and trajectories."""
        if not self.show_trajectories or len(gesture_data) < 2:
            return

        # Draw gesture trail
        points = np.array([(x, y) for x, y, _ in gesture_data], dtype=np.int32).reshape((-1, 1, 2))
        cv2.polylines(frame.frame_data, [points], False, (0, 255, 255), 3)  # Yellow trail

        # Draw trail dots with fading
        alpha = 1.0
        alpha_step = 1.0 / len(gesture_data)

        for i, (x, y, timestamp) in enumerate(reversed(gesture_data)):
            alpha = max(0.1, 1.0 - (i * alpha_step))
            color = tuple(int(c * alpha) for c in (0, 255, 255))  # Fading yellow
            cv2.circle(frame.frame_data, (x, y), 3, color, -1)

    def render_text_overlay(self, frame: RenderFrame, text: str, position: Tuple[int, int] = (10, 30)):
        """Render text overlay on the frame."""
        self._draw_text_with_background(frame.frame_data, text, position)

    def render_performance_overlay(self, frame: RenderFrame, fps: float, render_time: float):
        """Render performance metrics overlay."""
        perf_text = f"FPS: {fps:.1f} | Render: {render_time:.2f}ms"
        self.render_text_overlay(frame, perf_text, (self.width - 250, 30))

    def render_simulation_state(self, frame: RenderFrame, state_data: Dict[str, Any]):
        """Render simulation state information."""
        y_offset = 60

        # Entity count
        entity_count = state_data.get('entity_count', 0)
        self._draw_text_with_background(frame.frame_data, f"Entities: {entity_count}", (10, y_offset))

        # Sensor detections
        active_sensors = state_data.get('active_sensors', 0)
        self._draw_text_with_background(frame.frame_data, f"Active Sensors: {active_sensors}", (10, y_offset + 25))

        # Time information
        sim_time = state_data.get('simulation_time', 0)
        real_time = time.time()
        self._draw_text_with_background(frame.frame_data, f"Time: {sim_time:.1f}s", (10, y_offset + 50))

    def show_frame(self, frame: RenderFrame):
        """Display frame in OpenCV window."""
        if not self.window_created:
            cv2.namedWindow(self.window_name, cv2.WINDOW_NORMAL)
            cv2.resizeWindow(self.window_name, self.width, self.height)
            self.window_created = True

        cv2.imshow(self.window_name, frame.frame_data)
        cv2.waitKey(1)  # Allow window to update

    def save_frame(self, frame: RenderFrame, filepath: str):
        """Save frame to file."""
        success = cv2.imwrite(filepath, frame.frame_data)
        if not success:
            print(f"⚠️ Failed to save frame to {filepath}")
        return success

    def _draw_text_with_background(self, frame: np.ndarray, text: str, position: Tuple[int, int]):
        """Draw text with background rectangle for visibility."""
        (text_width, text_height), baseline = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, self.font_scale, 1)

        # Draw background rectangle
        x, y = position
        cv2.rectangle(frame, (x - 5, y - text_height - 5),
                     (x + text_width + 5, y + baseline + 5), (0, 0, 0), -1)

        # Draw text
        cv2.putText(frame, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX,
                   self.font_scale, self.text_color, 1, cv2.LINE_AA)

    def _draw_landmarks(self, frame: np.ndarray, landmarks: Dict[str, Any]):
        """Draw facial landmarks."""
        # Draw eyes
        eyes = landmarks.get('eyes', [])
        for eye in eyes:
            if len(eye) >= 2:
                cv2.circle(frame, tuple(map(int, eye)), 3, (0, 255, 0), -1)

        # Draw nose
        nose = landmarks.get('nose', [])
        if len(nose) >= 2:
            cv2.circle(frame, tuple(map(int, nose)), 3, (255, 0, 0), -1)

        # Draw mouth
        mouth = landmarks.get('mouth', [])
        if len(mouth) >= 2:
            cv2.circle(frame, tuple(map(int, mouth)), 3, (0, 0, 255), -1)

    def get_render_stats(self) -> Dict[str, Any]:
        """Get rendering performance statistics."""
        avg_render_time = sum(self.render_times) / max(1, len(self.render_times)) if self.render_times else 0

        return {
            "frames_rendered": self.frame_count,
            "avg_render_time": avg_render_time,
            "peak_render_time": max(self.render_times) if self.render_times else 0,
            "resolution": f"{self.width}x{self.height}",
            "target_fps": self.fps
        }


class SimulationDashboard:
    """
    Real-time simulation monitoring dashboard.

    Provides comprehensive visualization of simulation state:
    - Entity counts and status
    - Sensor activity monitoring
    - Action queue status
    - Performance metrics
    - System health indicators
    """

    def __init__(self, width: int = 800, height: int = 600, update_interval: float = 0.5):
        self.width = width
        self.height = height
        self.update_interval = update_interval

        # Dashboard state
        self.last_update = 0.0
        self.metrics_history: Dict[str, List[Tuple[float, Any]]] = {}
        self.max_history_points = 100

        # Layout configuration
        self.margin = 20
        self.panel_spacing = 10
        self.font_family = cv2.FONT_HERSHEY_SIMPLEX
        self.font_scale = 0.6
        self.header_color = (255, 255, 255)  # White headers
        self.text_color = (220, 220, 220)   # Light gray text
        self.warning_color = (0, 255, 255)   # Yellow warnings
        self.error_color = (0, 0, 255)       # Red errors

        # Panel configurations
        self.panels: Dict[str, Dict[str, Any]] = {}
        self._setup_panels()

    def _setup_panels(self):
        """Set up dashboard panel layout."""
        panel_height = 150
        panel_width = (self.width - 3 * self.margin) // 2

        self.panels = {
            "entities": {
                "title": "Entity Status",
                "position": (self.margin, self.margin),
                "size": (panel_width, panel_height),
                "metrics": ["entity_count", "active_entities", "static_entities", "interactive_entities"]
            },
            "sensors": {
                "title": "Sensor Activity",
                "position": (self.margin + panel_width + self.panel_spacing, self.margin),
                "size": (panel_width, panel_height),
                "metrics": ["vision_detections", "audio_detections", "tactile_contacts", "active_sensors"]
            },
            "actions": {
                "title": "Action System",
                "position": (self.margin, self.margin + panel_height + self.panel_spacing),
                "size": (panel_width, panel_height),
                "metrics": ["queued_actions", "running_actions", "completed_actions", "failed_actions"]
            },
            "performance": {
                "title": "Performance Metrics",
                "position": (self.margin + panel_width + self.panel_spacing,
                           self.margin + panel_height + self.panel_spacing),
                "size": (panel_width, panel_height),
                "metrics": ["fps", "frame_time", "memory_usage", "cpu_usage"]
            }
        }

    def update_metrics(self, metrics: Dict[str, Any]):
        """Update dashboard with new metrics."""
        current_time = time.time()

        # Store metrics in history
        for key, value in metrics.items():
            if key not in self.metrics_history:
                self.metrics_history[key] = []

            self.metrics_history[key].append((current_time, value))

            # Keep history size manageable
            if len(self.metrics_history[key]) > self.max_history_points:
                self.metrics_history[key].pop(0)

    def render_dashboard(self, frame: RenderFrame) -> RenderFrame:
        """Render the complete dashboard on a frame."""
        dashboard_frame = self.create_dashboard_frame()

        # Draw each panel
        for panel_name, panel_config in self.panels.items():
            self._render_panel(dashboard_frame, panel_name, panel_config)

        return dashboard_frame

    def create_dashboard_frame(self) -> RenderFrame:
        """Create a new dashboard frame."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (self.width, self.height), (10, 10, 30), -1)  # Dark blue background

        return RenderFrame(
            frame_data=frame,
            format=RenderFormat.OPENCV_FRAME,
            metadata={"dashboard": True, "width": self.width, "height": self.height}
        )

    def _render_panel(self, frame: RenderFrame, panel_name: str, panel_config: Dict[str, Any]):
        """Render a single dashboard panel."""
        x, y = panel_config["position"]
        w, h = panel_config["size"]
        title = panel_config["title"]
        metrics = panel_config["metrics"]

        # Panel background
        cv2.rectangle(frame.frame_data, (x, y), (x + w, y + h), (20, 20, 50), -1)
        cv2.rectangle(frame.frame_data, (x, y), (x + w, y + h), (100, 100, 150), 2)

        # Panel title
        title_size = cv2.getTextSize(title, self.font_family, self.font_scale * 1.2, 2)[0]
        title_x = x + (w - title_size[0]) // 2
        cv2.putText(frame.frame_data, title, (title_x, y + 25),
                   self.font_family, self.font_scale * 1.2, self.header_color, 2)

        # Panel metrics
        metric_y = y + 50
        for metric_name in metrics:
            if metric_name in self.metrics_history and self.metrics_history[metric_name]:
                _, latest_value = self.metrics_history[metric_name][-1]

                # Format metric display
                display_name = metric_name.replace('_', ' ').title()
                display_value = self._format_metric_value(latest_value)

                metric_text = f"{display_name}: {display_value}"
                cv2.putText(frame.frame_data, metric_text, (x + 10, metric_y),
                           self.font_family, self.font_scale, self.text_color, 1)

                metric_y += 20

    def _format_metric_value(self, value: Any) -> str:
        """Format metric values for display."""
        if isinstance(value, float):
            if value < 1.0:
                return f"{value:.3f}"
            elif value < 10.0:
                return f"{value:.2f}"
            else:
                return f"{value:.1f}"
        elif isinstance(value, int):
            return f"{value:,}"
        else:
            return str(value)

    def get_dashboard_snapshot(self) -> Dict[str, Any]:
        """Get current dashboard state snapshot."""
        snapshot = {}

        for metric_name, history in self.metrics_history.items():
            if history:
                snapshot[metric_name] = history[-1][1]  # Latest value

        return snapshot


class PerformanceVisualizer:
    """
    Performance metrics visualization with graphs and charts.

    Provides real-time visualization of:
    - Frame rate and frame time graphs
    - Memory usage over time
    - CPU usage monitoring
    - Sensor update latencies
    - Action execution times
    """

    def __init__(self, width: int = 1024, height: int = 768):
        self.width = width
        self.height = height

        # Graph configuration
        self.graph_margin = 60
        self.graph_width = self.width - 2 * self.graph_margin
        self.graph_height = (self.height - 3 * self.graph_margin) // 3

        # Colors for different metrics
        self.colors = {
            "fps": (0, 255, 0),        # Green for FPS
            "frame_time": (255, 0, 0), # Red for frame time
            "memory": (0, 0, 255),     # Blue for memory
            "cpu": (255, 255, 0),      # Yellow for CPU
        }

        # Performance history
        self.performance_history: Dict[str, List[Tuple[float, float]]] = {}
        self.max_data_points = 200
        self.history_seconds = 30.0  # Show last 30 seconds

    def update_performance_data(self, data: Dict[str, float]):
        """Update performance data for visualization."""
        current_time = time.time()

        for metric_name, value in data.items():
            if metric_name not in self.performance_history:
                self.performance_history[metric_name] = []

            self.performance_history[metric_name].append((current_time, value))

            # Remove old data points
            cutoff_time = current_time - self.history_seconds
            self.performance_history[metric_name] = [
                (t, v) for t, v in self.performance_history[metric_name]
                if t >= cutoff_time
            ]

    def render_performance_charts(self, frame: RenderFrame) -> RenderFrame:
        """Render performance visualization charts."""
        perf_frame = self.create_performance_frame()

        # Draw each performance metric chart
        chart_y = self.graph_margin

        chart_configs = [
            ("fps", "FPS", 0, 120, chart_y),
            ("frame_time", "Frame Time (ms)", 0, 50, chart_y + self.graph_height + self.graph_margin),
            ("memory", "Memory (MB)", 0, 1024, chart_y + 2 * (self.graph_height + self.graph_margin)),
        ]

        for metric_name, label, min_val, max_val, y_pos in chart_configs:
            self._render_metric_chart(perf_frame, metric_name, label, min_val, max_val, y_pos)

        return perf_frame

    def create_performance_frame(self) -> RenderFrame:
        """Create a performance visualization frame."""
        frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        cv2.rectangle(frame, (0, 0), (self.width, self.height), (5, 15, 25), -1)  # Dark blue-gray background

        return RenderFrame(
            frame_data=frame,
            format=RenderFormat.OPENCV_FRAME,
            metadata={"performance_viz": True, "graphs": ["fps", "frame_time", "memory"]}
        )

    def _render_metric_chart(self, frame: RenderFrame, metric_name: str, label: str,
                           min_val: float, max_val: float, y_pos: int):
        """Render a single performance metric chart."""
        # Chart background
        chart_bg_color = (15, 15, 40)
        cv2.rectangle(frame.frame_data,
                     (self.graph_margin - 10, y_pos - 10),
                     (self.graph_margin + self.graph_width + 10, y_pos + self.graph_height + 40),
                     chart_bg_color, -1)
        cv2.rectangle(frame.frame_data,
                     (self.graph_margin - 10, y_pos - 10),
                     (self.graph_margin + self.graph_width + 10, y_pos + self.graph_height + 40),
                     (80, 80, 120), 2)

        # Chart title
        cv2.putText(frame.frame_data, label,
                   (self.graph_margin, y_pos - 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        # Get data for this metric
        data = self.performance_history.get(metric_name, [])
        if not data:
            return

        # Draw grid lines and labels
        self._draw_chart_grid(frame.frame_data, min_val, max_val, self.graph_margin, y_pos, self.graph_width, self.graph_height)

        # Scale data points
        points = self._scale_data_points(data, min_val, max_val, self.graph_margin, y_pos, self.graph_width, self.graph_height)

        # Draw data line
        if len(points) > 1:
            color = self.colors.get(metric_name, (255, 255, 255))
            for i in range(1, len(points)):
                cv2.line(frame.frame_data, points[i-1], points[i], color, 2)

        # Draw current value
        if data:
            current_value = data[-1][1]
            current_text = f"Current: {current_value:.2f}"
            cv2.putText(frame.frame_data, current_text,
                       (self.graph_margin + self.graph_width - 150, y_pos + self.graph_height + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)

    def _draw_chart_grid(self, frame: np.ndarray, min_val: float, max_val: float,
                        x: int, y: int, width: int, height: int):
        """Draw chart grid lines and labels."""
        # Horizontal grid lines
        for i in range(5):
            line_y = y + height - (i * height // 4)
            grid_value = min_val + (max_val - min_val) * i / 4

            # Grid line
            cv2.line(frame, (x, line_y), (x + width, line_y), (60, 60, 80), 1)

            # Value label
            cv2.putText(frame, f"{grid_value:.0f}", (x - 40, line_y + 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

        # Vertical time indicators
        current_time = time.time()
        for i in range(4):
            time_offset = i * self.history_seconds / 3
            line_x = x + width - (i * width // 3)
            time_label = f"-{time_offset:.1f}s"

            cv2.line(frame, (line_x, y), (line_x, y + height), (60, 60, 80), 1)
            cv2.putText(frame, time_label, (line_x - 20, y + height + 15),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.4, (150, 150, 150), 1)

    def _scale_data_points(self, data: List[Tuple[float, float]], min_val: float, max_val: float,
                          x: int, y: int, width: int, height: int) -> List[Tuple[int, int]]:
        """Scale data points to chart coordinates."""
        points = []

        if not data or max_val <= min_val:
            return points

        current_time = time.time()
        time_range = self.history_seconds

        for timestamp, value in data:
            # Scale X (time)
            time_offset = current_time - timestamp
            x_pos = x + width - int((time_offset / time_range) * width)
            x_pos = max(x, min(x + width, x_pos))

            # Scale Y (value)
            normalized_value = (value - min_val) / (max_val - min_val)
            y_pos = y + height - int(normalized_value * height)
            y_pos = max(y, min(y + height, y_pos))

            points.append((x_pos, y_pos))

        return points


class DebugRenderer:
    """
    Developer debugging visualization tools.

    Provides comprehensive debugging visualizations:
    - Entity bounding boxes and identifiers
    - Sensor range visualization
    - Action queue status
    - Collision detection overlays
    - Pathfinding visualization
    - State machine debugging
    """

    def __init__(self, visualize_mode: VisualizationMode = VisualizationMode.NORMAL):
        self.visualize_mode = visualize_mode

        # Debug visualization settings
        self.show_entity_ids = True
        self.show_bounding_boxes = True
        self.show_sensor_ranges = True
        self.show_collision_shapes = True
        self.show_paths = True
        self.show_state_info = True

        # Colors for different debug elements
        self.colors = {
            "entity_bbox": (255, 255, 255),  # White for entities
            "sensor_range": (0, 255, 0),     # Green for sensors
            "collision": (255, 0, 0),        # Red for collisions
            "path": (0, 255, 255),           # Yellow for paths
            "selected": (0, 0, 255),         # Blue for selection
        }

        # Entity selection for debugging
        self.selected_entity_id: Optional[str] = None

    def render_debug_overlay(self, frame: RenderFrame, debug_data: Dict[str, Any]) -> RenderFrame:
        """Render debug visualization overlay."""

        if self.visualize_mode == VisualizationMode.NORMAL:
            return frame

        # Apply different visualization modes
        if self.visualize_mode == VisualizationMode.WIREFRAME:
            self._render_wireframe_view(frame, debug_data)
        elif self.visualize_mode == VisualizationMode.COLLISION_BOXES:
            self._render_collision_boxes(frame, debug_data)
        elif self.visualize_mode == VisualizationMode.SENSORS:
            self._render_sensor_visualization(frame, debug_data)
        elif self.visualize_mode == VisualizationMode.PERFORMANCE:
            self._render_performance_debug(frame, debug_data)
        elif self.visualize_mode == VisualizationMode.HEATMAP:
            self._render_heatmap_overlay(frame, debug_data)
        elif self.visualize_mode == VisualizationMode.PATHFINDING:
            self._render_pathfinding_debug(frame, debug_data)
        elif self.visualize_mode == VisualizationMode.STATE_DEBUG:
            self._render_state_machine_debug(frame, debug_data)

        return frame

    def _render_wireframe_view(self, frame: RenderFrame, debug_data: Dict[str, Any]):
        """Render wireframe view showing entity outlines."""
        entities = debug_data.get('entities', [])

        for entity in entities:
            self._draw_entity_wireframe(frame.frame_data, entity)

    def _render_collision_boxes(self, frame: RenderFrame, debug_data: Dict[str, Any]):
        """Render collision bounding boxes."""
        entities = debug_data.get('entities', [])

        for entity in entities:
            transform = entity.get_controller(Transform) if hasattr(entity, 'get_controller') else None
            if transform:
                # Draw collision box (assuming 32x32 for simplicity)
                half_w, half_h = 16, 16
                x1 = int(transform.x - half_w)
                y1 = int(transform.y - half_h)
                x2 = int(transform.x + half_w)
                y2 = int(transform.y + half_h)

                cv2.rectangle(frame.frame_data, (x1, y1), (x2, y2), self.colors["collision"], 2)

                # Draw entity ID
                if self.show_entity_ids:
                    cv2.putText(frame.frame_data, str(entity.name), (x1, y1 - 5),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors["entity_bbox"], 1)

    def _render_sensor_visualization(self, frame: RenderFrame, debug_data: Dict[str, Any]):
        """Render sensor range visualizations."""
        entities = debug_data.get('entities', [])

        for entity in entities:
            if hasattr(entity, 'sensor_manager'):
                sensor_manager = entity.sensor_manager
                for sensor_name, sensor in sensor_manager.sensors.items():
                    self._draw_sensor_range(frame.frame_data, entity, sensor)

    def _render_performance_debug(self, frame: RenderFrame, debug_data: Dict[str, Any]):
        """Render performance debugging information."""
        perf_metrics = debug_data.get('performance', {})

        y_offset = 50
        for key, value in perf_metrics.items():
            text = f"{key}: {value}"
            cv2.putText(frame.frame_data, text, (10, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
            y_offset += 25

    def _render_heatmap_overlay(self, frame: RenderFrame, debug_data: Dict[str, Any]):
        """Render activity heatmap overlay."""
        activity_data = debug_data.get('activity_heatmap', {})

        # Create heatmap overlay (simplified)
        if activity_data:
            overlay = np.zeros_like(frame.frame_data, dtype=np.uint8)

            # Draw activity regions
            for region, intensity in activity_data.items():
                # Simplified heatmap rendering
                pass

            # Blend with original frame
            alpha = 0.3
            cv2.addWeighted(overlay, alpha, frame.frame_data, 1 - alpha, 0, frame.frame_data)

    def _render_pathfinding_debug(self, frame: RenderFrame, debug_data: Dict[str, Any]):
        """Render pathfinding visualization."""
        path_data = debug_data.get('paths', [])

        for path_info in path_data:
            waypoints = path_info.get('waypoints', [])
            if len(waypoints) > 1:
                # Draw path lines
                for i in range(1, len(waypoints)):
                    p1 = tuple(map(int, waypoints[i-1]))
                    p2 = tuple(map(int, waypoints[i]))
                    cv2.line(frame.frame_data, p1, p2, self.colors["path"], 3)

                # Draw waypoints
                for waypoint in waypoints:
                    center = tuple(map(int, waypoint))
                    cv2.circle(frame.frame_data, center, 5, self.colors["path"], -1)

    def _render_state_machine_debug(self, frame: RenderFrame, debug_data: Dict[str, Any]):
        """Render state machine debug information."""
        entities = debug_data.get('entities', [])

        for entity in entities:
            if hasattr(entity, 'state_machine') and entity.state_machine:
                self._draw_state_info(frame.frame_data, entity)

    def _draw_entity_wireframe(self, frame: np.ndarray, entity: EnvironmentEntity):
        """Draw wireframe representation of entity."""
        transform = entity.get_controller(Transform) if hasattr(entity, 'get_controller') else None
        if not transform:
            return

        # Simple wireframe representation (cube)
        size = 20
        x, y = int(transform.x), int(transform.y)

        # Draw wireframe cube
        points = [
            (x - size, y - size), (x + size, y - size),
            (x + size, y + size), (x - size, y + size)
        ]

        # Draw edges
        for i in range(4):
            p1 = points[i]
            p2 = points[(i + 1) % 4]
            cv2.line(frame, p1, p2, self.colors["entity_bbox"], 1)

    def _draw_sensor_range(self, frame: np.ndarray, entity: EnvironmentEntity, sensor):
        """Draw sensor range visualization."""
        transform = entity.get_controller(Transform) if hasattr(entity, 'get_controller') else None
        if not transform:
            return

        center = (int(transform.x), int(transform.y))
        radius = int(sensor.detection_range)

        # Draw sensor range circle
        cv2.circle(frame, center, radius, self.colors["sensor_range"], 2)

        # Draw sensor type label
        sensor_type = sensor.sensor_type.value.upper()
        cv2.putText(frame, sensor_type, (center[0] - 30, center[1] + radius + 15),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, self.colors["sensor_range"], 1)

    def _draw_state_info(self, frame: np.ndarray, entity: EnvironmentEntity):
        """Draw state machine information for entity."""
        transform = entity.get_controller(Transform) if hasattr(entity, 'get_controller') else None
        if not transform or not hasattr(entity, 'state_machine'):
            return

        current_state = entity.state_machine.current_state.name if entity.state_machine.current_state else "IDLE"

        x, y = int(transform.x), int(transform.y)
        cv2.putText(frame, f"[{current_state}]", (x - 20, y - 25),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)

    def set_visualization_mode(self, mode: VisualizationMode):
        """Set the current visualization mode."""
        self.visualize_mode = mode
        print(f"🔍 Debug visualization mode set to: {mode.value}")

    def select_entity(self, entity_id: str):
        """Select an entity for detailed debugging."""
        self.selected_entity_id = entity_id

    def get_debug_info(self) -> Dict[str, Any]:
        """Get current debug configuration."""
        return {
            "visualization_mode": self.visualize_mode.value,
            "selected_entity": self.selected_entity_id,
            "show_options": {
                "entity_ids": self.show_entity_ids,
                "bounding_boxes": self.show_bounding_boxes,
                "sensor_ranges": self.show_sensor_ranges,
                "collision_shapes": self.show_collision_shapes,
                "paths": self.show_paths,
                "state_info": self.show_state_info
            }
        }


class SceneRenderer:
    """
    Unified scene rendering coordinator.

    Manages multiple rendering backends and composes final output:
    - Coordinates between different renderers
    - Manages rendering layers and order
    - Handles multiple output formats
    - Provides rendering performance monitoring
    """

    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height

        # Rendering backends
        self.opencv_renderer = OpenCVRenderer(width, height)
        self.dashboard = SimulationDashboard(800, 600)
        self.performance_viz = PerformanceVisualizer(1024, 768)
        self.debug_renderer = DebugRenderer()

        # Output management
        self.output_queues: Dict[str, Queue] = {}
        self.render_thread: Optional[threading.Thread] = None
        self.rendering_active = False
        self.target_fps = 30.0
        self.frame_interval = 1.0 / self.target_fps

        # Scene state
        self.registered_entities: List[EnvironmentEntity] = []
        self.scene_metrics: Dict[str, Any] = {}
        self.last_frame_time = time.time()

    def register_entity(self, entity: EnvironmentEntity):
        """Register an entity for rendering."""
        if entity not in self.registered_entities:
            self.registered_entities.append(entity)
            print(f"🎨 Entity '{entity.name}' registered for rendering")

    def unregister_entity(self, entity: EnvironmentEntity):
        """Unregister an entity from rendering."""
        if entity in self.registered_entities:
            self.registered_entities.remove(entity)
            print(f"🎨 Entity '{entity.name}' unregistered from rendering")

    def start_rendering(self):
        """Start async rendering loop."""
        if self.rendering_active:
            return

        self.rendering_active = True
        self.render_thread = threading.Thread(target=self._rendering_loop, daemon=True)
        self.render_thread.start()
        print("🎨 Scene rendering started")

    def stop_rendering(self):
        """Stop rendering loop."""
        self.rendering_active = False
        if self.render_thread:
            self.render_thread.join(timeout=2.0)
        print("🎨 Scene rendering stopped")

    def render_frame(self, output_format: RenderFormat = RenderFormat.OPENCV_FRAME) -> Optional[RenderFrame]:
        """Render a complete frame with all layers."""
        start_time = time.time()

        # Create base frame
        frame = self.opencv_renderer.create_frame()

        # Render entity layers
        self._render_entity_layers(frame)

        # Render debug overlay if enabled
        debug_data = self._collect_debug_data()
        frame = self.debug_renderer.render_debug_overlay(frame, debug_data)

        # Add performance overlay
        fps = 1.0 / max(0.001, time.time() - self.last_frame_time)
        render_time = (time.time() - start_time) * 1000  # ms
        self.opencv_renderer.render_performance_overlay(frame, fps, render_time)

        # Add simulation state overlay
        self.opencv_renderer.render_simulation_state(frame, self.scene_metrics)

        self.last_frame_time = time.time()

        # Convert output format if needed
        return self._convert_frame_format(frame, output_format)

    def _rendering_loop(self):
        """Main rendering loop."""
        while self.rendering_active:
            frame_start = time.time()

            # Render frame
            frame = self.render_frame()

            # Queue frame for output
            for queue_name, queue in self.output_queues.items():
                try:
                    queue.put(frame, timeout=0.1)
                except:
                    pass  # Queue full, skip

            # Maintain target FPS
            frame_time = time.time() - frame_start
            sleep_time = max(0, self.frame_interval - frame_time)
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _render_entity_layers(self, frame: RenderFrame):
        """Render all entity layers."""
        # Group entities by render layer
        layer_entities = {}
        for entity in self.registered_entities:
            layer = self._get_entity_render_layer(entity)
            if layer not in layer_entities:
                layer_entities[layer] = []
            layer_entities[layer].append(entity)

        # Render layers in order
        for layer in [RenderLayer.BACKGROUND, RenderLayer.ENTITIES, RenderLayer.SENSORS,
                     RenderLayer.DEBUG, RenderLayer.UI_OVERLAY]:
            entities_in_layer = layer_entities.get(layer, [])
            self._render_layer_entities(frame, layer, entities_in_layer)

    def _render_layer_entities(self, frame: RenderFrame, layer: RenderLayer, entities: List[EnvironmentEntity]):
        """Render entities in a specific layer."""
        for entity in entities:
            if layer == RenderLayer.ENTITY:
                self._render_entity_sprite(frame, entity)
            elif layer == RenderLayer.SENSORS:
                self._render_entity_sensors(frame, entity)
            elif layer == RenderLayer.DEBUG:
                self._render_entity_debug(frame, entity)

    def _render_entity_sprite(self, frame: RenderFrame, entity: EnvironmentEntity):
        """Render entity sprite/visual representation."""
        transform = entity.get_controller(Transform) if hasattr(entity, 'get_controller') else None
        if not transform:
            return

        # Simple colored rectangle representation
        size = 20
        color = self._get_entity_color(entity)
        x1 = int(transform.x - size // 2)
        y1 = int(transform.y - size // 2)
        x2 = int(transform.x + size // 2)
        y2 = int(transform.y + size // 2)

        cv2.rectangle(frame.frame_data, (x1, y1), (x2, y2), color, -1)
        cv2.rectangle(frame.frame_data, (x1, y1), (x2, y2), (255, 255, 255), 1)

    def _render_entity_sensors(self, frame: RenderFrame, entity: EnvironmentEntity):
        """Render entity sensor visualizations."""
        if not hasattr(entity, 'sensor_manager') or not entity.sensor_manager:
            return

        if self.debug_renderer.visualize_mode == VisualizationMode.SENSORS:
            debug_data = {'entities': [entity]}
            self.debug_renderer._render_sensor_visualization(frame, debug_data)

    def _render_entity_debug(self, frame: RenderFrame, entity: EnvironmentEntity):
        """Render entity debug information."""
        if self.debug_renderer.visualize_mode != VisualizationMode.NORMAL:
            debug_data = {'entities': [entity]}
            self.debug_renderer.render_debug_overlay(frame, debug_data)

    def _get_entity_render_layer(self, entity: EnvironmentEntity) -> RenderLayer:
        """Determine which render layer an entity belongs to."""
        if hasattr(entity, 'render_layer'):
            return entity.render_layer
        return RenderLayer.ENTITY

    def _get_entity_color(self, entity: EnvironmentEntity) -> Tuple[int, int, int]:
        """Get rendering color for entity."""
        entity_colors = {
            'Pawn': (0, 255, 0),      # Green for player characters
            'BotAgent': (255, 0, 0),  # Red for AI agents
            'StaticEntity': (128, 128, 128),  # Gray for static objects
            'InteractiveEntity': (0, 255, 255),  # Yellow for interactive objects
            'CameraEntity': (255, 0, 255),     # Magenta for cameras
        }

        entity_type = type(entity).__name__
        return entity_colors.get(entity_type, (255, 255, 255))  # White default

    def _collect_debug_data(self) -> Dict[str, Any]:
        """Collect debug data for visualization."""
        return {
            'entities': self.registered_entities,
            'performance': self._get_performance_metrics(),
            'activity_heatmap': {},
            'paths': []
        }

    def _get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        # This would integrate with actual performance monitoring
        return {
            'fps': self.target_fps,
            'entity_count': len(self.registered_entities),
            'render_time': 16.7,  # ~60fps
        }

    def _convert_frame_format(self, frame: RenderFrame, target_format: RenderFormat) -> RenderFrame:
        """Convert frame to target format."""
        if frame.format == target_format:
            return frame

        # For now, only handle basic conversions
        # Real implementation would handle JPEG encoding, etc.
        frame.format = target_format
        return frame

    def create_output_queue(self, name: str, max_size: int = 30):
        """Create an output queue for rendered frames."""
        self.output_queues[name] = Queue(maxsize=max_size)

    def get_output_queue(self, name: str) -> Optional[Queue]:
        """Get an output queue by name."""
        return self.output_queues.get(name)

    def update_scene_metrics(self, metrics: Dict[str, Any]):
        """Update scene-wide metrics for display."""
        self.scene_metrics.update(metrics)

    def get_rendering_stats(self) -> Dict[str, Any]:
        """Get comprehensive rendering statistics."""
        stats = {
            "active_renderers": bool(self.rendering_active),
            "registered_entities": len(self.registered_entities),
            "target_fps": self.target_fps,
            "output_queues": len(self.output_queues),
            "scene_metrics": self.scene_metrics.copy()
        }

        # Add individual renderer stats
        stats["opencv_stats"] = self.opencv_renderer.get_render_stats()
        stats["dashboard_snapshot"] = self.dashboard.get_dashboard_snapshot()
        stats["debug_config"] = self.debug_renderer.get_debug_info()

        return stats

# ===== EXPORTS =====

__all__ = [
    'RenderLayer',
    'RenderFormat',
    'VisualizationMode',
    'RenderFrame',
    'OpenCVRenderer',
    'SimulationDashboard',
    'PerformanceVisualizer',
    'DebugRenderer',
    'SceneRenderer'
]
