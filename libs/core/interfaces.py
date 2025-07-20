"""Abstract base classes and interfaces for the yesman-claude system."""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any

from .models import SessionInfo
from .prompt_detector import PromptInfo


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
    def get_all_sessions(self) -> list[SessionInfo]:
        """Get all available sessions."""

    @abstractmethod
    def get_session(self, session_name: str) -> SessionInfo | None:
        """Get a specific session by name."""

    @abstractmethod
    def invalidate_cache(self, session_name: str | None = None) -> None:
        """Invalidate session cache."""

    @abstractmethod
    def get_cache_stats(self) -> dict[str, Any]:
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
    def start(self) -> bool:
        """Start the controller."""

    @abstractmethod
    def stop(self) -> bool:
        """Stop the controller."""

    @abstractmethod
    def restart_claude_pane(self) -> bool:
        """Restart Claude pane."""

    @abstractmethod
    def set_model(self, model: str) -> bool:
        """Set the model."""

    @abstractmethod
    def set_auto_next(self, enabled: bool) -> bool:
        """Set auto next setting."""

    @abstractmethod
    def is_waiting_for_input(self) -> bool:
        """Check if waiting for input."""

    @abstractmethod
    def get_current_prompt(self) -> PromptInfo | None:
        """Get current prompt information."""

    @abstractmethod
    def send_input(self, response: str) -> bool:
        """Send input response."""

    @abstractmethod
    def clear_prompt_state(self) -> None:
        """Clear prompt state."""

    @abstractmethod
    def get_collection_stats(self) -> dict[str, Any]:
        """Get collection statistics."""


class IControllerManager(ABC):
    """Interface for controller management."""

    @abstractmethod
    def get_controller(self, session_name: str) -> IController | None:
        """Get controller for session."""

    @abstractmethod
    def create_controller(self, session_name: str, **kwargs) -> IController:
        """Create a new controller."""

    @abstractmethod
    def remove_controller(self, session_name: str) -> bool:
        """Remove a controller."""

    @abstractmethod
    def list_controllers(self) -> list[str]:
        """List all controller names."""


class ICache(ABC):
    """Interface for caching systems."""

    @abstractmethod
    def get(self, key: str, ttl: float | None = None) -> Any | None:
        """Get cached value."""

    @abstractmethod
    def put(self, key: str, value: Any, ttl: float | None = None) -> bool:
        """Store value in cache."""

    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """Invalidate specific cache entry."""

    @abstractmethod
    def clear(self) -> int:
        """Clear all cache entries."""

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""


class ICacheAnalytics(ABC):
    """Interface for cache analytics."""

    @abstractmethod
    def get_cache_health_report(self) -> dict[str, Any]:
        """Generate comprehensive cache health report."""

    @abstractmethod
    def get_visual_status_summary(self) -> dict[str, Any]:
        """Get cache status summary for visualization."""

    @abstractmethod
    def export_stats_json(self) -> str:
        """Export cache statistics as JSON."""


class IPromptDetector(ABC):
    """Interface for prompt detection."""

    @abstractmethod
    def detect_prompts(self, content: str, context: dict[str, Any] | None = None) -> list[PromptInfo]:
        """Detect prompts in content."""

    @abstractmethod
    def load_patterns(self, pattern_dir: str) -> bool:
        """Load detection patterns."""

    @abstractmethod
    def get_supported_types(self) -> list[str]:
        """Get supported prompt types."""


class IPatternLoader(ABC):
    """Interface for pattern loading."""

    @abstractmethod
    def load_pattern(self, pattern_type: str) -> dict[str, Any]:
        """Load a specific pattern."""

    @abstractmethod
    def get_available_patterns(self) -> list[str]:
        """Get list of available patterns."""

    @abstractmethod
    def reload_patterns(self) -> bool:
        """Reload all patterns."""


class IPlugin(ABC):
    """Base interface for plugins."""

    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the plugin."""

    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup plugin resources."""

    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""


class IControllerPlugin(IPlugin):
    """Interface for controller plugins."""

    @abstractmethod
    def on_controller_start(self, session_name: str, controller: IController) -> None:
        """Called when controller starts."""

    @abstractmethod
    def on_controller_stop(self, session_name: str, controller: IController) -> None:
        """Called when controller stops."""

    @abstractmethod
    def on_prompt_detected(self, session_name: str, prompt: PromptInfo) -> str | None:
        """Called when prompt is detected, return response or None."""


class ISessionPlugin(IPlugin):
    """Interface for session plugins."""

    @abstractmethod
    def on_session_created(self, session: SessionInfo) -> None:
        """Called when session is created."""

    @abstractmethod
    def on_session_destroyed(self, session_name: str) -> None:
        """Called when session is destroyed."""

    @abstractmethod
    def on_session_status_changed(self, session: SessionInfo, old_status: str) -> None:
        """Called when session status changes."""


class ICachePlugin(IPlugin):
    """Interface for cache plugins."""

    @abstractmethod
    def on_cache_hit(self, key: str, value: Any) -> None:
        """Called on cache hit."""

    @abstractmethod
    def on_cache_miss(self, key: str) -> None:
        """Called on cache miss."""

    @abstractmethod
    def on_cache_eviction(self, key: str, reason: str) -> None:
        """Called on cache eviction."""


class IPluginManager(ABC):
    """Interface for plugin management."""

    @abstractmethod
    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from path."""

    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin."""

    @abstractmethod
    def get_plugin(self, plugin_name: str) -> IPlugin | None:
        """Get a loaded plugin."""

    @abstractmethod
    def list_plugins(self) -> list[PluginMetadata]:
        """List all loaded plugins."""

    @abstractmethod
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin."""

    @abstractmethod
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin."""

    @abstractmethod
    def get_plugins_by_type(self, plugin_type: type) -> list[IPlugin]:
        """Get plugins of specific type."""


class IEventBus(ABC):
    """Interface for event bus system."""

    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[dict[str, Any]], None]) -> str:
        """Subscribe to events, returns subscription ID."""

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""

    @abstractmethod
    def publish(self, event_type: str, data: dict[str, Any]) -> None:
        """Publish an event."""

    @abstractmethod
    def get_event_types(self) -> list[str]:
        """Get available event types."""


class IConfigManager(ABC):
    """Interface for configuration management."""

    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""

    @abstractmethod
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value."""

    @abstractmethod
    def reload_config(self) -> bool:
        """Reload configuration."""

    @abstractmethod
    def get_all_config(self) -> dict[str, Any]:
        """Get all configuration."""

    @abstractmethod
    def validate_config(self) -> list[str]:
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
