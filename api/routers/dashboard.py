"""Web dashboard router for FastAPI"""

import logging
import secrets
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from fastapi.templating import Jinja2Templates

from libs.core.session_manager import SessionManager
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmapGenerator
from libs.dashboard.widgets.project_health import ProjectHealth
from libs.yesman_config import YesmanConfig

logger = logging.getLogger(__name__)

router = APIRouter(tags=["web-dashboard"])
templates = Jinja2Templates(directory="web-dashboard/static/templates")

# Initialize managers
session_manager = SessionManager()
config = YesmanConfig()
heatmap_generator = ActivityHeatmapGenerator(config)

# Legacy HTML dashboard route removed - now using SvelteKit at root


@router.get("/api/dashboard/sessions")
async def get_sessions():
    """Get session list"""
    try:
        # Get session information from SessionManager
        sessions = session_manager.get_all_sessions()

        # Convert SessionInfo objects to web-friendly format
        web_sessions = []
        for session in sessions:
            web_sessions.append(
                {
                    "session_name": session.session_name,
                    "project_name": session.project_name,
                    "template": session.template,
                    "status": session.status,
                    "exists": session.exists,
                    "controller_status": session.controller_status,
                    "windows": [
                        {
                            "name": w.name,
                            "index": w.index,
                            "panes": [
                                {
                                    "id": p.id,
                                    "command": p.command,
                                    "is_claude": p.is_claude,
                                    "is_controller": p.is_controller,
                                    "current_task": getattr(p, "current_task", None),
                                    "activity_score": getattr(p, "activity_score", 0),
                                }
                                for p in w.panes
                            ],
                        }
                        for w in session.windows
                    ],
                    "panes": sum(len(w.panes) for w in session.windows),
                    "claude_active": any(p.is_claude for w in session.windows for p in w.panes),
                }
            )

        return web_sessions
    except Exception as e:
        logger.error(f"Failed to get sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.get("/api/dashboard/health")
async def get_project_health():
    """Get project health metrics"""
    try:
        # Try to use ProjectHealth widget if available
        try:
            health_widget = ProjectHealth()
            health_data = health_widget.calculate_health()

            return {
                "overall_score": health_data.get("overall_score", 75),
                "categories": {
                    "build": {"score": health_data.get("build_score", 85), "status": "good"},
                    "tests": {"score": health_data.get("test_score", 70), "status": "warning"},
                    "dependencies": {"score": health_data.get("deps_score", 90), "status": "good"},
                    "security": {"score": health_data.get("security_score", 80), "status": "good"},
                    "performance": {"score": health_data.get("perf_score", 65), "status": "warning"},
                    "code_quality": {"score": health_data.get("quality_score", 85), "status": "good"},
                    "git": {"score": health_data.get("git_score", 95), "status": "excellent"},
                    "documentation": {"score": health_data.get("docs_score", 60), "status": "warning"},
                },
                "suggestions": health_data.get(
                    "suggestions",
                    [
                        "Consider increasing test coverage",
                        "Update outdated dependencies",
                        "Add more documentation",
                    ],
                ),
                "last_updated": datetime.now().isoformat(),
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
                    "documentation": {"score": 60, "status": "warning"},
                },
                "suggestions": [
                    "Consider increasing test coverage",
                    "Update outdated dependencies",
                    "Add more documentation",
                ],
                "last_updated": datetime.now().isoformat(),
            }
    except Exception as e:
        logger.error(f"Failed to get health data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get health data: {str(e)}")


@router.get("/api/dashboard/activity")
async def get_activity_data():
    """Get activity heatmap data"""
    try:
        # Try to get real git activity data
        import subprocess
        from collections import defaultdict
        from datetime import timedelta

        try:
            # Get git log for last 365 days
            cmd = ["git", "log", "--since=365 days ago", "--pretty=format:%ad", "--date=short"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Count activities per day
            activity_counts = defaultdict(int)
            for date_str in result.stdout.strip().split("\n"):
                if date_str:
                    activity_counts[date_str] += 1

            # Generate complete date range
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=364)

            activities = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                activities.append(
                    {
                        "date": date_str,
                        "activity_count": activity_counts.get(date_str, 0),
                    }
                )
                current_date += timedelta(days=1)

            active_days = sum(1 for a in activities if a["activity_count"] > 0)

            return {
                "activities": activities,
                "total_days": len(activities),
                "active_days": active_days,
                "max_activity": max((a["activity_count"] for a in activities), default=0),
                "avg_activity": sum(a["activity_count"] for a in activities) / len(activities) if activities else 0,
            }
        except (subprocess.CalledProcessError, ImportError, AttributeError):
            # Fallback with mock data for last 90 days
            from datetime import timedelta

            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=89)

            activities = []
            current_date = start_date
            while current_date <= end_date:
                # Generate mock activity data
                activity_count = secrets.randbelow(16) if secrets.randbelow(10) > 3 else 0
                activities.append(
                    {
                        "date": current_date.isoformat(),
                        "activity_count": activity_count,
                    }
                )
                current_date += timedelta(days=1)

            active_days = sum(1 for a in activities if a["activity_count"] > 0)

            return {
                "activities": activities,
                "total_days": len(activities),
                "active_days": active_days,
                "max_activity": max((a["activity_count"] for a in activities), default=0),
                "avg_activity": sum(a["activity_count"] for a in activities) / len(activities) if activities else 0,
            }
    except Exception as e:
        logger.error(f"Failed to get activity data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get activity data: {str(e)}")


@router.get("/api/dashboard/heatmap/{session_name}")
async def get_session_heatmap(session_name: str, days: int = Query(7, ge=1, le=30)):
    """세션별 히트맵 데이터 반환"""
    try:
        heatmap_data = heatmap_generator.generate_heatmap_data([session_name], days=days)
        return heatmap_data
    except Exception as e:
        logger.error(f"Failed to get heatmap data for {session_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get heatmap data: {str(e)}")


@router.get("/api/dashboard/stats")
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
            "last_update": datetime.now().isoformat(),
        }
    except Exception as e:
        logger.error(f"Failed to get stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")
