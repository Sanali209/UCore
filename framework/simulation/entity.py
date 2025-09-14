# framework/simulation/entity.py
from __future__ import annotations
from typing import List, Type, TypeVar

T = TypeVar('T')

class EnvironmentEntity:
    """
    Represents an object in the simulation environment.
    
    An entity can have a parent and multiple children, forming a scene graph.
    It can also have controllers attached to it, which define its behavior.
    """
    def __init__(self, name: str):
        self.name = name
        self.parent: EnvironmentEntity | None = None
        self.children: List[EnvironmentEntity] = []
        self.controllers: List = [] # List of controller instances

    def add_child(self, child: EnvironmentEntity):
        """Adds a child entity to this entity."""
        if child.parent:
            child.parent.remove_child(child)
        child.parent = self
        self.children.append(child)

    def remove_child(self, child: EnvironmentEntity):
        """Removes a child entity from this entity."""
        if child in self.children:
            child.parent = None
            self.children.remove(child)

    def add_controller(self, controller_instance):
        """Adds a controller instance to this entity."""
        controller_instance.entity = self
        self.controllers.append(controller_instance)
        return controller_instance

    def get_controller(self, controller_type: Type[T]) -> T | None:
        """
        Finds and returns the first controller of a specific type.
        
        :param controller_type: The class of the controller to find.
        :return: The controller instance or None if not found.
        """
        for controller in self.controllers:
            if isinstance(controller, controller_type):
                return controller
        return None

    def __repr__(self):
        return f"<EnvironmentEntity(name='{self.name}')>"
