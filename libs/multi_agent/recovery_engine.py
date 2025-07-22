# Copyright notice.

import asyncio
import contextlib
import json
import logging
import re
import shutil
import subprocess
import time
import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path

from .branch_manager import BranchInfo
from .types import Agent, AgentState, Task, TaskStatus

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Rollback mechanism and error recovery system for multi-agent operations."""


logger = logging.getLogger(__name__)


class RecoveryAction(Enum):
    """Types of recovery actions."""

    RETRY = "retry"
    ROLLBACK = "rollback"
    SKIP = "skip"
    ESCALATE = "escalate"
    RESET_AGENT = "reset_agent"
    RESTORE_STATE = "restore_state"


class OperationType(Enum):
    """Types of operations that can be rolled back."""

    TASK_EXECUTION = "task_execution"
    BRANCH_OPERATION = "branch_operation"
    AGENT_ASSIGNMENT = "agent_assignment"
    FILE_MODIFICATION = "file_modification"
    SYSTEM_CONFIG = "system_config"
    TEST_EXECUTION = "test_execution"


@dataclass
class OperationSnapshot:
    """Snapshot of system state before an operation."""

    snapshot_id: str
    operation_type: OperationType
    timestamp: datetime
    description: str

    # System state snapshots
    agent_states: dict[str, dict[str, str | int | bool | list[str]]] = field(default_factory=dict)
    task_states: dict[str, dict[str, str | int | bool | float | list[str]]] = field(default_factory=dict)
    file_states: dict[str, str] = field(default_factory=dict)  # file_path -> backup_path
    branch_state: dict[str, str | dict[str, str | int | bool | list[str]]] | None = None

    # Operation context
    operation_context: dict[str, str | int | bool | float | list[str]] = field(default_factory=dict)
    rollback_instructions: list[dict[str, str | int | bool | list[str]]] = field(default_factory=list)

    def to_dict(self) -> dict[str, str | int | bool | float | list[str] | dict[str, str | int | bool | float | list[str]] | dict[str, str | int | bool | list[str]]]:
        """Convert to dictionary for serialization."""
        return {
            "snapshot_id": self.snapshot_id,
            "operation_type": self.operation_type.value,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "agent_states": self.agent_states,
            "task_states": self.task_states,
            "file_states": self.file_states,
            "branch_state": self.branch_state,
            "operation_context": self.operation_context,
            "rollback_instructions": self.rollback_instructions,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str | int | bool | float | list[str] | dict[str, str | int | bool | float | list[str]]]) -> "OperationSnapshot":
        """Create from dictionary."""
        data["operation_type"] = OperationType(data["operation_type"])
        data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        return cls(**data)


@dataclass
class RecoveryStrategy:
    """Strategy for recovering from specific types of errors."""

    error_pattern: str  # Regex pattern to match error messages
    max_retries: int = 3
    retry_delay: float = 1.0  # Seconds
    recovery_actions: list[RecoveryAction] = field(default_factory=list)
    escalation_threshold: int = 5  # Number of failures before escalation
    custom_handler: Callable[[Exception, dict[str, str | int | bool | float | list[str]]], Awaitable[bool]] | None = None


class RecoveryEngine:
    """Comprehensive rollback and error recovery system."""

    def __init__(
        self,
        work_dir: str = ".scripton/yesman",
        max_snapshots: int = 50,
        auto_cleanup_hours: int = 24,
    ) -> None:
        """Initialize recovery engine.

        Args:
            work_dir: Directory for storing snapshots and recovery data
            max_snapshots: Maximum number of snapshots to keep
            auto_cleanup_hours: Hours after which old snapshots are cleaned up
        """
        self.work_dir = Path(work_dir) / "recovery"
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.snapshots_dir = self.work_dir / "snapshots"
        self.snapshots_dir.mkdir(exist_ok=True)

        self.backups_dir = self.work_dir / "backups"
        self.backups_dir.mkdir(exist_ok=True)

        # Configuration
        self.max_snapshots = max_snapshots
        self.auto_cleanup_hours = auto_cleanup_hours

        # State management
        self.snapshots: dict[str, OperationSnapshot] = {}
        self.recovery_strategies: dict[str, RecoveryStrategy] = {}
        self.operation_history: list[dict[str, str | bool | dict[str, str | int | bool | float | list[str]]]] = []
        self.failure_counts: dict[str, int] = {}

        # Monitoring
        self.active_operations: dict[str, str] = {}  # operation_id -> snapshot_id
        self.recovery_metrics = {
            "total_operations": 0,
            "failed_operations": 0,
            "successful_recoveries": 0,
            "failed_recoveries": 0,
            "rollbacks_performed": 0,
        }

        # Load existing state
        self._load_state()
        self._setup_default_strategies()

    def _get_state_file(self) -> Path:
        """Get path to recovery state file."""
        return self.work_dir / "recovery_state.json"

    def _load_state(self) -> None:
        """Load recovery engine state."""
        state_file = self._get_state_file()

        if state_file.exists():
            try:
                with state_file.open() as f:
                    data = json.load(f)

                # Load snapshots
                for snapshot_data in data.get("snapshots", []):
                    snapshot = OperationSnapshot.from_dict(snapshot_data)
                    self.snapshots[snapshot.snapshot_id] = snapshot

                self.operation_history = data.get("operation_history", [])
                self.failure_counts = data.get("failure_counts", {})
                self.recovery_metrics = data.get("recovery_metrics", self.recovery_metrics)

                logger.info("Loaded {len(self.snapshots)} recovery snapshots")

            except Exception:
                logger.exception("Failed to load recovery state")

        # Also load individual snapshot files
        try:
            for snapshot_file in self.snapshots_dir.glob("*.json"):
                if snapshot_file.stem not in self.snapshots:
                    try:
                        with snapshot_file.open() as f:
                            snapshot_data = json.load(f)
                        snapshot = OperationSnapshot.from_dict(snapshot_data)
                        self.snapshots[snapshot.snapshot_id] = snapshot
                    except (OSError, json.JSONDecodeError, KeyError, TypeError) as e:
                        logger.warning("Failed to load snapshot file %s: %s", snapshot_file, e)
        except (OSError, PermissionError) as e:
            logger.warning("Failed to load snapshot files: %s", e)

    def _save_state(self) -> None:
        """Save recovery engine state."""
        state_file = self._get_state_file()

        try:
            data = {
                "snapshots": [s.to_dict() for s in self.snapshots.values()],
                "operation_history": self.operation_history[-1000:],  # Keep last 1000
                "failure_counts": self.failure_counts,
                "recovery_metrics": self.recovery_metrics,
                "saved_at": datetime.now(UTC).isoformat(),
            }

            with state_file.open("w") as f:
                json.dump(data, f, indent=2)

        except Exception:
            logger.exception("Failed to save recovery state")

    def _setup_default_strategies(self) -> None:
        """Setup default recovery strategies."""
        # Task execution failures
        self.register_recovery_strategy(
            name="task_timeout",
            error_pattern=r"timed? ?out|timeout",
            max_retries=2,
            retry_delay=5.0,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.RESET_AGENT],
        )

        self.register_recovery_strategy(
            name="agent_error",
            error_pattern=r"agent.*error|agent.*fail",
            max_retries=3,
            retry_delay=2.0,
            recovery_actions=[RecoveryAction.RESET_AGENT, RecoveryAction.RETRY],
        )

        # Branch operation failures
        self.register_recovery_strategy(
            name="git_conflict",
            error_pattern=r"merge conflict|conflict.*merge",
            max_retries=1,
            recovery_actions=[RecoveryAction.ROLLBACK, RecoveryAction.ESCALATE],
        )

        self.register_recovery_strategy(
            name="git_error",
            error_pattern=r"git.*error|fatal:.*git",
            max_retries=2,
            retry_delay=1.0,
            recovery_actions=[RecoveryAction.RESTORE_STATE, RecoveryAction.RETRY],
        )

        # Resource errors
        self.register_recovery_strategy(
            name="resource_exhaustion",
            error_pattern=r"memory|disk.*full|no.*space|resource.*limit",
            max_retries=1,
            recovery_actions=[RecoveryAction.SKIP, RecoveryAction.ESCALATE],
        )

        # Generic failures
        self.register_recovery_strategy(
            name="generic_failure",
            error_pattern=r".*",  # Catch-all
            max_retries=1,
            recovery_actions=[RecoveryAction.RETRY, RecoveryAction.ROLLBACK],
        )

    def register_recovery_strategy(
        self,
        name: str,
        error_pattern: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        recovery_actions: list[RecoveryAction] | None = None,
        escalation_threshold: int = 5,
        custom_handler: Callable | None = None,
    ) -> None:
        """Register a recovery strategy."""
        if recovery_actions is None:
            recovery_actions = [RecoveryAction.RETRY, RecoveryAction.ROLLBACK]

        strategy = RecoveryStrategy(
            error_pattern=error_pattern,
            max_retries=max_retries,
            retry_delay=retry_delay,
            recovery_actions=recovery_actions,
            escalation_threshold=escalation_threshold,
            custom_handler=custom_handler,
        )

        self.recovery_strategies[name] = strategy
        logger.info("Registered recovery strategy: {name}")

    async def create_snapshot(
        self,
        operation_type: OperationType,
        description: str,
        agent_pool: object | None = None,
        branch_manager: object | None = None,
        files_to_backup: list[str] | None = None,
        operation_context: dict[str, str | int | bool | float | list[str]] | None = None,
    ) -> str:
        """Create a snapshot before a critical operation.

        Args:
            operation_type: Type of operation being performed
            description: Human-readable description
            agent_pool: AgentPool instance to snapshot
            branch_manager: BranchManager instance to snapshot
            files_to_backup: List of file paths to backup
            operation_context: Additional context for the operation

        Returns:
            Snapshot ID
        """
        snapshot_id = f"snap-{int(time.time())}-{str(uuid.uuid4())[:8]}"

        snapshot = OperationSnapshot(
            snapshot_id=snapshot_id,
            operation_type=operation_type,
            timestamp=datetime.now(UTC),
            description=description,
            operation_context=operation_context or {},
        )

        try:
            # Snapshot agent states
            if agent_pool:
                snapshot.agent_states = {agent_id: agent.to_dict() for agent_id, agent in agent_pool.agents.items()}

                snapshot.task_states = {task_id: task.to_dict() for task_id, task in agent_pool.tasks.items()}

            # Snapshot branch state
            if branch_manager:
                try:
                    current_branch = branch_manager._get_current_branch()
                    branch_status = branch_manager.get_branch_status(current_branch)
                    snapshot.branch_state = {
                        "current_branch": current_branch,
                        "status": branch_status,
                        "branches": {name: info.to_dict() for name, info in branch_manager.branches.items()},
                    }
                except (AttributeError, KeyError, TypeError) as e:
                    logger.warning("Failed to snapshot branch state: %s", e)

            # Backup files
            if files_to_backup:
                for file_path in files_to_backup:
                    try:
                        backup_path = await self._backup_file(snapshot_id, file_path)
                        if backup_path:
                            snapshot.file_states[file_path] = backup_path
                    except (OSError, PermissionError, shutil.Error) as e:
                        logger.warning("Failed to backup file %s: %s", file_path, e)

            # Store snapshot
            self.snapshots[snapshot_id] = snapshot

            # Save snapshot to disk
            snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
            with snapshot_file.open("w") as f:
                json.dump(snapshot.to_dict(), f, indent=2)

            self.recovery_metrics["total_operations"] += 1

            logger.info("Created snapshot %s for %s: %s", snapshot_id, operation_type.value, description)

            # Cleanup old snapshots
            await self._cleanup_old_snapshots()

            return snapshot_id

        except Exception:
            logger.exception("Failed to create snapshot")
            raise

    async def _backup_file(self, snapshot_id: str, file_path: str) -> str | None:
        """Backup a file for potential rollback."""
        try:
            source_path = Path(file_path)
            if not source_path.exists():
                return None

            backup_path = self.backups_dir / snapshot_id / source_path.name
            backup_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.copy2(source_path, backup_path)
            return str(backup_path)

        except Exception:
            logger.exception(f"Failed to backup file {file_path}")  # noqa: G004
            return None

    async def rollback_operation(
        self,
        snapshot_id: str,
        agent_pool: object | None = None,
        branch_manager: object | None = None,
        restore_files: bool = True,  # noqa: FBT001
    ) -> bool:
        """Rollback to a previous snapshot.

        Args:
            snapshot_id: ID of snapshot to rollback to
            agent_pool: AgentPool instance to restore
            branch_manager: BranchManager instance to restore
            restore_files: Whether to restore backed up files

        Returns:
            True if rollback successful, False otherwise
        """
        if snapshot_id not in self.snapshots:
            logger.error("Snapshot {snapshot_id} not found")
            return False

        snapshot = self.snapshots[snapshot_id]

        try:
            logger.info("Rolling back to snapshot {snapshot_id}: {snapshot.description}")

            # Restore agent states
            if agent_pool and snapshot.agent_states:
                await self._restore_agent_states(agent_pool, snapshot.agent_states)

            # Restore task states
            if agent_pool and snapshot.task_states:
                await self._restore_task_states(agent_pool, snapshot.task_states)

            # Restore branch state
            if branch_manager and snapshot.branch_state:
                await self._restore_branch_state(branch_manager, snapshot.branch_state)

            # Restore files
            if restore_files and snapshot.file_states:
                await self._restore_files(snapshot.file_states)

            # Execute custom rollback instructions
            for instruction in snapshot.rollback_instructions:
                await self._execute_rollback_instruction(instruction)

            self.recovery_metrics["rollbacks_performed"] += 1

            logger.info("Successfully rolled back to snapshot {snapshot_id}")
            return True

        except Exception:
            logger.exception(f"Failed to rollback to snapshot {snapshot_id}")  # noqa: G004
            return False

    @staticmethod
    async def _restore_agent_states(agent_pool: object | None, agent_states: dict[str, dict[str, str | int | bool | list[str]]]) -> None:
        """Restore agent states from snapshot."""
        for agent_id, agent_data in agent_states.items():
            try:
                if agent_id in agent_pool.agents:
                    # Update existing agent
                    agent = agent_pool.agents[agent_id]
                    agent.state = AgentState(agent_data["state"])
                    agent.current_task = agent_data.get("current_task")
                    agent.branch_name = agent_data.get("branch_name")

                    # Terminate any running process
                    if agent.process:
                        try:
                            agent.process.terminate()
                            await asyncio.wait_for(agent.process.wait(), timeout=5)
                        except (TimeoutError, ProcessLookupError):
                            with contextlib.suppress(Exception):
                                agent.process.kill()
                        agent.process = None
                else:
                    # Recreate agent
                    agent = Agent.from_dict(agent_data)
                    agent.process = None  # Don't restore processes
                    agent_pool.agents[agent_id] = agent

            except (KeyError, AttributeError, TypeError, ValueError) as e:
                logger.warning("Failed to restore agent %s: %s", agent_id, e)

    @staticmethod
    async def _restore_task_states(agent_pool: object | None, task_states: dict[str, dict[str, str | int | bool | float | list[str]]]) -> None:
        """Restore task states from snapshot."""
        # Clear current tasks and restore from snapshot
        agent_pool.tasks.clear()

        for task_id, task_data in task_states.items():
            try:
                task = Task.from_dict(task_data)

                # Reset execution state
                if task.status in {TaskStatus.RUNNING, TaskStatus.ASSIGNED}:
                    task.status = TaskStatus.PENDING
                    task.assigned_agent = None
                    task.start_time = None
                    task.end_time = None

                agent_pool.tasks[task_id] = task

            except (KeyError, AttributeError, TypeError, ValueError) as e:
                logger.warning("Failed to restore task %s: %s", task_id, e)

    @staticmethod
    async def _restore_branch_state(branch_manager: object | None, branch_state: dict[str, str | dict[str, str | int | bool | list[str]]]) -> None:
        """Restore branch state from snapshot."""
        try:
            current_branch = branch_state.get("current_branch")
            if current_branch:
                success = branch_manager.switch_branch(current_branch)
                if not success:
                    logger.warning("Failed to switch to branch {current_branch}")

            # Restore branch metadata
            branches_data = branch_state.get("branches", {})
            for branch_name, branch_data in branches_data.items():
                try:

                    branch_info = BranchInfo.from_dict(branch_data)
                    branch_manager.branches[branch_name] = branch_info
                except (KeyError, AttributeError, TypeError, ImportError) as e:
                    logger.warning("Failed to restore branch %s: %s", branch_name, e)

            # Save restored branch metadata
            branch_manager._save_branch_metadata()

        except (AttributeError, KeyError, ImportError, OSError) as e:
            logger.warning("Failed to restore branch state: %s", e)

    @staticmethod
    async def _restore_files(file_states: dict[str, str]) -> None:
        """Restore files from backup."""
        for original_path, backup_path in file_states.items():
            try:
                if Path(backup_path).exists():
                    shutil.copy2(backup_path, original_path)
                    logger.debug("Restored file %s", original_path)
                else:
                    logger.warning("Backup file %s not found", backup_path)
            except (OSError, PermissionError, shutil.Error) as e:
                logger.warning("Failed to restore file %s: %s", original_path, e)

    @staticmethod
    async def _execute_rollback_instruction(instruction: dict[str, str | int | bool | list[str]]) -> None:
        """Execute a custom rollback instruction."""
        try:
            instruction_type = instruction.get("type")

            if instruction_type == "git_command":
                command = instruction.get("command", [])
                if command:
                    result = subprocess.run(
                        command,
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=30,
                    )
                    if result.returncode != 0:
                        logger.warning("Rollback git command failed: {result.stderr}")

            elif instruction_type == "file_operation":
                operation = instruction.get("operation")
                file_path = instruction.get("file_path")

                if operation == "delete" and file_path:
                    Path(file_path).unlink(missing_ok=True)
                elif operation == "create" and file_path:
                    Path(file_path).touch()

            # Add more instruction types as needed

        except (OSError, subprocess.CalledProcessError, KeyError, TypeError) as e:
            logger.warning("Failed to execute rollback instruction %s: %s", instruction, e)

    async def handle_operation_failure(
        self,
        operation_id: str,
        exception: Exception,
        context: dict[str, str | int | bool | float | list[str]] | None = None,
        agent_pool: object | None = None,
        branch_manager: object | None = None,
    ) -> bool:
        """Handle an operation failure with automatic recovery.

        Args:
            operation_id: ID of the failed operation
            exception: The exception that occurred
            context: Additional context about the failure
            agent_pool: AgentPool instance for recovery
            branch_manager: BranchManager instance for recovery

        Returns:
            True if recovery was successful, False otherwise
        """
        self.recovery_metrics["failed_operations"] += 1

        error_message = str(exception)
        operation_key = context.get("operation_type", "unknown") if context else "unknown"

        # Track failure count
        self.failure_counts[operation_key] = self.failure_counts.get(operation_key, 0) + 1

        logger.error("Operation {operation_id} failed: {error_message}")

        # Find matching recovery strategy
        strategy = self._find_recovery_strategy(error_message)
        if not strategy:
            logger.warning("No recovery strategy found for error: {error_message}")
            return False

        logger.info("Applying recovery strategy for {operation_id}")

        # Get snapshot for rollback
        snapshot_id = self.active_operations.get(operation_id)

        try:
            # Try custom handler first
            if strategy.custom_handler:
                custom_success = await strategy.custom_handler(exception, context or {})
                if custom_success:
                    self.recovery_metrics["successful_recoveries"] += 1
                    return True

            # Execute recovery actions
            for action in strategy.recovery_actions:
                success = await self._execute_recovery_action(
                    action,
                    snapshot_id,
                    exception,
                    context,
                    agent_pool,
                    branch_manager,
                )

                if success:
                    self.recovery_metrics["successful_recoveries"] += 1
                    logger.info("Recovery action {action.value} succeeded for {operation_id}")
                    return True

            # If all recovery actions failed
            logger.error("All recovery actions failed for operation {operation_id}")
            self.recovery_metrics["failed_recoveries"] += 1

            # Check if we should escalate
            if self.failure_counts[operation_key] >= strategy.escalation_threshold:
                await self._escalate_failure(operation_id, exception, context)

            return False

        except Exception:
            logger.exception(f"Recovery process failed for {operation_id}")  # noqa: G004
            self.recovery_metrics["failed_recoveries"] += 1
            return False

        finally:
            # Clean up
            if operation_id in self.active_operations:
                del self.active_operations[operation_id]

            # Record operation in history
            self.operation_history.append(
                {
                    "operation_id": operation_id,
                    "timestamp": datetime.now(UTC).isoformat(),
                    "error": error_message,
                    "recovery_attempted": True,
                    "context": context,
                }
            )

            self._save_state()

    def _find_recovery_strategy(self, error_message: str) -> RecoveryStrategy | None:
        """Find the best matching recovery strategy for an error."""
        # Try to find a specific match first
        for name, strategy in self.recovery_strategies.items():
            if name != "generic_failure" and re.search(strategy.error_pattern, error_message, re.IGNORECASE):
                return strategy

        # Fall back to generic strategy
        return self.recovery_strategies.get("generic_failure")

    async def _execute_recovery_action(
        self,
        action: RecoveryAction,
        snapshot_id: str | None,
        exception: Exception,
        context: dict[str, str | int | bool | float | list[str]],
        agent_pool: object | None = None,
        branch_manager: object | None = None,
    ) -> bool:
        """Execute a specific recovery action."""
        try:
            if action == RecoveryAction.RETRY:
                # Retry logic should be handled by the caller
                return False

            if action == RecoveryAction.ROLLBACK:
                if snapshot_id:
                    return await self.rollback_operation(
                        snapshot_id,
                        agent_pool,
                        branch_manager,
                    )
                logger.warning("No snapshot available for rollback")
                return False

            if action == RecoveryAction.RESET_AGENT:
                if agent_pool and context.get("agent_id"):
                    agent_id = context["agent_id"]
                    if agent_id in agent_pool.agents:
                        agent = agent_pool.agents[agent_id]

                        # Terminate any running process
                        if agent.process:
                            try:
                                agent.process.terminate()
                                await asyncio.wait_for(agent.process.wait(), timeout=5)
                            except (TimeoutError, ProcessLookupError):
                                with contextlib.suppress(Exception):
                                    agent.process.kill()
                            agent.process = None

                        # Reset agent state
                        agent.state = AgentState.IDLE
                        agent.current_task = None

                        logger.info("Reset agent {agent_id}")
                        return True
                return False

            if action == RecoveryAction.RESTORE_STATE:
                if snapshot_id:
                    return await self.rollback_operation(
                        snapshot_id,
                        agent_pool,
                        branch_manager,
                        restore_files=False,
                    )
                return False

            if action == RecoveryAction.SKIP:
                # Mark operation as skipped
                logger.info("Skipping failed operation")
                return True

            if action == RecoveryAction.ESCALATE:
                await self._escalate_failure(context.get("operation_id", "unknown"), exception, context)
                return False

            return False

        except Exception:
            logger.exception(f"Failed to execute recovery action {action.value}")  # noqa: G004
            return False

    async def _escalate_failure(
        self,
        operation_id: str,
        exception: Exception,
        context: dict[str, str | int | bool | float | list[str]],
    ) -> None:
        """Escalate a failure to higher level handling."""
        escalation_data = {
            "operation_id": operation_id,
            "error": str(exception),
            "context": context,
            "timestamp": datetime.now(UTC).isoformat(),
            "failure_count": self.failure_counts.get(context.get("operation_type", "unknown"), 0),
        }

        # Save escalation data
        escalation_file = self.work_dir / "escalations.json"
        escalations = []

        if escalation_file.exists():
            try:
                with escalation_file.open() as f:
                    escalations = json.load(f)
            except (OSError, json.JSONDecodeError):
                pass

        escalations.append(escalation_data)

        # Keep only last 100 escalations
        escalations = escalations[-100:]

        with escalation_file.open("w") as f:
            json.dump(escalations, f, indent=2)

        logger.critical("Escalated failure for operation {operation_id}: {exception}")

    async def _cleanup_old_snapshots(self) -> None:
        """Clean up old snapshots to prevent disk space issues."""
        try:
            current_time = datetime.now(UTC)
            cutoff_time = current_time - timedelta(hours=self.auto_cleanup_hours)

            # Find snapshots to remove
            to_remove = []
            for snapshot_id, snapshot in self.snapshots.items():
                if snapshot.timestamp < cutoff_time:
                    to_remove.append(snapshot_id)

            # Enforce max snapshots limit
            if len(self.snapshots) > self.max_snapshots:
                # Sort by timestamp and remove oldest
                sorted_snapshots = sorted(
                    self.snapshots.items(),
                    key=lambda x: x[1].timestamp,
                )
                excess_count = len(self.snapshots) - self.max_snapshots
                for snapshot_id, _ in sorted_snapshots[:excess_count]:
                    if snapshot_id not in to_remove:
                        to_remove.append(snapshot_id)

            # Remove old snapshots
            for snapshot_id in to_remove:
                await self._remove_snapshot(snapshot_id)

            if to_remove:
                logger.info("Cleaned up {len(to_remove)} old snapshots")

        except Exception:
            logger.exception("Failed to cleanup old snapshots")

    async def _remove_snapshot(self, snapshot_id: str) -> None:
        """Remove a snapshot and its associated backups."""
        try:
            # Remove from memory
            if snapshot_id in self.snapshots:
                del self.snapshots[snapshot_id]

            # Remove snapshot file
            snapshot_file = self.snapshots_dir / f"{snapshot_id}.json"
            if snapshot_file.exists():
                snapshot_file.unlink()

            # Remove backup directory
            backup_dir = self.backups_dir / snapshot_id
            if backup_dir.exists():
                shutil.rmtree(backup_dir)

        except (OSError, PermissionError, shutil.Error) as e:
            logger.warning("Failed to remove snapshot %s: %s", snapshot_id, e)

    def start_operation(self, operation_id: str, snapshot_id: str) -> None:
        """Register that an operation is starting with a snapshot."""
        self.active_operations[operation_id] = snapshot_id

    def complete_operation(self, operation_id: str) -> None:
        """Mark an operation as completed successfully."""
        if operation_id in self.active_operations:
            del self.active_operations[operation_id]

    def get_recovery_metrics(self) -> dict[str, int | float | dict[str, int]]:
        """Get recovery and rollback metrics."""
        return {
            **self.recovery_metrics,
            "active_operations": len(self.active_operations),
            "total_snapshots": len(self.snapshots),
            "failure_counts": self.failure_counts.copy(),
            "disk_usage_mb": self._calculate_disk_usage(),
        }

    def _calculate_disk_usage(self) -> float:
        """Calculate disk usage of recovery system in MB."""
        try:
            total_size = 0
            for file_path in self.work_dir.rglob("*"):
                if file_path.is_file():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)  # Convert to MB
        except (OSError, PermissionError):
            return 0.0

    def get_recent_operations(self, limit: int = 20) -> list[dict[str, str | bool | dict[str, str | int | bool | float | list[str]]]]:
        """Get recent operation history."""
        return self.operation_history[-limit:]

    def get_snapshot_info(self, snapshot_id: str) -> dict[str, str | int | bool | float | list[str] | dict[str, str | int | bool | float | list[str]] | dict[str, str | int | bool | list[str]]] | None:
        """Get information about a specific snapshot."""
        if snapshot_id in self.snapshots:
            return self.snapshots[snapshot_id].to_dict()
        return None

    async def manual_rollback(
        self,
        snapshot_id: str,
        agent_pool: object | None = None,
        branch_manager: object | None = None,
    ) -> bool:
        """Manually trigger a rollback to a specific snapshot."""
        logger.info("Manual rollback requested to snapshot {snapshot_id}")
        return await self.rollback_operation(snapshot_id, agent_pool, branch_manager)
