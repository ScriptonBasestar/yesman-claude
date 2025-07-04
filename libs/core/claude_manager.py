"""Claude manager for dashboard integration - Refactored"""

import logging
from typing import Optional, Dict, Callable
from .claude_session_manager import ClaudeSessionManager
from .claude_process_controller import ClaudeProcessController
from .claude_status_manager import ClaudeStatusManager
from .claude_monitor import ClaudeMonitor
from .prompt_detector import PromptInfo


class DashboardController:
    """Main controller that orchestrates Claude session management, process control, and monitoring"""

    def __init__(self, session_name: str, pane_id: Optional[str] = None):
        self.session_name = session_name
        self.pane_id = pane_id
        
        # Initialize component managers
        self.session_manager = ClaudeSessionManager(session_name, pane_id)
        self.status_manager = ClaudeStatusManager(session_name)
        self.process_controller = ClaudeProcessController(self.session_manager, self.status_manager)
        self.monitor = ClaudeMonitor(self.session_manager, self.process_controller, self.status_manager)
        
        self.logger = logging.getLogger(f"yesman.dashboard.controller.{session_name}")
        
        # Try to initialize session, but don't fail if session doesn't exist
        if not self.session_manager.initialize_session():
            self.status_manager.update_status(f"[yellow]Session '{session_name}' not found[/]")

    @property
    def claude_pane(self):
        """Get the Claude pane (for backward compatibility)"""
        return self.session_manager.get_claude_pane()

    @property
    def is_running(self) -> bool:
        """Check if monitoring is running"""
        return self.monitor.is_running

    @property
    def is_auto_next_enabled(self) -> bool:
        """Check if auto-next is enabled"""
        return self.monitor.is_auto_next_enabled

    @property
    def selected_model(self) -> str:
        """Get selected model"""
        return self.process_controller.selected_model

    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self.status_manager.set_status_callback(callback)

    def set_activity_callback(self, callback: Callable):
        """Set callback for activity updates"""
        self.status_manager.set_activity_callback(callback)

    def start(self) -> bool:
        """Start the controller"""
        # Re-initialize in case session was created after initialization
        if not self.claude_pane:
            self.session_manager.initialize_session()
                
        return self.monitor.start_monitoring()

    def stop(self) -> bool:
        """Stop the controller"""
        return self.monitor.stop_monitoring()

    def restart_claude_pane(self) -> bool:
        """Restart Claude pane"""
        return self.process_controller.restart_claude_pane()

    def set_model(self, model: str):
        """Set the selected model"""
        self.process_controller.set_model(model)

    def set_auto_next(self, enabled: bool):
        """Enable or disable auto-next responses"""
        self.monitor.set_auto_next(enabled)

    def set_mode_yn(self, mode: str, response: str):
        """Set manual override for Y/N prompts"""
        self.monitor.set_mode_yn(mode, response)

    def set_mode_12(self, mode: str, response: str):
        """Set manual override for 1/2 prompts"""
        self.monitor.set_mode_12(mode, response)

    def set_mode_123(self, mode: str, response: str):
        """Set manual override for 1/2/3 prompts"""
        self.monitor.set_mode_123(mode, response)

    def capture_pane_content(self, lines: int = 50) -> str:
        """Capture content from Claude pane"""
        content = self.session_manager.capture_pane_content(lines)
        if content:
            # Save capture to file
            self.status_manager.save_capture_to_file(content, self.pane_id)
        return content

    def send_input(self, text: str):
        """Send input to Claude pane"""
        self.process_controller.send_input(text)

    def is_waiting_for_input(self) -> bool:
        """Check if Claude is currently waiting for user input"""
        return self.monitor.is_waiting_for_input()

    def get_current_prompt(self) -> Optional[PromptInfo]:
        """Get the current prompt information"""
        return self.monitor.get_current_prompt()

    def get_response_history(self) -> list:
        """Get the response history"""
        return self.status_manager.get_response_history()

    def get_collection_stats(self) -> dict:
        """Get content collection statistics"""
        return self.monitor.get_collection_stats()

    def cleanup_old_collections(self, days_to_keep: int = 7) -> int:
        """Clean up old collection files"""
        return self.monitor.cleanup_old_collections(days_to_keep)

    # Legacy compatibility methods (deprecated but kept for backward compatibility)
    def detect_trust_prompt(self, content: str) -> bool:
        """Detect trust prompt in content (deprecated - use monitor methods)"""
        return self.monitor._detect_trust_prompt(content)

    def auto_trust_if_needed(self) -> bool:
        """Auto-respond to trust prompts if detected (deprecated - use monitor methods)"""
        return self.monitor._auto_trust_if_needed()

    def auto_respond_to_selection(self, prompt_info: PromptInfo) -> bool:
        """Auto-respond to selection prompts (deprecated - use monitor methods)"""
        return self.monitor._auto_respond_to_selection(prompt_info)

    def check_for_prompt(self, content: str) -> Optional[PromptInfo]:
        """Check if content contains a prompt waiting for input (deprecated - use monitor methods)"""
        return self.monitor._check_for_prompt(content)

    def clear_prompt_state(self) -> None:
        """Clear the current prompt state (deprecated - use monitor methods)"""
        self.monitor._clear_prompt_state()


class ClaudeManager:
    """Manages multiple dashboard controllers"""
    
    def __init__(self):
        self.controllers: Dict[str, DashboardController] = {}
        self.logger = logging.getLogger("yesman.dashboard.claude_manager")
    
    def get_controller(self, session_name: str, pane_id: Optional[str] = None) -> DashboardController:
        """Get or create controller for session"""
        if session_name not in self.controllers:
            self.controllers[session_name] = DashboardController(session_name, pane_id)
        return self.controllers[session_name]
    
    def remove_controller(self, session_name: str):
        """Remove controller for session"""
        if session_name in self.controllers:
            controller = self.controllers[session_name]
            controller.stop()
            del self.controllers[session_name]
    
    def stop_all(self):
        """Stop all controllers"""
        for controller in self.controllers.values():
            controller.stop()
        self.controllers.clear()