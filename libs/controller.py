#!/usr/bin/env python3
import click
import time
import libtmux
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import subprocess
import re
from libs.yesman_config import YesmanConfig

class Controller:
    def __init__(self, session_name: str, pane_id: Optional[str] = None):
        self.session_name = session_name
        self.pane_id = pane_id
        self.server = libtmux.Server()
        self.logger = logging.getLogger(f"yesman.controller.{session_name}")
        self.config = YesmanConfig()
        
        # Find the session and claude pane
        self.session = self._find_session()
        self.claude_pane = self._find_claude_pane()
        
    def _find_session(self):
        """Find the tmux session by name"""
        session = self.server.find_where({"session_name": self.session_name})
        if not session:
            raise ValueError(f"Session '{self.session_name}' not found")
        return session
    
    def _find_claude_pane(self):
        """Find the pane running claude command"""
        if self.pane_id:
            # If pane_id is specified, use it directly
            for window in self.session.list_windows():
                for pane in window.list_panes():
                    if pane.get("pane_id") == self.pane_id:
                        return pane
        
        # Otherwise, search for pane with claude command
        for window in self.session.list_windows():
            for pane in window.list_panes():
                # Check if pane is running claude
                cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                if "claude" in cmd.lower():
                    self.logger.info(f"Found claude pane: {pane.get('pane_id')}")
                    return pane
        
        raise ValueError(f"No claude pane found in session '{self.session_name}'")
    
    def capture_pane_content(self, lines: int = 50) -> str:
        """Capture the current content of the claude pane"""
        # Capture pane content
        content = self.claude_pane.cmd("capture-pane", "-p", "-S", f"-{lines}").stdout
        return "\n".join(content)
    
    def send_input(self, text: str):
        """Send input to the claude pane"""
        self.claude_pane.send_keys(text)
        self.logger.info(f"Sent input to pane: {text}")
    
    def detect_prompt_type(self, content: str) -> Optional[Dict[str, Any]]:
        """Detect if there's a selection prompt in the content"""
        lines = content.strip().split('\n')
        
        # Look for patterns indicating a selection prompt
        selection_patterns = [
            r"^\s*\[(\d+)\]\s+(.+)$",  # [1] Option format
            r"^\s*(\d+)\)\s+(.+)$",     # 1) Option format
            r"^\s*(\d+)\.\s+(.+)$",     # 1. Option format
        ]
        
        yn_patterns = [
            r"(yes|no|y/n)",
            r"continue\?",
            r"proceed\?",
            r"confirm\?",
        ]
        
        # Check for numbered options
        options = []
        for line in lines[-20:]:  # Check last 20 lines
            for pattern in selection_patterns:
                match = re.match(pattern, line)
                if match:
                    options.append({
                        'number': match.group(1),
                        'text': match.group(2).strip()
                    })
        
        if options:
            return {
                'type': 'numbered',
                'options': options,
                'count': len(options)
            }
        
        # Check for yes/no prompts
        last_lines = "\n".join(lines[-5:]).lower()
        for pattern in yn_patterns:
            if re.search(pattern, last_lines):
                return {
                    'type': 'yn',
                    'pattern': pattern
                }
        
        return None
    
    def auto_respond(self, prompt_info: Dict[str, Any]) -> str:
        """Generate automatic response based on prompt type"""
        prompt_type = prompt_info['type']
        
        # Get choice configuration
        choices = self.config.get('choise', {})
        
        if prompt_type == 'yn':
            return choices.get('yn', 'yes')
        elif prompt_type == 'numbered':
            count = prompt_info['count']
            if count == 2:
                return str(choices.get('12', '1'))
            elif count == 3:
                return str(choices.get('123', '1'))
            else:
                # Default to first option
                return '1'
        
        return ''
    
    def monitor_and_control(self, interval: float = 1.0):
        """Main monitoring loop"""
        self.logger.info(f"Starting controller for session '{self.session_name}'")
        last_content = ""
        idle_time = 0
        
        while True:
            try:
                # Capture current pane content
                current_content = self.capture_pane_content()
                
                # Check if content has changed
                if current_content != last_content:
                    last_content = current_content
                    idle_time = 0
                else:
                    idle_time += interval
                
                # If idle for more than 1 second, check for prompts
                if idle_time >= 1.0:
                    prompt_info = self.detect_prompt_type(current_content)
                    if prompt_info:
                        self.logger.info(f"Detected prompt: {prompt_info}")
                        response = self.auto_respond(prompt_info)
                        if response:
                            self.send_input(response)
                            self.send_input('\n')  # Send Enter key
                            idle_time = 0  # Reset idle time after responding
                
                time.sleep(interval)
                
            except KeyboardInterrupt:
                self.logger.info("Controller stopped by user")
                break
            except Exception as e:
                self.logger.error(f"Error in controller: {e}")
                time.sleep(interval)

def run_controller(session_name: str, pane_id: Optional[str] = None):
    """Run the controller for a specific session"""
    controller = Controller(session_name, pane_id)
    controller.monitor_and_control()