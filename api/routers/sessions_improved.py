#!/usr/bin/env python3
"""
Improved sessions router with dependency injection and proper error handling
"""

from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Any, Optional
import logging

from libs.core.types import SessionAPIData, APIResponse
from libs.core.error_handling import YesmanError, ErrorCategory, safe_execute
from libs.core.base_command import SessionCommandMixin, ConfigCommandMixin
from libs.core.session_manager import SessionManager
from libs.core.settings import settings
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig
from api import models


# Set up logger
logger = logging.getLogger("yesman.api.sessions")

# Dependency injection functions
def get_config() -> YesmanConfig:
    """Get YesmanConfig instance"""
    try:
        return YesmanConfig()
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuration loading failed"
        )

def get_tmux_manager(config: YesmanConfig = Depends(get_config)) -> TmuxManager:
    """Get TmuxManager instance"""
    try:
        return TmuxManager(config)
    except Exception as e:
        logger.error(f"Failed to initialize TmuxManager: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="TmuxManager initialization failed"
        )

def get_session_manager() -> SessionManager:
    """Get SessionManager instance"""
    try:
        return SessionManager()
    except Exception as e:
        logger.error(f"Failed to initialize SessionManager: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SessionManager initialization failed"
        )


class SessionService:
    """Service class for session operations"""
    
    def __init__(self, 
                 session_manager: SessionManager,
                 tmux_manager: TmuxManager):
        self.session_manager = session_manager
        self.tmux_manager = tmux_manager
        self.logger = logging.getLogger("yesman.api.sessions.service")
    
    def get_all_sessions(self) -> List[SessionAPIData]:
        """Get all sessions with error handling"""
        try:
            sessions_data = self.session_manager.get_all_sessions()
            return [self._convert_session_to_api_data(session) for session in sessions_data]
        except Exception as e:
            self.logger.error(f"Failed to get sessions: {e}")
            raise YesmanError(
                "Failed to retrieve sessions",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def get_session_by_name(self, session_name: str) -> Optional[SessionAPIData]:
        """Get specific session by name"""
        try:
            session_data = self.session_manager.get_session_info(session_name)
            if session_data:
                return self._convert_session_to_api_data(session_data)
            return None
        except Exception as e:
            self.logger.error(f"Failed to get session {session_name}: {e}")
            raise YesmanError(
                f"Failed to retrieve session '{session_name}'",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def setup_session(self, session_name: str) -> Dict[str, Any]:
        """Set up a specific session"""
        try:
            # Check if session already exists
            if self._session_exists(session_name):
                raise YesmanError(
                    f"Session '{session_name}' already exists",
                    category=ErrorCategory.VALIDATION
                )
            
            # Load projects configuration
            projects = self.tmux_manager.load_projects().get("sessions", {})
            if session_name not in projects:
                raise YesmanError(
                    f"Session '{session_name}' not found in projects configuration",
                    category=ErrorCategory.CONFIGURATION
                )
            
            # Set up session (this would integrate with the improved setup logic)
            result = self._setup_session_internal(session_name, projects[session_name])
            
            return {
                "session_name": session_name,
                "status": "created",
                "details": result
            }
            
        except YesmanError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to setup session {session_name}: {e}")
            raise YesmanError(
                f"Failed to setup session '{session_name}'",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def teardown_session(self, session_name: str) -> Dict[str, Any]:
        """Teardown a specific session"""
        try:
            if not self._session_exists(session_name):
                raise YesmanError(
                    f"Session '{session_name}' not found",
                    category=ErrorCategory.VALIDATION
                )
            
            # Teardown session
            self._teardown_session_internal(session_name)
            
            return {
                "session_name": session_name,
                "status": "removed"
            }
            
        except YesmanError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to teardown session {session_name}: {e}")
            raise YesmanError(
                f"Failed to teardown session '{session_name}'",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def get_session_status(self, session_name: str) -> Dict[str, Any]:
        """Get session status information"""
        try:
            session_data = self.session_manager.get_session_info(session_name)
            if not session_data:
                return {
                    "session_name": session_name,
                    "status": "not_found",
                    "exists": False
                }
            
            return {
                "session_name": session_name,
                "status": session_data.status,
                "exists": True,
                "windows": len(session_data.windows),
                "last_activity": session_data.last_activity
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get status for session {session_name}: {e}")
            raise YesmanError(
                f"Failed to get status for session '{session_name}'",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def _convert_session_to_api_data(self, session_data) -> SessionAPIData:
        """Convert internal session data to API format"""
        try:
            return {
                'session_name': session_data.session_name,
                'status': session_data.status,
                'windows': [
                    {
                        'index': int(w.index) if hasattr(w, 'index') else i,
                        'name': w.name if hasattr(w, 'name') else f'window_{i}',
                        'panes': [
                            {
                                'command': p.command if hasattr(p, 'command') else '',
                                'is_claude': p.is_claude if hasattr(p, 'is_claude') else False,
                                'is_controller': p.is_controller if hasattr(p, 'is_controller') else False
                            } for p in (w.panes if hasattr(w, 'panes') else [])
                        ]
                    } for i, w in enumerate(session_data.windows)
                ],
                'created_at': getattr(session_data, 'created_at', None),
                'last_activity': getattr(session_data, 'last_activity', None)
            }
        except Exception as e:
            self.logger.error(f"Failed to convert session data: {e}")
            raise YesmanError(
                "Failed to convert session data format",
                category=ErrorCategory.SYSTEM,
                cause=e
            )
    
    def _session_exists(self, session_name: str) -> bool:
        """Check if session exists"""
        try:
            sessions = self.tmux_manager.get_all_sessions()
            return any(
                session.get('session_name') == session_name 
                for session in sessions
            )
        except Exception:
            return False
    
    def _setup_session_internal(self, session_name: str, session_config: Dict[str, Any]) -> Dict[str, Any]:
        """Internal session setup logic"""
        # This would integrate with the improved SessionSetupService
        # For now, return a placeholder
        return {"message": "Session setup completed"}
    
    def _teardown_session_internal(self, session_name: str) -> None:
        """Internal session teardown logic"""
        import subprocess
        try:
            subprocess.run(['tmux', 'kill-session', '-t', session_name], 
                         check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            raise YesmanError(f"Failed to kill session: {e}")


# Router with dependency injection
router = APIRouter(tags=["sessions"])


@router.get("/sessions", 
           response_model=List[models.SessionInfo],
           summary="Get all sessions",
           description="Retrieve information about all active tmux sessions")
def get_all_sessions(session_manager: SessionManager = Depends(get_session_manager),
                    tmux_manager: TmuxManager = Depends(get_tmux_manager)):
    """Get all tmux sessions with detailed information"""
    try:
        service = SessionService(session_manager, tmux_manager)
        sessions_data = service.get_all_sessions()
        
        # Convert to Pydantic models
        return [
            models.SessionInfo(
                session_name=session['session_name'],
                project_name=session.get('project_name', ''),
                status=session['status'],
                template=session.get('template', ''),
                windows=[
                    models.WindowInfo(
                        index=window['index'],
                        name=window['name'],
                        panes=[
                            models.PaneInfo(
                                command=pane['command'],
                                is_claude=pane['is_claude'],
                                is_controller=pane['is_controller']
                            ) for pane in window['panes']
                        ]
                    ) for window in session['windows']
                ]
            ) for session in sessions_data
        ]
        
    except YesmanError as e:
        logger.error(f"YesmanError in get_all_sessions: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_all_sessions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/sessions/{session_name}",
           response_model=models.SessionInfo,
           summary="Get specific session",
           description="Retrieve information about a specific session")
def get_session(session_name: str,
               session_manager: SessionManager = Depends(get_session_manager),
               tmux_manager: TmuxManager = Depends(get_tmux_manager)):
    """Get specific session by name"""
    try:
        service = SessionService(session_manager, tmux_manager)
        session_data = service.get_session_by_name(session_name)
        
        if not session_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session '{session_name}' not found"
            )
        
        # Convert to Pydantic model
        return models.SessionInfo(
            session_name=session_data['session_name'],
            project_name=session_data.get('project_name', ''),
            status=session_data['status'],
            template=session_data.get('template', ''),
            windows=[
                models.WindowInfo(
                    index=window['index'],
                    name=window['name'],
                    panes=[
                        models.PaneInfo(
                            command=pane['command'],
                            is_claude=pane['is_claude'],
                            is_controller=pane['is_controller']
                        ) for pane in window['panes']
                    ]
                ) for window in session_data['windows']
            ]
        )
        
    except HTTPException:
        raise
    except YesmanError as e:
        logger.error(f"YesmanError in get_session: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/sessions/{session_name}/setup",
            summary="Setup session",
            description="Create and setup a tmux session")
def setup_session(session_name: str,
                 session_manager: SessionManager = Depends(get_session_manager),
                 tmux_manager: TmuxManager = Depends(get_tmux_manager)):
    """Setup a specific session"""
    try:
        service = SessionService(session_manager, tmux_manager)
        result = service.setup_session(session_name)
        return result
        
    except YesmanError as e:
        logger.error(f"YesmanError in setup_session: {e.message}")
        status_code = status.HTTP_400_BAD_REQUEST if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in setup_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/sessions/{session_name}",
              summary="Teardown session", 
              description="Remove a tmux session")
def teardown_session(session_name: str,
                    session_manager: SessionManager = Depends(get_session_manager),
                    tmux_manager: TmuxManager = Depends(get_tmux_manager)):
    """Teardown a specific session"""
    try:
        service = SessionService(session_manager, tmux_manager)
        result = service.teardown_session(session_name)
        return result
        
    except YesmanError as e:
        logger.error(f"YesmanError in teardown_session: {e.message}")
        status_code = status.HTTP_404_NOT_FOUND if e.category == ErrorCategory.VALIDATION else status.HTTP_500_INTERNAL_SERVER_ERROR
        raise HTTPException(status_code=status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error in teardown_session: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/sessions/{session_name}/status",
           summary="Get session status",
           description="Get current status of a session")
def get_session_status(session_name: str,
                      session_manager: SessionManager = Depends(get_session_manager),
                      tmux_manager: TmuxManager = Depends(get_tmux_manager)):
    """Get session status"""
    try:
        service = SessionService(session_manager, tmux_manager)
        result = service.get_session_status(session_name)
        return result
        
    except YesmanError as e:
        logger.error(f"YesmanError in get_session_status: {e.message}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=e.message
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_session_status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )