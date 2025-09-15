"""
Specialized Entity Types for UCore Simulation Framework
======================================================

This module contains specialized entity implementations that extend the basic
EnvironmentEntity with advanced abstract systems for comprehensive simulation.

Entity Types:
- Pawn: Player-controlled entity with attribute system and state management
- BotAgent: AI-controlled entity with decision making using behavior trees
- StaticEntity: Non-interactive world geometry with attribute support
- InteractiveEntity: Clickable objects with state machines and effects
- CameraEntity: Viewport management with attribute-based controls
"""

from __future__ import annotations
from typing import List, Optional, Tuple, Dict, Any, Callable
from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from .entity import EnvironmentEntity
    from .controller import EntityController

from .entity import EnvironmentEntity
from .controllers import Transform, BotAgent
from .abstract_systems import (
    AttributeSystem, AttributeType, AttributeModifier, StateMachine, State,
    ComponentRegistry, EffectManager
)


class Pawn(EnvironmentEntity):
    """
    A player-controlled entity with advanced attribute system and state management.

    Features:
    - Comprehensive attribute system (health, stamina, stats)
    - State-based behavior management
    - Inventory and equipment management
    - Dynamic modifiers and effects on attributes
    - Input handling with attribute-based movement
    """

    def __init__(self, name: str, position: Tuple[float, float] = (0, 0)):
        super().__init__(name)

        # Core systems
        self.attribute_system = AttributeSystem(self)
        self.effect_manager = EffectManager()
        self.state_machine = StateMachine(f"{name}_states")

        # Initialize attributes with attribute system
        self._setup_attributes()
        self._setup_states()

        # Input and state
        self.input_enabled = True
        self.movement_input = {"forward": 0, "right": 0, "jump": False}
        self.action_input = {"interact": False, "use": False, "attack": False}

        # Equipment and inventory
        self.inventory = []
        self.equipment_slots = ["helmet", "armor", "weapon", "shield", "boots"]

        # Attach required controllers
        self.add_controller(Transform(position[0], position[1]))

        # Setup attribute change callbacks
        self.attribute_system.on_attribute_changed = self._on_attribute_changed

        print(f"🧑 Pawn '{name}' created with {self.attribute_system.get_statistics()['attribute_count']} attributes")

    def _setup_attributes(self):
        """Initialize all character attributes using the attribute system."""
        # Core vital attributes
        self.attribute_system.create_attribute("health", AttributeType.INTEGER, 100, 0, 200)
        self.attribute_system.create_attribute("max_health", AttributeType.INTEGER, 100, 0, 500)
        self.attribute_system.create_attribute("stamina", AttributeType.INTEGER, 100, 0, 200)
        self.attribute_system.create_attribute("max_stamina", AttributeType.INTEGER, 100, 0, 500)

        # Physical attributes
        self.attribute_system.create_attribute("strength", AttributeType.INTEGER, 10, 1, 100)
        self.attribute_system.create_attribute("agility", AttributeType.INTEGER, 10, 1, 100)
        self.attribute_system.create_attribute("endurance", AttributeType.INTEGER, 10, 1, 100)
        self.attribute_system.create_attribute("intelligence", AttributeType.INTEGER, 10, 1, 100)

        # Movement attributes
        self.attribute_system.create_attribute("speed", AttributeType.FLOAT, 5.0, 0.1, 20.0)
        self.attribute_system.create_attribute("acceleration", AttributeType.FLOAT, 2.0, 0.1, 10.0)

        # Status attributes
        self.attribute_system.create_attribute("level", AttributeType.INTEGER, 1, 1, 100)
        self.attribute_system.create_attribute("experience", AttributeType.INTEGER, 0, 0, 1000000)
        self.attribute_system.create_attribute("gold", AttributeType.INTEGER, 0, 0, 999999)

    def _setup_states(self):
        """Initialize state machine for pawn behavior."""
        # Create states
        idle_state = State("idle")
        moving_state = State("moving")
        interacting_state = State("interacting")
        dead_state = State("dead")

        # State transitions
        idle_state.add_transition("move", moving_state)
        idle_state.add_transition("interact", interacting_state)
        moving_state.add_transition("stop", idle_state)
        interacting_state.add_transition("finish", idle_state)
        # Any state can transition to dead when health <= 0

        # Add all states to state machine
        self.state_machine.initial_state = idle_state
        # Note: In full implementation, would need to properly set up hierarchical states

    def _on_attribute_changed(self, attr_name: str, old_value: Any, new_value: Any):
        """Handle attribute changes and trigger effects."""
        print(f"📊 Pawn '{self.name}' {attr_name}: {old_value} → {new_value}")

        # Handle critical attribute changes
        if attr_name == "health" and self.attribute_system.get_value("health", 0) <= 0:
            self.state_machine.transition("die")
            self.die()

        elif attr_name == "experience":
            self._check_level_up()

    def _check_level_up(self):
        """Check if pawn should level up based on experience."""
        current_exp = self.attribute_system.get_value("experience", 0)
        current_level = self.attribute_system.get_value("level", 1)

        # Simple leveling formula
        exp_needed = current_level * 100

        if current_exp >= exp_needed:
            self.level_up()

    def level_up(self):
        """Level up the pawn and improve attributes."""
        current_level = self.attribute_system.get_value("level", 1)
        new_level = current_level + 1

        self.attribute_system.set_base_value("level", new_level)

        # Grant attribute improvements
        health_boost = 10
        stamina_boost = 8
        self.attribute_system.set_base_value("max_health",
            self.attribute_system.get_value("max_health", 100) + health_boost)
        self.attribute_system.set_base_value("max_stamina",
            self.attribute_system.get_value("max_stamina", 100) + stamina_boost)

        # Heal to full on level up
        self.attribute_system.set_base_value("health",
            self.attribute_system.get_value("max_health", 100))
        self.attribute_system.set_base_value("stamina",
            self.attribute_system.get_value("max_stamina", 100))

        print(f"⬆️ Pawn '{self.name}' leveled up to level {new_level}")

    def update_input(self, input_data: Dict[str, Any]):
        """Update pawn input state from external source."""
        if not self.input_enabled:
            return

        # Movement inputs (normalized -1.0 to 1.0)
        self.movement_input["forward"] = input_data.get("forward", 0)
        self.movement_input["right"] = input_data.get("right", 0)
        self.movement_input["jump"] = input_data.get("jump", False)

        # Action inputs (boolean)
        self.action_input["interact"] = input_data.get("interact", False)
        self.action_input["use"] = input_data.get("use", False)
        self.action_input["attack"] = input_data.get("attack", False)

    def take_damage(self, damage: float):
        """Apply damage using the attribute system."""
        current_health = self.attribute_system.get_value("health", 0)
        new_health = max(0, current_health - damage)
        self.attribute_system.set_base_value("health", new_health)

    def heal(self, amount: float):
        """Restore health using attribute system."""
        max_health = self.attribute_system.get_value("max_health", 100)
        current_health = self.attribute_system.get_value("health", 0)
        new_health = min(max_health, current_health + amount)
        self.attribute_system.set_base_value("health", new_health)

    def consume_stamina(self, amount: float) -> bool:
        """Consume stamina using attribute system."""
        current_stamina = self.attribute_system.get_value("stamina", 0)
        if current_stamina >= amount:
            self.attribute_system.set_base_value("stamina", current_stamina - amount)
            return True
        return False

    def regenerate_stamina(self, amount: float):
        """Regenerate stamina over time."""
        max_stamina = self.attribute_system.get_value("max_stamina", 100)
        current_stamina = self.attribute_system.get_value("stamina", 0)
        new_stamina = min(max_stamina, current_stamina + amount)
        self.attribute_system.set_base_value("stamina", new_stamina)

    def die(self):
        """Handle pawn death."""
        print(f"💀 Pawn '{self.name}' has died")
        # Death handling logic would go here

    def respawn(self, position: Tuple[float, float]):
        """Respawn pawn at given position."""
        transform = self.get_controller(Transform)
        if transform:
            transform.x, transform.y = position

        # Restore to full health and stamina
        max_health = self.attribute_system.get_value("max_health", 100)
        max_stamina = self.attribute_system.get_value("max_stamina", 100)
        self.attribute_system.set_base_value("health", max_health)
        self.attribute_system.set_base_value("stamina", max_stamina)

        print(f"🔄 Pawn '{self.name}' respawned at {position}")

    def add_to_inventory(self, item: Any):
        """Add item to pawn inventory."""
        self.inventory.append(item)

    def equip_item(self, item: Any, slot: str):
        """Equip item in specified slot using attribute modifiers."""
        if slot in self.equipment_slots:
            # Future: Add attribute modifiers based on equipment
            # For now, just track equipped items
            setattr(self, f"equipped_{slot}", item)
            print(f"⚔️ Pawn '{self.name}' equipped {slot}: {item}")

    def gain_experience(self, amount: int):
        """Grant experience and handle leveling."""
        current_exp = self.attribute_system.get_value("experience", 0)
        self.attribute_system.set_base_value("experience", current_exp + amount)

    def get_stats(self) -> Dict[str, Any]:
        """Get pawn statistics from attribute system."""
        return {
            "name": self.name,
            "attributes": self.attribute_system.get_all_values(),
            "attribute_stats": self.attribute_system.get_statistics(),
            "inventory_count": len(self.inventory),
            "equipped_items": len([getattr(self, f"equipped_{slot}", None) for slot in self.equipment_slots if getattr(self, f"equipped_{slot}", None)]),
            "current_state": self.state_machine.current_state.name if self.state_machine.current_state else "none"
        }

    def update(self, delta_time: float):
        """Update pawn systems."""
        # Update attribute system (effects, etc.)
        self.attribute_system.update(delta_time)

        # Update state machine
        self.state_machine.update(delta_time)

        # Update effect manager
        self.effect_manager.update_effects(delta_time)

        # Auto-regenerate stamina
        if self.attribute_system.get_value("stamina", 0) < self.attribute_system.get_value("max_stamina", 100):
            regen_rate = 10 * delta_time  # 10 points per second
            self.regenerate_stamina(regen_rate)

    def __repr__(self):
        return f"<Pawn(name='{self.name}', level={self.attribute_system.get_value('level', 1)}, health={self.attribute_system.get_value('health', 0)}/{self.attribute_system.get_value('max_health', 100)})>"


class BotAgentEntity(EnvironmentEntity):
    """
    An AI-controlled entity with advanced decision making and attribute system.

    Features:
    - Attribute-based AI abilities and stats
    - State machine for complex behavior management
    - Behavior tree integration
    - Learning and adaptation systems
    - Social interaction capabilities
    - Effect and modifier support
    """

    def __init__(self, name: str, ai_type: str = "generic", position: Tuple[float, float] = (0, 0)):
        super().__init__(name)

        # Core systems
        self.attribute_system = AttributeSystem(self)
        self.effect_manager = EffectManager()
        self.state_machine = StateMachine(f"{name}_states")

        self.ai_type = ai_type

        # Initialize systems
        self._setup_attributes()
        self._setup_states()
        self._setup_ai_personality()

        # AI state
        self.is_active = True
        self.current_goal = "idle"
        self.behavior_state = "explore"
        self.last_decision_time = 0

        # Perception and awareness
        self.awareness_radius = 50.0
        self.visible_entities = []
        self.memory = []
        self.knowledge_base = {}

        # Behavior counters
        self.actions_performed = 0
        self.decisions_made = 0
        self.interactions = 0

        # Attach required controllers
        self.add_controller(Transform(position[0], position[1]))
        self.add_controller(BotAgent())

        # Setup attribute change callbacks
        self.attribute_system.on_attribute_changed = self._on_attribute_changed

        print(f"🤖 BotAgent '{name}' created with AI type '{ai_type}' and {self.attribute_system.get_statistics()['attribute_count']} attributes")

    def _setup_attributes(self):
        """Initialize AI-specific attributes using attribute system."""
        # Core AI attributes
        self.attribute_system.create_attribute("intelligence", AttributeType.INTEGER, 50, 1, 100)
        self.attribute_system.create_attribute("aggression", AttributeType.FLOAT, 0.5, 0.0, 1.0)
        self.attribute_system.create_attribute("curiosity", AttributeType.FLOAT, 0.7, 0.0, 1.0)
        self.attribute_system.create_attribute("social_drive", AttributeType.FLOAT, 0.6, 0.0, 1.0)

        # Performance attributes
        self.attribute_system.create_attribute("reaction_time", AttributeType.FLOAT, 0.5, 0.1, 2.0)
        self.attribute_system.create_attribute("decision_accuracy", AttributeType.FLOAT, 0.8, 0.0, 1.0)
        self.attribute_system.create_attribute("learning_rate", AttributeType.FLOAT, 0.5, 0.0, 1.0)

        # Physical attributes (if applicable)
        self.attribute_system.create_attribute("health", AttributeType.INTEGER, 100, 0, 200)
        self.attribute_system.create_attribute("speed", AttributeType.FLOAT, 3.0, 0.1, 15.0)
        self.attribute_system.create_attribute("endurance", AttributeType.INTEGER, 100, 0, 300)

    def _setup_states(self):
        """Initialize state machine for AI behavior."""
        # Create AI states
        idle_state = State("idle")
        exploring_state = State("exploring")
        interacting_state = State("interacting")
        learning_state = State("learning")
        fleeing_state = State("fleeing")
        combat_state = State("combat")

        # State transitions based on AI personality and situation
        idle_state.add_transition("explore", exploring_state)
        idle_state.add_transition("socialize", interacting_state)
        exploring_state.add_transition("finish", idle_state)
        interacting_state.add_transition("finish", idle_state)
        idle_state.add_transition("threatened", fleeing_state)
        fleeing_state.add_transition("safe", idle_state)
        idle_state.add_transition("aggressive", combat_state)
        combat_state.add_transition("retreat", fleeing_state)

        self.state_machine.initial_state = idle_state

    def _setup_ai_personality(self):
        """Initialize AI personality through attribute modifiers."""
        # Set personality-based modifiers
        personality_boost = AttributeModifier(
            "personality_boost", self,
            "multiplicative", 1.2, 10
        )
        self.attribute_system.add_modifier("intelligence", personality_boost)

    def _on_attribute_changed(self, attr_name: str, old_value: Any, new_value: Any):
        """Handle attribute changes and adapt behavior."""
        print(f"🧠 BotAgent '{self.name}' {attr_name}: {old_value} → {new_value}")

        # Adjust behavior based on attribute changes
        if attr_name == "aggression" and new_value > 0.8:
            self.current_goal = "confrontational"

        elif attr_name == "intelligence" and new_value > 80:
            # Higher intelligence enables more complex behaviors
            self.awareness_radius *= 1.5

    def make_decision(self, current_time: float) -> str:
        """Make decisions based on attribute-driven personality."""
        if not self.is_active:
            return "idle"

        self.last_decision_time = current_time
        self.decisions_made += 1

        # Get personality values from attributes
        aggression = self.attribute_system.get_value("aggression", 0.5)
        curiosity = self.attribute_system.get_value("curiosity", 0.7)
        social = self.attribute_system.get_value("social_drive", 0.6)

        decisions = []

        # Personality-based decision weights
        if aggression > 0.8:
            decisions.extend(["confront", "territorial", "compete"])
        if curiosity > 0.6:
            decisions.extend(["explore", "investigate", "observe"])
        if social > 0.5:
            decisions.extend(["approach", "communicate", "follow"])
        if self.visible_entities:
            decisions.extend(["approach", "observe", "communicate"])

        decisions.extend(["idle", "move_randomly", "patrol_area"])

        # Choose based on personality-modified probability
        decision_weights = self._calculate_decision_weights(decisions, aggression, curiosity, social)
        decision = random.choices(decisions, weights=decision_weights, k=1)[0]

        return decision

    def _calculate_decision_weights(self, decisions: List[str], aggression: float,
                                   curiosity: float, social: float) -> List[float]:
        """Calculate decision weights based on personality."""
        weights = []
        for decision in decisions:
            base_weight = 1.0

            # Apply personality modifiers
            if "confront" in decision or "territorial" in decision:
                base_weight *= max(0.1, aggression ** 2)
            elif "explore" in decision or "investigate" in decision:
                base_weight *= max(0.1, curiosity ** 2)
            elif "approach" in decision or "communicate" in decision:
                base_weight *= max(0.1, social ** 2)

            weights.append(base_weight)

        return weights

    def perceive_environment(self):
        """Update perception using attribute-based awareness."""
        self.visible_entities = []

        transform = self.get_controller(Transform)
        if not transform:
            return

        # Use intelligence-based awareness radius
        effective_radius = self.awareness_radius * (self.attribute_system.get_value("intelligence", 50) / 100.0 + 0.5)

        # Find entities within range (simplified - would use spatial system in practice)
        root = self.root()
        for child in root.children if root != self else []:
            if self != child:
                child_transform = child.get_controller(Transform)
                if child_transform:
                    distance = ((transform.x - child_transform.x) ** 2 +
                              (transform.y - child_transform.y) ** 2) ** 0.5
                    if distance <= effective_radius:
                        self.visible_entities.append(child)

    def execute_action(self, action: str):
        """Execute action using attribute-based performance."""
        self.actions_performed += 1

        # Apply stamina cost
        stamina_cost = 5  # Base cost
        if self.attribute_system.get_value("stamina", 0) >= stamina_cost:
            self.attribute_system.set_base_value("stamina",
                self.attribute_system.get_value("stamina") - stamina_cost)
        else:
            print(f"😴 BotAgent '{self.name}' too tired to perform '{action}'")
            return

        print(f"🤖 {self.name} executes: {action}")

        # Execute action with attribute-based performance
        if action == "move_randomly":
            transform = self.get_controller(Transform)
            if transform:
                speed = self.attribute_system.get_value("speed", 3.0)
                distance = speed * 2  # 2 second travel
                transform.x += random.uniform(-distance, distance)
                transform.y += random.uniform(-distance, distance)

    def learn_from_experience(self, experience: Dict[str, Any]):
        """Learn and adapt personality based on experiences."""
        self.memory.append(experience)

        learning_rate = self.attribute_system.get_value("learning_rate", 0.5)
        adjustment = learning_rate * 0.05  # Small adjustments

        if experience.get("outcome") == "positive":
            # Positive experiences boost intelligence and curiosity
            current_int = self.attribute_system.get_value("intelligence", 50)
            current_cur = self.attribute_system.get_value("curiosity", 0.7)

            self.attribute_system.set_base_value("intelligence", min(100, current_int + adjustment * 10))
            self.attribute_system.set_base_value("curiosity", min(1.0, current_cur + adjustment))

        elif experience.get("outcome") == "negative":
            # Negative experiences increase caution but decrease aggression
            current_agg = self.attribute_system.get_value("aggression", 0.5)
            self.attribute_system.set_base_value("aggression", max(0.0, current_agg - adjustment))

    def communicate(self, target_entity: EnvironmentEntity, message: str):
        """Send communication to another entity."""
        self.interactions += 1
        social_skill = self.attribute_system.get_value("social_drive", 0.6)

        # Communication effectiveness based on social skills
        communication_boost = 1.0 + (social_skill - 0.5) * 0.5

        print(f"💬 {self.name} (skill:{social_skill:.1f}) tells {target_entity.name}: {message}")
        print(f"   Communication boost: {communication_boost:.1f}x")

    def initiate_interaction(self, target_entity: EnvironmentEntity):
        """Initiate interaction with intelligence-based approach."""
        if target_entity in self.visible_entities:
            intelligence = self.attribute_system.get_value("intelligence", 50)
            social_skill = self.attribute_system.get_value("social_drive", 0.6)

            distance = self._calculate_distance(target_entity)

            # Smart AI may choose different interaction strategies
            if intelligence > 70 and social_skill > 0.7:
                print(f"🎭 {self.name} approaches {target_entity.name} diplomatically")
            elif intelligence < 30:
                print(f"🔥 {self.name} approaches {target_entity.name} bluntly")

            if distance < 25:  # Close enough
                self.interactions += 1
                print(f"🤝 {self.name} interacts with {target_entity.name}")

    def _calculate_distance(self, other_entity: EnvironmentEntity) -> float:
        """Calculate distance to another entity."""
        self_transform = self.get_controller(Transform)
        other_transform = other_entity.get_controller(Transform)

        if self_transform and other_transform:
            return ((self_transform.x - other_transform.x) ** 2 +
                   (self_transform.y - other_transform.y) ** 2) ** 0.5

        return float('inf')

    def get_ai_stats(self) -> Dict[str, Any]:
        """Get comprehensive AI statistics."""
        return {
            "ai_type": self.ai_type,
            "is_active": self.is_active,
            "current_goal": self.current_goal,
            "behavior_state": self.behavior_state,
            "current_state": self.state_machine.current_state.name if self.state_machine.current_state else "none",
            "attributes": self.attribute_system.get_all_values(),
            "attribute_stats": self.attribute_system.get_statistics(),
            "visible_entities": len(self.visible_entities),
            "memory_entries": len(self.memory),
            "actions_performed": self.actions_performed,
            "decisions_made": self.decisions_made,
            "interactions": self.interactions,
            "awareness_radius": self.awareness_radius
        }

    def root(self) -> EnvironmentEntity:
        """Find the root entity in the scene graph."""
        current = self
        while current.parent:
            current = current.parent
        return current

    def update(self, delta_time: float):
        """Update AI systems."""
        # Update attribute system (effects, etc.)
        self.attribute_system.update(delta_time)

        # Update state machine
        self.state_machine.update(delta_time)

        # Update effect manager
        self.effect_manager.update_effects(delta_time)

        # AI thinking (simplified)
        current_time = 0  # Would use real time
        if current_time - self.last_decision_time > 2.0:  # Think every 2 seconds
            decision = self.make_decision(current_time)
            self.execute_action(decision)

    def __repr__(self):
        intelligence = self.attribute_system.get_value("intelligence", 50)
        aggression = self.attribute_system.get_value("aggression", 0.5)
        return f"<BotAgentEntity(name='{self.name}', type='{self.ai_type}', goal='{self.current_goal}', int={intelligence}, agg={aggression:.1f})>"


# Simplified existing entities (StaticEntity, InteractiveEntity, CameraEntity, Scene remain similar)
# but could be enhanced to use abstract systems as well...

class StaticEntity(EnvironmentEntity):
    """
    A non-interactive entity representing world geometry or static objects.

    Features:
    - No behavior or AI
    - Collision geometry only
    - Visual representation
    - Performance optimizations (no controller updates)
    """

    def __init__(self, name: str, entity_type: str = "geometric", position: Tuple[float, float] = (0,
