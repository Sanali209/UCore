"""
Action System for UCore Simulation Framework
===========================================

High-level action execution system providing composable behavior patterns,
movement controls, and interaction frameworks for simulation entities.

Action Types:
- MovementAction: Navigation and locomotion behaviors
- InteractionAction: Entity-to-entity and object interactions
- CommunicationAction: Messaging and signaling between entities
- CompositeAction: Sequential and parallel action execution
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional, Callable, Type, Tuple
from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass
import time
import math

from .entity import EnvironmentEntity
from .controllers import Transform


class ActionStatus(Enum):
    """Possible states of an action execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ActionPriority(Enum):
    """Action execution priorities for queue management."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ActionResult:
    """Result information from action execution."""
    success: bool
    status: ActionStatus
    data: Dict[str, Any] = None
    message: str = ""
    duration: float = 0.0

    def __post_init__(self):
        if self.data is None:
            self.data = {}


class Action(ABC):
    """
    Abstract base class for all executable actions in the simulation.

    Actions represent atomic behaviors that entities can perform.
    They can be combined, sequenced, or executed conditionally.
    """

    def __init__(self, name: str = "", priority: ActionPriority = ActionPriority.NORMAL,
                 timeout: float = -1.0, can_interrupt: bool = True):
        self.name = name or self.__class__.__name__
        self.priority = priority
        self.timeout = timeout  # -1 for no timeout
        self.can_interrupt = can_interrupt

        # Execution state
        self.status = ActionStatus.PENDING
        self.start_time = 0.0
        self.entity: Optional[EnvironmentEntity] = None

        # Callbacks
        self.on_complete: Optional[Callable[[ActionResult], None]] = None
        self.on_fail: Optional[Callable[[ActionResult], None]] = None
        self.on_cancel: Optional[Callable[[], None]] = None

    def assign_entity(self, entity: EnvironmentEntity):
        """Assign this action to an entity."""
        self.entity = entity

    def start(self, entity: EnvironmentEntity) -> ActionResult:
        """Start executing the action."""
        self.entity = entity
        self.status = ActionStatus.RUNNING
        self.start_time = time.time()

        try:
            result = self._start_impl()
            if isinstance(result, ActionResult):
                return result
            elif result is True or result is None:
                return ActionResult(True, ActionStatus.RUNNING, message="Action started successfully")
            else:
                return ActionResult(False, ActionStatus.FAILED, message=str(result))
        except Exception as e:
            return ActionResult(False, ActionStatus.FAILED, message=f"Start failed: {e}")

    def update(self, delta_time: float) -> ActionResult:
        """Update action execution. Called each frame while running."""
        if self.status != ActionStatus.RUNNING:
            return ActionResult(False, self.status, message="Action not running")

        # Check timeout
        if self.timeout > 0 and time.time() - self.start_time > self.timeout:
            self.status = ActionStatus.FAILED
            result = ActionResult(False, ActionStatus.FAILED, message="Action timed out")
            if self.on_fail:
                self.on_fail(result)
            return result

        try:
            update_result = self._update_impl(delta_time)
            if isinstance(update_result, ActionResult):
                if update_result.success and update_result.status == ActionStatus.COMPLETED:
                    self._complete(update_result)
                    return update_result
                elif not update_result.success:
                    self._fail(update_result)
                    return update_result
                return update_result
            elif update_result is True:
                result = ActionResult(True, ActionStatus.COMPLETED, message="Action completed")
                self._complete(result)
                return result
            else:
                return ActionResult(True, ActionStatus.RUNNING)

        except Exception as e:
            result = ActionResult(False, ActionStatus.FAILED, message=f"Update failed: {e}")
            self._fail(result)
            return result

    def cancel(self):
        """Cancel the action execution."""
        if self.status == ActionStatus.RUNNING:
            self.status = ActionStatus.CANCELLED
            self._cancel_impl()
            if self.on_cancel:
                self.on_cancel()

    @abstractmethod
    def _start_impl(self) -> Any:
        """Implementation of action start logic."""
        pass

    @abstractmethod
    def _update_impl(self, delta_time: float) -> Any:
        """Implementation of action update logic."""
        pass

    def _cancel_impl(self):
        """Implementation of action cancellation cleanup."""
        pass

    def _complete(self, result: ActionResult):
        """Handle action completion."""
        self.status = ActionStatus.COMPLETED
        result.duration = time.time() - self.start_time
        if self.on_complete:
            self.on_complete(result)

    def _fail(self, result: ActionResult):
        """Handle action failure."""
        self.status = ActionStatus.FAILED
        result.duration = time.time() - self.start_time
        if self.on_fail:
            self.on_fail(result)

    def can_interrupt_current(self) -> bool:
        """Check if this action can interrupt the current action."""
        return self.can_interrupt

    def get_description(self) -> str:
        """Get human-readable description of the action."""
        return f"{self.name} (priority: {self.priority.name})"

    def __repr__(self):
        return f"<{self.__class__.__name__}(name='{self.name}', status='{self.status.value}')>"


class MovementAction(Action):
    """
    Base class for movement and navigation actions.

    Provides path planning, obstacle avoidance, and movement execution.
    """

    def __init__(self, target_position: Tuple[float, float], speed: float = 5.0,
                 tolerance: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.target_position = target_position
        self.speed = speed
        self.tolerance = tolerance
        self.path: List[Tuple[float, float]] = []
        self.current_path_index = 0

    def _start_impl(self) -> Any:
        """Calculate path to target and begin movement."""
        if not self.entity:
            return False

        transform = self.entity.get_controller(Transform)
        if not transform:
            return "Entity has no transform component"

        # For now, direct path (would use proper pathfinding)
        self.path = [self.target_position]
        self.current_path_index = 0

        print(f"🚶 {self.entity.name} starting movement to {self.target_position}")
        return True

    def _update_impl(self, delta_time: float) -> Any:
        """Move towards target position."""
        if not self.entity:
            return False

        transform = self.entity.get_controller(Transform)
        if not transform:
            return False

        if not self.path:
            return True  # No path, complete immediately

        # Get current waypoint
        current_target = self.path[self.current_path_index]

        # Calculate direction and distance
        dx = current_target[0] - transform.x
        dy = current_target[1] - transform.y
        distance = math.sqrt(dx*dx + dy*dy)

        if distance <= self.tolerance:
            # Reached waypoint
            if self.current_path_index >= len(self.path) - 1:
                # Final destination reached
                transform.x = self.target_position[0]
                transform.y = self.target_position[1]
                return True
            else:
                # Move to next waypoint
                self.current_path_index += 1
        else:
            # Move towards current target
            if distance > 0:
                move_distance = self.speed * delta_time
                ratio = move_distance / distance

                # Don't overshoot
                ratio = min(ratio, 1.0)

                transform.x += dx * ratio
                transform.y += dy * ratio

        return False  # Still moving


class WalkAction(MovementAction):
    """Walk to a specific position at normal speed."""

    def __init__(self, target_position: Tuple[float, float], **kwargs):
        super().__init__(target_position, speed=3.0, **kwargs)
        if not self.name or self.name == "WalkAction":
            self.name = f"Walk to {target_position}"


class RunAction(MovementAction):
    """Run to a specific position at increased speed."""

    def __init__(self, target_position: Tuple[float, float], **kwargs):
        super().__init__(target_position, speed=8.0, **kwargs)
        if not self.name or self.name == "RunAction":
            self.name = f"Run to {target_position}"


class PatrolAction(Action):
    """Patrol between multiple waypoints."""

    def __init__(self, waypoints: List[Tuple[float, float]], loop: bool = True,
                 speed: float = 3.0, **kwargs):
        super().__init__(**kwargs)
        self.waypoints = waypoints
        self.loop = loop
        self.speed = speed
        self.current_waypoint = 0
        self.movement_action: Optional[MovementAction] = None

    def _start_impl(self) -> Any:
        """Start patrolling through waypoints."""
        if not self.waypoints:
            return "No waypoints specified"

        self.current_waypoint = 0
        next_pos = self.waypoints[0]
        self.movement_action = MovementAction(next_pos, self.speed, can_interrupt=False)
        return self.movement_action.start(self.entity)

    def _update_impl(self, delta_time: float) -> Any:
        """Continue patrolling."""
        if not self.movement_action:
            return True

        result = self.movement_action.update(delta_time)

        if result.success and result.status == ActionStatus.COMPLETED:
            # Reached current waypoint, move to next
            self.current_waypoint += 1

            if self.current_waypoint >= len(self.waypoints):
                if self.loop:
                    self.current_waypoint = 0
                else:
                    return True  # Patrol complete

            next_pos = self.waypoints[self.current_waypoint]
            self.movement_action = MovementAction(next_pos, self.speed, can_interrupt=False)

            # Start next movement
            start_result = self.movement_action.start(self.entity)
            if not start_result.success:
                return start_result

        return False

    def get_description(self) -> str:
        return f"Patrol {len(self.waypoints)} waypoints"


class IdleAction(Action):
    """Do nothing for a specified duration."""

    def __init__(self, duration: float = 1.0, **kwargs):
        super().__init__(**kwargs)
        self.duration = duration

    def _start_impl(self) -> Any:
        """Start idle timer."""
        print(f"😐 {self.entity.name if self.entity else 'Entity'} idling for {self.duration}s")
        return True

    def _update_impl(self, delta_time: float) -> Any:
        """Wait until duration expires."""
        return time.time() - self.start_time >= self.duration


class InteractionAction(Action):
    """Base class for actions that interact with other entities or objects."""

    def __init__(self, target_entity: EnvironmentEntity, **kwargs):
        super().__init__(**kwargs)
        self.target_entity = target_entity
        self.interaction_range = 50.0

    def _start_impl(self) -> Any:
        """Check if interaction is possible."""
        if not self.entity or not self.target_entity:
            return False

        # Check distance
        distance = self._calculate_distance()
        if distance > self.interaction_range:
            return f"Target too far ({distance:.1f} > {self.interaction_range})"

        print(f"🤝 {self.entity.name} interacting with {self.target_entity.name}")
        return True

    def _calculate_distance(self) -> float:
        """Calculate distance to target entity."""
        if not self.entity or not self.target_entity:
            return float('inf')

        entity_transform = self.entity.get_controller(Transform)
        target_transform = self.target_entity.get_controller(Transform)

        if entity_transform and target_transform:
            dx = target_transform.x - entity_transform.x
            dy = target_transform.y - entity_transform.y
            return math.sqrt(dx*dx + dy*dy)

        return float('inf')


class ExamineAction(InteractionAction):
    """Examine an entity or object in detail."""

    def _start_impl(self) -> Any:
        result = super()._start_impl()
        if not result or result is not True:
            return result

        print(f"👁️ {self.entity.name} examines {self.target_entity.name}")
        # Could trigger detailed examination UI or information display
        return True

    def _update_impl(self, delta_time: float) -> Any:
        """Examination is instantaneous."""
        return True


class UseAction(InteractionAction):
    """Use an interactive entity or object."""

    def _start_impl(self) -> Any:
        result = super()._start_impl()
        if not result or result is not True:
            return result

        # Check if target supports interaction
        if hasattr(self.target_entity, 'interact'):
            interaction_result = self.target_entity.interact(self.entity, 'use')
            if interaction_result:
                print(f"🔧 {self.entity.name} uses {self.target_entity.name}")
                return True
            else:
                return "Interaction not allowed"
        else:
            return "Target not interactive"

    def _update_impl(self, delta_time: float) -> Any:
        return True


class PickupAction(InteractionAction):
    """Pick up an object or item."""

    def _start_impl(self) -> Any:
        result = super()._start_impl()
        if not result or result is not True:
            return result

        # Check if target can be picked up
        if hasattr(self.target_entity, 'interact'):
            interaction_result = self.target_entity.interact(self.entity, 'pickup')
            if interaction_result:
                print(f"📦 {self.entity.name} picks up {self.target_entity.name}")
                # Remove from scene (would need scene reference)
                return True
            else:
                return "Cannot pick up target"
        else:
            return "Target not pickupable"

    def _update_impl(self, delta_time: float) -> Any:
        return True


class CommunicationAction(Action):
    """Send a message to one or more entities."""

    def __init__(self, message: str, recipients: List[EnvironmentEntity] = None, **kwargs):
        super().__init__(**kwargs)
        self.message = message
        self.recipients = recipients or []

    def _start_impl(self) -> Any:
        """Send the message."""
        if not self.entity:
            return False

        if not self.recipients:
            # Broadcast to all entities (would need scene reference)
            print(f"📢 {self.entity.name} broadcasts: '{self.message}'")
        else:
            for recipient in self.recipients:
                print(f"💬 {self.entity.name} → {recipient.name}: '{self.message}'")

        return True

    def _update_impl(self, delta_time: float) -> Any:
        """Communication is instantaneous."""
        return True


class CompositeAction(Action):
    """Execute multiple actions in sequence or parallel."""

    def __init__(self, actions: List[Action], parallel: bool = False,
                 fail_on_first_failure: bool = True, **kwargs):
        super().__init__(**kwargs)
        self.actions = actions
        self.parallel = parallel  # True for parallel, False for sequential
        self.fail_on_first_failure = fail_on_first_failure

        self.completed_actions: List[Action] = []
        self.running_actions: List[Action] = []
        self.failed_actions: List[Action] = []

    def _start_impl(self) -> Any:
        """Start all actions (parallel) or first action (sequential)."""
        if not self.actions:
            return "No actions to execute"

        if self.parallel:
            # Start all actions
            for action in self.actions:
                action.assign_entity(self.entity)
                result = action.start(self.entity)
                if result.success:
                    self.running_actions.append(action)
                else:
                    self.failed_actions.append(action)
                    if self.fail_on_first_failure:
                        return f"Action failed: {result.message}"
        else:
            # Start first action
            first_action = self.actions[0]
            first_action.assign_entity(self.entity)
            result = first_action.start(self.entity)
            if result.success:
                self.running_actions.append(first_action)
            else:
                return f"First action failed: {result.message}"

        return True

    def _update_impl(self, delta_time: float) -> Any:
        """Update all running actions."""
        if not self.running_actions:
            return True  # All done

        # Update all running actions
        completed_this_frame = []

        for action in self.running_actions[:]:  # Copy to avoid modification
            result = action.update(delta_time)

            if result.success and result.status == ActionStatus.COMPLETED:
                self.completed_actions.append(action)
                self.running_actions.remove(action)
                completed_this_frame.append(action)
            elif not result.success:
                self.failed_actions.append(action)
                self.running_actions.remove(action)
                if self.fail_on_first_failure:
                    return False

        # If sequential, start next action when current completes
        if not self.parallel and completed_this_frame and self.actions:
            next_index = len(self.completed_actions)
            if next_index < len(self.actions):
                next_action = self.actions[next_index]
                next_action.assign_entity(self.entity)
                result = next_action.start(self.entity)
                if result.success:
                    self.running_actions.append(next_action)
                else:
                    if self.fail_on_first_failure:
                        return False

        # Check if all actions completed
        if not self.running_actions:
            if self.failed_actions and self.fail_on_first_failure:
                return False
            return True

        return False

    def _cancel_impl(self):
        """Cancel all running actions."""
        for action in self.running_actions:
            action.cancel()
        self.running_actions.clear()

    def get_progress(self) -> Dict[str, Any]:
        """Get progress information."""
        return {
            "total_actions": len(self.actions),
            "completed": len(self.completed_actions),
            "running": len(self.running_actions),
            "failed": len(self.failed_actions),
            "mode": "parallel" if self.parallel else "sequential"
        }


class ActionQueue:
    """
    Queue and manager for executing actions with priorities and interruption.
    """

    def __init__(self, max_queue_size: int = 100):
        self.queue: List[Action] = []
        self.current_action: Optional[Action] = None
        self.max_queue_size = max_queue_size
        self.history: List[ActionResult] = []

    def enqueue(self, action: Action, entity: EnvironmentEntity) -> bool:
        """Add action to queue. Returns False if queue full."""
        if len(self.queue) >= self.max_queue_size:
            return False

        action.assign_entity(entity)
        self.queue.append(action)
        self._sort_queue()
        return True

    def interrupt_current(self, new_action: Action, entity: EnvironmentEntity) -> bool:
        """Interrupt current action with new higher-priority action."""
        if not new_action.can_interrupt_current():
            return False

        new_action.assign_entity(entity)

        # Check if new action has higher priority
        if self.current_action and new_action.priority.value <= self.current_action.priority.value:
            return False

        # Cancel current action
        if self.current_action:
            result = ActionResult(False, ActionStatus.CANCELLED,
                                message="Interrupted by higher priority action")
            self.history.append(result)

            if self.current_action.on_fail:
                self.current_action.on_fail(result)

            self.current_action.cancel()
            # Re-queue current action if it can be interrupted
            if self.current_action.can_interrupt:
                self.queue.insert(0, self.current_action)

        # Start new action
        self.current_action = new_action
        result = self.current_action.start(entity)
        if not result.success:
            self.current_action = None
            return False

        return True

    def update(self, delta_time: float):
        """Update current action and advance queue."""
        if not self.current_action:
            self._start_next_action()
            return

        # Update current action
        result = self.current_action.update(delta_time)

        if result.success and result.status == ActionStatus.COMPLETED:
            # Action completed successfully
            self.history.append(result)
            if self.current_action.on_complete:
                self.current_action.on_complete(result)

            self.current_action = None
            self._start_next_action()

        elif not result.success:
            # Action failed
            self.history.append(result)
            if self.current_action.on_fail:
                self.current_action.on_fail(result)

            self.current_action = None
            self._start_next_action()

    def clear_queue(self):
        """Clear all queued actions."""
        for action in self.queue:
            if action.on_fail:
                result = ActionResult(False, ActionStatus.CANCELLED, message="Queue cleared")
                action.on_fail(result)

        self.queue.clear()

    def _start_next_action(self):
        """Start the next action in queue."""
        if self.queue:
            next_action = self.queue.pop(0)
            result = next_action.start(next_action.entity)

            if result.success:
                self.current_action = next_action
            else:
                # Action failed to start, skip it
                self.history.append(result)
                if next_action.on_fail:
                    next_action.on_fail(result)

    def _sort_queue(self):
        """Sort queue by priority (highest first)."""
        self.queue.sort(key=lambda a: a.priority.value, reverse=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        return {
            "queue_size": len(self.queue),
            "has_current_action": self.current_action is not None,
            "current_action": self.current_action.name if self.current_action else None,
            "total_completed": len([h for h in self.history if h.success]),
            "total_failed": len([h for h in self.history if not h.success])
        }

    def __repr__(self):
        queue_names = [a.name for a in self.queue]
        current = self.current_action.name if self.current_action else "None"
        return f"<ActionQueue(current='{current}', queue={queue_names})>"


# ===== EXPORTS =====

__all__ = [
    'ActionStatus',
    'ActionPriority',
    'ActionResult',
    'Action',
    'MovementAction',
    'WalkAction',
    'RunAction',
    'PatrolAction',
    'IdleAction',
    'InteractionAction',
    'ExamineAction',
    'UseAction',
    'PickupAction',
    'CommunicationAction',
    'CompositeAction',
    'ActionQueue'
]
