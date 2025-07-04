"""Abstract base classes and interfaces for the yesman-claude system"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

from .models import SessionInfo, PromptInfo


class ControllerState(Enum):
    """Controller states"""
    READY = "ready"
    RUNNING = "running" 
    STOPPED = "stopped"
    ERROR = "error"


class CacheStrategy(Enum):
    """Cache invalidation strategies"""
    TIME_BASED = "time_based"
    CONTENT_CHANGE = "content_change"
    DEPENDENCY = "dependency"
    MANUAL = "manual"


@dataclass
class PluginMetadata:
    """Plugin metadata information"""
    name: str
    version: str
    description: str
    author: str
    dependencies: List[str]
    enabled: bool = True


class ISessionManager(ABC):
    """Interface for session management"""
    
    @abstractmethod
    def get_all_sessions(self) -> List[SessionInfo]:
        """Get all available sessions"""
        pass
    
    @abstractmethod
    def get_session(self, session_name: str) -> Optional[SessionInfo]:
        """Get a specific session by name"""
        pass
    
    @abstractmethod
    def invalidate_cache(self, session_name: Optional[str] = None) -> None:
        """Invalidate session cache"""
        pass
    
    @abstractmethod
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass


class IController(ABC):
    """Interface for Claude controllers"""
    
    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Check if controller is running"""
        pass
    
    @property
    @abstractmethod
    def selected_model(self) -> str:
        """Get selected model"""
        pass
    
    @property
    @abstractmethod
    def is_auto_next_enabled(self) -> bool:
        """Check if auto next is enabled"""
        pass
    
    @abstractmethod
    def start(self) -> bool:
        """Start the controller"""
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """Stop the controller"""
        pass
    
    @abstractmethod
    def restart_claude_pane(self) -> bool:
        """Restart Claude pane"""
        pass
    
    @abstractmethod
    def set_model(self, model: str) -> bool:
        """Set the model"""
        pass
    
    @abstractmethod
    def set_auto_next(self, enabled: bool) -> bool:
        """Set auto next setting"""
        pass
    
    @abstractmethod
    def is_waiting_for_input(self) -> bool:
        """Check if waiting for input"""
        pass
    
    @abstractmethod
    def get_current_prompt(self) -> Optional[PromptInfo]:
        """Get current prompt information"""
        pass
    
    @abstractmethod
    def send_input(self, response: str) -> bool:
        """Send input response"""
        pass
    
    @abstractmethod
    def clear_prompt_state(self) -> None:
        """Clear prompt state"""
        pass
    
    @abstractmethod
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get collection statistics"""
        pass


class IControllerManager(ABC):
    """Interface for controller management"""
    
    @abstractmethod
    def get_controller(self, session_name: str) -> Optional[IController]:
        """Get controller for session"""
        pass
    
    @abstractmethod
    def create_controller(self, session_name: str, **kwargs) -> IController:
        """Create a new controller"""
        pass
    
    @abstractmethod
    def remove_controller(self, session_name: str) -> bool:
        """Remove a controller"""
        pass
    
    @abstractmethod
    def list_controllers(self) -> List[str]:
        """List all controller names"""
        pass


class ICache(ABC):
    """Interface for caching systems"""
    
    @abstractmethod
    def get(self, key: str, ttl: Optional[float] = None) -> Optional[Any]:
        """Get cached value"""
        pass
    
    @abstractmethod
    def put(self, key: str, value: Any, ttl: Optional[float] = None) -> bool:
        """Store value in cache"""
        pass
    
    @abstractmethod
    def invalidate(self, key: str) -> bool:
        """Invalidate specific cache entry"""
        pass
    
    @abstractmethod
    def clear(self) -> int:
        """Clear all cache entries"""
        pass
    
    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        pass


class ICacheAnalytics(ABC):
    """Interface for cache analytics"""
    
    @abstractmethod
    def get_cache_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive cache health report"""
        pass
    
    @abstractmethod
    def get_visual_status_summary(self) -> Dict[str, Any]:
        """Get cache status summary for visualization"""
        pass
    
    @abstractmethod
    def export_stats_json(self) -> str:
        """Export cache statistics as JSON"""
        pass


class IPromptDetector(ABC):
    """Interface for prompt detection"""
    
    @abstractmethod
    def detect_prompts(self, content: str, context: Optional[Dict[str, Any]] = None) -> List[PromptInfo]:
        """Detect prompts in content"""
        pass
    
    @abstractmethod
    def load_patterns(self, pattern_dir: str) -> bool:
        """Load detection patterns"""
        pass
    
    @abstractmethod
    def get_supported_types(self) -> List[str]:
        """Get supported prompt types"""
        pass


class IPatternLoader(ABC):
    """Interface for pattern loading"""
    
    @abstractmethod
    def load_pattern(self, pattern_type: str) -> Dict[str, Any]:
        """Load a specific pattern"""
        pass
    
    @abstractmethod
    def get_available_patterns(self) -> List[str]:
        """Get list of available patterns"""
        pass
    
    @abstractmethod
    def reload_patterns(self) -> bool:
        """Reload all patterns"""
        pass


class IPlugin(ABC):
    """Base interface for plugins"""
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata"""
        pass
    
    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin"""
        pass
    
    @abstractmethod
    def cleanup(self) -> bool:
        """Cleanup plugin resources"""
        pass
    
    @abstractmethod
    def is_enabled(self) -> bool:
        """Check if plugin is enabled"""
        pass


class IControllerPlugin(IPlugin):
    """Interface for controller plugins"""
    
    @abstractmethod
    def on_controller_start(self, session_name: str, controller: IController) -> None:
        """Called when controller starts"""
        pass
    
    @abstractmethod
    def on_controller_stop(self, session_name: str, controller: IController) -> None:
        """Called when controller stops"""
        pass
    
    @abstractmethod
    def on_prompt_detected(self, session_name: str, prompt: PromptInfo) -> Optional[str]:
        """Called when prompt is detected, return response or None"""
        pass


class ISessionPlugin(IPlugin):
    """Interface for session plugins"""
    
    @abstractmethod
    def on_session_created(self, session: SessionInfo) -> None:
        """Called when session is created"""
        pass
    
    @abstractmethod
    def on_session_destroyed(self, session_name: str) -> None:
        """Called when session is destroyed"""
        pass
    
    @abstractmethod
    def on_session_status_changed(self, session: SessionInfo, old_status: str) -> None:
        """Called when session status changes"""
        pass


class ICachePlugin(IPlugin):
    """Interface for cache plugins"""
    
    @abstractmethod
    def on_cache_hit(self, key: str, value: Any) -> None:
        """Called on cache hit"""
        pass
    
    @abstractmethod
    def on_cache_miss(self, key: str) -> None:
        """Called on cache miss"""
        pass
    
    @abstractmethod
    def on_cache_eviction(self, key: str, reason: str) -> None:
        """Called on cache eviction"""
        pass


class IPluginManager(ABC):
    """Interface for plugin management"""
    
    @abstractmethod
    def load_plugin(self, plugin_path: str) -> bool:
        """Load a plugin from path"""
        pass
    
    @abstractmethod
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        pass
    
    @abstractmethod
    def get_plugin(self, plugin_name: str) -> Optional[IPlugin]:
        """Get a loaded plugin"""
        pass
    
    @abstractmethod
    def list_plugins(self) -> List[PluginMetadata]:
        """List all loaded plugins"""
        pass
    
    @abstractmethod
    def enable_plugin(self, plugin_name: str) -> bool:
        """Enable a plugin"""
        pass
    
    @abstractmethod
    def disable_plugin(self, plugin_name: str) -> bool:
        """Disable a plugin"""
        pass
    
    @abstractmethod
    def get_plugins_by_type(self, plugin_type: type) -> List[IPlugin]:
        """Get plugins of specific type"""
        pass


class IEventBus(ABC):
    """Interface for event bus system"""
    
    @abstractmethod
    def subscribe(self, event_type: str, handler: Callable[[Dict[str, Any]], None]) -> str:
        """Subscribe to events, returns subscription ID"""
        pass
    
    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events"""
        pass
    
    @abstractmethod
    def publish(self, event_type: str, data: Dict[str, Any]) -> None:
        """Publish an event"""
        pass
    
    @abstractmethod
    def get_event_types(self) -> List[str]:
        """Get available event types"""
        pass


class IConfigManager(ABC):
    """Interface for configuration management"""
    
    @abstractmethod
    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        pass
    
    @abstractmethod
    def set_config(self, key: str, value: Any) -> bool:
        """Set configuration value"""
        pass
    
    @abstractmethod
    def reload_config(self) -> bool:
        """Reload configuration"""
        pass
    
    @abstractmethod
    def get_all_config(self) -> Dict[str, Any]:
        """Get all configuration"""
        pass
    
    @abstractmethod
    def validate_config(self) -> List[str]:
        """Validate configuration, return list of errors"""
        pass


# Event types for the event bus
class EventTypes:
    """Standard event types"""
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