import pytest

from libs.core.container import DIContainer, container
from libs.core.services import (
    get_config,
    get_tmux_manager,
    initialize_services,
    register_test_services,
)
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Tests for the Dependency Injection Container."""


class TestDIContainer:
    """Test cases for DIContainer."""

    def setup_method(self) -> None:
        """Set up test environment before each test."""
        self.container = DIContainer()

    def test_register_and_resolve_singleton(self) -> None:
        """Test singleton registration and resolution."""
        config = YesmanConfig()
        self.container.register_singleton(YesmanConfig, config)

        resolved = self.container.resolve(YesmanConfig)
        assert resolved is config

        # Should return the same instance
        resolved2 = self.container.resolve(YesmanConfig)
        assert resolved2 is config

    def test_register_and_resolve_factory(self) -> None:
        """Test factory registration and resolution."""
        call_count = 0

        def config_factory() -> object:
            nonlocal call_count
            call_count += 1
            return YesmanConfig()

        self.container.register_factory(YesmanConfig, config_factory)

        # First resolution should call factory and cache result
        resolved1 = self.container.resolve(YesmanConfig)
        assert call_count == 1
        assert isinstance(resolved1, YesmanConfig)

        # Second resolution should return cached instance
        resolved2 = self.container.resolve(YesmanConfig)
        assert call_count == 1  # Should not call factory again
        assert resolved2 is resolved1

    def test_register_and_resolve_transient(self) -> None:
        """Test transient service registration and resolution."""
        call_count = 0

        def config_factory() -> object:
            nonlocal call_count
            call_count += 1
            return YesmanConfig()

        self.container.register_transient(YesmanConfig, config_factory)

        # Each resolution should call factory
        resolved1 = self.container.resolve(YesmanConfig)
        assert call_count == 1
        assert isinstance(resolved1, YesmanConfig)

        resolved2 = self.container.resolve(YesmanConfig)
        assert call_count == 2  # Should call factory again
        assert resolved2 is not resolved1  # Should be different instances

    def test_service_not_registered(self) -> None:
        """Test error when resolving unregistered service."""
        with pytest.raises(ValueError, match="Service YesmanConfig is not registered"):
            self.container.resolve(YesmanConfig)

    def test_circular_dependency_detection(self) -> None:
        """Test circular dependency detection."""

        def factory_a() -> object:
            return self.container.resolve(TmuxManager)  # This would create a circular dependency

        def factory_b() -> object:
            return self.container.resolve(YesmanConfig)

        self.container.register_factory(YesmanConfig, factory_a)
        self.container.register_factory(TmuxManager, factory_b)

        with pytest.raises(ValueError, match="Circular dependency detected"):
            self.container.resolve(YesmanConfig)

    def test_is_registered(self) -> None:
        """Test is_registered method."""
        assert not self.container.is_registered(YesmanConfig)

        self.container.register_singleton(YesmanConfig, YesmanConfig())
        assert self.container.is_registered(YesmanConfig)

    def test_clear_container(self) -> None:
        """Test clearing the container."""
        config = YesmanConfig()
        self.container.register_singleton(YesmanConfig, config)
        assert self.container.is_registered(YesmanConfig)

        self.container.clear()
        assert not self.container.is_registered(YesmanConfig)

    def test_get_registered_services(self) -> None:
        """Test getting information about registered services."""
        config = YesmanConfig()
        self.container.register_singleton(YesmanConfig, config)
        self.container.register_factory(TmuxManager, lambda: TmuxManager(config))

        services = self.container.get_registered_services()
        assert "YesmanConfig" in services
        assert "TmuxManager" in services
        assert services["YesmanConfig"] == "singleton"
        assert services["TmuxManager"] == "factory"


class TestServicesModule:
    """Test cases for the services module."""

    @staticmethod
    def setup_method() -> None:
        """Set up test environment before each test."""
        # Clear container before each test

        container.clear()

    @staticmethod
    def test_register_test_services() -> None:
        """Test registering mock services for testing."""
        mock_config = YesmanConfig()
        register_test_services(config=mock_config)

        resolved_config = get_config()
        assert resolved_config is mock_config

    @staticmethod
    def test_get_convenience_functions() -> None:
        """Test convenience functions for getting services."""
        register_test_services()

        config = get_config()
        assert isinstance(config, YesmanConfig)

        tmux_manager = get_tmux_manager()
        assert isinstance(tmux_manager, TmuxManager)

    @staticmethod
    def test_auto_initialization() -> None:
        """Test that services are auto-initialized when module is imported."""
        # Since we cleared the container in setup_method, we need to trigger initialization

        initialize_services()

        # Should be able to resolve services without explicit registration
        config = get_config()
        assert isinstance(config, YesmanConfig)

        tmux_manager = get_tmux_manager()
        assert isinstance(tmux_manager, TmuxManager)
