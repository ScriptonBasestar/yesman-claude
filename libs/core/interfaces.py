# Copyright notice.

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .models import SessionInfo
from .prompt_detector import PromptInfo

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Abstract base classes and interfaces for the yesman-claude system."""


class ControllerState(Enum):
    """Controller states."""

    READY = "ready"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class CacheStrategy(Enum):
    """Cache invalidation strategies."""

    TIME_BASED = "time_based"
    CONTENT_CHANGE = "content_change"
    DEPENDENCY = "dependency"
    MANUAL = "manual"


@dataclass
class PluginMetadata:
    """Plugin metadata information."""

    name: str
    version: str
    description: str
    author: str
    dependencies: list[str]
    enabled: bool = True


class ISessionManager(ABC):
    """Interface for session management."""

    @abstractmethod
    @staticmethod
    def get_all_sessions() -> list[SessionInfo]:
        """Get all available sessions."""

    @abstractmethod
    @staticmethod
    def get_session(session_name: str) -> SessionInfo | None:
        """Get a specific session by name."""

    @abstractmethod
    @staticmethod
    def invalidate_cache(session_name: str | None = None) -> None:
        """Invalidate session cache."""

    @abstractmethod
    @staticmethod
    def get_cache_stats() -> dict[str, Any]:
        """Get cache statistics."""


class IController(ABC):
    """Interface for Claude controllers."""

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if controller is running."""

    @property
    @abstractmethod
    def selected_model(self) -> str:
        """Get selected model."""

    @property
    @abstractmethod
    def is_auto_next_enabled(self) -> bool:
        """Check if auto next is enabled."""

    @abstractmethod
    @staticmethod
    def start() -> bool:
        """Start the controller."""

    @abstractmethod
    @staticmethod
    def stop() -> bool:
        """Stop the controller."""

    @abstractmethod
    @staticmethod
    def restart_claude_pane() -> bool:
        """Restart Claude pane."""

    @abstractmethod
    @staticmethod
    def set_model(model: str) -> bool:
        """Set the model."""

    @abstractmethod
    @staticmethod
    def set_auto_next(enabled: bool) -> bool:  # noqa: FBT001
        """Set auto next setting."""

    @abstractmethod
    @staticmethod
    def is_waiting_for_input() -> bool:
        """Check if waiting for input."""

    @abstractmethod
    @staticmethod
    def get_current_prompt() -> PromptInfo | None:
        """Get current prompt information."""

    @abstractmethod
    @staticmethod
    def send_input(response: str) -> bool:
        """Send input response."""

    @abstractmethod
    @staticmethod
    def clear_prompt_state() -> None:
        """Clear prompt state."""

    @abstractmethod
    @staticmethod
    def get_collection_stats() -> dict[str, Any]:
        """Get collection statistics."""


class IControllerManager(ABC):
    """Interface for controller management."""

    @abstractmethod
    @staticmethod
    def get_controller(session_name: str) -> IController | None:
        """Get controller for session."""

    @abstractmethod
    @staticmethod
    def create_controller(session_name: str, **kwargs: Any) -> IController:
        """Create a new controller."""

    @abstractmethod
    @staticmethod
    def remove_controller(session_name: str) -> bool:
        """Remove a controller."""

    @abstractmethod
    @staticmethod
    def list_controllers() -> list[str]:
        """List all controller names."""


class ICache(ABC):
    """Interface for caching systems."""

    @abstractmethod
    @staticmethod
    def get(key: str, ttl: float | None = None) -> object | None:
        """Get cached value."""

    @abstractmethod
    @staticmethod
    def put(key: str, value: object, ttl: float | None = None) -> bool:
        """Store value in cache."""

    @abstractmethod
    @staticmethod
    def invalidate(key: str) -> bool:
        """Invalidate specific cache entry."""

    @abstractmethod
    @staticmethod
    def clear() -> int:
        """Clear all cache entries."""

    @abstractmethod
    @staticmethod
    def get_stats() -> dict[str, Any]:
        """Get cache statistics."""


class ICacheAnalytics(ABC):
    """Interface for cache analytics."""

    @abstractmethod
    @staticmethod
    def get_cache_health_report() -> dict[str, Any]:
        """Generate comprehensive cache health report."""

    @abstractmethod
    @staticmethod
    def get_visual_status_summary() -> dict[str, Any]:
        """Get cache status summary for visualization."""

    @abstractmethod
    @staticmethod
    def export_stats_json() -> str:
        """Export cache statistics as JSON."""


class IPromptDetector(ABC):
    """Interface for prompt detection."""

    @abstractmethod
    @staticmethod
    def detect_prompts(
        content: str, context: dict[str, Any] | None = None
    ) -> list[PromptInfo]:
        """Detect prompts in content."""

    @abstractmethod
    @staticmethod
    def load_patterns(pattern_dir: str) -> bool:
        """Load detection patterns."""

    @abstractmethod
    @staticmethod
    def get_supported_types() -> list[str]:
        """Get supported prompt types."""


class IPatternLoader(ABC):
    """Interface for pattern loading."""

    @abstractmethod
    @staticmethod
    def load_pattern(pattern_type: str) -> dict[str, Any]:
        """Load a specific pattern."""

    @abstractmethod
    @staticmethod
    def get_available_patterns() -> list[str]:
        """Get list of available patterns."""

    @abstractmethod
    @staticmethod
    def reload_patterns() -> bool:
        """Reload all patterns."""


class IPlugin(ABC):
    """Base interface for plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""

    @abstractmethod
    @staticmethod
    def initialize(config: dict[str, Any]) -> bool:
        """Initialize the plugin."""

    @abstractmethod
    @staticmethod
    def cleanup() -> bool:
        """Cleanup plugin resources."""

    @abstractmethod
    @staticmethod
    def is_enabled() -> bool:
        """Check if plugin is enabled."""


class IControllerPlugin(IPlugin):
    """Interface for controller plugins."""

    @abstractmethod
    @staticmethod
    def on_controller_start(session_name: str, controller: IController) -> None:
        """Called when controller starts."""

    @abstractmethod
    @staticmethod
    def on_controller_stop(session_name: str, controller: IController) -> None:
        """Called when controller stops."""

    @abstractmethod
    @staticmethod
    def on_prompt_detected(session_name: str, prompt: PromptInfo) -> str | None:
        """Called when prompt is detected, return response or None."""


class ISessionPlugin(IPlugin):
    """Interface for session plugins."""

    @abstractmethod
    @staticmethod
    def on_session_created(session: SessionInfo) -> None:
        """Called when session is created."""

    @abstractmethod
    @staticmethod
    def on_session_destroyed(session_name: str) -> None:
        """Called when session is destroyed."""

    @abstractmethod
    @staticmethod
    def on_session_status_changed(session: SessionInfo, old_status: str) -> None:
        """Called when session status changes."""


class ICachePlugin(IPlugin):
    """Interface for cache plugins."""

    @abstractmethod
    @staticmethod
    def on_cache_hit(key: str, value: object) -> None:
        """Called on cache hit."""

    @abstractmethod
    @staticmethod
    def on_cache_miss(key: str) -> None:
        """Called on cache miss."""

    @abstractmethod
    @staticmethod
    def on_cache_eviction(key: str, reason: str) -> None:
        """Called on cache eviction."""


class IPluginManager(ABC):
    """Interface for plugin management."""

    @abstractmethod
    @staticmethod
    def load_plugin(plugin_path: str) -> bool:
        """Load a plugin from path."""

    @abstractmethod
    @staticmethod
    def unload_plugin(plugin_name: str) -> bool:
        """Unload a plugin."""

    @abstractmethod
    @staticmethod
    def get_plugin(plugin_name: str) -> IPlugin | None:
        """Get a loaded plugin."""

    @abstractmethod
    @staticmethod
    def list_plugins() -> list[PluginMetadata]:
        """List all loaded plugins."""

    @abstractmethod
    @staticmethod
    def enable_plugin(plugin_name: str) -> bool:
        """Enable a plugin."""

    @abstractmethod
    @staticmethod
    def disable_plugin(plugin_name: str) -> bool:
        """Disable a plugin."""

    @abstractmethod
    @staticmethod
    def get_plugins_by_type(plugin_type: type) -> list[IPlugin]:
        """Get plugins of specific type."""


class IEventBus(ABC):
    """Interface for event bus system."""

    @abstractmethod
    @staticmethod
    def subscribe(event_type: str, handler: Callable[[dict[str, Any]], None]) -> str:
        """Subscribe to events, returns subscription ID."""

    @abstractmethod
    @staticmethod
    def unsubscribe(subscription_id: str) -> bool:
        """Unsubscribe from events."""

    @abstractmethod
    @staticmethod
    def publish(event_type: str, data: dict[str, Any]) -> None:
        """Publish an event."""

    @abstractmethod
    @staticmethod
    def get_event_types() -> list[str]:
        """Get available event types."""


class IConfigManager(ABC):
    """Interface for configuration management."""

    @abstractmethod
    @staticmethod
    def get_config(key: str, default: object = None) -> object:
        """Get configuration value."""

    @abstractmethod
    @staticmethod
    def set_config(key: str, value: object) -> bool:
        """Set configuration value."""

    @abstractmethod
    @staticmethod
    def reload_config() -> bool:
        """Reload configuration."""

    @abstractmethod
    @staticmethod
    def get_all_config() -> dict[str, Any]:
        """Get all configuration."""

    @abstractmethod
    @staticmethod
    def validate_config() -> list[str]:
        """Validate configuration, return list of errors."""


# Event types for the event bus
class EventTypes:
    """Standard event types."""

    CONTROLLER_STARTED = "controller.started"
    CONTROLLER_STOPPED = "controller.stopped"
    CONTROLLER_ERROR = "controller.error"

    SESSION_CREATED = "session.created"
    SESSION_DESTROYED = "session.destroyed"
    SESSION_STATUS_CHANGED = "session.status_changed"

    PROMPT_DETECTED = "prompt.detected"
    PROMPT_RESPONDED = "prompt.responded"

    CACHE_HIT = "cache.hit"
    CACHE_MISS = "cache.miss"
    CACHE_EVICTION = "cache.eviction"

    PLUGIN_LOADED = "plugin.loaded"
    PLUGIN_UNLOADED = "plugin.unloaded"
    PLUGIN_ERROR = "plugin.error"
