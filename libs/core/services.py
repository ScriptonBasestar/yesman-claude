# Copyright notice.

from libs.core.container import container
from libs.core.session_manager import SessionManager
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig
# Auto-initialize services when module is imported

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Service registration and DI container setup."""


def register_core_services() -> None:
    """Register all core services with the DI container."""
    # Register YesmanConfig as a singleton factory
    container.register_factory(YesmanConfig, YesmanConfig)

    # Register TmuxManager as a singleton factory that depends on YesmanConfig
    container.register_factory(TmuxManager, lambda: TmuxManager(container.resolve(YesmanConfig)))

    # Register SessionManager as a singleton factory
    container.register_factory(SessionManager, SessionManager)


def register_test_services(config: YesmanConfig | None = None, tmux_manager: TmuxManager | None = None) -> None:
    """Register mock services for testing.

    Args:
        config: Optional mock config instance
        tmux_manager: Optional mock tmux manager instance."""
    # Clear existing registrations
    container.clear()

    # Register provided mocks or create default ones
    if config is not None:
        container.register_singleton(YesmanConfig, config)
    else:
        container.register_factory(YesmanConfig, YesmanConfig)

    if tmux_manager is not None:
        container.register_singleton(TmuxManager, tmux_manager)
    else:
        container.register_factory(TmuxManager, lambda: TmuxManager(container.resolve(YesmanConfig)))

    # Always register SessionManager for tests
    container.register_factory(SessionManager, SessionManager)


def get_config() -> YesmanConfig:
    """Convenience function to get YesmanConfig from container.

    Returns:
        YesmanConfig: Description of return value.
    """
    return container.resolve(YesmanConfig)


def get_tmux_manager() -> TmuxManager:
    """Convenience function to get TmuxManager from container.

    Returns:
        TmuxManager: Description of return value.
    """
    return container.resolve(TmuxManager)


def get_session_manager() -> SessionManager:
    """Convenience function to get SessionManager from container.

    Returns:
        SessionManager: Description of return value.
    """
    return container.resolve(SessionManager)


def is_container_initialized() -> bool:
    """Check if the container has been initialized with core services.

    Returns:
        bool: Description of return value.
    """
    return container.is_registered(YesmanConfig) and container.is_registered(TmuxManager) and container.is_registered(SessionManager)


def initialize_services() -> None:
    """Initialize services if not already done."""
    if not is_container_initialized():
        register_core_services()


initialize_services()
