"""Dependency injection container."""

from typing import Dict, Any, Type, Callable, Optional
import threading
from functools import wraps


class DIContainer:
    """Simple dependency injection container."""
    
    def __init__(self):
        """Initialize the container."""
        self._services: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._singletons: Dict[Type, Any] = {}
        self._lock = threading.Lock()
    
    def register(
        self,
        interface: Type,
        implementation: Any = None,
        factory: Callable = None,
        singleton: bool = True
    ) -> None:
        """Register a service in the container."""
        with self._lock:
            if factory:
                self._factories[interface] = factory
                if singleton:
                    self._singletons[interface] = None
            elif implementation:
                if singleton:
                    self._services[interface] = implementation
                else:
                    self._factories[interface] = lambda: implementation
            else:
                raise ValueError("Either implementation or factory must be provided")
    
    def resolve(self, interface: Type) -> Any:
        """Resolve a service from the container."""
        with self._lock:
            # Check if it's a singleton service
            if interface in self._services:
                return self._services[interface]
            
            # Check if it's a singleton factory that's already been created
            if interface in self._singletons:
                if self._singletons[interface] is not None:
                    return self._singletons[interface]
            
            # Check if it's a factory
            if interface in self._factories:
                instance = self._factories[interface]()
                
                # Cache singleton instances
                if interface in self._singletons:
                    self._singletons[interface] = instance
                
                return instance
            
            raise KeyError(f"Service {interface} not registered")
    
    def register_instance(self, interface: Type, instance: Any) -> None:
        """Register an existing instance as a singleton."""
        with self._lock:
            self._services[interface] = instance
    
    def has_service(self, interface: Type) -> bool:
        """Check if a service is registered."""
        return (
            interface in self._services or
            interface in self._factories
        )
    
    def clear(self) -> None:
        """Clear all registered services."""
        with self._lock:
            self._services.clear()
            self._factories.clear()
            self._singletons.clear()


# Global container instance
_container: Optional[DIContainer] = None
_container_lock = threading.Lock()


def get_container() -> DIContainer:
    """Get the global dependency injection container."""
    global _container
    with _container_lock:
        if _container is None:
            _container = DIContainer()
        return _container


def inject(**dependencies):
    """Decorator for dependency injection."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()
            
            # Inject dependencies
            for name, interface in dependencies.items():
                if name not in kwargs:
                    kwargs[name] = container.resolve(interface)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator


def injectable(interface: Type):
    """Class decorator to make a class injectable."""
    def decorator(cls):
        # Register the class with the container
        container = get_container()
        container.register(interface, factory=cls, singleton=True)
        return cls
    return decorator