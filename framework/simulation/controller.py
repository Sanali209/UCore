# framework/simulation/controller.py
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .entity import EnvironmentEntity

class EntityController:
    """
    Base class for all controllers that can be attached to an EnvironmentEntity.
    
    Controllers define the behavior of an entity.
    """
    def __init__(self):
        self._entity: EnvironmentEntity | None = None

    @property
    def entity(self) -> EnvironmentEntity:
        """The entity this controller is attached to."""
        if self._entity is None:
            raise RuntimeError("Controller is not attached to an entity.")
        return self._entity

    @entity.setter
    def entity(self, value: EnvironmentEntity):
        self._entity = value

    def start(self):
        """Called when the simulation starts or the controller is added."""
        pass

    def stop(self):
        """Called when the simulation stops or the controller is removed."""
        pass

    def update(self, delta_time: float):
        """
        Called on every simulation tick.
        
        :param delta_time: The time elapsed since the last frame.
        """
        pass

    def __repr__(self):
        return f"<{self.__class__.__name__}>"
