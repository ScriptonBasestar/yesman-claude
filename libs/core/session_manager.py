"""Session management for dashboard"""

import libtmux
import logging
from typing import List, Dict, Any
from pathlib import Path

from libs.yesman_config import YesmanConfig
from libs.tmux_manager import TmuxManager
from .models import SessionInfo, WindowInfo, PaneInfo
from .session_cache import SessionCache
from ..utils import ensure_log_directory


class SessionManager:
    """Manages tmux session information for dashboard"""
    
    def __init__(self):
        self.config = YesmanConfig()
        self.tmux_manager = TmuxManager(self.config)
        self.server = libtmux.Server()
        self.logger = self._setup_logger()
        
        # Initialize session cache with 3-second TTL for dashboard responsiveness
        self.cache = SessionCache(default_ttl=3.0, max_entries=100)
        
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
    
    def get_all_sessions(self) -> List[SessionInfo]:
        """Get information about all yesman sessions with caching"""
        cache_key = "all_sessions"
        
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
        
        # Use cache with compute function
        return self.cache.get_or_compute(cache_key, compute_sessions)
    
    def _get_session_info(self, project_name: str, project_conf: Dict[str, Any]) -> SessionInfo:
        """Get information for a single session with caching"""
        cache_key = f"session_{project_name}"
        
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
        
        # Use cache with compute function
        return self.cache.get_or_compute(cache_key, compute_session_info)
    
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
    
    def invalidate_cache(self, project_name: str = None) -> None:
        """
        Invalidate session cache entries
        
        Args:
            project_name: Specific project to invalidate, or None for all
        """
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
        """Invalidate the all_sessions cache specifically"""
        invalidated = self.cache.invalidate("all_sessions")
        if invalidated:
            self.logger.debug("Invalidated all_sessions cache")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        stats = self.cache.get_stats()
        return {
            'hits': stats.hits,
            'misses': stats.misses,
            'hit_rate': round(stats.hit_rate, 2),
            'total_entries': stats.total_entries,
            'memory_size_bytes': stats.memory_size_bytes,
            'evictions': stats.evictions
        }