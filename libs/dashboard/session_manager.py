"""Session management for dashboard"""

import libtmux
import logging
from typing import List, Dict, Any
from pathlib import Path

from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
from .models import SessionInfo, WindowInfo, PaneInfo


class SessionManager:
    """Manages tmux session information for dashboard"""
    
    def __init__(self):
        self.config = YesmanConfig()
        self.tmux_manager = TmuxManager(self.config)
        self.server = libtmux.Server()
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file-only output"""
        logger = logging.getLogger("yesman.dashboard.session_manager")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        log_path_str = self.config.get("log_path", "~/tmp/logs/yesman/")
        log_path = Path(log_path_str).expanduser()
        log_path.mkdir(parents=True, exist_ok=True)
        
        log_file = log_path / "session_manager.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        return logger
    
    def get_all_sessions(self) -> List[SessionInfo]:
        """Get information about all yesman sessions"""
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
    
    def _get_session_info(self, project_name: str, project_conf: Dict[str, Any]) -> SessionInfo:
        """Get information for a single session"""
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
    
    def _get_window_info(self, window) -> WindowInfo:
        """Get information for a single window"""
        panes = []
        
        for pane in window.list_panes():
            try:
                cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                pane_info = PaneInfo(
                    id=pane.get('pane_id'),
                    command=cmd,
                    is_claude='claude' in cmd.lower(),
                    is_controller='controller' in cmd.lower() or 'yesman' in cmd.lower()
                )
                panes.append(pane_info)
            except Exception as e:
                self.logger.error(f"Error getting pane info: {e}")
        
        return WindowInfo(
            name=window.get('window_name'),
            index=window.get('window_index'),
            panes=panes
        )