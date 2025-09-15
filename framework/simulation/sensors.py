"""
Sensor System for UCore Simulation Framework
===========================================

Perception and sensing system enabling entities to detect and respond to
environmental stimuli, other entities, and dynamic events.

Sensor Types:
- Vision Sensor: Line-of-sight and visual perception
- Audio Sensor: Sound detection and propagation
- Tactile Sensor: Physical contact and collision detection
- Environmental Sensor: Weather, temperature, and ambient conditions
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable, Type, Tuple, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
import time
import math
from collections import defaultdict

from .entity import EnvironmentEntity
from .controllers import Transform


class SensorType(Enum):
    """Types of sensors available in the system."""
    VISION = "vision"
    AUDIO = "audio"
    TACTILE = "tactile"
    ENVIRONMENTAL = "environmental"
    PROXIMITY = "proximity"
    MOTION = "motion"


class SensorMode(Enum):
    """Operational modes for sensors."""
    PASSIVE = "passive"  # Always-on background sensing
    ACTIVE = "active"    # Trigger-based sensing
    INTERMITTENT = "intermittent"  # Periodic sensing
    EVENT_DRIVEN = "event_driven"  # Respond to specific events


@dataclass
class SensorData:
    """Container for sensor detection results."""
    sensor_type: SensorType
    entity_id: str
    target_id: Optional[str] = None
    position: Optional[Tuple[float, float]] = None
    distance: float = 0.0
    strength: float = 1.0  # Signal strength (0.0 to 1.0)
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def is_relevant(self, max_age: float = 1.0) -> bool:
        """Check if sensor data is still relevant."""
        return time.time() - self.timestamp <= max_age

    def __repr__(self):
        target = f"→{self.target_id}" if self.target_id else ""
        return f"<SensorData({self.sensor_type.value}, {self.entity_id}{target}, d={self.distance:.1f}, s={self.strength:.2f})>"


class SensorEvent:
    """Event triggered by sensor detection."""

    def __init__(self, event_type: str, sensor_entity: EnvironmentEntity,
                 sensor_data: SensorData, metadata: Optional[Dict[str, Any]] = None):
        self.event_type = event_type  # "entity_detected", "sound_heard", etc.
        self.sensor_entity = sensor_entity
        self.sensor_data = sensor_data
        self.metadata = metadata if metadata is not None else {}
        self.timestamp = time.time()

    def __repr__(self):
        return f"<SensorEvent({self.event_type}, {self.sensor_entity.name}, {self.sensor_data})>"


class BaseSensor(ABC):
    """
    Abstract base class for all sensor types.

    Sensors provide perception capabilities to entities, allowing them to
    detect and respond to their environment and other entities.
    """

    def __init__(self, sensor_type: SensorType, mode: SensorMode = SensorMode.ACTIVE,
                 detection_range: float = 50.0, update_interval: float = 0.1,
                 enabled: bool = True):
        self.sensor_type = sensor_type
        self.mode = mode
        self.detection_range = detection_range
        self.update_interval = update_interval
        self.enabled = enabled

        # Entity and timing
        self.entity: Optional[EnvironmentEntity] = None
        self.last_update = 0.0

        # Detection state
        self.detected_entities: Dict[str, SensorData] = {}
        self.last_detections: List[SensorData] = []
        self.max_detections_history = 100

        # Callbacks
        self.on_detection: Optional[Callable[[SensorEvent], None]] = None
        self.on_loss: Optional[Callable[[SensorEvent], None]] = None

        # Performance tracking
        self.update_count = 0
        self.avg_update_time = 0.0
        self.total_detections = 0

    def attach_to_entity(self, entity: EnvironmentEntity):
        """Attach this sensor to an entity."""
        self.entity = entity
        sensor_type_name = self.sensor_type.value.capitalize()
        print(f"📡 {sensor_type_name} sensor attached to {entity.name}")

    def update(self, delta_time: float) -> List[SensorEvent]:
        """Update sensor and get detection events."""
        if not self.enabled or not self.entity:
            return []

        current_time = time.time()
        if current_time - self.last_update < self.update_interval:
            return []

        start_time = time.time()
        self.last_update = current_time

        # Perform sensor-specific detection
        events = self._detect_impl(delta_time)

        # Update performance metrics
        update_time = time.time() - start_time
        self.update_count += 1
        self.avg_update_time = (self.avg_update_time * (self.update_count - 1) + update_time) / self.update_count

        return events

    @abstractmethod
    def _detect_impl(self, delta_time: float) -> List[SensorEvent]:
        """Implementation of sensor detection logic."""
        pass

    def get_detected_entities(self) -> List[SensorData]:
        """Get currently detected entities."""
        return list(self.detected_entities.values())

    def is_entity_detected(self, entity_id: str) -> bool:
        """Check if an entity is currently being detected."""
        return entity_id in self.detected_entities

    def get_entity_data(self, entity_id: str) -> Optional[SensorData]:
        """Get detection data for a specific entity."""
        return self.detected_entities.get(entity_id)

    def clear_detections(self):
        """Clear all current detections."""
        self.detected_entities.clear()

    def set_detection_range(self, range_: float):
        """Change detection range."""
        self.detection_range = max(0.0, range_)
        print(f"📏 {self.sensor_type.value.capitalize()} sensor range set to {self.detection_range}")

    def set_enabled(self, enabled: bool):
        """Enable or disable the sensor."""
        self.enabled = enabled
        status = "enabled" if enabled else "disabled"
        print(f"📡 {self.sensor_type.value.capitalize()} sensor {status}")

    def _calculate_distance(self, entity1: EnvironmentEntity, entity2: EnvironmentEntity) -> float:
        """Calculate distance between two entities."""
        transform1 = entity1.get_controller(Transform)
        transform2 = entity2.get_controller(Transform)

        if transform1 and transform2:
            dx = transform2.x - transform1.x
            dy = transform2.y - transform1.y
            return math.sqrt(dx*dx + dy*dy)

        return float('inf')

    def _calculate_strength(self, distance: float) -> float:
        """Calculate signal strength based on distance."""
        if distance >= self.detection_range:
            return 0.0
        elif distance <= 0:
            return 1.0
        else:
            # Linear falloff
            return 1.0 - (distance / self.detection_range)

    def _add_detection(self, entity_id: str, sensor_data: SensorData):
        """Add or update entity detection."""
        was_detected = entity_id in self.detected_entities
        self.detected_entities[entity_id] = sensor_data

        # Add to history
        self.last_detections.append(sensor_data)
        if len(self.last_detections) > self.max_detections_history:
            self.last_detections.pop(0)

        self.total_detections += 1

        # Trigger callback if newly detected
        if not was_detected and self.on_detection and self.entity:
            event = SensorEvent("entity_detected", self.entity, sensor_data)
            self.on_detection(event)

    def _remove_detection(self, entity_id: str):
        """Remove entity detection."""
        if entity_id in self.detected_entities:
            sensor_data = self.detected_entities[entity_id]
            del self.detected_entities[entity_id]

            # Trigger callback
            if self.on_loss:
                event = SensorEvent("entity_lost", self.entity, sensor_data)
                self.on_loss(event)

    def get_statistics(self) -> Dict[str, Any]:
        """Get sensor performance statistics."""
        return {
            "sensor_type": self.sensor_type.value,
            "enabled": self.enabled,
            "detection_range": self.detection_range,
            "update_interval": self.update_interval,
            "update_count": self.update_count,
            "avg_update_time": self.avg_update_time,
            "current_detections": len(self.detected_entities),
            "total_detections": self.total_detections,
            "mode": self.mode.value
        }

    def __repr__(self):
        detections = len(self.detected_entities)
        return f"<{self.__class__.__name__}(range={self.detection_range}, detections={detections})>"


class VisionSensor(BaseSensor):
    """
    Sensor for visual perception and line-of-sight detection.

    Provides:
    - Line-of-sight calculations
    - Vision cones and angles
    - Occlusion detection
    - Distance-based visibility
    """

    def __init__(self, field_of_view: float = 120.0,  # degrees
                 max_distance: float = 100.0, facing_angle: float = 0.0, **kwargs):
        super().__init__(SensorType.VISION, **kwargs)
        self.field_of_view = field_of_view  # Viewing angle in degrees
        self.max_distance = max_distance
        self.facing_angle = facing_angle  # Direction entity is facing
        self.half_fov = field_of_view / 2.0

        # Vision cone in radians
        self.fov_radians = math.radians(field_of_view)
        self.half_fov_radians = math.radians(self.half_fov)

        # Detection parameters
        self.detect_entities = True
        self.detect_static_objects = True
        self.require_line_of_sight = True
        self.occlusion_radius = 5.0  # Size of occluding objects

    def _detect_impl(self, delta_time: float) -> List[SensorEvent]:
        """Perform vision-based detection."""
        if not self.entity:
            return []

        events = []
        entity_transform = self.entity.get_controller(Transform)
        if not entity_transform:
            return events

        # Get all potential targets (simulated - would be provided by scene manager)
        # For now, we'll assume access to scene entities
        targets = self._get_potential_targets()

        for target in targets:
            target_transform = target.get_controller(Transform)
            if not target_transform or target == self.entity:
                continue

            # Calculate distance
            dx = target_transform.x - entity_transform.x
            dy = target_transform.y - entity_transform.y
            distance = math.sqrt(dx*dx + dy*dy)

            # Check distance range
            if distance > self.max_distance or distance > self.detection_range:
                self._remove_detection(target.name)
                continue

            # Check field of view
            if not self._is_in_field_of_view(dx, dy, distance):
                self._remove_detection(target.name)
                continue

            # Check line of sight (simplified)
            if self.require_line_of_sight and self._is_occluded(target):
                self._remove_detection(target.name)
                continue

            # Calculate signal strength
            strength = self._calculate_strength(distance)

            # Create detection data
            sensor_data = SensorData(
                sensor_type=SensorType.VISION,
                entity_id=self.entity.name,
                target_id=target.name,
                position=(target_transform.x, target_transform.y),
                distance=distance,
                strength=strength,
                data={
                    "visible": True,
                    "in_fov": True,
                    "line_of_sight": not self.require_line_of_sight or not self._is_occluded(target),
                    "angle_to_target": math.degrees(math.atan2(dy, dx))
                }
            )

            self._add_detection(target.name, sensor_data)
            events.append(SensorEvent("entity_visible", self.entity, sensor_data))

        return events

    def _is_in_field_of_view(self, dx: float, dy: float, distance: float) -> bool:
        """Check if target is within field of view."""
        if distance == 0:
            return True

        # Calculate angle to target
        target_angle = math.atan2(dy, dx)
        facing_angle = math.radians(self.facing_angle)

        # Normalize angles
        angle_diff = math.fabs(target_angle - facing_angle)
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi

        return abs(angle_diff) <= self.half_fov_radians

    def _is_occluded(self, target: EnvironmentEntity) -> bool:
        """Check if line of sight to target is blocked."""
        # Simplified occlusion check - would use ray tracing in full implementation
        # For now, assume no occlusion unless very close to occluding objects
        return False

    def _get_potential_targets(self) -> List[EnvironmentEntity]:
        """Get entities that could potentially be seen."""
        # This would normally query the scene manager for entities in range
        # For demonstration, return empty list (would be implemented with scene integration)
        return []

    def set_field_of_view(self, fov_degrees: float):
        """Set field of view in degrees."""
        self.field_of_view = max(1.0, min(360.0, fov_degrees))
        self.half_fov = self.field_of_view / 2.0
        self.fov_radians = math.radians(self.field_of_view)
        self.half_fov_radians = math.radians(self.half_fov)

    def set_facing_angle(self, angle_degrees: float):
        """Set the direction the sensor is facing."""
        self.facing_angle = angle_degrees

    def get_visible_entities(self) -> Dict[str, SensorData]:
        """Get all currently visible entities."""
        return self.detected_entities.copy()


class AudioSensor(BaseSensor):
    """
    Sensor for auditory detection and sound propagation.

    Provides:
    - Sound source localization
    - Volume-based detection
    - Echo/sound reflection simulation
    - Frequency filtering
    """

    def __init__(self, hearing_range: float = 75.0, sensitivity: float = 1.0,
                 frequency_range: Tuple[float, float] = (20.0, 20000.0), **kwargs):
        super().__init__(SensorType.AUDIO, **kwargs)
        self.hearing_range = hearing_range
        self.sensitivity = sensitivity  # Multiplier for detection effectiveness
        self.frequency_range = frequency_range  # Min/max frequencies that can be heard

        # Detection parameters
        self.detect_sounds = True
        self.detect_entities = False  # Whether to detect entity movements/speech
        self.volume_threshold = 0.1   # Minimum volume to detect

        # Environmental factors
        self.background_noise = 0.0   # Ambient noise level
        self.echo_enabled = True      # Simulate sound reflections

    def _detect_impl(self, delta_time: float) -> List[SensorEvent]:
        """Perform audio-based detection."""
        if not self.entity:
            return []

        events = []

        # Listen for sounds (simplified - would receive sound events from scene)
        # For demonstration, we could detect nearby entities making "noise"
        sounds = self._get_audible_sounds()

        for sound_data in sounds:
            distance = sound_data.get('distance', 0.0)
            volume = sound_data.get('volume', 1.0)
            frequency = sound_data.get('frequency', 1000.0)

            # Check hearing range
            if distance > self.hearing_range:
                continue

            # Check frequency range
            if not (self.frequency_range[0] <= frequency <= self.frequency_range[1]):
                continue

            # Calculate effective volume (includes distance attenuation)
            effective_volume = self._calculate_volume(volume, distance)

            # Check if above threshold (accounting for background noise)
            if effective_volume < self.volume_threshold + self.background_noise:
                continue

            # Calculate signal strength
            strength = min(effective_volume * self.sensitivity, 1.0)

            # Create sensor data
            sensor_data = SensorData(
                sensor_type=SensorType.AUDIO,
                entity_id=self.entity.name,
                target_id=sound_data.get('source_id'),
                position=sound_data.get('position'),
                distance=distance,
                strength=strength,
                data={
                    "sound_type": sound_data.get('type', 'unknown'),
                    "volume": volume,
                    "effective_volume": effective_volume,
                    "frequency": frequency,
                    "direction": sound_data.get('direction', 0.0)
                }
            )

            # For now, just create detection events
            events.append(SensorEvent("sound_detected", self.entity, sensor_data))

        return events

    def _calculate_volume(self, base_volume: float, distance: float) -> float:
        """Calculate volume falloff with distance."""
        if distance <= 1.0:
            return base_volume

        # Inverse square law for sound attenuation
        attenuation = 1.0 / (distance * distance)
        return base_volume * attenuation

    def _get_audible_sounds(self) -> List[Dict[str, Any]]:
        """Get currently audible sounds."""
        # This would normally receive sound events from the simulation
        # For demonstration, return empty list
        return []

    def emit_sound(self, sound_type: str, volume: float = 1.0,
                   frequency: float = 1000.0, **kwargs) -> SensorData:
        """Emit a sound from this entity's position."""
        transform = self.entity.get_controller(Transform) if self.entity else None
        position = (transform.x, transform.y) if transform else (0, 0)

        return SensorData(
            sensor_type=SensorType.AUDIO,
            entity_id=self.entity.name if self.entity else "unknown",
            target_id=self.entity.name if self.entity else "unknown",
            position=position,
            distance=0.0,
            strength=volume,
            data={
                "sound_type": sound_type,
                "volume": volume,
                "frequency": frequency,
                "source": "entity",
                **kwargs
            }
        )

    def set_hearing_range(self, range_: float):
        """Set maximum hearing distance."""
        self.hearing_range = max(1.0, range_)

    def set_sensitivity(self, sensitivity: float):
        """Set hearing sensitivity multiplier."""
        self.sensitivity = max(0.0, sensitivity)


class TactileSensor(BaseSensor):
    """
    Sensor for physical contact and collision detection.

    Provides:
    - Touch/contact detection
    - Pressure sensing
    - Collision response
    - Proximity warnings
    """

    def __init__(self, touch_radius: float = 10.0, pressure_sensitivity: float = 1.0,
                 detect_collisions: bool = True, detect_proximity: bool = True, **kwargs):
        super().__init__(SensorType.TACTILE, **kwargs)
        self.touch_radius = touch_radius
        self.pressure_sensitivity = pressure_sensitivity
        self.detect_collisions = detect_collisions
        self.detect_proximity = detect_proximity

        # Detection thresholds
        self.collision_threshold = 5.0   # Distance for collision detection
        self.proximity_threshold = 15.0  # Distance for proximity warnings

        # Touch state
        self.touching_entities: Set[str] = set()
        self.last_touch_positions: Dict[str, Tuple[float, float]] = {}

    def _detect_impl(self, delta_time: float) -> List[SensorEvent]:
        """Perform tactile detection."""
        if not self.entity:
            return []

        events = []
        current_touching: Set[str] = set()

        # Check for collisions and proximity
        nearby_entities = self._get_nearby_entities()

        for other_entity in nearby_entities:
            if other_entity == self.entity:
                continue

            distance = self._calculate_distance(self.entity, other_entity)

            if distance <= self.collision_threshold and self.detect_collisions:
                # Collision detected
                current_touching.add(other_entity.name)
                sensor_data = SensorData(
                    sensor_type=SensorType.TACTILE,
                    entity_id=self.entity.name,
                    target_id=other_entity.name,
                    distance=distance,
                    strength=self._calculate_collision_strength(distance),
                    data={
                        "collision": True,
                        "pressure": self._calculate_pressure(distance),
                        "first_contact": other_entity.name not in self.last_touch_positions
                    }
                )

                # Track touch position
                transform = other_entity.get_controller(Transform)
                if transform:
                    self.last_touch_positions[other_entity.name] = (transform.x, transform.y)

                self._add_detection(other_entity.name, sensor_data)
                events.append(SensorEvent("collision_detected", self.entity, sensor_data))

            elif distance <= self.proximity_threshold and self.detect_proximity and distance > self.collision_threshold:
                # Proximity warning
                sensor_data = SensorData(
                    sensor_type=SensorType.TACTILE,
                    entity_id=self.entity.name,
                    target_id=other_entity.name,
                    distance=distance,
                    strength=self._calculate_proximity_strength(distance),
                    data={"proximity": True, "safe_distance": distance > self.touch_radius}
                )

                self._add_detection(f"proximity_{other_entity.name}", sensor_data)
                events.append(SensorEvent("proximity_detected", self.entity, sensor_data))

        # Handle lost contacts
        for lost_entity in self.touching_entities - current_touching:
            self._remove_detection(lost_entity)
            events.append(SensorEvent("contact_lost", self.entity,
                                    SensorData(SensorType.TACTILE, self.entity.name,
                                             target_id=lost_entity, data={"lost": True})))

        self.touching_entities = current_touching

        return events

    def _calculate_collision_strength(self, distance: float) -> float:
        """Calculate collision strength based on distance."""
        if distance <= 0:
            return 1.0

        # Stronger collisions at closer distances
        return min(1.0, (self.collision_threshold - distance) / self.collision_threshold)

    def _calculate_pressure(self, distance: float) -> float:
        """Calculate perceived pressure based on distance."""
        collision_strength = self._calculate_collision_strength(distance)
        return collision_strength * self.pressure_sensitivity

    def _calculate_proximity_strength(self, distance: float) -> float:
        """Calculate proximity warning strength."""
        if distance >= self.proximity_threshold:
            return 0.0

        # Linear falloff from proximity threshold to touch radius
        safe_range = self.proximity_threshold - self.collision_threshold
        if safe_range <= 0:
            return 1.0

        proximity_distance = self.proximity_threshold - distance
        return min(1.0, proximity_distance / safe_range)

    def _get_nearby_entities(self) -> List[EnvironmentEntity]:
        """Get entities within detection range."""
        # This would query the scene for nearby entities
        return []

    def get_touching_entities(self) -> Set[str]:
        """Get currently touching entity IDs."""
        return self.touching_entities.copy()

    def is_touching(self, entity_id: str) -> bool:
        """Check if touching a specific entity."""
        return entity_id in self.touching_entities


class SensorManager:
    """
    Manages multiple sensors for an entity.
    """

    def __init__(self, owner_entity: EnvironmentEntity):
        self.owner_entity = owner_entity
        self.sensors: Dict[str, BaseSensor] = {}
        self.events: List[SensorEvent] = []
        self.max_events = 100

        # Global settings
        self.global_enabled = True
        self.event_callbacks: List[Callable[[SensorEvent], None]] = []

    def add_sensor(self, name: str, sensor: BaseSensor):
        """Add a sensor to this manager."""
        sensor.attach_to_entity(self.owner_entity)
        self.sensors[name] = sensor
        print(f"📡 Sensor '{name}' added to {self.owner_entity.name}")

    def remove_sensor(self, name: str) -> bool:
        """Remove a sensor by name."""
        if name in self.sensors:
            sensor = self.sensors[name]
            if sensor.entity:
                print(f"📡 Sensor '{name}' removed from {sensor.entity.name}")
            del self.sensors[name]
            return True
        return False

    def get_sensor(self, name: str) -> Optional[BaseSensor]:
        """Get a sensor by name."""
        return self.sensors.get(name)

    def update(self, delta_time: float) -> List[SensorEvent]:
        """Update all sensors and collect events."""
        if not self.global_enabled or not self.owner_entity:
            return []

        all_events = []

        for sensor in self.sensors.values():
            sensor_events = sensor.update(delta_time)
            all_events.extend(sensor_events)

            # Add to global event history
            self.events.extend(sensor_events)
            if len(self.events) > self.max_events:
                self.events = self.events[-self.max_events:]

        # Trigger callbacks
        for event in all_events:
            for callback in self.event_callbacks:
                try:
                    callback(event)
                except Exception as e:
                    print(f"⚠️ Sensor callback error: {e}")

        return all_events

    def set_global_enabled(self, enabled: bool):
        """Enable or disable all sensors."""
        self.global_enabled = enabled
        status = "enabled" if enabled else "disabled"
        print(f"📡 All sensors {status} for {self.owner_entity.name}")

    def clear_all_detections(self):
        """Clear detections from all sensors."""
        for sensor in self.sensors.values():
            sensor.clear_detections()

    def get_all_detections(self) -> Dict[str, List[SensorData]]:
        """Get detections from all sensors."""
        return {name: sensor.get_detected_entities() for name, sensor in self.sensors.items()}

    def add_event_callback(self, callback: Callable[[SensorEvent], None]):
        """Add a global event callback."""
        self.event_callbacks.append(callback)

    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive sensor statistics."""
        sensor_stats = {}
        total_detections = 0
        total_updates = 0

        for name, sensor in self.sensors.items():
            stats = sensor.get_statistics()
            sensor_stats[name] = stats
            total_detections += stats.get('total_detections', 0)
            total_updates += stats.get('update_count', 0)

        return {
            "total_sensors": len(self.sensors),
            "global_enabled": self.global_enabled,
            "total_events": len(self.events),
            "total_detections": total_detections,
            "total_updates": total_updates,
            "sensor_stats": sensor_stats
        }

    def __repr__(self):
        sensors = list(self.sensors.keys())
        return f"<SensorManager(owner='{self.owner_entity.name}', sensors={sensors})>"

    def __getitem__(self, name: str) -> Optional[BaseSensor]:
        """Get sensor by name using dict access."""
        return self.get_sensor(name)

    def __contains__(self, name: str) -> bool:
        """Check if sensor exists."""
        return name in self.sensors


# ===== EXPORTS =====

__all__ = [
    'SensorType',
    'SensorMode',
    'SensorData',
    'SensorEvent',
    'BaseSensor',
    'VisionSensor',
    'AudioSensor',
    'TactileSensor',
    'SensorManager'
]
