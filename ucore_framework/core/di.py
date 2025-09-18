# framework/di.py
import inspect
import sys
from enum import Enum
from typing import Any, Callable, Dict, List, Type, TypeVar, get_origin, get_args, Union

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
            # Only resolve if annotation is present and not a primitive or generic type
            if param.annotation is not inspect.Parameter.empty:
                resolved_type = None
                if isinstance(param.annotation, str):
                    # Handle forward references
                    try:
                        module = getattr(implementation, '__module__', '')
                        globals_dict = {}
                        import UCoreFrameworck.app
                        for mod in [UCoreFrameworck.app]:
                            globals_dict.update(mod.__dict__)
                        if module and module in sys.modules:
                            globals_dict.update(sys.modules[module].__dict__)
                        if param.annotation in globals_dict:
                            resolved_type = globals_dict[param.annotation]
                        else:
                            resolved_type = eval(param.annotation, globals_dict)
                    except (NameError, AttributeError):
                        try:
                            resolved_type = eval(param.annotation, __builtins__)
                        except:
                            resolved_type = None
                else:
                    resolved_type = param.annotation

                # Skip generic types (e.g., List, Dict, etc.)
                origin = get_origin(resolved_type)
                if origin is not None:
                    # For Optional[T] (Union), try to resolve T, else use default/None
                    if origin is Union:
                        args = get_args(resolved_type)
                        found = False
                        for arg in args:
                            if arg is not type(None) and isinstance(arg, type) and arg not in primitive_types:
                                try:
                                    dependencies[name] = self.get(arg, resolve_path[:])
                                    found = True
                                    break
                                except NoProviderError:
                                    continue
                        if not found:
                            # For Optionals, use default or None, never raise for required
                            if param.default is not inspect.Parameter.empty:
                                dependencies[name] = param.default
                            else:
                                dependencies[name] = None
                    # For other generics (List, Dict, etc.), skip resolution (use default)
                    continue

                elif resolved_type is not None and resolved_type not in primitive_types:
                    try:
                        dependencies[name] = self.get(resolved_type, resolve_path[:])
                    except NoProviderError:
                        if param.default is not inspect.Parameter.empty:
                            dependencies[name] = param.default
                        elif param.default is inspect.Parameter.empty and param.kind not in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                            raise NoProviderError(f"No provider found for required argument '{name}' in {implementation.__name__}")
                        else:
                            dependencies[name] = None
                # If unresolved or primitive, skip

        # Fill in missing required arguments with None if not provided
        for name, param in params.items():
            if name not in dependencies:
                if param.default is not inspect.Parameter.empty:
                    dependencies[name] = param.default
                else:
                    # If we are missing a required dependency, raise NoProviderError
                    raise NoProviderError(f"No provider found for required argument '{name}' in {implementation.__name__}")

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
