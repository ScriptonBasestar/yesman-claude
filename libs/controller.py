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
import sys

class Controller:
    def __init__(self, session_name: str, pane_id: Optional[str] = None):
        self.session_name = session_name
        self.pane_id = pane_id if pane_id is not None else 0
        self.server = libtmux.Server()
        self.config = YesmanConfig()

        # Setup console logger for immediate feedback
        self.logger = logging.getLogger(f"yesman.controller.{session_name}")
        
        # Add console handler if not already present
        if not any(isinstance(h, logging.StreamHandler) for h in self.logger.handlers):
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(
                logging.Formatter('%(asctime)s - [CONTROLLER] %(levelname)s - %(message)s')
            )
            self.logger.addHandler(console_handler)
        
        # Set log level based on config or default to INFO
        log_level = self.config.get('log_level', 'info').upper()
        self.logger.setLevel(getattr(logging, log_level, logging.INFO))
        
        # Find the session and claude pane
        self.logger.info(f"Initializing controller for session: {session_name}")
        self.session = self._find_session()
        self.claude_pane = self._find_claude_pane()
        
    def _find_session(self):
        """Find the tmux session by name"""
        self.logger.info(f"Searching for tmux session: {self.session_name}")
        session = self.server.find_where({"session_name": self.session_name})
        if not session:
            self.logger.error(f"Session '{self.session_name}' not found")
            raise ValueError(f"Session '{self.session_name}' not found")
        self.logger.info(f"Found session: {self.session_name}")
        return session
    
    def _find_claude_pane(self):
        """Find the pane running claude command"""
        if self.pane_id:
            self.logger.info(f"Looking for specific pane ID: {self.pane_id}")
            # If pane_id is specified, use it directly
            for window in self.session.list_windows():
                for pane in window.list_panes():
                    if pane.get("pane_id") == self.pane_id:
                        self.logger.info(f"Found specified pane: {self.pane_id}")
                        return pane
        
        # Otherwise, search for pane with claude command
        self.logger.info("Searching for claude pane in all windows...")
        
        # Patterns to identify claude panes
        claude_patterns = ["claude", "bash", "zsh", "sh", "fish"]
        
        for window in self.session.list_windows():
            window_name = window.get('window_name')
            self.logger.debug(f"Checking window: {window_name}")
            
            # Skip controller window
            if window_name and "controller" in window_name.lower():
                continue
                
            for pane in window.list_panes():
                # Get both current command and pane start command
                try:
                    current_cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    start_cmd = pane.cmd("display-message", "-p", "#{pane_start_command}").stdout[0] if hasattr(pane, 'start_command') else ""
                    
                    self.logger.debug(f"  Pane {pane.get('pane_id')} - current: {current_cmd}, start: {start_cmd}")
                    
                    # Check if this is likely a claude pane
                    # Priority 1: Explicitly running claude
                    if "claude" in current_cmd.lower() or "claude" in start_cmd.lower():
                        self.logger.info(f"Found claude pane (explicit): {pane.get('pane_id')} in window '{window_name}'")
                        return pane
                    
                    # Priority 2: Shell pane in first window (likely where claude will run)
                    if window.get('window_index') == '0' and any(shell in current_cmd.lower() for shell in claude_patterns[1:]):
                        self.logger.info(f"Found potential claude pane (shell): {pane.get('pane_id')} in window '{window_name}'")
                        return pane
                        
                except Exception as e:
                    self.logger.debug(f"Error checking pane {pane.get('pane_id')}: {e}")
        
        # If still not found, use the first pane of the first window
        first_window = self.session.list_windows()[0]
        if first_window:
            first_pane = first_window.list_panes()[0]
            if first_pane:
                self.logger.warning(f"No explicit claude pane found. Using first pane: {first_pane.get('pane_id')}")
                return first_pane
        
        self.logger.error(f"No suitable pane found in session '{self.session_name}'")
        raise ValueError(f"No suitable pane found in session '{self.session_name}'")
    
    def capture_pane_content(self, lines: int = 50) -> str:
        """Capture the current content of the claude pane"""
        # Capture only the visible pane content
        content = self.claude_pane.cmd("capture-pane", "-p", "-S", "-").stdout
        return "\n".join(content)
    
    def send_input(self, text: str):
        """Send input to the claude pane"""
        # Ensure text is a string
        text = str(text)
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
            self.logger.debug(f"Detected {len(options)} numbered options")
            return {
                'type': 'numbered',
                'options': options,
                'count': len(options)
            }
        
        # Check for yes/no prompts
        last_lines = "\n".join(lines[-5:]).lower()
        for pattern in yn_patterns:
            if re.search(pattern, last_lines):
                self.logger.debug(f"Detected yes/no prompt with pattern: {pattern}")
                return {
                    'type': 'yn',
                    'pattern': pattern
                }
        
        return None
    
    def auto_respond(self, prompt_info: Dict[str, Any]) -> str:
        """Generate automatic response based on prompt type"""
        prompt_type = prompt_info['type']
        
        # Get choice configuration (check both 'choice' and 'choice' for backward compatibility)
        choices = self.config.get('choice', self.config.get('choice', {}))
        
        if prompt_type == 'yn':
            response = choices.get('yn', 'yes')
            # Ensure it's a string
            return str(response)
        elif prompt_type == 'numbered':
            count = prompt_info['count']
            if count == 2:
                response = choices.get('12', '1')
            elif count == 3:
                response = choices.get('123', '1')
            else:
                # Default to first option
                response = '1'
            # Ensure it's a string
            return str(response)
        
        return ''
    
    def detect_trust_prompt(self, content: str) -> bool:
        """화면에 trust 프롬프트가 있는지 감지"""
        trust_patterns = [
            r"Do you trust the files in this folder\?",
            r"Claude Code may read files in this folder",
            r"Yes, proceed",
        ]
        for pattern in trust_patterns:
            if pattern in content:
                return True
        return False

    def is_idle_screen(self, content: str) -> bool:
        """claude가 대기(웰컴/팁/프롬프트) 상태인지 감지"""
        idle_patterns = [
            r"Welcome to Claude Code!",
            r"/help for help",
            r"Tip: Use /memory",
            r"cwd: ",
            r"for shortcuts",
            r"Try \"fix typecheck errors\"",
            r"\s*>\s*$",  # 빈 프롬프트
        ]
        for pattern in idle_patterns:
            if pattern in content:
                return True
        return False

    def auto_trust_if_needed(self):
        """trust 프롬프트가 있으면 1을 입력"""
        content = self.capture_pane_content()
        # 마지막 박스의 내용을 확인
        last_box_start = content.rfind("╭")
        last_box_end = content.rfind("╰")
        if last_box_start != -1 and last_box_end != -1:
            last_box_content = content[last_box_start:last_box_end]
            # 1. trust 프롬프트가 마지막 박스에 있으면 무조건 1 입력
            if self.detect_trust_prompt(last_box_content):
                self.logger.info("[AUTO] 'Do you trust the files in this folder?' 프롬프트 감지됨. 1 입력.")
                self.send_input('1')
                return True
        # 2. 그 외에 idle 화면이면 아무것도 하지 않음
        if self.is_idle_screen(content):
            return False
        return False
    
    def monitor_and_control(self, interval: float = 1.0):
        """Main monitoring loop"""
        self.logger.info(f"Starting controller for session '{self.session_name}'")
        self.logger.info(f"Monitoring claude pane: {self.claude_pane.get('pane_id')}")
        self.logger.info(f"Check interval: {interval}s")
        self.logger.info("Controller is running. Press Ctrl+C to stop.")
        
        # claude 콘솔이 아니면 경고 후 종료
        current_cmd = self.claude_pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
        if "claude" not in current_cmd.lower():
            self.logger.error("현재 창이 claude 콘솔이 아닙니다. 컨트롤러를 종료합니다.")
            click.echo("[경고] 현재 창이 claude 콘솔이 아닙니다. 컨트롤러를 종료합니다.")
            return

        last_content = self.capture_pane_content()
        shown_progress_text = False
        try:
            while True:
                time.sleep(interval)
                content = self.capture_pane_content()
                # Claude Code가 실행 중인지 확인
                current_cmd = self.claude_pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                if "claude" in current_cmd.lower():
                    # trust 프롬프트 자동 응답
                    if self.auto_trust_if_needed():
                        continue
                if content == last_content:
                    if not shown_progress_text:
                        click.echo("진행중: ", nl=False)
                        shown_progress_text = True
                    # 1초에 1개씩만 네모 추가
                    click.echo("□", nl=False)
                    sys.stdout.flush()
                else:
                    click.echo("\r", nl=False)  # 줄 초기화
                    shown_progress_text = False
                last_content = content
        except KeyboardInterrupt:
            self.logger.info("Controller stopped by user.")
            click.echo("\n컨트롤러가 중지되었습니다.")

def run_controller(session_name: str, pane_id: Optional[str] = None):
    """Run the controller for a specific session"""
    controller = Controller(session_name, pane_id)
    controller.monitor_and_control()
