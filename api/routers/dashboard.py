"""Web dashboard router for FastAPI"""

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime
import random
import logging

from libs.core.session_manager import SessionManager
from libs.dashboard.widgets.project_health import ProjectHealth
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmap

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/web", tags=["web-dashboard"])
templates = Jinja2Templates(directory="web-dashboard/static/templates")

# Initialize managers
session_manager = SessionManager()

@router.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Web dashboard main page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Yesman Claude Dashboard"
    })

@router.get("/api/sessions")
async def get_sessions():
    """Get session list"""
    try:
        # Get session information from SessionManager
        sessions = session_manager.get_cached_sessions_list()
        
        # Convert to web-friendly format
        web_sessions = []
        for session in sessions:
            session_detail = session_manager.get_session_info(session['session_name'])
            web_sessions.append({
                'name': session['session_name'],
                'id': session.get('session_id', ''),
                'active': True,  # Since these are from active session list
                'created': session.get('session_created'),
                'windows': session_detail.get('windows', []) if session_detail else [],
                'panes': sum(len(w.get('panes', [])) for w in session_detail.get('windows', [])) if session_detail else 0,
                'claude_active': any(p.get('has_claude', False) for w in session_detail.get('windows', []) for p in w.get('panes', [])) if session_detail else False
            })
        
        return {
            "sessions": web_sessions,
            "total": len(web_sessions),
            "active": len(web_sessions)
        }
    except Exception as e:
        logger.error(f"Failed to get sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")

@router.get("/api/health")
async def get_project_health():
    """Get project health metrics"""
    try:
        # Try to use ProjectHealth widget if available
        try:
            health_widget = ProjectHealth()
            health_data = health_widget.calculate_health()
            
            return {
                "overall_score": health_data.get('overall_score', 75),
                "categories": {
                    "build": {"score": health_data.get('build_score', 85), "status": "good"},
                    "tests": {"score": health_data.get('test_score', 70), "status": "warning"},
                    "dependencies": {"score": health_data.get('deps_score', 90), "status": "good"},
                    "security": {"score": health_data.get('security_score', 80), "status": "good"},
                    "performance": {"score": health_data.get('perf_score', 65), "status": "warning"},
                    "code_quality": {"score": health_data.get('quality_score', 85), "status": "good"},
                    "git": {"score": health_data.get('git_score', 95), "status": "excellent"},
                    "documentation": {"score": health_data.get('docs_score', 60), "status": "warning"}
                },
                "suggestions": health_data.get('suggestions', [
                    "Consider increasing test coverage",
                    "Update outdated dependencies",
                    "Add more documentation"
                ]),
                "last_updated": datetime.now().isoformat()
            }
        except ImportError:
            # Fallback with mock data if ProjectHealth is not available
            return {
                "overall_score": 78.5,
                "categories": {
                    "build": {"score": 85, "status": "good"},
                    "tests": {"score": 70, "status": "warning"},
                    "dependencies": {"score": 90, "status": "good"},
                    "security": {"score": 80, "status": "good"},
                    "performance": {"score": 65, "status": "warning"},
                    "code_quality": {"score": 85, "status": "good"},
                    "git": {"score": 95, "status": "excellent"},
                    "documentation": {"score": 60, "status": "warning"}
                },
                "suggestions": [
                    "Consider increasing test coverage",
                    "Update outdated dependencies",
                    "Add more documentation"
                ],
                "last_updated": datetime.now().isoformat()
            }
    except Exception as e:
        logger.error(f"Failed to get health data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health data: {str(e)}")

@router.get("/api/activity")
async def get_activity_data():
    """Get activity heatmap data"""
    try:
        # Try to use ActivityHeatmap widget if available
        try:
            activity_widget = ActivityHeatmap()
            activity_data = activity_widget.get_activity_data()
            
            # Format for web
            activities = []
            for day_data in activity_data:
                activities.append({
                    "date": day_data.get("date"),
                    "activity_count": day_data.get("count", 0)
                })
                
            return {
                "activities": activities,
                "total_days": len(activities),
                "active_days": sum(1 for a in activities if a["activity_count"] > 0),
                "max_activity": max((a["activity_count"] for a in activities), default=0),
                "avg_activity": sum(a["activity_count"] for a in activities) / len(activities) if activities else 0
            }
        except (ImportError, AttributeError):
            # Fallback with mock data for last 90 days
            from datetime import timedelta
            
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=89)
            
            activities = []
            current_date = start_date
            while current_date <= end_date:
                # Generate mock activity data
                activity_count = random.randint(0, 15) if random.random() > 0.3 else 0
                activities.append({
                    "date": current_date.isoformat(),
                    "activity_count": activity_count
                })
                current_date += timedelta(days=1)
            
            active_days = sum(1 for a in activities if a['activity_count'] > 0)
            
            return {
                "activities": activities,
                "total_days": len(activities),
                "active_days": active_days,
                "max_activity": max((a['activity_count'] for a in activities), default=0),
                "avg_activity": sum(a['activity_count'] for a in activities) / len(activities) if activities else 0
            }
    except Exception as e:
        logger.error(f"Failed to get activity data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get activity data: {str(e)}")

@router.get("/api/stats")
async def get_dashboard_stats():
    """Get dashboard statistics summary"""
    try:
        # Get data from other endpoints
        sessions_data = await get_sessions()
        health_data = await get_project_health()
        activity_data = await get_activity_data()
        
        return {
            "active_sessions": sessions_data["active"],
            "total_projects": 1,  # Current project count
            "health_score": health_data["overall_score"],
            "activity_streak": activity_data["active_days"],
            "last_update": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")