# Copyright notice.

import re
from .models import SessionProgress, TaskPhase, TaskProgress

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Progress tracking for Claude sessions."""


class ProgressAnalyzer:
    """Analyzes pane output to determine task progress."""

    # Phase detection patterns
    PHASE_PATTERNS = {
        TaskPhase.STARTING: [
            r"starting|initializing|beginning",
            r"let me|i'll|i will",
            r"first|to begin",
        ],
        TaskPhase.ANALYZING: [
            r"analyzing|examining|looking at|checking",
            r"understanding|reviewing|investigating",
            r"let me (?:look|check|see|examine)",
        ],
        TaskPhase.IMPLEMENTING: [
            r"implementing|coding|writing|creating",
            r"adding|modifying|updating|editing",
            r"let me (?:implement|create|add|modify)",
        ],
        TaskPhase.TESTING: [
            r"testing|running tests|executing tests",
            r"verifying|validating|checking",
            r"pytest|npm test|cargo test",
        ],
        TaskPhase.COMPLETING: [
            r"completing|finishing|done|completed",
            r"successfully|finished|all tests pass",
            r"task completed|implementation complete",
        ],
    }

    # Activity detection patterns
    FILE_ACTIVITY_PATTERNS = {
        "created": r"(?:created?|wrote|new file|added file).*?([/\w\-\.]+\.\w+)",
        "modified": r"(?:modified?|updated?|edited?|changed?).*?([/\w\-\.]+\.\w+)",
        "reading": r"(?:reading|examining|looking at).*?([/\w\-\.]+\.\w+)",
    }

    COMMAND_PATTERNS = {
        "executing": r"(?:running|executing|►|\$)\s+(.+)",
        "success": r"(?:success|✓|passed|completed successfully)",
        "failure": r"(?:failed|error|✗|exception|traceback)",
    }

    TODO_PATTERNS = {
        "identified": r"(?:todo|TODO|task):\s*(.+)",
        "completed": r"(?:✓|done|completed|finished).*?(?:todo|task)",
    }

    def __init__(self) -> None:
        self.session_progress: dict[str, SessionProgress] = {}

    def analyze_pane_output(self, session_name: str, pane_output: list[str]) -> SessionProgress | None:
        """Analyze pane output to determine progress.

            Returns:
                Sessionprogress | None object.


        """
        if not pane_output:
            return None

        # Get or create session progress
        if session_name not in self.session_progress:
            self.session_progress[session_name] = SessionProgress(session_name=session_name)

        progress = self.session_progress[session_name]

        # Get or create current task
        task = progress.get_current_task()
        if not task or task.phase == TaskPhase.COMPLETED:
            task = progress.add_task()

        # Analyze recent output (last 20 lines)
        recent_output = pane_output[-20:] if len(pane_output) > 20 else pane_output
        output_text = "\n".join(recent_output).lower()

        # Detect phase
        new_phase = self._detect_phase(output_text, task.phase)
        if new_phase != task.phase:
            task.update_phase(new_phase)

        # Analyze activity
        self._analyze_file_activity(recent_output, task)
        self._analyze_command_activity(recent_output, task)
        self._analyze_todo_activity(recent_output, task)

        # Update phase progress based on activity
        self._update_phase_progress(task)

        # Update aggregates
        progress.update_aggregates()

        return progress

    def _detect_phase(self, output_text: str, current_phase: TaskPhase) -> TaskPhase:
        """Detect the current phase from output.

        Returns:
        TaskPhase: Description of return value.
        """
        # Check for phase transitions
        for phase, patterns in self.PHASE_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, output_text, re.IGNORECASE):
                    # Only transition to a later phase (except IDLE)
                    if phase == TaskPhase.IDLE:
                        continue
                    phase_order = list(TaskPhase)
                    if phase_order.index(phase) >= phase_order.index(current_phase):
                        return phase

        return current_phase

    def _analyze_file_activity(self, output_lines: list[str], task: TaskProgress) -> None:
        """Analyze file-related activity."""
        for line in output_lines:
            # Check for file creation
            match = re.search(self.FILE_ACTIVITY_PATTERNS["created"], line, re.IGNORECASE)
            if match:
                task.files_created += 1
                continue

            # Check for file modification
            match = re.search(self.FILE_ACTIVITY_PATTERNS["modified"], line, re.IGNORECASE)
            if match:
                task.files_modified += 1

    def _analyze_command_activity(self, output_lines: list[str], task: TaskProgress) -> None:
        """Analyze command execution activity."""
        for i, line in enumerate(output_lines):
            # Check for command execution
            if re.search(self.COMMAND_PATTERNS["executing"], line):
                task.commands_executed += 1

                # Look ahead for success/failure
                for j in range(i + 1, min(i + 10, len(output_lines))):
                    if re.search(self.COMMAND_PATTERNS["success"], output_lines[j]):
                        task.commands_succeeded += 1
                        break
                    if re.search(self.COMMAND_PATTERNS["failure"], output_lines[j]):
                        task.commands_failed += 1
                        break

    def _analyze_todo_activity(self, output_lines: list[str], task: TaskProgress) -> None:
        """Analyze TODO-related activity."""
        for line in output_lines:
            # Check for TODO identification
            if re.search(self.TODO_PATTERNS["identified"], line, re.IGNORECASE):
                task.todos_identified += 1

            # Check for TODO completion
            if re.search(self.TODO_PATTERNS["completed"], line, re.IGNORECASE):
                task.todos_completed += 1

    @staticmethod
    def _update_phase_progress(task: TaskProgress) -> None:
        """Update phase progress based on activity indicators."""
        if task.phase == TaskPhase.STARTING:
            # Starting phase is quick
            task.phase_progress = min(100.0, task.phase_progress + 50.0)

        elif task.phase == TaskPhase.ANALYZING:
            # Progress based on files read
            files_analyzed = task.files_created + task.files_modified
            task.phase_progress = min(100.0, files_analyzed * 20.0)

        elif task.phase == TaskPhase.IMPLEMENTING:
            # Progress based on file changes and commands
            activity_score = (task.files_created + task.files_modified) * 10 + task.commands_executed * 5
            task.phase_progress = min(100.0, activity_score)

        elif task.phase == TaskPhase.TESTING:
            # Progress based on test commands
            if task.commands_succeeded > 0:
                success_rate = task.commands_succeeded / max(1, task.commands_executed)
                task.phase_progress = min(100.0, success_rate * 100)
            else:
                task.phase_progress = min(100.0, task.commands_executed * 25.0)

        elif task.phase == TaskPhase.COMPLETING:
            # Completing phase is quick
            task.phase_progress = 100.0

        # Recalculate overall progress
        task._recalculate_overall_progress()

    def get_session_progress(self, session_name: str) -> SessionProgress | None:
        """Get progress for a specific session.

        Returns:
        object: Description of return value.
        """
        return self.session_progress.get(session_name)

    def get_all_progress(self) -> dict[str, SessionProgress]:
        """Get progress for all sessions.

        Returns:
        object: Description of return value.
        """
        return self.session_progress.copy()

    def reset_session_progress(self, session_name: str) -> None:
        """Reset progress for a specific session."""
        if session_name in self.session_progress:
            del self.session_progress[session_name]
