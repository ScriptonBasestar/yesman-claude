"""Claude manager for dashboard integration"""

import asyncio
import logging
import time
import re
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import libtmux
import subprocess
import threading
from ..utils import ensure_log_directory, get_default_log_path
from .content_collector import ClaudeContentCollector
from .prompt_detector import ClaudePromptDetector, PromptInfo


class DashboardController:
    """Controller that can be managed from the dashboard"""

    def __init__(self, session_name: str, pane_id: Optional[str] = None):
        self.session_name = session_name
        self.pane_id = pane_id
        self.server = libtmux.Server()
        self.session = None
        self.claude_pane = None
        self.is_running = False
        self.is_auto_next_enabled = False
        self.selected_model = "default"
        self.logger = self._setup_logger()
        self.status_callback: Optional[Callable] = None
        self.activity_callback: Optional[Callable] = None
        self.response_history = []  # Track auto-response history
        self._monitor_thread = None
        self._loop = None
        self.content_collector = ClaudeContentCollector(session_name)
        self.prompt_detector = ClaudePromptDetector()
        self.current_prompt: Optional[PromptInfo] = None
        self.waiting_for_input = False
        
        # Try to initialize session, but don't fail if session doesn't exist
        try:
            self._initialize_session()
        except Exception as e:
            self.logger.warning(f"Could not initialize session: {e}")
            self._update_status(f"[yellow]Session '{session_name}' not found[/]")

    def _initialize_session(self):
        """Initialize tmux session and find Claude pane"""
        self.session = self.server.find_where({"session_name": self.session_name})
        if not self.session:
            raise ValueError(f"Session '{self.session_name}' not found")
        
        # Find Claude pane
        self.claude_pane = self._find_claude_pane()
        if not self.claude_pane:
            self.logger.warning(f"No Claude pane found in session '{self.session_name}'")

    def _find_claude_pane(self):
        """Find pane running Claude"""
        if not self.session:
            return None
            
        for window in self.session.list_windows():
            for pane in window.list_panes():
                try:
                    # Check both command and pane content
                    cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    
                    # Capture pane content to check for Claude indicators
                    capture_result = pane.cmd("capture-pane", "-p")
                    content = "\n".join(capture_result.stdout) if capture_result.stdout else ""
                    
                    # Enhanced Claude detection patterns
                    claude_indicators = [
                        "claude" in cmd.lower(),
                        "Welcome to Claude Code" in content,
                        "? for shortcuts" in content,
                        "Claude Code" in content,
                        "anthropic" in content.lower(),
                        "claude.ai" in content.lower()
                    ]
                    
                    if any(claude_indicators):
                        self.logger.info(f"Found Claude pane: {window.name}:{pane.index}")
                        return pane
                        
                except Exception as e:
                    self.logger.debug(f"Error checking pane {window.name}:{pane.index}: {e}")
                    continue
        
        self.logger.warning("No Claude pane found in any window")
        return None

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for dashboard controller"""
        logger = logging.getLogger(f"yesman.dashboard.claude_manager.{self.session_name}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = ensure_log_directory(get_default_log_path())
        
        log_file = log_path / f"claude_manager_{self.session_name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def set_status_callback(self, callback: Callable):
        """Set callback for status updates"""
        self.status_callback = callback
    
    def set_activity_callback(self, callback: Callable):
        """Set callback for activity updates"""
        self.activity_callback = callback
    
    def _update_status(self, message: str):
        """Update status through callback"""
        if self.status_callback:
            self.status_callback(message)
        self.logger.info(message)
    
    def _update_activity(self, activity: str):
        """Update activity through callback"""
        if self.activity_callback:
            self.activity_callback(activity)
    
    def start(self) -> bool:
        """Start the controller"""
        # Re-initialize in case session was created after initialization
        if not self.claude_pane:
            try:
                self._initialize_session()
            except Exception:
                pass
                
        if not self.claude_pane:
            self._update_status(f"[red]Cannot start: No Claude pane in session '{self.session_name}'[/]")
            return False
            
        if self.is_running:
            self._update_status("[yellow]Controller already running[/]")
            return False
        
        try:
            self.is_running = True
            self._update_status(f"[green]Starting claude manager for {self.session_name}[/]")
            
            # Start monitoring in a separate thread with its own event loop
            self._monitor_thread = threading.Thread(target=self._run_monitor_loop, daemon=True)
            self._monitor_thread.start()
            
            return True
            
        except Exception as e:
            self.is_running = False
            self._update_status(f"[red]Failed to start claude manager: {e}[/]")
            self.logger.error(f"Failed to start claude manager: {e}", exc_info=True)
            return False
    
    def stop(self) -> bool:
        """Stop the controller"""
        if not self.is_running:
            self._update_status("[yellow]Claude manager not running[/]")
            return False
        
        self.is_running = False
        
        # Stop the event loop if it's running
        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)
        
        # Wait for thread to finish
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=2.0)
        
        self._update_status(f"[red]Stopped claude manager for {self.session_name}[/]")
        return True
    
    def restart_claude_pane(self) -> bool:
        """Restart Claude pane"""
        if not self.claude_pane:
            self._update_status(f"[red]Cannot restart: No Claude pane in session '{self.session_name}'[/]")
            return False
            
        try:
            self._update_status("[yellow]Restarting Claude pane...[/]")
            
            # Force kill any existing claude process and clear the pane
            self._terminate_claude_process()
            
            # Start claude with selected model
            claude_cmd = self._get_claude_command()
            self.claude_pane.send_keys(claude_cmd)
            
            self._update_status(f"[green]Claude pane restarted with {self.selected_model} model[/]")
            return True
            
        except Exception as e:
            self._update_status(f"[red]Failed to restart Claude pane: {e}[/]")
            self.logger.error(f"Failed to restart Claude pane: {e}")
            return False
    
    def _terminate_claude_process(self) -> None:
        """Terminate any existing claude process in the pane"""
        try:
            # Send multiple Ctrl+C to ensure termination
            self.claude_pane.send_keys("C-c")
            time.sleep(0.5)
            self.claude_pane.send_keys("C-c")
            time.sleep(0.5)
            
            # Send Ctrl+D to exit any interactive shell
            self.claude_pane.send_keys("C-d")
            time.sleep(0.5)
            
            # Clear the screen and any remaining input
            self.claude_pane.send_keys("clear")
            time.sleep(0.5)
            
            # Wait for processes to fully terminate
            max_attempts = 5
            for attempt in range(max_attempts):
                try:
                    # Check if claude is still running by checking the command
                    cmd = self.claude_pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    if "claude" not in cmd.lower():
                        self.logger.info(f"Claude process terminated after {attempt + 1} attempts")
                        break
                except Exception:
                    # If we can't get the command, assume it's terminated
                    break
                    
                # Try more aggressive termination
                self.claude_pane.send_keys("C-c")
                time.sleep(1)
            
            # Final clear and prepare for new command
            self.claude_pane.send_keys("clear")
            time.sleep(0.2)
            
        except Exception as e:
            self.logger.warning(f"Error during claude process termination: {e}")
    
    def _get_claude_command(self) -> str:
        """Get claude command based on selected model"""
        if self.selected_model == "opus":
            return "claude --model claude-3-5-opus-20241022"
        elif self.selected_model == "sonnet":
            return "claude --model claude-3-5-sonnet-20241022"
        else:
            return "claude"
    
    def set_model(self, model: str):
        """Set the selected model"""
        self.selected_model = model
        self._update_status(f"[cyan]Model set to: {model}[/]")
    
    def set_auto_next(self, enabled: bool):
        """Enable/disable auto next functionality"""
        self.is_auto_next_enabled = enabled
        status = "enabled" if enabled else "disabled"
        self._update_status(f"[cyan]Auto next {status}[/]")
    
    def capture_pane_content(self, lines: int = 50) -> str:
        """Capture content from Claude pane"""
        if not self.claude_pane:
            return ""
        
        try:
            # Get the last N lines from the pane
            result = self.claude_pane.cmd("capture-pane", "-p", "-S", f"-{lines}")
            return result.stdout[0] if result.stdout else ""
        except Exception as e:
            self.logger.error(f"Error capturing pane content: {e}")
            return ""
    
    def detect_trust_prompt(self, content: str) -> bool:
        """Detect trust prompt in content"""
        trust_patterns = [
            r"Do you trust the files in this folder",
            r"\[1\] Yes, proceed",
            r"\[2\] No, cancel"
        ]
        
        for pattern in trust_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return True
        return False
    
    def auto_trust_if_needed(self) -> bool:
        """Auto-respond to trust prompts if detected"""
        content = self.capture_pane_content()
        if self.detect_trust_prompt(content):
            self.send_input("1")
            return True
        return False
    
    def check_for_prompt(self, content: str) -> Optional[PromptInfo]:
        """Check if content contains a prompt waiting for input"""
        prompt_info = self.prompt_detector.detect_prompt(content)
        
        if prompt_info:
            self.current_prompt = prompt_info
            self.waiting_for_input = True
            self.logger.info(f"Prompt detected: {prompt_info.type.value} - {prompt_info.question}")
        else:
            # Check if we're still waiting for input based on content patterns
            self.waiting_for_input = self.prompt_detector.is_waiting_for_input(content)
        
        return prompt_info
    
    def is_waiting_for_input(self) -> bool:
        """Check if Claude is currently waiting for user input"""
        return self.waiting_for_input
    
    def get_current_prompt(self) -> Optional[PromptInfo]:
        """Get the current prompt information"""
        return self.current_prompt
    
    def clear_prompt_state(self) -> None:
        """Clear the current prompt state"""
        self.current_prompt = None
        self.waiting_for_input = False
    
    def send_input(self, text: str):
        """Send input to Claude pane"""
        if self.claude_pane:
            self.claude_pane.send_keys(text)
    
    def _record_response(self, prompt_type: str, response: str, content: str):
        """Record auto-response in history"""
        import datetime
        record = {
            'timestamp': datetime.datetime.now().isoformat(),
            'prompt_type': prompt_type,
            'response': response,
            'content_snippet': content[-200:]  # Last 200 chars for context
        }
        self.response_history.append(record)
        self.logger.info(f"Auto-response recorded: {prompt_type} -> {response}")
        
        # Keep only last 100 responses
        if len(self.response_history) > 100:
            self.response_history = self.response_history[-100:]
    
    def get_response_history(self) -> list:
        """Get the response history"""
        return self.response_history
    
    def get_collection_stats(self) -> dict:
        """Get content collection statistics"""
        return self.content_collector.get_collection_stats()
    
    def cleanup_old_collections(self, days_to_keep: int = 7) -> int:
        """Clean up old collection files"""
        return self.content_collector.cleanup_old_files(days_to_keep)

    def _run_monitor_loop(self):
        """Run the monitor loop in its own thread with event loop"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._monitor_loop())
        except Exception as e:
            self.logger.error(f"Monitor loop error: {e}", exc_info=True)
        finally:
            self._loop.close()
            self.is_running = False

    async def _monitor_loop(self):
        """Main monitoring loop that runs in background"""
        if not self.claude_pane:
            self.logger.error(f"Cannot start monitoring: no Claude pane for {self.session_name}")
            self.is_running = False
            return
            
        self.logger.info(f"Starting monitoring loop for {self.session_name}")
        last_content = ""
        
        try:
            while self.is_running:
                await asyncio.sleep(1)  # Check every second
                
                try:
                    content = self.capture_pane_content()
                    
                    # Check if Claude is still running
                    try:
                        current_cmd = self.claude_pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                        if "claude" not in current_cmd.lower():
                            if self.is_auto_next_enabled:
                                self._update_activity("🔄 Auto-restarting Claude...")
                                self.restart_claude_pane()
                                continue
                            else:
                                self._update_status("[yellow]Claude not running. Auto-restart disabled.[/]")
                                continue
                    except Exception:
                        # If we can't get the command, assume Claude is not running
                        self._update_status("[yellow]Could not check Claude status[/]")
                        continue
                    
                    # Auto-respond to trust prompts
                    if self.auto_trust_if_needed():
                        self._update_activity("✅ Auto-responded to trust prompt")
                        self._record_response("trust_prompt", "1", content)
                        continue
                    
                    # Check for prompts (no auto-response)
                    prompt_info = self.check_for_prompt(content)
                    
                    if prompt_info:
                        self._update_activity(f"⏳ Waiting for input: {prompt_info.type.value}")
                        self.logger.debug(f"Prompt detected: {prompt_info.type.value} - {prompt_info.question}")
                    elif self.waiting_for_input:
                        self._update_activity("⏳ Waiting for user input...")
                    else:
                        # Clear prompt state if no longer waiting
                        self.clear_prompt_state()
                    
                    # Collect content for pattern analysis
                    if content != last_content and len(content.strip()) > 0:
                        try:
                            # Convert PromptInfo to dict for collection compatibility
                            prompt_dict = None
                            if prompt_info:
                                prompt_dict = {
                                    'type': prompt_info.type.value,
                                    'question': prompt_info.question,
                                    'options': prompt_info.options,
                                    'confidence': prompt_info.confidence
                                }
                            self.content_collector.collect_interaction(content, prompt_dict, None)
                        except Exception as e:
                            self.logger.error(f"Failed to collect content: {e}")
                    
                    # Update activity if content changed
                    if content != last_content:
                        self._update_activity("📝 Content updated")
                        last_content = content
                
                except Exception as e:
                    self.logger.error(f"Error in monitoring loop: {e}")
                    await asyncio.sleep(5)  # Wait longer on errors
                    
        except asyncio.CancelledError:
            self.logger.info("Monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Monitoring loop error: {e}")
        finally:
            self.is_running = False
            self._update_status("[red]Claude manager stopped[/]")


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