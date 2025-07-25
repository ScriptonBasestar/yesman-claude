# Copyright notice.

import logging
import secrets
import subprocess
from collections import defaultdict
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, TypedDict

from fastapi import APIRouter, HTTPException, Query
from fastapi.templating import Jinja2Templates

from api.shared import claude_manager
from libs.core.session_manager import SessionManager
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmapGenerator
from libs.dashboard.widgets.project_health import ProjectHealth
from libs.yesman_config import YesmanConfig

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Web dashboard router for FastAPI."""

# Constants
ACTIVITY_THRESHOLD = 3
MAX_ACTIVITY_COUNT = 16
RANDOM_BOUND = 10


class ActivityData(TypedDict):
    """Type definition for activity data."""

    date: str
    activity_count: int


logger = logging.getLogger(__name__)

router = APIRouter(tags=["web-dashboard"])
templates = Jinja2Templates(directory="web-dashboard/static/templates")

# Initialize managers
session_manager = SessionManager()
config = YesmanConfig()
heatmap_generator = ActivityHeatmapGenerator(config)

# Legacy HTML dashboard route removed - now using SvelteKit at root


@router.get("/api/dashboard/sessions")
async def get_sessions() -> list[dict[str, Any]]:
    """Get session list.

    Returns:
        list[dict[str, Any]]: List of session information dictionaries.

    Raises:
        HTTPException: If session retrieval fails.
    """
    try:
        # Get session information from SessionManager
        sessions = session_manager.get_all_sessions()

        # Convert SessionInfo objects to web-friendly format
        web_sessions = []
        for session in sessions:
            # Get accurate controller status using ClaudeManager
            # (same as individual controller status API)
            try:
                controller = claude_manager.get_controller(session.session_name)
                actual_controller_status = "running" if controller.is_running else "stopped"
            except Exception:
                # Fallback to original status if controller lookup fails
                actual_controller_status = session.controller_status

            web_sessions.append(
                {
                    "session_name": session.session_name,
                    "project_name": session.project_name,
                    "template": session.template,
                    "status": session.status,
                    "exists": session.exists,
                    "controller_status": actual_controller_status,
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
        logger.exception("Failed to get sessions")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {e!s}")


@router.get("/api/dashboard/health")
async def get_project_health() -> dict[str, Any]:
    """Get project health metrics.

    Returns:
        dict[str, Any]: Project health data including scores and suggestions.

    Raises:
        HTTPException: If health data retrieval fails.
    """
    try:
        # Try to use ProjectHealth widget if available
        try:
            health_widget = ProjectHealth()
            health_data = health_widget.calculate_health()

            return {
                "overall_score": health_data.get("overall_score", 75),
                "categories": {
                    "build": {
                        "score": health_data.get("build_score", 85),
                        "status": "good",
                    },
                    "tests": {
                        "score": health_data.get("test_score", 70),
                        "status": "warning",
                    },
                    "dependencies": {
                        "score": health_data.get("deps_score", 90),
                        "status": "good",
                    },
                    "security": {
                        "score": health_data.get("security_score", 80),
                        "status": "good",
                    },
                    "performance": {
                        "score": health_data.get("perf_score", 65),
                        "status": "warning",
                    },
                    "code_quality": {
                        "score": health_data.get("quality_score", 85),
                        "status": "good",
                    },
                    "git": {
                        "score": health_data.get("git_score", 95),
                        "status": "excellent",
                    },
                    "documentation": {
                        "score": health_data.get("docs_score", 60),
                        "status": "warning",
                    },
                },
                "suggestions": health_data.get(
                    "suggestions",
                    [
                        "Consider increasing test coverage",
                        "Update outdated dependencies",
                        "Add more documentation",
                    ],
                ),
                "last_updated": datetime.now(UTC).isoformat(),
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
                "last_updated": datetime.now(UTC).isoformat(),
            }
    except Exception as e:
        logger.exception("Failed to get health data")
        raise HTTPException(status_code=500, detail=f"Failed to get health data: {e!s}")


@router.get("/api/dashboard/activity")
async def get_activity_data() -> dict[str, Any]:
    """Get activity heatmap data.

    Returns:
        dict[str, Any]: Activity data with daily statistics and metrics.

    Raises:
        HTTPException: If activity data retrieval fails.
    """
    try:
        # Try to get real git activity data

        activities: list[ActivityData]
        try:
            # Get git log for last 365 days
            cmd = [
                "git",
                "log",
                "--since=365 days ago",
                "--pretty=format:%ad",
                "--date=short",
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            # Count activities per day
            activity_counts: dict[str, int] = defaultdict(int)
            for date_str in result.stdout.strip().split("\n"):
                if date_str:
                    activity_counts[date_str] += 1

            # Generate complete date range
            end_date = datetime.now(UTC).date()
            start_date = end_date - timedelta(days=364)

            activities = []
            current_date = start_date
            while current_date <= end_date:
                date_str = current_date.isoformat()
                activities.append(
                    ActivityData(
                        date=date_str,
                        activity_count=activity_counts.get(date_str, 0),
                    )
                )
                current_date += timedelta(days=1)

            active_days = sum(1 for a in activities if a["activity_count"] > 0)

            return {
                "activities": activities,
                "total_days": len(activities),
                "active_days": active_days,
                "max_activity": max((a["activity_count"] for a in activities), default=0),
                "avg_activity": (sum(a["activity_count"] for a in activities) / len(activities) if activities else 0),
            }
        except (subprocess.CalledProcessError, ImportError, AttributeError):
            # Fallback with mock data for last 90 days

            end_date = datetime.now(UTC).date()
            start_date = end_date - timedelta(days=89)

            activities = []
            current_date = start_date
            while current_date <= end_date:
                # Generate mock activity data
                activity_count = secrets.randbelow(MAX_ACTIVITY_COUNT) if secrets.randbelow(RANDOM_BOUND) > ACTIVITY_THRESHOLD else 0
                activities.append(
                    ActivityData(
                        date=current_date.isoformat(),
                        activity_count=activity_count,
                    )
                )
                current_date += timedelta(days=1)

            active_days = sum(1 for a in activities if a["activity_count"] > 0)

            return {
                "activities": activities,
                "total_days": len(activities),
                "active_days": active_days,
                "max_activity": max((a["activity_count"] for a in activities), default=0),
                "avg_activity": (sum(a["activity_count"] for a in activities) / len(activities) if activities else 0),
            }
    except Exception as e:
        logger.exception("Failed to get activity data")
        raise HTTPException(status_code=500, detail=f"Failed to get activity data: {e!s}")


@router.get("/api/dashboard/heatmap/{session_name}")
async def get_session_heatmap(session_name: str, days: Annotated[int, Query(ge=1, le=30)] = 7) -> dict[str, Any]:
    """세션별 히트맵 데이터 반환.

    Args:
        session_name: Name of the session to get heatmap for.
        days: Number of days to include in heatmap (1-30).

    Returns:
        dict[str, Any]: Heatmap data for the specified session.

    Raises:
        HTTPException: If heatmap data retrieval fails.
    """
    try:
        return heatmap_generator.generate_heatmap_data([session_name], days=days)
    except Exception as e:
        logger.exception("Failed to get heatmap data for {session_name}")
        raise HTTPException(status_code=500, detail=f"Failed to get heatmap data: {e!s}")


@router.get("/api/dashboard/stats")
async def get_dashboard_stats() -> dict[str, Any]:
    """Get dashboard statistics summary.

    Returns:
        dict[str, Any]: Dashboard statistics including session counts and health metrics.

    Raises:
        HTTPException: If statistics retrieval fails.
    """
    try:
        # Get data from other endpoints
        sessions_data = await get_sessions()
        health_data = await get_project_health()
        activity_data = await get_activity_data()

        return {
            "active_sessions": len([s for s in sessions_data if s.get("status") == "active"]),
            "total_projects": 1,  # Current project count
            "health_score": health_data["overall_score"],
            "activity_streak": activity_data["active_days"],
            "last_update": datetime.now(UTC).isoformat(),
        }
    except Exception as e:
        logger.exception("Failed to get stats")
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {e!s}")
