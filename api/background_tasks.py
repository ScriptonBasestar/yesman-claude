# Copyright notice.

import asyncio
import hashlib
import json
import logging
import subprocess
import traceback
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, cast

from api.routers.websocket_router import manager
from libs.core.session_manager import SessionManager
from libs.dashboard.health_calculator import HealthCalculator
from libs.tmux_manager import TmuxManager
from libs.yesman_config import YesmanConfig

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Background task system for real-time updates."""


# Note: Removed typing.Any usage to fix ANN401 errors

logger = logging.getLogger(__name__)

# Constants for status scoring
SCORE_EXCELLENT_THRESHOLD = 90
SCORE_GOOD_THRESHOLD = 80
SCORE_WARNING_THRESHOLD = 60


@dataclass
class TaskState:
    """State tracking for background tasks."""

    name: str
    last_run: datetime | None = None
    last_data_hash: str | None = None
    error_count: int = 0
    is_running: bool = False


class BackgroundTaskRunner:
    """Manages background tasks for real-time monitoring."""

    def __init__(self) -> None:
        """Initialize the background task runner."""
        self.tasks: list[asyncio.Task] = []
        self.is_running = False
        self.task_states: dict[str, TaskState] = {}

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

    async def start(self) -> None:
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

        logger.info("Started %d background tasks", len(self.tasks))

    async def stop(self) -> None:
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

    @staticmethod
    def _calculate_data_hash(data: object) -> str:
        """Calculate hash of data for change detection.

        Returns:
        str: Description of return value.
        """
        json_str = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(json_str.encode()).hexdigest()

    async def _run_task_safely(
        self,
        task_name: str,
        task_func: Callable,
        interval: int,
    ) -> None:
        """Run a task with error handling and state tracking."""
        state = TaskState(name=task_name)
        self.task_states[task_name] = state

        while self.is_running:
            try:
                state.is_running = True
                await task_func()
                state.last_run = datetime.now(UTC)
                state.error_count = 0

            except asyncio.CancelledError:
                logger.info("Task %s cancelled", task_name)
                break

            except Exception:
                state.error_count += 1
                logger.exception("Error in task %s", task_name)
                logger.debug(traceback.format_exc())

                # Exponential backoff on errors
                error_delay = min(interval * (2**state.error_count), 300)
                await asyncio.sleep(error_delay)
                continue

            finally:
                state.is_running = False

            # Wait for next iteration
            await asyncio.sleep(interval)

    async def monitor_sessions(self) -> None:
        """Monitor session changes and broadcast updates."""

        async def check_sessions() -> None:
            try:
                # Get current session data
                sessions = self.session_manager.get_all_sessions()

                # Get project configuration
                config = YesmanConfig()
                # Load projects using tmux_manager

                tmux_manager = TmuxManager(config)
                project_sessions = cast("dict[str, Any]", tmux_manager.load_projects().get("sessions", {}))

                # Format session data
                formatted_sessions = []
                for project_name, project_config in project_sessions.items():
                    session_name = project_config.get("override", {}).get(
                        "session_name",
                        project_name,
                    )
                    session_exists = any(s.session_name == session_name for s in sessions)
                    session_detail = self.session_manager._get_session_info(project_name, project_config) if session_exists else None

                    formatted_sessions.append(
                        {
                            "session_name": session_name,
                            "project_name": project_name,
                            "template": project_config.get("template_name", "default"),
                            "status": "active" if session_exists else "stopped",
                            "exists": session_exists,
                            "windows": (len(session_detail.windows) if session_detail else 0),
                            "panes": (sum(len(w.panes) for w in session_detail.windows) if session_detail else 0),
                            "claude_active": (any(p.is_claude for w in session_detail.windows for p in w.panes) if session_detail else False),
                        },
                    )

                # Calculate data hash
                data_hash = self._calculate_data_hash(formatted_sessions)

                # Check if data has changed
                if self.last_data["sessions"] != data_hash:
                    self.last_data["sessions"] = data_hash  # type: ignore[assignment]

                    # Broadcast update via WebSocket
                    await manager.broadcast_session_update({"sessions": formatted_sessions})

                    logger.debug(
                        "Session data updated and broadcast (%d sessions)",
                        len(formatted_sessions),
                    )

            except Exception:
                logger.exception("Error monitoring sessions")
                raise

        await self._run_task_safely(
            "sessions",
            check_sessions,
            self.intervals["sessions"],
        )

    async def monitor_health(self) -> None:
        """Monitor project health and broadcast updates."""

        async def check_health() -> None:
            try:
                # Calculate health metrics
                health_data = await self.health_calculator.calculate_health()

                # Get category scores from health data
                category_scores = health_data.category_scores

                # Format health data
                formatted_health = {
                    "overall_score": health_data.overall_score,
                    "categories": {
                        "build": {
                            "score": category_scores.get("build", 0),
                            "status": self._get_status(
                                category_scores.get("build", 0),
                            ),
                        },
                        "tests": {
                            "score": category_scores.get("tests", 0),
                            "status": self._get_status(
                                category_scores.get("tests", 0),
                            ),
                        },
                        "dependencies": {
                            "score": category_scores.get("dependencies", 0),
                            "status": self._get_status(
                                category_scores.get("dependencies", 0),
                            ),
                        },
                        "security": {
                            "score": category_scores.get("security", 0),
                            "status": self._get_status(
                                category_scores.get("security", 0),
                            ),
                        },
                        "performance": {
                            "score": category_scores.get("performance", 0),
                            "status": self._get_status(
                                category_scores.get("performance", 0),
                            ),
                        },
                        "code_quality": {
                            "score": category_scores.get("code_quality", 0),
                            "status": self._get_status(
                                category_scores.get("code_quality", 0),
                            ),
                        },
                        "git": {
                            "score": category_scores.get("git", 0),
                            "status": self._get_status(category_scores.get("git", 0)),
                        },
                        "documentation": {
                            "score": category_scores.get("documentation", 0),
                            "status": self._get_status(
                                category_scores.get("documentation", 0),
                            ),
                        },
                    },
                    "suggestions": [metric.description for metric in health_data.metrics if metric.description],
                    "last_updated": datetime.now(UTC).isoformat(),
                }

                # Calculate data hash
                data_hash = self._calculate_data_hash(formatted_health)

                # Check if data has changed
                if self.last_data["health"] != data_hash:
                    self.last_data["health"] = data_hash  # type: ignore[assignment]

                    # Broadcast update via WebSocket
                    await manager.broadcast_health_update(formatted_health)

                    logger.debug(
                        "Health data updated and broadcast (score: %s)",
                        formatted_health["overall_score"],
                    )

            except Exception:
                logger.exception("Error monitoring health")
                raise

        await self._run_task_safely("health", check_health, self.intervals["health"])

    async def monitor_activity(self) -> None:
        """Monitor activity data and broadcast updates."""

        async def check_activity() -> None:
            try:
                # Get git activity data
                activity_counts: defaultdict[str, int] = defaultdict(int)

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
                        cmd,
                        capture_output=True,
                        text=True,
                        check=True,
                    )

                    for date_str in result.stdout.strip().split("\n"):
                        if date_str:
                            activity_counts[date_str] += 1

                except subprocess.CalledProcessError:
                    logger.warning("Could not get git activity data")

                # Generate complete date range
                end_date = datetime.now(UTC).date()
                start_date = end_date - timedelta(days=364)

                activities: list[dict[str, str | int]] = []
                current_date = start_date
                while current_date <= end_date:
                    date_str = current_date.isoformat()
                    activities.append(
                        {
                            "date": date_str,
                            "activity_count": activity_counts.get(date_str, 0),
                        },
                    )
                    current_date += timedelta(days=1)

                # Calculate statistics
                activity_counts_list = [int(a["activity_count"]) for a in activities]
                active_days = sum(1 for count in activity_counts_list if count > 0)
                max_activity = max(activity_counts_list, default=0)
                avg_activity = sum(activity_counts_list) / len(activity_counts_list) if activity_counts_list else 0

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
                    self.last_data["activity"] = data_hash  # type: ignore[assignment]

                    # Broadcast update via WebSocket
                    await manager.broadcast_activity_update(formatted_activity)

                    logger.debug(
                        "Activity data updated and broadcast (%d active days)",
                        active_days,
                    )

            except Exception:
                logger.exception("Error monitoring activity")
                raise

        await self._run_task_safely(
            "activity",
            check_activity,
            self.intervals["activity"],
        )

    async def cleanup_task(self) -> None:
        """Periodic cleanup of resources."""

        async def cleanup() -> None:  # noqa: RUF029
            try:
                # Clean up old connections

                # Get connection statistics
                stats = manager.get_connection_stats()
                logger.debug("Active connections: %d", stats["total_connections"])

                # Clean up stale session cache
                self.session_manager._cleanup_cache()

                # Log task states
                for name, state in self.task_states.items():
                    if state.last_run:
                        age = (datetime.now(UTC) - state.last_run).total_seconds()
                        logger.debug(
                            "Task %s: last run %.1fs ago, errors: %d",
                            name,
                            age,
                            state.error_count,
                        )

            except Exception:
                logger.exception("Error in cleanup task")
                raise

        await self._run_task_safely("cleanup", cleanup, self.intervals["cleanup"])

    @staticmethod
    def _get_status(score: float) -> str:
        """Get status string based on score.

        Returns:
        str: Description of return value.
        """
        if score >= SCORE_EXCELLENT_THRESHOLD:
            return "excellent"
        if score >= SCORE_GOOD_THRESHOLD:
            return "good"
        if score >= SCORE_WARNING_THRESHOLD:
            return "warning"
        return "poor"

    def get_task_states(self) -> dict[str, dict]:
        """Get current state of all tasks.

        Returns:
        object: Description of return value.
        """
        states = {}
        for name, state in self.task_states.items():
            states[name] = {
                "is_running": state.is_running,
                "last_run": state.last_run.isoformat() if state.last_run else None,
                "error_count": state.error_count,
                "interval": self.intervals.get(
                    name.replace("monitor_", "").replace("_task", ""),
                ),
            }
        return states


# Global task runner instance
task_runner = BackgroundTaskRunner()

__all__ = ["BackgroundTaskRunner", "task_runner"]