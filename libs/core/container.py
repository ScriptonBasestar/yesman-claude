# Copyright notice.

from collections.abc import Callable
from typing import object, TypeVar, cast

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Dependency Injection Container for managing service instances and dependencies."""


T = TypeVar("T")


class DIContainer:
    """Dependency Injection Container.

    Provides service registration and resolution with support for:
    - Singleton instances
    - Factory functions
    - Type-safe service resolution
    - Lifecycle management
    """

    def __init__(self) -> None:
        self._services: dict[type, object] = {}
        self._factories: dict[type, Callable] = {}
        self._singletons: dict[type, object] = {}
        self._resolving: set = set()  # Track circular dependencies

    def register_singleton(self, service_type: type[T], instance: T) -> None:
        """Register a singleton instance.

        Args:
            service_type: The type/interface to register
            instance: The singleton instance to register."""
        self._singletons[service_type] = instance
        # Remove from factories if it was registered there
        self._factories.pop(service_type, None)
        self._services.pop(service_type, None)

    def register_factory(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """Register a factory function.

        Args:
            service_type: The type/interface to register
            factory: Factory function that creates instances."""
        self._factories[service_type] = factory
        # Remove from singletons if it was registered there
        self._singletons.pop(service_type, None)
        self._services.pop(service_type, None)

    def register_transient(self, service_type: type[T], factory: Callable[[], T]) -> None:
        """Register a transient service (new instance each time).

        Args:
            service_type: The type/interface to register
            factory: Factory function that creates instances."""
        self._services[service_type] = factory
        # Remove from other registrations
        self._singletons.pop(service_type, None)
        self._factories.pop(service_type, None)

    def resolve(self, service_type: type[T]) -> T:
        """Resolve a service instance.

        Args:
            service_type: The type/interface to resolve

        Returns:
            Instance of the requested service

        Raises:
            ValueError: If service is not registered or circular dependency detected
        """
        # Check for circular dependencies
        if service_type in self._resolving:
            msg = f"Circular dependency detected for {service_type.__name__}"
            raise ValueError(msg)

        # Check singleton first
        if service_type in self._singletons:
            return cast("T", self._singletons[service_type])

        # Check factory (lazy singleton)
        if service_type in self._factories:
            self._resolving.add(service_type)
            try:
                instance = self._factories[service_type]()
                self._singletons[service_type] = instance
                self._factories.pop(service_type)
                return cast("T", instance)
            finally:
                self._resolving.discard(service_type)

        # Check transient service
        if service_type in self._services:
            self._resolving.add(service_type)
            try:
                return cast("T", self._services[service_type]())
            finally:
                self._resolving.discard(service_type)

        msg = f"Service {service_type.__name__} is not registered"
        raise ValueError(msg)

    def is_registered(self, service_type: type[T]) -> bool:
        """Check if a service type is registered.

        Args:
            service_type: The type/interface to check

        Returns:
            True if service is registered, False otherwise
        """
        return service_type in self._singletons or service_type in self._factories or service_type in self._services

    def clear(self) -> None:
        """Clear all registrations and reset the container."""
        self._services.clear()
        self._factories.clear()
        self._singletons.clear()
        self._resolving.clear()

    def get_registered_services(self) -> dict[str, str]:
        """Get information about all registered services.

        Returns:
            Dictionary mapping service names to registration types
        """
        info = {}

        for service_type in self._singletons:
            info[service_type.__name__] = "singleton"

        for service_type in self._factories:
            info[service_type.__name__] = "factory"

        for service_type in self._services:
            info[service_type.__name__] = "transient"

        return info


# Global container instance
container = DIContainer()
