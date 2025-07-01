"""Session management for dashboard"""

import libtmux
import logging
import os
import subprocess
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
from enum import Enum
from datetime import datetime

# Try to import psutil, fall back to basic functionality if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None

from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
from .models import SessionInfo, WindowInfo, PaneInfo
from .session_cache import SessionCache
from ..utils import ensure_log_directory


class OperationMode(Enum):
    """Operation modes for different cache behaviors"""
    CLI = "cli"          # Command-line interface mode (no caching)
    DAEMON = "daemon"    # Long-running daemon mode (aggressive caching)
    WEB = "web"          # Web dashboard mode (moderate caching)


class SessionManager:
    """Manages tmux session information for dashboard"""
    
    def __init__(self, operation_mode: Optional[OperationMode] = None):
        self.config = YesmanConfig()
        self.tmux_manager = TmuxManager(self.config)
        self.server = libtmux.Server()
        self.logger = self._setup_logger()
        
        # Detect operation mode if not specified
        self.operation_mode = operation_mode or self._detect_operation_mode()
        
        # Initialize cache based on operation mode
        self.cache = self._init_cache_for_mode()
        
        self.logger.info(f"SessionManager initialized in {self.operation_mode.value} mode")
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file-only output"""
        logger = logging.getLogger("yesman.dashboard.session_manager")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path_str = self.config.get("log_path", "~/tmp/logs/yesman/")
        log_path = ensure_log_directory(Path(log_path_str))
        
        log_file = log_path / "session_manager.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def _detect_operation_mode(self) -> OperationMode:
        """Detect operation mode based on environment"""
        # Check if running in Streamlit (web dashboard)
        if 'streamlit' in os.environ.get('_', '').lower() or 'STREAMLIT_SERVER_PORT' in os.environ:
            return OperationMode.WEB
        
        # Check if running as daemon (has TMUX or SSH_TTY)
        if os.environ.get('TMUX') or os.environ.get('SSH_TTY'):
            return OperationMode.DAEMON
        
        # Default to CLI mode
        return OperationMode.CLI
    
    def _init_cache_for_mode(self) -> Optional[SessionCache]:
        """Initialize cache based on operation mode"""
        if self.operation_mode == OperationMode.CLI:
            # CLI mode: No caching for immediate, fresh data
            self.logger.info("CLI mode: Caching disabled")
            return None
            
        elif self.operation_mode == OperationMode.DAEMON:
            # Daemon mode: Aggressive caching for long-running processes
            cache = SessionCache(default_ttl=30.0, max_entries=500)
            self.logger.info("Daemon mode: Aggressive caching (30s TTL, 500 entries)")
            return cache
            
        else:  # WEB mode
            # Web mode: Moderate caching for dashboard responsiveness
            cache = SessionCache(default_ttl=3.0, max_entries=100)
            self.logger.info("Web mode: Moderate caching (3s TTL, 100 entries)")
            return cache
    
    def get_all_sessions(self) -> List[SessionInfo]:
        """Get information about all yesman sessions with mode-aware caching"""
        def compute_sessions():
            sessions_info = []
            
            try:
                # Load project configurations
                projects = self.tmux_manager.load_projects().get("sessions", {})
                self.logger.info(f"Loaded {len(projects)} projects")
                
                for project_name, project_conf in projects.items():
                    session_info = self._get_session_info(project_name, project_conf)
                    sessions_info.append(session_info)
                
                return sessions_info
                
            except Exception as e:
                self.logger.error(f"Error getting sessions: {e}", exc_info=True)
                return []
        
        # CLI mode: Always compute fresh data (no caching)
        if self.operation_mode == OperationMode.CLI or self.cache is None:
            self.logger.debug("CLI mode: Computing fresh session data")
            return compute_sessions()
        
        # Other modes: Use cache with compute function
        cache_key = "all_sessions"
        return self.cache.get_or_compute(cache_key, compute_sessions)
    
    def _get_session_info(self, project_name: str, project_conf: Dict[str, Any]) -> SessionInfo:
        """Get information for a single session with mode-aware caching"""
        def compute_session_info():
            override = project_conf.get("override", {})
            session_name = override.get("session_name", project_name)
            
            # Check if session exists
            session = self.server.find_where({"session_name": session_name})
            
            windows = []
            controller_status = 'unknown'
            
            if session:
                # Get window information
                for window in session.list_windows():
                    window_info = self._get_window_info(window)
                    windows.append(window_info)
                    
                    # Update controller status based on panes
                    for pane in window_info.panes:
                        if pane.is_controller:
                            controller_status = 'running'
                
                # If no controller found, mark as not running
                if controller_status == 'unknown':
                    controller_status = 'not running'
            
            # Get template name with proper fallback
            template_name = project_conf.get("template_name")
            if template_name is None:
                template_display = "none"
            else:
                # Check if template file actually exists
                template_path = Path(self.config.get_config_dir()) / "templates" / f"{template_name}.yaml"
                if template_path.exists():
                    template_display = template_name
                else:
                    template_display = "N/A"  # Template defined but file missing
            
            return SessionInfo(
                project_name=project_name,
                session_name=session_name,
                template=template_display,
                exists=session is not None,
                status='running' if session else 'stopped',
                windows=windows,
                controller_status=controller_status
            )
        
        # CLI mode: Always compute fresh data (no caching)
        if self.operation_mode == OperationMode.CLI or self.cache is None:
            return compute_session_info()
        
        # Other modes: Use cache with compute function
        cache_key = f"session_{project_name}"
        return self.cache.get_or_compute(cache_key, compute_session_info)
    
    def _get_window_info(self, window) -> WindowInfo:
        """Get information for a single window with detailed pane metrics"""
        panes = []
        
        for pane in window.list_panes():
            try:
                pane_info = self._get_detailed_pane_info(pane)
                panes.append(pane_info)
            except Exception as e:
                self.logger.error(f"Error getting pane info: {e}")
                # Fallback to basic pane info
                try:
                    cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    basic_pane = PaneInfo(
                        id=pane.get('pane_id'),
                        command=cmd,
                        is_claude='claude' in cmd.lower(),
                        is_controller='controller' in cmd.lower() or 'yesman' in cmd.lower()
                    )
                    panes.append(basic_pane)
                except:
                    pass
        
        return WindowInfo(
            name=window.get('window_name'),
            index=window.get('window_index'),
            panes=panes
        )
    
    def _get_detailed_pane_info(self, pane) -> PaneInfo:
        """Get detailed information for a single pane including metrics"""
        try:
            # Get basic pane information
            cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
            pane_id = pane.get('pane_id')
            
            # Get pane PID and process info
            pid_info = pane.cmd("display-message", "-p", "#{pane_pid}").stdout[0]
            pid = int(pid_info) if pid_info.isdigit() else None
            
            # Initialize detailed metrics
            cpu_usage = 0.0
            memory_usage = 0.0
            running_time = 0.0
            status = "unknown"
            current_task = None
            
            # Get process metrics if PID is available and psutil is installed
            if pid and PSUTIL_AVAILABLE:
                try:
                    process = psutil.Process(pid)
                    cpu_usage = process.cpu_percent()
                    memory_info = process.memory_info()
                    memory_usage = memory_info.rss / 1024 / 1024  # Convert to MB
                    
                    # Calculate running time
                    create_time = process.create_time()
                    running_time = datetime.now().timestamp() - create_time
                    
                    # Determine process status
                    status = process.status()
                    
                    # Try to determine current task from command line
                    try:
                        cmdline = process.cmdline()
                        current_task = self._analyze_current_task(cmdline, cmd)
                    except:
                        current_task = cmd
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # Process might have ended or we don't have permission
                    pass
            elif pid and not PSUTIL_AVAILABLE:
                # Fallback: basic task analysis without psutil
                current_task = self._analyze_current_task([cmd], cmd)
            
            # Get pane activity information
            try:
                # Get last pane activity time (approximation)
                pane_activity = pane.cmd("display-message", "-p", "#{pane_activity}").stdout[0]
                activity_timestamp = int(pane_activity) if pane_activity.isdigit() else 0
                
                # Calculate idle time and activity score
                current_time = datetime.now().timestamp()
                idle_time = current_time - activity_timestamp if activity_timestamp > 0 else 0
                
                # Activity score: higher for recent activity, lower for idle panes
                activity_score = max(0, 100 - (idle_time / 60))  # Decreases over minutes
                
            except:
                idle_time = 0.0
                activity_score = 50.0  # Default moderate activity
            
            # Get recent pane output for analysis
            last_output = None
            output_lines = 0
            try:
                # Capture last few lines of pane content
                pane_content = pane.cmd("capture-pane", "-p").stdout
                if pane_content:
                    lines = [line for line in pane_content if line.strip()]
                    output_lines = len(lines)
                    if lines:
                        last_output = lines[-1][:100]  # Last line, truncated
            except:
                pass
            
            # Create enhanced PaneInfo
            pane_info = PaneInfo(
                id=pane_id,
                command=cmd,
                is_claude='claude' in cmd.lower(),
                is_controller='controller' in cmd.lower() or 'yesman' in cmd.lower(),
                current_task=current_task,
                idle_time=idle_time,
                last_activity=datetime.fromtimestamp(activity_timestamp) if activity_timestamp > 0 else datetime.now(),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                pid=pid,
                running_time=running_time,
                status=status,
                activity_score=activity_score,
                last_output=last_output,
                output_lines=output_lines
            )
            
            return pane_info
            
        except Exception as e:
            self.logger.error(f"Error getting detailed pane info: {e}")
            # Return basic pane info as fallback
            return PaneInfo(
                id=pane.get('pane_id', 'unknown'),
                command=cmd if 'cmd' in locals() else 'unknown',
                is_claude=False,
                is_controller=False
            )
    
    def _analyze_current_task(self, cmdline: List[str], command: str) -> str:
        """Analyze command line to determine current task"""
        if not cmdline:
            return command
        
        # Join command line for analysis
        full_cmd = ' '.join(cmdline)
        
        # Claude-specific task detection
        if 'claude' in full_cmd.lower():
            if '--read' in full_cmd:
                return "Reading files"
            elif '--edit' in full_cmd or '--write' in full_cmd:
                return "Editing code"
            elif 'dashboard' in full_cmd:
                return "Running dashboard"
            else:
                return "Claude interactive"
        
        # Controller-specific task detection
        elif 'yesman' in full_cmd.lower() or 'controller' in full_cmd.lower():
            if 'dashboard' in full_cmd:
                return "Dashboard controller"
            elif 'setup' in full_cmd:
                return "Setting up sessions"
            elif 'teardown' in full_cmd:
                return "Tearing down sessions"
            else:
                return "Yesman controller"
        
        # Common development tasks
        elif any(term in full_cmd.lower() for term in ['vim', 'nano', 'code', 'nvim']):
            return "Editing files"
        elif any(term in full_cmd.lower() for term in ['python', 'node', 'npm', 'pip']):
            return "Running application"
        elif any(term in full_cmd.lower() for term in ['git', 'commit', 'push', 'pull']):
            return "Git operations"
        elif any(term in full_cmd.lower() for term in ['test', 'pytest', 'jest']):
            return "Running tests"
        elif any(term in full_cmd.lower() for term in ['build', 'compile', 'make']):
            return "Building project"
        elif 'bash' in full_cmd.lower() or 'zsh' in full_cmd.lower():
            return "Terminal session"
        else:
            # Extract the main command (first meaningful part)
            main_cmd = cmdline[0].split('/')[-1] if cmdline else command
            return f"Running {main_cmd}"
    
    def attach_to_pane(self, session_name: str, window_index: str, pane_id: str) -> Dict[str, Any]:
        """
        Attach to a specific tmux pane
        
        Args:
            session_name: Name of the tmux session
            window_index: Index of the window containing the pane
            pane_id: ID of the pane to attach to
            
        Returns:
            Dictionary with result status and information
        """
        try:
            # Find the session
            session = self.server.find_where({"session_name": session_name})
            if not session:
                return {
                    "success": False,
                    "error": f"Session '{session_name}' not found",
                    "action": "none"
                }
            
            # Find the window
            window = session.find_where({"window_index": window_index})
            if not window:
                return {
                    "success": False,
                    "error": f"Window {window_index} not found in session '{session_name}'",
                    "action": "none"
                }
            
            # Find the pane
            pane = window.find_where({"pane_id": pane_id})
            if not pane:
                return {
                    "success": False,
                    "error": f"Pane {pane_id} not found in window {window_index}",
                    "action": "none"
                }
            
            # Generate attachment command
            attach_cmd = f"tmux attach-session -t {session_name} \\; select-window -t {window_index} \\; select-pane -t {pane_id}"
            
            return {
                "success": True,
                "session_name": session_name,
                "window_index": window_index,
                "pane_id": pane_id,
                "attach_command": attach_cmd,
                "action": "attach",
                "message": f"Ready to attach to pane {pane_id} in {session_name}:{window_index}"
            }
            
        except Exception as e:
            self.logger.error(f"Error attaching to pane: {e}")
            return {
                "success": False,
                "error": f"Attachment failed: {str(e)}",
                "action": "error"
            }
    
    def create_terminal_script(self, attach_command: str, script_path: str = None) -> str:
        """
        Create a terminal script for pane attachment
        
        Args:
            attach_command: The tmux attach command
            script_path: Optional path for the script file
            
        Returns:
            Path to the created script file
        """
        if script_path is None:
            script_path = f"/tmp/yesman_attach_{os.getpid()}.sh"
        
        script_content = f"""#!/bin/bash
# Auto-generated tmux attachment script
# Generated at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

echo "Attaching to tmux pane..."
{attach_command}
"""
        
        try:
            with open(script_path, 'w') as f:
                f.write(script_content)
            
            # Make script executable
            os.chmod(script_path, 0o755)
            
            self.logger.info(f"Created attachment script: {script_path}")
            return script_path
            
        except Exception as e:
            self.logger.error(f"Error creating attachment script: {e}")
            raise
    
    def execute_pane_attachment(self, session_name: str, window_index: str, pane_id: str) -> Dict[str, Any]:
        """
        Execute pane attachment with error handling
        
        Args:
            session_name: Name of the tmux session
            window_index: Index of the window containing the pane
            pane_id: ID of the pane to attach to
            
        Returns:
            Dictionary with execution result
        """
        try:
            # First, validate the attachment
            attach_info = self.attach_to_pane(session_name, window_index, pane_id)
            
            if not attach_info["success"]:
                return attach_info
            
            # Create and execute the attachment script
            script_path = self.create_terminal_script(attach_info["attach_command"])
            
            # Return information for client-side execution
            return {
                "success": True,
                "script_path": script_path,
                "attach_command": attach_info["attach_command"],
                "session_name": session_name,
                "window_index": window_index,
                "pane_id": pane_id,
                "action": "execute",
                "message": f"Attachment script created: {script_path}"
            }
            
        except Exception as e:
            self.logger.error(f"Error executing pane attachment: {e}")
            return {
                "success": False,
                "error": f"Execution failed: {str(e)}",
                "action": "error"
            }
    
    def invalidate_cache(self, project_name: str = None) -> None:
        """
        Invalidate session cache entries (mode-aware)
        
        Args:
            project_name: Specific project to invalidate, or None for all
        """
        # CLI mode: No cache to invalidate
        if self.operation_mode == OperationMode.CLI or self.cache is None:
            self.logger.debug("CLI mode: No cache to invalidate")
            return
        
        if project_name:
            # Invalidate specific session
            session_key = f"session_{project_name}"
            invalidated = self.cache.invalidate(session_key)
            if invalidated:
                self.logger.debug(f"Invalidated cache for project: {project_name}")
        else:
            # Invalidate all sessions
            cleared = self.cache.clear()
            self.logger.info(f"Cleared all session cache entries: {cleared}")
    
    def invalidate_all_sessions_cache(self) -> None:
        """Invalidate the all_sessions cache specifically (mode-aware)"""
        # CLI mode: No cache to invalidate
        if self.operation_mode == OperationMode.CLI or self.cache is None:
            self.logger.debug("CLI mode: No cache to invalidate")
            return
        
        invalidated = self.cache.invalidate("all_sessions")
        if invalidated:
            self.logger.debug("Invalidated all_sessions cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics (mode-aware)"""
        # CLI mode: Return empty stats
        if self.operation_mode == OperationMode.CLI or self.cache is None:
            return {
                'hits': 0,
                'misses': 0,
                'hit_rate': 0.0,
                'total_entries': 0,
                'memory_size_bytes': 0,
                'evictions': 0,
                'mode': self.operation_mode.value,
                'cache_enabled': False
            }
        
        stats = self.cache.get_stats()
        return {
            'hits': stats.hits,
            'misses': stats.misses,
            'hit_rate': round(stats.hit_rate, 2),
            'total_entries': stats.total_entries,
            'memory_size_bytes': stats.memory_size_bytes,
            'evictions': stats.evictions,
            'mode': self.operation_mode.value,
            'cache_enabled': True
        }