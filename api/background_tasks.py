"""Background task system for real-time updates."""

import asyncio
import hashlib
import json
import logging
import traceback
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional

from libs.core.session_manager import SessionManager
from libs.dashboard.health_calculator import HealthCalculator

logger = logging.getLogger(__name__)


@dataclass
class TaskState:
    """State tracking for background tasks."""

    name: str
    last_run: Optional[datetime] = None
    last_data_hash: Optional[str] = None
    error_count: int = 0
    is_running: bool = False


class BackgroundTaskRunner:
    """Manages background tasks for real-time monitoring."""

    def __init__(self):
        """Initialize the background task runner."""
        self.tasks: List[asyncio.Task] = []
        self.is_running = False
        self.task_states: Dict[str, TaskState] = {}

        # Initialize managers
        self.session_manager = SessionManager()
        self.health_calculator = HealthCalculator()

        # Task intervals (in seconds)
        self.intervals = {
            "sessions": 1,  # Check sessions every 1 second
            "health": 30,  # Check health every 30 seconds
            "activity": 60,  # Check activity every 60 seconds
            "cleanup": 300,  # Clean up every 5 minutes
        }

        # Data caches for change detection
        self.last_data = {"sessions": None, "health": None, "activity": None}

    async def start(self):
        """Start all background tasks."""
        if self.is_running:
            logger.warning("Background tasks are already running")
            return

        logger.info("Starting background tasks...")
        self.is_running = True

        # Create tasks
        self.tasks = [
            asyncio.create_task(self.monitor_sessions()),
            asyncio.create_task(self.monitor_health()),
            asyncio.create_task(self.monitor_activity()),
            asyncio.create_task(self.cleanup_task()),
        ]

        logger.info(f"Started {len(self.tasks)} background tasks")

    async def stop(self):
        """Stop all background tasks gracefully."""
        logger.info("Stopping background tasks...")
        self.is_running = False

        # Cancel all tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Wait for tasks to complete
        await asyncio.gather(*self.tasks, return_exceptions=True)

        self.tasks = []
        logger.info("Background tasks stopped")

    def _calculate_data_hash(self, data: Any) -> str:
        """Calculate hash of data for change detection."""
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.md5(json_str.encode(), usedforsecurity=False).hexdigest()

    async def _run_task_safely(
        self, task_name: str, task_func: Callable, interval: int
    ):
        """Run a task with error handling and state tracking."""
        state = TaskState(name=task_name)
        self.task_states[task_name] = state

        while self.is_running:
            try:
                state.is_running = True
                await task_func()
                state.last_run = datetime.now()
                state.error_count = 0

            except asyncio.CancelledError:
                logger.info(f"Task {task_name} cancelled")
                break

            except Exception as e:
                state.error_count += 1
                logger.error(f"Error in task {task_name}: {str(e)}")
                logger.debug(traceback.format_exc())

                # Exponential backoff on errors
                error_delay = min(interval * (2**state.error_count), 300)
                await asyncio.sleep(error_delay)
                continue

            finally:
                state.is_running = False

            # Wait for next iteration
            await asyncio.sleep(interval)

    async def monitor_sessions(self):
        """Monitor session changes and broadcast updates."""

        async def check_sessions():
            try:
                # Get current session data
                sessions = self.session_manager.get_cached_sessions_list()

                # Get project configuration
                from libs.yesman_config import YesmanConfig

                config = YesmanConfig()
                project_sessions = config.get_projects()

                # Format session data
                formatted_sessions = []
                for project_name, project_config in project_sessions.items():
                    session_name = project_config.get("override", {}).get(
                        "session_name", project_name
                    )
                    session_exists = any(
                        s["session_name"] == session_name for s in sessions
                    )
                    session_detail = (
                        self.session_manager.get_session_info(session_name)
                        if session_exists
                        else None
                    )

                    formatted_sessions.append(
                        {
                            "session_name": session_name,
                            "project_name": project_name,
                            "template": project_config.get("template_name", "default"),
                            "status": "active" if session_exists else "stopped",
                            "exists": session_exists,
                            "windows": (
                                session_detail.get("windows", [])
                                if session_detail
                                else []
                            ),
                            "panes": (
                                sum(
                                    len(w.get("panes", []))
                                    for w in session_detail.get("windows", [])
                                )
                                if session_detail
                                else 0
                            ),
                            "claude_active": (
                                any(
                                    p.get("has_claude", False)
                                    for w in session_detail.get("windows", [])
                                    for p in w.get("panes", [])
                                )
                                if session_detail
                                else False
                            ),
                        }
                    )

                # Calculate data hash
                data_hash = self._calculate_data_hash(formatted_sessions)

                # Check if data has changed
                if self.last_data["sessions"] != data_hash:
                    self.last_data["sessions"] = data_hash

                    # Broadcast update via WebSocket
                    from api.routers.websocket import manager

                    await manager.broadcast_session_update(formatted_sessions)

                    logger.debug(
                        "Session data updated and broadcast "
                        f"({len(formatted_sessions)} sessions)"
                    )

            except Exception as e:
                logger.error(f"Error monitoring sessions: {str(e)}")
                raise

        await self._run_task_safely(
            "sessions", check_sessions, self.intervals["sessions"]
        )

    async def monitor_health(self):
        """Monitor project health and broadcast updates."""

        async def check_health():
            try:
                # Calculate health metrics
                health_data = await self.health_calculator.calculate_health()

                # Format health data
                formatted_health = {
                    "overall_score": health_data.get("overall_score", 0),
                    "categories": {
                        "build": {
                            "score": health_data.get("build_score", 0),
                            "status": self._get_status(
                                health_data.get("build_score", 0)
                            ),
                        },
                        "tests": {
                            "score": health_data.get("test_score", 0),
                            "status": self._get_status(
                                health_data.get("test_score", 0)
                            ),
                        },
                        "dependencies": {
                            "score": health_data.get("deps_score", 0),
                            "status": self._get_status(
                                health_data.get("deps_score", 0)
                            ),
                        },
                        "security": {
                            "score": health_data.get("security_score", 0),
                            "status": self._get_status(
                                health_data.get("security_score", 0)
                            ),
                        },
                        "performance": {
                            "score": health_data.get("perf_score", 0),
                            "status": self._get_status(
                                health_data.get("perf_score", 0)
                            ),
                        },
                        "code_quality": {
                            "score": health_data.get("quality_score", 0),
                            "status": self._get_status(
                                health_data.get("quality_score", 0)
                            ),
                        },
                        "git": {
                            "score": health_data.get("git_score", 0),
                            "status": self._get_status(health_data.get("git_score", 0)),
                        },
                        "documentation": {
                            "score": health_data.get("docs_score", 0),
                            "status": self._get_status(
                                health_data.get("docs_score", 0)
                            ),
                        },
                    },
                    "suggestions": health_data.get("suggestions", []),
                    "last_updated": datetime.now().isoformat(),
                }

                # Calculate data hash
                data_hash = self._calculate_data_hash(formatted_health)

                # Check if data has changed
                if self.last_data["health"] != data_hash:
                    self.last_data["health"] = data_hash

                    # Broadcast update via WebSocket
                    from api.routers.websocket import manager

                    await manager.broadcast_health_update(formatted_health)

                    logger.debug(
                        "Health data updated and broadcast "
                        f"(score: {formatted_health['overall_score']})"
                    )

            except Exception as e:
                logger.error(f"Error monitoring health: {str(e)}")
                raise

        await self._run_task_safely("health", check_health, self.intervals["health"])

    async def monitor_activity(self):
        """Monitor activity data and broadcast updates."""

        async def check_activity():
            try:
                import subprocess  # nosec
                from collections import defaultdict

                # Get git activity data
                activity_counts = defaultdict(int)

                try:
                    # Get git log for last 365 days
                    cmd = [
                        "git",
                        "log",
                        "--since=365 days ago",
                        "--pretty=format:%ad",
                        "--date=short",
                    ]
                    result = subprocess.run(  # nosec
                        cmd, capture_output=True, text=True, check=True
                    )

                    for date_str in result.stdout.strip().split("\n"):
                        if date_str:
                            activity_counts[date_str] += 1

                except subprocess.CalledProcessError:
                    logger.warning("Could not get git activity data")

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

                # Calculate statistics
                active_days = sum(1 for a in activities if a["activity_count"] > 0)
                max_activity = max((a["activity_count"] for a in activities), default=0)
                avg_activity = (
                    sum(a["activity_count"] for a in activities) / len(activities)
                    if activities
                    else 0
                )

                formatted_activity = {
                    "activities": activities,
                    "total_days": len(activities),
                    "active_days": active_days,
                    "max_activity": max_activity,
                    "avg_activity": avg_activity,
                }

                # Calculate data hash
                data_hash = self._calculate_data_hash(formatted_activity)

                # Check if data has changed
                if self.last_data["activity"] != data_hash:
                    self.last_data["activity"] = data_hash

                    # Broadcast update via WebSocket
                    from api.routers.websocket import manager

                    await manager.broadcast_activity_update(formatted_activity)

                    logger.debug(
                        "Activity data updated and broadcast "
                        f"({active_days} active days)"
                    )

            except Exception as e:
                logger.error(f"Error monitoring activity: {str(e)}")
                raise

        await self._run_task_safely(
            "activity", check_activity, self.intervals["activity"]
        )

    async def cleanup_task(self):
        """Periodic cleanup of resources."""

        async def cleanup():
            try:
                # Clean up old connections
                from api.routers.websocket import manager

                # Get connection statistics
                stats = manager.get_connection_stats()
                logger.debug(f"Active connections: {stats['total_connections']}")

                # Clean up stale session cache
                self.session_manager._cleanup_cache()

                # Log task states
                for name, state in self.task_states.items():
                    if state.last_run:
                        age = (datetime.now() - state.last_run).total_seconds()
                        logger.debug(
                            f"Task {name}: last run {age:.1f}s ago, "
                            f"errors: {state.error_count}"
                        )

            except Exception as e:
                logger.error(f"Error in cleanup task: {str(e)}")
                raise

        await self._run_task_safely("cleanup", cleanup, self.intervals["cleanup"])

    def _get_status(self, score: float) -> str:
        """Get status string based on score."""
        if score >= 90:
            return "excellent"
        elif score >= 80:
            return "good"
        elif score >= 60:
            return "warning"
        else:
            return "poor"

    def get_task_states(self) -> Dict[str, Dict]:
        """Get current state of all tasks."""
        states = {}
        for name, state in self.task_states.items():
            states[name] = {
                "is_running": state.is_running,
                "last_run": state.last_run.isoformat() if state.last_run else None,
                "error_count": state.error_count,
                "interval": self.intervals.get(
                    name.replace("monitor_", "").replace("_task", "")
                ),
            }
        return states


# Global task runner instance
task_runner = BackgroundTaskRunner()

__all__ = ["BackgroundTaskRunner", "task_runner"]
