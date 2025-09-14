# tests/test_simulation.py
import pytest
from framework.simulation.entity import EnvironmentEntity
from framework.simulation.controller import EntityController

def test_entity_creation():
    """Tests basic entity creation."""
    entity = EnvironmentEntity(name="test_entity")
    assert entity.name == "test_entity"
    assert entity.parent is None
    assert len(entity.children) == 0
    assert len(entity.controllers) == 0

def test_entity_parent_child_relationship():
    """Tests adding and removing child entities."""
    parent = EnvironmentEntity(name="parent")
    child1 = EnvironmentEntity(name="child1")
    child2 = EnvironmentEntity(name="child2")

    parent.add_child(child1)
    parent.add_child(child2)

    assert len(parent.children) == 2
    assert child1.parent == parent
    assert child2.parent == parent

    parent.remove_child(child1)
    assert len(parent.children) == 1
    assert child1.parent is None
    assert parent.children[0] == child2

    # Test re-parenting
    new_parent = EnvironmentEntity(name="new_parent")
    new_parent.add_child(child2)
    assert len(parent.children) == 0
    assert child2.parent == new_parent

def test_controller_attachment():
    """Tests adding and retrieving controllers."""
    entity = EnvironmentEntity(name="controlled_entity")
    
    class TestControllerA(EntityController):
        pass

    class TestControllerB(EntityController):
        pass

    controller_a = entity.add_controller(TestControllerA())
    controller_b = entity.add_controller(TestControllerB())

    assert len(entity.controllers) == 2
    assert controller_a.entity == entity
    assert controller_b.entity == entity

    # Test retrieving controllers
    retrieved_a = entity.get_controller(TestControllerA)
    retrieved_b = entity.get_controller(TestControllerB)
    
    assert retrieved_a is controller_a
    assert retrieved_b is controller_b

def test_get_missing_controller():
    """Tests that get_controller returns None if the controller is not found."""
    entity = EnvironmentEntity(name="entity")
    class MissingController(EntityController):
        pass
    
    assert entity.get_controller(MissingController) is None

def test_controller_access_entity_before_attachment():
    """
    Tests that accessing the .entity property of a controller before it's
    attached to an entity raises a RuntimeError.
    """
    controller = EntityController()
    with pytest.raises(RuntimeError):
        _ = controller.entity
