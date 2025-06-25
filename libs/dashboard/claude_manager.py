"""Claude manager for dashboard integration"""

import asyncio
import logging
import time
import re
from typing import Optional, Dict, Any, Callable
from pathlib import Path
import libtmux
import subprocess


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
                    cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    if "claude" in cmd.lower():
                        return pane
                except Exception:
                    continue
        return None

    def _setup_logger(self) -> logging.Logger:
        """Setup logger for dashboard controller"""
        logger = logging.getLogger(f"yesman.dashboard.claude_manager.{self.session_name}")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path = Path("~/tmp/logs/yesman/").expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        
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
        if not self.claude_pane:
            self._update_status(f"[red]Cannot start: No Claude pane in session '{self.session_name}'[/]")
            return False
            
        if self.is_running:
            self._update_status("[yellow]Controller already running[/]")
            return False
        
        try:
            self.is_running = True
            self._update_status(f"[green]Starting claude manager for {self.session_name}[/]")
            
            # Start the monitoring loop in background
            asyncio.create_task(self._monitor_loop())
            return True
            
        except Exception as e:
            self.is_running = False
            self._update_status(f"[red]Failed to start claude manager: {e}[/]")
            self.logger.error(f"Failed to start claude manager: {e}")
            return False
    
    def stop(self) -> bool:
        """Stop the controller"""
        if not self.is_running:
            self._update_status("[yellow]Claude manager not running[/]")
            return False
        
        self.is_running = False
        self._update_status(f"[red]Stopped claude manager for {self.session_name}[/]")
        return True
    
    def restart_claude_pane(self) -> bool:
        """Restart Claude pane"""
        if not self.claude_pane:
            self._update_status(f"[red]Cannot restart: No Claude pane in session '{self.session_name}'[/]")
            return False
            
        try:
            self._update_status("[yellow]Restarting Claude pane...[/]")
            
            # Send Ctrl+C to stop current claude process
            self.claude_pane.send_keys("C-c")
            time.sleep(1)
            
            # Start claude with selected model
            claude_cmd = self._get_claude_command()
            self.claude_pane.send_keys(claude_cmd)
            
            self._update_status(f"[green]Claude pane restarted with {self.selected_model} model[/]")
            return True
            
        except Exception as e:
            self._update_status(f"[red]Failed to restart Claude pane: {e}[/]")
            self.logger.error(f"Failed to restart Claude pane: {e}")
            return False
    
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
    
    def detect_prompt_type(self, content: str) -> Optional[Dict[str, Any]]:
        """Detect type of prompt in content"""
        # Check for numbered selections
        numbered_pattern = r'\[(\d+)\]\s+(.+?)(?=\n|\[|$)'
        numbered_matches = re.findall(numbered_pattern, content, re.MULTILINE)
        
        if len(numbered_matches) >= 2:
            return {
                'type': 'numbered',
                'options': numbered_matches,
                'count': len(numbered_matches)
            }
        
        # Check for yes/no prompts
        yn_patterns = [
            r'\(y/n\)',
            r'\(yes/no\)',
            r'\[Y/n\]',
            r'Continue\?',
            r'Proceed\?'
        ]
        
        for pattern in yn_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return {'type': 'yn'}
        
        return None
    
    def auto_respond(self, prompt_info: Dict[str, Any]) -> Optional[str]:
        """Generate auto response based on prompt type"""
        if prompt_info['type'] == 'numbered':
            return "1"  # Always select first option
        elif prompt_info['type'] == 'yn':
            return "yes"
        return None
    
    def send_input(self, text: str):
        """Send input to Claude pane"""
        if self.claude_pane:
            self.claude_pane.send_keys(text)

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
                        continue
                    
                    # Detect and respond to selection prompts
                    prompt_info = self.detect_prompt_type(content)
                    if prompt_info:
                        response = self.auto_respond(prompt_info)
                        if response:
                            self.send_input(response)
                            if prompt_info['type'] == 'numbered':
                                self._update_activity(f"🔢 Auto-selected option {response}")
                            elif prompt_info['type'] == 'yn':
                                self._update_activity(f"✅ Auto-responded: {response}")
                    
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