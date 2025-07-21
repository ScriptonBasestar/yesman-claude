# Copyright notice.

import logging
import os
import tempfile
from datetime import UTC, datetime
from pathlib import Path
import libtmux
# Try to import psutil, fall back to basic functionality if not available
import psutil
from libs.utils import ensure_log_directory
from .models import PaneInfo, SessionInfo, TaskPhase, WindowInfo
from .progress_tracker import ProgressAnalyzer
        # Import here to avoid circular import
from libs.yesman_config import YesmanConfig
        # Lazy import to avoid circular dependency
from libs.tmux_manager import TmuxManager

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Session management for dashboard."""



try:

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    psutil = None




class SessionManager:
    """Manages tmux session information for dashboard."""

    def __init__(self) -> None:

        self.config = YesmanConfig()

        self.tmux_manager = TmuxManager(self.config)
        self.server = libtmux.Server()
        self.logger = self._setup_logger()

        # Initialize progress analyzer
        self.progress_analyzer = ProgressAnalyzer()

        self.logger.info("SessionManager initialized")

    def _setup_logger(self) -> logging.Logger:
        """Setup logger with file-only output.

    Returns:
        Logging.Logger object."""
        logger = logging.getLogger("yesman.dashboard.session_manager")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        log_path_str = self.config.get("log_path", "~/.scripton/yesman/logs/")
        log_path = ensure_log_directory(Path(log_path_str))

        log_file = log_path / "session_manager.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        return logger

    def get_all_sessions(self) -> list[SessionInfo]:
        """Get information about all yesman sessions.

    Returns:
        List of the requested data."""
        sessions_info = []

        try:
            # Load project configurations
            projects = self.tmux_manager.load_projects().get("sessions", {})
            self.logger.info("Loaded %d projects", len(projects))

            for project_name, project_conf in projects.items():
                session_info = self._get_session_info(project_name, project_conf)
                sessions_info.append(session_info)

            return sessions_info

        except Exception:
            self.logger.error("Error getting sessions", exc_info=True)
            return []

    def _get_session_info(self, project_name: str, project_conf: dict[str]) -> SessionInfo:
        """Get information for a single session with mode-aware caching.

    Returns:
        Dict containing service information."""

        def compute_session_info() -> SessionInfo:
            override = project_conf.get("override", {})
            session_name = override.get("session_name", project_name)

            # Check if session exists
            session = self.server.find_where({"session_name": session_name})

            windows: list[WindowInfo] = []
            controller_status = "unknown"

            if session:
                # Get window information
                for window in session.list_windows():
                    window_info = self._get_window_info(window)
                    windows.append(window_info)

                    # Update controller status based on panes
                    for pane in window_info.panes:
                        if pane.is_controller:
                            controller_status = "running"

                # If no controller found, mark as not running
                if controller_status == "unknown":
                    controller_status = "not running"

            # Get template name with proper fallback
            template_name = project_conf.get("template_name")
            if template_name is None:
                template_display = "none"
            else:
                # Check if template file actually exists
                template_path = self.config.get_templates_dir() / f"{template_name}.yaml"
                if template_path.exists():
                    template_display = template_name
                else:
                    template_display = "N/A"  # Template defined but file missing

            # Analyze progress if session is running
            progress = None
            if session:
                # Collect output from all Claude panes
                claude_output = []
                for window_info in windows:
                    for pane_info in window_info.panes:
                        if pane_info.is_claude and pane_info.last_output:
                            # Get full pane content for better analysis
                            try:
                                tmux_pane = session.find_where({"pane_id": pane_info.id})
                                if tmux_pane:
                                    pane_content = tmux_pane.cmd("capture-pane", "-p").stdout
                                    claude_output.extend(pane_content)
                            except Exception as e:
                                self.logger.warning("Could not get pane content for %s: %s", pane_info.id, e)

                # Analyze progress
                if claude_output:
                    progress = self.progress_analyzer.analyze_pane_output(session_name, claude_output)

            return SessionInfo(
                project_name=project_name,
                session_name=session_name,
                template=template_display,
                exists=session is not None,
                status="running" if session else "stopped",
                windows=windows,
                controller_status=controller_status,
                progress=progress,
            )

        return compute_session_info()

    def _get_window_info(self, window: object) -> WindowInfo:
        """Get information for a single window with detailed pane metrics.

    Returns:
        Dict containing service information."""
        panes: list[PaneInfo] = []

        for pane in window.list_panes():
            try:
                pane_info = self._get_detailed_pane_info(pane)
                panes.append(pane_info)
            except Exception:
                self.logger.exception("Error getting pane info")
                # Fallback to basic pane info
                try:
                    cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
                    basic_pane = PaneInfo(
                        id=pane.get("pane_id"),
                        command=cmd,
                        is_claude="claude" in cmd.lower(),
                        is_controller="controller" in cmd.lower() or "yesman" in cmd.lower(),
                    )
                    panes.append(basic_pane)
                except Exception as e:
                    self.logger.debug("Could not get basic pane info: %s", e)

        return WindowInfo(
            name=window.get("window_name"),
            index=window.get("window_index"),
            panes=panes,
        )

    def _get_detailed_pane_info(self, pane: object) -> PaneInfo:
        """Get detailed information for a single pane including metrics.

    Returns:
        Dict containing service information."""
        try:
            # Get basic pane information
            cmd = pane.cmd("display-message", "-p", "#{pane_current_command}").stdout[0]
            pane_id = pane.get("pane_id")

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
                    running_time = datetime.now(UTC).timestamp() - create_time

                    # Determine process status
                    status = process.status()

                    # Try to determine current task from command line
                    try:
                        cmdline = process.cmdline()
                        current_task = self._analyze_current_task(cmdline, cmd)
                    except Exception:
                        current_task = cmd

                except (
                    psutil.NoSuchProcess,
                    psutil.AccessDenied,
                    psutil.ZombieProcess,
                ):
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
                current_time = datetime.now(UTC).timestamp()
                idle_time = current_time - activity_timestamp if activity_timestamp > 0 else 0

                # Activity score: higher for recent activity, lower for idle panes
                activity_score = max(0, 100 - (idle_time / 60))  # Decreases over minutes

            except Exception:
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
            except Exception as e:
                self.logger.debug("Could not capture pane output: %s", e)

            # Create enhanced PaneInfo
            return PaneInfo(
                id=pane_id,
                command=cmd,
                is_claude="claude" in cmd.lower(),
                is_controller="controller" in cmd.lower() or "yesman" in cmd.lower(),
                current_task=current_task,
                idle_time=idle_time,
                last_activity=(datetime.fromtimestamp(activity_timestamp, UTC) if activity_timestamp > 0 else datetime.now(UTC)),
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                pid=pid,
                running_time=running_time,
                status=status,
                activity_score=activity_score,
                last_output=last_output,
                output_lines=output_lines,
            )

        except Exception:
            self.logger.exception("Error getting detailed pane info")
            # Return basic pane info as fallback
            return PaneInfo(
                id=pane.get("pane_id", "unknown"),
                command=cmd if "cmd" in locals() else "unknown",
                is_claude=False,
                is_controller=False,
            )

    @staticmethod
    def _analyze_current_task(cmdline: list[str], command: str) -> str:
        """Analyze command line to determine current task.

    Returns:
        String containing."""
        if not cmdline:
            return command

        # Join command line for analysis
        full_cmd = " ".join(cmdline)

        # Claude-specific task detection
        if "claude" in full_cmd.lower():
            if "--read" in full_cmd:
                return "Reading files"
            if "--edit" in full_cmd or "--write" in full_cmd:
                return "Editing code"
            if "dashboard" in full_cmd:
                return "Running dashboard"
            return "Claude interactive"

        # Controller-specific task detection
        if "yesman" in full_cmd.lower() or "controller" in full_cmd.lower():
            if "dashboard" in full_cmd:
                return "Dashboard controller"
            if "setup" in full_cmd:
                return "Setting up sessions"
            if "teardown" in full_cmd:
                return "Tearing down sessions"
            return "Yesman controller"

        # Common development tasks
        if any(term in full_cmd.lower() for term in ["vim", "nano", "code", "nvim"]):
            return "Editing files"
        if any(term in full_cmd.lower() for term in ["python", "node", "npm", "pip"]):
            return "Running application"
        if any(term in full_cmd.lower() for term in ["git", "commit", "push", "pull"]):
            return "Git operations"
        if any(term in full_cmd.lower() for term in ["test", "pytest", "jest"]):
            return "Running tests"
        if any(term in full_cmd.lower() for term in ["build", "compile", "make"]):
            return "Building project"
        if "bash" in full_cmd.lower() or "zsh" in full_cmd.lower():
            return "Terminal session"
        # Extract the main command (first meaningful part)
        main_cmd = cmdline[0].split("/")[-1] if cmdline else command
        return f"Running {main_cmd}"

    def attach_to_pane(self, session_name: str, window_index: str, pane_id: str) -> dict[str]:
        """Attach to a specific tmux pane.

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
                    "action": "none",
                }

            # Find the window
            window = session.find_where({"window_index": window_index})
            if not window:
                return {
                    "success": False,
                    "error": f"Window {window_index} not found in session '{session_name}'",
                    "action": "none",
                }

            # Find the pane
            pane = window.find_where({"pane_id": pane_id})
            if not pane:
                return {
                    "success": False,
                    "error": f"Pane {pane_id} not found in window {window_index}",
                    "action": "none",
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
                "message": f"Ready to attach to pane {pane_id} in {session_name}:{window_index}",
            }

        except Exception as e:
            self.logger.exception("Error attaching to pane")
            return {
                "success": False,
                "error": f"Attachment failed: {e!s}",
                "action": "error",
            }

    def get_progress_overview(self) -> dict[str]:
        """Get progress overview for all sessions.

    Returns:
        Dict containing the requested data."""
        sessions = self.get_all_sessions()

        # Collect progress data
        total_sessions = len(sessions)
        sessions_with_progress = 0
        overall_progress = 0.0
        active_tasks = 0
        completed_tasks = 0
        total_files_changed = 0
        total_commands = 0

        session_progress_list = []

        for session in sessions:
            if session.progress:
                sessions_with_progress += 1
                progress = session.progress

                # Count tasks
                for task in progress.tasks:
                    if task.phase == TaskPhase.COMPLETED:
                        completed_tasks += 1
                    elif task.phase != TaskPhase.IDLE:
                        active_tasks += 1

                # Aggregate metrics
                overall_progress += progress.calculate_overall_progress()
                total_files_changed += progress.total_files_changed
                total_commands += progress.total_commands

                # Add to session list
                session_progress_list.append(
                    {
                        "session_name": session.session_name,
                        "project_name": session.project_name,
                        "overall_progress": progress.calculate_overall_progress(),
                        "current_phase": (progress.get_current_task().phase.value if progress.get_current_task() else "idle"),
                        "tasks_count": len(progress.tasks),
                        "files_changed": progress.total_files_changed,
                        "commands_executed": progress.total_commands,
                    }
                )

        # Calculate averages
        avg_progress = overall_progress / sessions_with_progress if sessions_with_progress > 0 else 0.0

        return {
            "total_sessions": total_sessions,
            "sessions_with_progress": sessions_with_progress,
            "average_progress": avg_progress,
            "active_tasks": active_tasks,
            "completed_tasks": completed_tasks,
            "total_files_changed": total_files_changed,
            "total_commands_executed": total_commands,
            "sessions": session_progress_list,
        }

    def create_terminal_script(self, attach_command: str, script_path: str | None = None) -> str:
        """Create a terminal script for pane attachment.

        Args:
            attach_command: The tmux attach command
            script_path: Optional path for the script file

        Returns:
            Path to the created script file
        """
        if script_path is None:
            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".sh", prefix="yesman_attach_", encoding="utf-8") as f:
                script_path = f.name

        script_content = f"""#!/bin/bash
# Auto-generated tmux attachment script
# Generated at: {datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")}

echo "Attaching to tmux pane..."
{attach_command}
"""

        try:
            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Make script executable
            os.chmod(script_path, 0o700)

            self.logger.info("Created attachment script: %s", script_path)
            return script_path

        except Exception:
            self.logger.exception("Error creating attachment script")
            raise

    def execute_pane_attachment(self, session_name: str, window_index: str, pane_id: str) -> dict[str]:
        """Execute pane attachment with error handling.

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
                "message": f"Attachment script created: {script_path}",
            }

        except Exception as e:
            self.logger.exception("Error executing pane attachment")
            return {
                "success": False,
                "error": f"Execution failed: {e!s}",
                "action": "error",
            }

    @staticmethod
    def _cleanup_cache() -> None:
        """Clean up stale cached session data."""
        # This is a placeholder method to satisfy the API contract
        # The actual SessionManager doesn't use caching currently
