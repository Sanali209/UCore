"""
Abstract Systems for UCore Simulation Framework
===============================================

High-level abstractions providing extensible foundations for simulation components.
Focused on future extensibility and generic attribute/property management.

Systems:
- Attribute System: Dynamic property management with modifiers and effects
- Behavior System: Abstract action execution framework
- Effect System: Temporary modifications with duration and stacking
- State System: Hierarchical state management with transitions
- Component System: Meta-component management and registration
"""

from __future__ import annotations
from typing import Dict, List, Any, Optional, Callable, Type, Union, Set
from typing import TYPE_CHECKING
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import time
from enum import Enum

if TYPE_CHECKING:
    from .entity import EnvironmentEntity


# ===== ATTRIBUTE SYSTEM =====

class AttributeType(Enum):
    """Common attribute types for type hints and validation."""
    NONE = "none"
    INTEGER = "int"
    FLOAT = "float"
    STRING = "str"
    BOOLEAN = "bool"
    VECTOR2 = "vec2"
    VECTOR3 = "vec3"
    LIST = "list"
    DICT = "dict"


@dataclass
class AttributeModifier:
    """
    A modifier that can be applied to an attribute.

    Modifiers can be:
    - Additive: value + modifier
    - Multiplicative: value * modifier
    - Override: replace value completely
    """
    modifier_id: str
    source: Any  # What created this modifier
    modifier_type: str = "additive"  # "additive", "multiplicative", "override"
    value: Any = 0
    priority: int = 0  # Higher priority applied last

    def apply(self, base_value: Any) -> Any:
        """Apply this modifier to a base value."""
        if self.modifier_type == "override":
            return self.value
        elif self.modifier_type == "multiplicative":
            if isinstance(base_value, (int, float)) and isinstance(self.value, (int, float)):
                return base_value * self.value
        elif self.modifier_type == "additive":
            if isinstance(base_value, (int, float)) and isinstance(self.value, (int, float)):
                return base_value + self.value

        return base_value

    def __repr__(self):
        return f"<AttributeModifier(id='{self.modifier_id}', type='{self.modifier_type}', value={self.value})>"


@dataclass
class AttributeEffect:
    """
    A temporary effect that modifies attributes over time.
    """
    effect_id: str
    source: Any
    attribute_name: str
    modifier: AttributeModifier
    duration: float = -1.0  # -1 for permanent
    start_time: float = field(default_factory=time.time)
    tick_interval: float = 1.0
    last_tick: float = field(default_factory=time.time)
    on_tick: Optional[Callable[[float], None]] = None
    on_expire: Optional[Callable[[], None]] = None

    def is_expired(self) -> bool:
        """Check if this effect has expired."""
        if self.duration < 0:
            return False
        return time.time() - self.start_time >= self.duration

    def should_tick(self) -> bool:
        """Check if this effect should tick this frame."""
        if not self.on_tick or self.tick_interval <= 0:
            return False
        return time.time() - self.last_tick >= self.tick_interval

    def tick(self, delta_time: float):
        """Execute a tick of this effect."""
        if self.on_tick:
            self.on_tick(delta_time)
        self.last_tick = time.time()

    def expire(self):
        """Execute expiration logic."""
        if self.on_expire:
            self.on_expire()

    def time_remaining(self) -> float:
        """Get time remaining for this effect."""
        if self.duration < 0:
            return -1.0
        return max(0.0, self.duration - (time.time() - self.start_time))

    def __repr__(self):
        remaining = self.time_remaining()
        duration_str = "∞" if remaining < 0 else f"{remaining:.1f}s"
        return f"<AttributeEffect(id='{self.effect_id}', attr='{self.attribute_name}', remaining={duration_str})>"


class Attribute:
    """
    A single attribute that can have a base value and multiple modifiers.
    """

    def __init__(self, name: str, attribute_type: AttributeType = AttributeType.NONE,
                 default_value: Any = None, min_value: Any = None, max_value: Any = None):
        self.name = name
        self.attribute_type = attribute_type
        self._base_value = default_value
        self.min_value = min_value
        self.max_value = max_value

        self.modifiers: Dict[str, AttributeModifier] = {}
        self.effects: List[AttributeEffect] = []
        self._cached_value = None
        self._cache_dirty = True

    @property
    def base_value(self) -> Any:
        """Get the base value of this attribute."""
        return self._base_value

    @base_value.setter
    def base_value(self, value: Any):
        """Set the base value and mark cache as dirty."""
        self._base_value = value
        self._cache_dirty = True

    @property
    def effective_value(self) -> Any:
        """Get the effective value after all modifiers and effects."""
        if self._cache_dirty:
            self._cached_value = self._calculate_effective_value()
            self._cache_dirty = False
        return self._cached_value

    def _calculate_effective_value(self) -> Any:
        """Calculate the effective value with all modifiers."""
        value = self._base_value

        # Apply modifiers in priority order
        sorted_modifiers = sorted(self.modifiers.values(), key=lambda m: m.priority)

        for modifier in sorted_modifiers:
            value = modifier.apply(value)

        # Apply effect modifiers
        for effect in self.effects:
            if not effect.is_expired():
                value = effect.modifier.apply(value)

        # Clamp to min/max if specified
        if self.min_value is not None and isinstance(value, (int, float)):
            value = max(value, self.min_value)
        if self.max_value is not None and isinstance(value, (int, float)):
            value = min(value, self.max_value)

        return value

    def add_modifier(self, modifier: AttributeModifier):
        """Add a modifier to this attribute."""
        self.modifiers[modifier.modifier_id] = modifier
        self._cache_dirty = True

    def remove_modifier(self, modifier_id: str) -> bool:
        """Remove a modifier by ID."""
        if modifier_id in self.modifiers:
            del self.modifiers[modifier_id]
            self._cache_dirty = True
            return True
        return False

    def add_effect(self, effect: AttributeEffect):
        """Add an effect to this attribute."""
        self.effects.append(effect)
        self._cache_dirty = True

    def remove_effect(self, effect_id: str) -> bool:
        """Remove an effect by ID."""
        for i, effect in enumerate(self.effects):
            if effect.effect_id == effect_id:
                self.effects.pop(i)
                self._cache_dirty = True
                return True
        return False

    def update_effects(self, delta_time: float):
        """Update effects and remove expired ones."""
        expired_effects = []
        for effect in self.effects[:]:  # Copy to avoid modification during iteration
            if effect.should_tick():
                effect.tick(delta_time)

            if effect.is_expired():
                effect.expire()
                expired_effects.append(effect.effect_id)
                self.effects.remove(effect)

        if expired_effects:
            self._cache_dirty = True

    def __repr__(self):
        return f"<Attribute(name='{self.name}', base={self._base_value}, effective={self.effective_value})>"


class AttributeSystem:
    """
    Manages a collection of attributes for an entity with events and serialization.
    """

    def __init__(self, owner: Any = None):
        self.owner = owner  # Typically an entity
        self.attributes: Dict[str, Attribute] = {}
        self.on_attribute_changed: Optional[Callable[[str, Any, Any], None]] = None

    def create_attribute(self, name: str, attribute_type: AttributeType = AttributeType.NONE,
                        default_value: Any = None, min_value: Any = None, max_value: Any = None) -> Attribute:
        """Create a new attribute."""
        if name in self.attributes:
            raise ValueError(f"Attribute '{name}' already exists")

        attr = Attribute(name, attribute_type, default_value, min_value, max_value)
        self.attributes[name] = attr
        return attr

    def get_attribute(self, name: str) -> Optional[Attribute]:
        """Get an attribute by name."""
        return self.attributes.get(name)

    def get_value(self, name: str, default: Any = None) -> Any:
        """Get the effective value of an attribute."""
        attr = self.attributes.get(name)
        if attr:
            return attr.effective_value
        return default

    def set_base_value(self, name: str, value: Any) -> bool:
        """Set the base value of an attribute."""
        attr = self.attributes.get(name)
        if attr:
            old_value = attr.effective_value
            attr.base_value = value
            new_value = attr.effective_value

            if self.on_attribute_changed and old_value != new_value:
                self.on_attribute_changed(name, old_value, new_value)

            return True
        return False

    def add_modifier(self, attribute_name: str, modifier: AttributeModifier) -> bool:
        """Add a modifier to an attribute."""
        attr = self.attributes.get(attribute_name)
        if attr:
            old_value = attr.effective_value
            attr.add_modifier(modifier)
            new_value = attr.effective_value

            if self.on_attribute_changed and old_value != new_value:
                self.on_attribute_changed(attribute_name, old_value, new_value)

            return True
        return False

    def add_effect(self, attribute_name: str, effect: AttributeEffect) -> bool:
        """Add an effect to an attribute."""
        attr = self.attributes.get(attribute_name)
        if attr:
            attr.add_effect(effect)
            return True
        return False

    def remove_modifier(self, attribute_name: str, modifier_id: str) -> bool:
        """Remove a modifier from an attribute."""
        attr = self.attributes.get(attribute_name)
        if attr:
            old_value = attr.effective_value
            result = attr.remove_modifier(modifier_id)
            if result:
                new_value = attr.effective_value
                if self.on_attribute_changed and old_value != new_value:
                    self.on_attribute_changed(attribute_name, old_value, new_value)
            return result
        return False

    def remove_effect(self, attribute_name: str, effect_id: str) -> bool:
        """Remove an effect from an attribute."""
        attr = self.attributes.get(attribute_name)
        if attr:
            return attr.remove_effect(effect_id)
        return False

    def update(self, delta_time: float):
        """Update all effects across all attributes."""
        for attribute in self.attributes.values():
            attribute.update_effects(delta_time)

    def serialize_state(self) -> Dict[str, Any]:
        """Serialize the current state for persistence."""
        return {
            "attributes": {
                name: {
                    "base_value": attr.base_value,
                    "modifiers": {
                        mod_id: {
                            "modifier_type": mod.modifier_type,
                            "value": mod.value,
                            "priority": mod.priority
                        } for mod_id, mod in attr.modifiers.items()
                    },
                    "effects": [
                        {
                            "effect_id": effect.effect_id,
                            "attribute_name": effect.attribute_name,
                            "modifier": {
                                "modifier_type": effect.modifier.modifier_type,
                                "value": effect.modifier.value,
                                "priority": effect.modifier.priority
                            },
                            "duration": effect.duration,
                            "start_time": effect.start_time,
                            "tick_interval": effect.tick_interval
                        } for effect in attr.effects
                    ]
                } for name, attr in self.attributes.items()
            }
        }

    def deserialize_state(self, state: Dict[str, Any]):
        """Deserialize and restore state from saved data."""
        attrs_data = state.get("attributes", {})

        for attr_name, attr_data in attrs_data.items():
            attr = self.get_attribute(attr_name)
            if attr:
                # Restore base value
                if "base_value" in attr_data:
                    attr.base_value = attr_data["base_value"]

                # Restore modifiers
                attr.modifiers.clear()
                for mod_id, mod_data in attr_data.get("modifiers", {}).items():
                    modifier = AttributeModifier(
                        modifier_id=mod_id,
                        source=None,  # Effects are temporary, source may not exist
                        modifier_type=mod_data["modifier_type"],
                        value=mod_data["value"],
                        priority=mod_data["priority"]
                    )
                    attr.add_modifier(modifier)

                # Restore effects
                attr.effects.clear()
                for effect_data in attr_data.get("effects", []):
                    modifier_data = effect_data["modifier"]
                    modifier = AttributeModifier(
                        modifier_id=effect_data["effect_id"],
                        source=None,
                        modifier_type=modifier_data["modifier_type"],
                        value=modifier_data["value"],
                        priority=modifier_data["priority"]
                    )

                    effect = AttributeEffect(
                        effect_id=effect_data["effect_id"],
                        source=None,
                        attribute_name=effect_data["attribute_name"],
                        modifier=modifier,
                        duration=effect_data["duration"],
                        start_time=effect_data["start_time"],
                        tick_interval=effect_data["tick_interval"]
                    )
                    attr.add_effect(effect)

    def get_all_values(self) -> Dict[str, Any]:
        """Get effective values for all attributes."""
        return {name: attr.effective_value for name, attr in self.attributes.items()}

    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        total_modifiers = sum(len(attr.modifiers) for attr in self.attributes.values())
        total_effects = sum(len(attr.effects) for attr in self.attributes.values())
        expired_effects = sum(sum(1 for effect in attr.effects if effect.is_expired())
                             for attr in self.attributes.values())

        return {
            "attribute_count": len(self.attributes),
            "total_modifiers": total_modifiers,
            "total_effects": total_effects,
            "expired_effects": expired_effects
        }

    def __repr__(self):
        return f"<AttributeSystem(owner={self.owner}, attributes={list(self.attributes.keys())})>"

    def __getitem__(self, key: str) -> Any:
        """Get attribute value using dict-like access."""
        return self.get_value(key)

    def __setitem__(self, key: str, value: Any):
        """Set attribute base value using dict-like access."""
        self.set_base_value(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if attribute exists."""
        return key in self.attributes


# ===== BEHAVIOR SYSTEM =====

class BehaviorNode(ABC):
    """
    Abstract base class for behavior nodes in a behavior tree.
    """

    def __init__(self, name: str = ""):
        self.name = name

    @abstractmethod
    def execute(self, context: Dict[str, Any]) -> str:
        """
        Execute this behavior node.

        Returns:
            "success", "failure", or "running"
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class BehaviorTree:
    """
    A behavior tree composed of behavior nodes.
    """

    def __init__(self, root: BehaviorNode, name: str = ""):
        self.name = name
        self.root = root

    def execute(self, context: Dict[str, Any] = None) -> str:
        """Execute the behavior tree."""
        if context is None:
            context = {}
        return self.root.execute(context)

    def __repr__(self):
        return f"<BehaviorTree(name='{self.name}', root={self.root})>"


# ===== STATE SYSTEM =====

class State:
    """
    A state in a hierarchical state machine.
    """

    def __init__(self, name: str, parent: Optional[State] = None):
        self.name = name
        self.parent = parent
        self.children: Dict[str, State] = {}
        self.transitions: Dict[str, State] = {}
        self.on_enter: Optional[Callable] = None
        self.on_exit: Optional[Callable] = None
        self.on_update: Optional[Callable[[float], None]] = None

    def add_child(self, child: State):
        """Add a child state."""
        self.children[child.name] = child
        child.parent = self

    def add_transition(self, event: str, target_state: State):
        """Add a transition triggered by an event."""
        self.transitions[event] = target_state

    def can_transition(self, event: str) -> bool:
        """Check if a transition exists for an event."""
        return event in self.transitions

    def get_transition_target(self, event: str) -> Optional[State]:
        """Get the target state for an event."""
        return self.transitions.get(event)

    def get_full_path(self) -> str:
        """Get the full path to this state in the hierarchy."""
        if self.parent:
            return f"{self.parent.get_full_path()}.{self.name}"
        return self.name

    def __repr__(self):
        return f"<State(name='{self.name}', children={list(self.children.keys())})>"

    def __getitem__(self, key: str) -> State:
        """Get a child state by name."""
        return self.children[key]


class StateMachine:
    """
    A hierarchical state machine.
    """

    def __init__(self, name: str = "", initial_state: Optional[State] = None):
        self.name = name
        self.initial_state = initial_state
        self.current_state = initial_state
        self.history: List[State] = []
        self.on_state_changed: Optional[Callable[[State, State], None]] = None

    def start(self):
        """Start the state machine."""
        if self.initial_state:
            self.current_state = self.initial_state
            if self.current_state.on_enter:
                self.current_state.on_enter()
            self.history.append(self.current_state)

    def transition(self, event: str) -> bool:
        """Attempt to transition based on an event."""
        if not self.current_state:
            return False

        target_state = None

        # Check current state first
        if self.current_state.can_transition(event):
            target_state = self.current_state.get_transition_target(event)

        # If no transition, check parent states
        elif self.current_state.parent:
            current = self.current_state.parent
            while current:
                if current.can_transition(event):
                    target_state = current.get_transition_target(event)
                    # Transition to substate of target state?
                    if target_state and target_state.children:
                        # For now, just transition to target state
                        break
                current = current.parent

        if target_state:
            self._change_state(target_state)
            return True

        return False

    def _change_state(self, new_state: State):
        """Change to a new state."""
        if not self.current_state:
            return

        old_state = self.current_state

        # Exit current state
        if self.current_state.on_exit:
            self.current_state.on_exit()

        # Enter new state
        self.current_state = new_state
        if new_state.on_enter:
            new_state.on_enter()

        # Update history
        self.history.append(new_state)

        # Notify listeners
        if self.on_state_changed:
            self.on_state_changed(old_state, new_state)

    def update(self, delta_time: float):
        """Update the current state."""
        if self.current_state and self.current_state.on_update:
            self.current_state.on_update(delta_time)

    def get_full_state_path(self) -> str:
        """Get the full path of the current state."""
        if self.current_state:
            return self.current_state.get_full_path()
        return ""

    def can_handle_event(self, event: str) -> bool:
        """Check if the current state can handle an event."""
        if not self.current_state:
            return False

        # Check current state and parents
        current = self.current_state
        while current:
            if current.can_transition(event):
                return True
            current = current.parent

        return False

    def __repr__(self):
        current = self.current_state.name if self.current_state else "None"
        return f"<StateMachine(name='{self.name}', current='{current}')>"


# ===== COMPONENT REGISTRY =====

class ComponentRegistry:
    """
    Meta-component management system for registering and discovering components dynamically.
    """

    def __init__(self):
        self.components: Dict[str, Dict[str, Any]] = {}
        self.component_types: Dict[str, type] = {}

    def register_component_type(self, component_type: type, metadata: Optional[Dict[str, Any]] = None):
        """Register a component type with optional metadata."""
        type_name = component_type.__name__
        self.component_types[type_name] = component_type
        self.components[type_name] = metadata if metadata is not None else {}

    def get_component_type(self, type_name: str) -> Optional[type]:
        """Get a component type by name."""
        return self.component_types.get(type_name)

    def get_component_metadata(self, type_name: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a component type."""
        return self.components.get(type_name)

    def list_component_types(self) -> List[str]:
        """List all registered component type names."""
        return list(self.component_types.keys())

    def create_component_instance(self, type_name: str, *args, **kwargs) -> Any:
        """Create an instance of a registered component type."""
        component_type = self.component_types.get(type_name)
        if component_type:
            return component_type(*args, **kwargs)
        raise ValueError(f"Unknown component type: {type_name}")

    def has_component_type(self, type_name: str) -> bool:
        """Check if a component type is registered."""
        return type_name in self.component_types


# ===== EFFECT SYSTEM =====

class Effect(ABC):
    """
    Abstract base class for effects that can be applied to entities.
    """

    def __init__(self, duration: float = -1.0):
        self.duration = duration  # -1 for permanent
        self.start_time = time.time()
        self.target: Optional[Any] = None

    @abstractmethod
    def apply(self, target: Any):
        """Apply this effect to a target."""
        pass

    @abstractmethod
    def remove(self, target: Any):
        """Remove this effect from a target."""
        pass

    def is_expired(self) -> bool:
        """Check if this effect has expired."""
        if self.duration < 0:
            return False
        return time.time() - self.start_time >= self.duration

    def time_remaining(self) -> float:
        """Get time remaining for this effect."""
        if self.duration < 0:
            return -1.0
        return max(0.0, self.duration - (time.time() - self.start_time))

    def tick(self, delta_time: float):
        """Update this effect each frame."""
        pass


class EffectManager:
    """
    Manages effects applied to entities.
    """

    def __init__(self):
        self.active_effects: Dict[str, Effect] = {}

    def apply_effect(self, effect_id: str, effect: Effect, target: Any):
        """Apply an effect to a target."""
        effect.target = target
        effect.apply(target)
        self.active_effects[effect_id] = effect

    def remove_effect(self, effect_id: str):
        """Remove an effect by ID."""
        if effect_id in self.active_effects:
            effect = self.active_effects[effect_id]
            effect.remove(effect.target)
            del self.active_effects[effect_id]

    def update_effects(self, delta_time: float):
        """Update all effects and remove expired ones."""
        expired_ids = []
        for effect_id, effect in self.active_effects.items():
            effect.tick(delta_time)
            if effect.is_expired():
                effect.remove(effect.target)
                expired_ids.append(effect_id)

        for effect_id in expired_ids:
            del self.active_effects[effect_id]

    def get_active_effects(self) -> List[str]:
        """Get list of active effect IDs."""
        return list(self.active_effects.keys())


# ===== EXPORTS =====

__all__ = [
    'AttributeType',
    'AttributeModifier',
    'AttributeEffect',
    'Attribute',
    'AttributeSystem',
    'BehaviorNode',
    'BehaviorTree',
    'State',
    'StateMachine',
    'ComponentRegistry',
    'Effect',
    'EffectManager'
]
