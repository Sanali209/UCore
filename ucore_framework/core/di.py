# framework/di.py
import inspect
import sys
from enum import Enum
from typing import Any, Callable, Dict, List, Type, TypeVar, get_origin, get_args, Union, Generic, Optional

T = TypeVar('T')

class Scope(Enum):
    SINGLETON = "singleton"
    TRANSIENT = "transient"

class DependencyError(Exception):
    """Base exception for dependency injection errors."""

class CircularDependencyError(DependencyError):
    """Raised when a circular dependency is detected."""

class NoProviderError(DependencyError):
    """Raised when no provider is found for a dependency."""

class Container(Generic[T]):
    """
    A Dependency Injection container that manages object lifetimes,
    detects circular dependencies, and supports explicit registration.
    """
    def __init__(self: 'Container[T]') -> None:
        self._providers: Dict[Type[Any], Any] = {}
        self._singletons: Dict[Type[Any], Any] = {}

    def register(
        self,
        dependency: Type[T],
        implementation: Optional[Type[Any]] = None,
        scope: Scope = Scope.TRANSIENT
    ) -> None:
        """
        Registers a dependency with a specific implementation and scope.
        """
        if implementation is None:
            implementation = dependency

        if not inspect.isclass(implementation):
            raise TypeError("Implementation must be a class.")

        self._providers[dependency] = (implementation, scope)

    def register_instance(self, instance: T, dependency: Optional[Type[T]] = None) -> None:
        """
        Registers a pre-existing instance as a singleton.
        """
        if dependency is None:
            dependency = type(instance)
        self._singletons[dependency] = instance

    def get(self, dependency: Type[T]) -> T:
        """
        Resolves and returns an instance of a dependency.
        """
        if dependency not in self._singletons:
            if dependency not in self._providers:
                raise NoProviderError(f"No provider found for {dependency.__name__}")
            implementation, scope = self._providers[dependency]
            instance = implementation()
            if scope == Scope.SINGLETON:
                self._singletons[dependency] = instance
            else:
                return instance
        return self._singletons[dependency]

def Depends(dependency: Callable[..., Any]) -> Any:
    """
    Marks a parameter as a dependency to be resolved by the container.
    This is primarily for use in functions or methods outside of class constructors.
    """
    setattr(dependency, '_is_dependency_marker', True)
    return dependency

# --- MVVM/Advanced Feature Registrations ---
try:
    from ucore_framework.mvvm.data_provisioning import DataProvisioningMixin
    from ucore_framework.mvvm.transformation_pipeline import TransformationPipelineMixin
    from ucore_framework.mvvm.grouping_filter import GroupingFilterMixin
    from ucore_framework.mvvm.data_provider import DataProviderPluginBase
    container = Container()
    container.register_instance(DataProvisioningMixin())
    container.register_instance(TransformationPipelineMixin())
    container.register_instance(GroupingFilterMixin())
    container.register_instance(DataProviderPluginBase)
except ImportError:
    pass
