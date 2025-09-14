# framework/di.py
import inspect
from enum import Enum
from typing import Any, Callable, Dict, List, Type, TypeVar

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

class Container:
    """
    A Dependency Injection container that manages object lifetimes,
    detects circular dependencies, and supports explicit registration.
    """
    def __init__(self):
        self._providers: Dict[Type[Any], tuple[Type[Any], Scope]] = {}
        self._singletons: Dict[Type[Any], Any] = {}

    def register(
        self,
        dependency: Type[T],
        implementation: Type[Any] = None,
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

    def register_instance(self, instance: Any, dependency: Type[Any] = None) -> None:
        """
        Registers a pre-existing instance as a singleton.
        """
        if dependency is None:
            dependency = type(instance)
        self._singletons[dependency] = instance

    def get(self, dependency: Type[T], resolve_path: List[Type[Any]] = None) -> T:
        """
        Resolves and returns an instance of a dependency.
        """
        if resolve_path is None:
            resolve_path = []

        if dependency in resolve_path:
            path = " -> ".join(getattr(d, '__name__', str(d)) for d in resolve_path) + f" -> {getattr(dependency, '__name__', str(dependency))}"
            raise CircularDependencyError(f"Circular dependency detected: {path}")

        resolve_path.append(dependency)

        if dependency in self._singletons:
            return self._singletons[dependency]

        provider = self._providers.get(dependency)
        if not provider:
            raise NoProviderError(f"No provider found for {dependency.__name__}")

        implementation, scope = provider

        # Resolve constructor parameters
        params = inspect.signature(implementation).parameters
        dependencies = {}
        primitive_types = (str, int, float, bool, type(None))
        for name, param in params.items():
            if param.annotation is not inspect.Parameter.empty:
                resolved_type = None
                if isinstance(param.annotation, str):
                    # Handle forward references
                    try:
                        # Attempt to resolve the string annotation to a type
                        # Look in the implementation class's module first, then test module, then globally
                        module = getattr(implementation, '__module__', '')
                        globals_dict = {}

                        # Add commonly used framework classes to globals
                        import framework.app
                        import framework.component
                        import framework.config
                        import framework.logging

                        # Add framework modules' classes
                        for mod in [framework.app, framework.component, framework.config, framework.logging]:
                            globals_dict.update(mod.__dict__)

                        # Try to resolve simple class names from module's globals
                        if module and module in sys.modules:
                            globals_dict.update(sys.modules[module].__dict__)

                        # Fallback: try direct lookup if it's a simple class name
                        if param.annotation in globals_dict:
                            resolved_type = globals_dict[param.annotation]
                        else:
                            resolved_type = eval(param.annotation, globals_dict)
                    except (NameError, AttributeError):
                        try:
                            # Try with builtins if local resolution fails
                            resolved_type = eval(param.annotation, __builtins__)
                        except:
                            resolved_type = None
                else:
                    resolved_type = param.annotation
                if resolved_type is not None and resolved_type not in primitive_types:
                    dependencies[name] = self.get(resolved_type, resolve_path[:])
                # If resolved_type is None (unresolved forward reference), skip the argument

        instance = implementation(**dependencies)

        if scope == Scope.SINGLETON:
            self._singletons[dependency] = instance

        return instance

def Depends(dependency: Callable[..., Any]) -> Any:
    """
    Marks a parameter as a dependency to be resolved by the container.
    This is primarily for use in functions or methods outside of class constructors.
    """
    setattr(dependency, '_is_dependency_marker', True)
    return dependency
