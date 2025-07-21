# Copyright notice.

import asyncio
import json
import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from .context_detector import ContextInfo, ContextType

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Workflow engine for executing automation chains."""


# Type aliases for complex types
WorkflowStatusType = dict[str, int | dict[str, str | int | bool | list[str]]]


logger = logging.getLogger(__name__)


class ActionType(Enum):
    """Types of actions that can be executed."""

    SHELL_COMMAND = "shell_command"
    TMUX_COMMAND = "tmux_command"
    CLAUDE_INPUT = "claude_input"
    FILE_OPERATION = "file_operation"
    NOTIFICATION = "notification"
    DELAY = "delay"
    CONDITION_CHECK = "condition_check"
    PARALLEL_EXECUTION = "parallel_execution"


class WorkflowStatus(Enum):
    """Status of workflow execution."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class WorkflowAction:
    """A single action in a workflow."""

    action_type: ActionType
    command: str
    parameters: dict[str, str | int | float | bool | list[str] | dict[str, str]] = field(default_factory=dict)
    timeout: int = 60
    retry_count: int = 0
    retry_delay: int = 5
    continue_on_failure: bool = False
    condition: str | None = None  # Python expression to evaluate

    def to_dict(self) -> dict[str, str | int | bool | dict[str, str | int | float | bool | list[str] | dict[str, str]]]:
        """Convert to dictionary for serialization.

        Returns:
        object: Description of return value.
        """
        return {
            "action_type": self.action_type.value,
            "command": self.command,
            "parameters": self.parameters,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "continue_on_failure": self.continue_on_failure,
            "condition": self.condition,
        }


@dataclass
class WorkflowChain:
    """A chain of workflow actions triggered by specific contexts."""

    name: str
    trigger_contexts: list[ContextType]
    actions: list[WorkflowAction]
    priority: int = 1
    enabled: bool = True
    description: str = ""

    def to_dict(self) -> dict[str, str | int | bool | list[str] | list[dict[str, str | int | bool | dict[str, str | int | float | bool | list[str] | dict[str, str]]]]]:
        """Convert to dictionary for serialization.

        Returns:
        object: Description of return value.
        """
        return {
            "name": self.name,
            "trigger_contexts": [ctx.value for ctx in self.trigger_contexts],
            "actions": [action.to_dict() for action in self.actions],
            "priority": self.priority,
            "enabled": self.enabled,
            "description": self.description,
        }


@dataclass
class WorkflowExecution:
    """Represents an executing or completed workflow."""

    workflow_name: str
    context_info: ContextInfo
    status: WorkflowStatus
    start_time: float
    end_time: float | None = None
    current_action: int = 0
    results: list[dict[str, str | int | float | bool]] = field(default_factory=list)
    error_message: str | None = None

    def to_dict(self) -> dict[str, str | float | int | list[dict[str, str | int | float | bool]] | dict[str, str | float | int | list[str]]]:
        """Convert to dictionary for serialization.

        Returns:
        object: Description of return value.
        """
        return {
            "workflow_name": self.workflow_name,
            "context_info": self.context_info.to_dict(),
            "status": self.status.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "current_action": self.current_action,
            "results": self.results,
            "error_message": self.error_message,
        }


class ConditionEvaluator:
    """Safe condition evaluator that replaces eval() with regex-based parsing."""

    def __init__(self, context_info: ContextInfo) -> None:
        self.context = {
            "context_type": context_info.context_type.value,
            "confidence": context_info.confidence,
            "details": context_info.details,
            "project_path": str(context_info.project_path) if context_info.project_path else None,
            "session_name": context_info.session_name,
            "timestamp": context_info.timestamp,
        }

        # Supported operators
        self.operators = {
            "==": self._equals,
            "!=": self._not_equals,
            ">": self._greater_than,
            "<": self._less_than,
            ">=": self._greater_equal,
            "<=": self._less_equal,
            "in": self._contains,
            "not in": self._not_contains,
        }

        # Condition pattern: variable operator value
        self.condition_pattern = re.compile(r"^\s*(\w+)\s+(==|!=|>=|<=|>|<|not\s+in|in)\s+(.+?)\s*$")

    def evaluate(self, condition: str) -> bool:
        """Evaluate a condition string safely.

        Returns:
        bool: Description of return value.
        """
        # Handle simple boolean literals
        condition_lower = condition.strip().lower()
        if condition_lower in {"true", "1"}:
            return True
        if condition_lower in {"false", "0"}:
            return False

        # Parse complex conditions
        match = self.condition_pattern.match(condition)
        if not match:
            logger.warning("Invalid condition format: %s", condition)
            return False

        variable, operator, value_str = match.groups()

        # Check if variable exists in context
        if variable not in self.context:
            logger.warning("Unknown variable in condition: %s", variable)
            return False

        # Get variable value
        var_value = self.context[variable]

        # Parse the expected value
        expected_value = self._parse_value(value_str)

        # Apply operator
        if operator not in self.operators:
            logger.warning("Unsupported operator: %s", operator)
            return False

        return self.operators[operator](var_value, expected_value)

    @staticmethod
    def _parse_value(value_str: str) -> str | int | float | bool | None:
        """Parse a value string into appropriate Python type.

        Returns:
        object: Description of return value.
        """
        value_str = value_str.strip()

        # String literal (quoted)
        if (value_str.startswith('"') and value_str.endswith('"')) or (value_str.startswith("'") and value_str.endswith("'")):
            return value_str[1:-1]  # Remove quotes

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # None
        if value_str.lower() == "none":
            return None

        # Number
        try:
            if "." in value_str:
                return float(value_str)
            return int(value_str)
        except ValueError:
            pass

        # Default to string
        return value_str

    @staticmethod
    def _equals(left: str | int | float | bool | None, right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Equality comparison.

        Returns:
        bool: Description of return value.
        """
        return bool(left == right)

    @staticmethod
    def _not_equals(left: str | int | float | bool | None, right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Inequality comparison.

        Returns:
        bool: Description of return value.
        """
        return bool(left != right)

    @staticmethod
    def _greater_than(left: str | int | float | bool | None, right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Greater than comparison.

        Returns:
        bool: Description of return value.
        """
        try:
            return bool(left > right)
        except TypeError:
            return False

    @staticmethod
    def _less_than(left: str | int | float | bool | None, right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Less than comparison.

        Returns:
        bool: Description of return value.
        """
        try:
            return bool(left < right)
        except TypeError:
            return False

    @staticmethod
    def _greater_equal(left: str | int | float | bool | None, right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Greater than or equal comparison.

        Returns:
        bool: Description of return value.
        """
        try:
            return bool(left >= right)
        except TypeError:
            return False

    @staticmethod
    def _less_equal(left: str | int | float | bool | None, right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Less than or equal comparison.

        Returns:
        bool: Description of return value.
        """
        try:
            return bool(left <= right)
        except TypeError:
            return False

    @staticmethod
    def _contains(left: str | list[str] | dict[str, str], right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Containment check.

        Returns:
        bool: Description of return value.
        """
        try:
            return right in left
        except TypeError:
            return False

    @staticmethod
    def _not_contains(left: str | list[str] | dict[str, str], right: str | int | float | bool | None) -> bool:  # noqa: FBT001
        """Not containment check.

        Returns:
        bool: Description of return value.
        """
        try:
            return right not in left
        except TypeError:
            return True


class WorkflowEngine:
    """Engine for executing workflow automation chains."""

    def __init__(self, project_path: Path | None = None) -> None:
        self.project_path = project_path or Path.cwd()
        self.logger = logging.getLogger("yesman.workflow_engine")

        self.workflows: dict[str, WorkflowChain] = {}
        self.active_executions: dict[str, WorkflowExecution] = {}
        self.execution_history: list[WorkflowExecution] = []

        # Load default workflows
        self._load_default_workflows()

    def register_workflow(self, workflow: WorkflowChain) -> None:
        """Register a new workflow chain.

        """
        self.workflows[workflow.name] = workflow
        self.logger.info("Registered workflow: %s", workflow.name)

    def trigger_workflows(self, context_info: ContextInfo) -> list[str]:
        """Trigger workflows based on detected context.

        Returns:
        object: Description of return value.
        """
        triggered_workflows = []

        for workflow_name, workflow in self.workflows.items():
            if not workflow.enabled:
                continue

            if context_info.context_type in workflow.trigger_contexts:
                execution_id = f"{workflow_name}_{int(time.time())}"

                execution = WorkflowExecution(
                    workflow_name=workflow_name,
                    context_info=context_info,
                    status=WorkflowStatus.PENDING,
                    start_time=time.time(),
                )

                self.active_executions[execution_id] = execution
                triggered_workflows.append(execution_id)

                # Start execution asynchronously
                asyncio.create_task(self._execute_workflow(execution_id, workflow))

        return triggered_workflows

    async def _execute_workflow(self, execution_id: str, workflow: WorkflowChain) -> None:
        """Execute a workflow chain."""
        execution = self.active_executions[execution_id]
        execution.status = WorkflowStatus.RUNNING

        self.logger.info("Starting workflow execution: %s", workflow.name)

        try:
            for i, action in enumerate(workflow.actions):
                execution.current_action = i

                # Check condition if specified
                if action.condition and not self._evaluate_condition(action.condition, execution.context_info):
                    self.logger.debug("Skipping action %s due to condition: %s", i, action.condition)
                    continue

                # Execute action with retries
                success = await self._execute_action_with_retry(action, execution)

                if not success and not action.continue_on_failure:
                    execution.status = WorkflowStatus.FAILED
                    execution.error_message = f"Action {i} failed and continue_on_failure is False"
                    break

            else:
                # All actions completed successfully
                execution.status = WorkflowStatus.COMPLETED

        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.error_message = str(e)
            self.logger.error("Workflow %s failed: %s", workflow.name, e, exc_info=True)

        finally:
            execution.end_time = time.time()

            # Move to history and cleanup
            self.execution_history.append(execution)
            del self.active_executions[execution_id]

            # Keep only last 100 executions in history
            if len(self.execution_history) > 100:
                self.execution_history = self.execution_history[-100:]

            self.logger.info("Workflow %s completed with status: %s", workflow.name, execution.status.value)

    async def _execute_action_with_retry(self, action: WorkflowAction, execution: WorkflowExecution) -> bool:
        """Execute an action with retry logic."""
        for attempt in range(action.retry_count + 1):
            try:
                result = await self._execute_single_action(action, execution)
                execution.results.append(
                    {
                        "action_index": execution.current_action,
                        "attempt": attempt + 1,
                        "success": True,
                        "result": result,
                        "timestamp": time.time(),
                    }
                )
                return True

            except Exception as e:
                error_info = {
                    "action_index": execution.current_action,
                    "attempt": attempt + 1,
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time(),
                }
                execution.results.append(error_info)

                if attempt < action.retry_count:
                    self.logger.warning("Action failed (attempt %s), retrying in %ss: %s", attempt + 1, action.retry_delay, e)
                    await asyncio.sleep(action.retry_delay)
                else:
                    self.logger.exception("Action failed after %s attempts")

        return False

    async def _execute_single_action(self, action: WorkflowAction, execution: WorkflowExecution) -> dict[str, str | int | bool | list[str | Exception]]:
        """Execute a single action."""
        self.logger.debug("Executing action: %s - %s", action.action_type.value, action.command)

        if action.action_type == ActionType.SHELL_COMMAND:
            return await self._execute_shell_command(action)

        if action.action_type == ActionType.TMUX_COMMAND:
            return await self._execute_tmux_command(action, execution)

        if action.action_type == ActionType.CLAUDE_INPUT:
            return await self._execute_claude_input(action, execution)

        if action.action_type == ActionType.FILE_OPERATION:
            return await self._execute_file_operation(action)

        if action.action_type == ActionType.NOTIFICATION:
            return await self._execute_notification(action)

        if action.action_type == ActionType.DELAY:
            return await self._execute_delay(action)

        if action.action_type == ActionType.CONDITION_CHECK:
            return await self._execute_condition_check(action, execution)

        if action.action_type == ActionType.PARALLEL_EXECUTION:
            return await self._execute_parallel_actions(action, execution)

        msg = f"Unsupported action type: {action.action_type}"
        raise ValueError(msg)

    async def _execute_shell_command(self, action: WorkflowAction) -> dict[str, int | str]:
        """Execute shell command."""
        process = await asyncio.create_subprocess_shell(
            action.command,
            cwd=self.project_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=action.timeout,
            )

            return {
                "returncode": process.returncode,
                "stdout": stdout.decode("utf-8"),
                "stderr": stderr.decode("utf-8"),
            }

        except TimeoutError as e:
            process.kill()
            msg = f"Command timed out after {action.timeout}s: {action.command}"
            raise TimeoutError(msg) from e

    @staticmethod
    async def _execute_tmux_command(action: WorkflowAction, execution: WorkflowExecution) -> dict[str, int | str]:
        """Execute tmux command."""
        session_name = execution.context_info.session_name or action.parameters.get("session_name")

        if not session_name:
            msg = "No session name provided for tmux command"
            raise ValueError(msg)

        tmux_cmd = f"tmux send-keys -t {session_name} '{action.command}' Enter"

        process = await asyncio.create_subprocess_shell(
            tmux_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        stdout, stderr = await process.communicate()

        return {
            "returncode": process.returncode,
            "session_name": session_name,
            "command_sent": action.command,
        }

    @staticmethod
    async def _execute_claude_input(action: WorkflowAction, execution: WorkflowExecution) -> dict[str, str]:
        """Send input to Claude through the dashboard controller."""
        # This would integrate with the ClaudeManager
        # For now, simulate the action
        await asyncio.sleep(0.1)

        return {
            "input_sent": action.command,
            "session_name": execution.context_info.session_name,
        }

    async def _execute_file_operation(self, action: WorkflowAction) -> dict[str, str | int]:
        """Execute file operation."""
        operation = action.parameters.get("operation", "read")
        file_path = Path(self.project_path) / action.command

        if operation == "read":
            content = file_path.read_text()
            return {"operation": "read", "content_length": len(content)}

        if operation == "write":
            content = action.parameters.get("content", "")
            file_path.write_text(content)
            return {"operation": "write", "bytes_written": len(content)}

        if operation == "delete":
            file_path.unlink()
            return {"operation": "delete", "file_deleted": str(file_path)}

        msg = f"Unsupported file operation: {operation}"
        raise ValueError(msg)

    async def _execute_notification(self, action: WorkflowAction) -> dict[str, str]:
        """Send notification."""
        # Platform-specific notification
        title = action.parameters.get("title", "Yesman Automation")

        try:
            # macOS notification
            cmd = f'osascript -e \'display notification "{action.command}" with title "{title}"\''
            process = await asyncio.create_subprocess_shell(cmd)
            await process.communicate()

        except Exception:
            # Fallback to logging
            self.logger.info("NOTIFICATION: %s - %s", title, action.command)

        return {"notification_sent": action.command}

    @staticmethod
    async def _execute_delay(action: WorkflowAction) -> dict[str, int]:
        """Execute delay."""
        delay_seconds = int(action.command)
        await asyncio.sleep(delay_seconds)
        return {"delay_seconds": delay_seconds}

    async def _execute_condition_check(self, action: WorkflowAction, execution: WorkflowExecution) -> dict[str, str | bool]:
        """Execute condition check."""
        result = self._evaluate_condition(action.command, execution.context_info)
        return {"condition": action.command, "result": result}

    async def _execute_parallel_actions(self, action: WorkflowAction, execution: WorkflowExecution) -> dict[str, list[dict[str, str | int | bool | list[str | Exception]] | Exception] | int]:
        """Execute multiple actions in parallel."""
        parallel_actions = action.parameters.get("actions", [])

        tasks = []
        for parallel_action_data in parallel_actions:
            parallel_action = WorkflowAction(**parallel_action_data)
            task = asyncio.create_task(self._execute_single_action(parallel_action, execution))
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        return {"parallel_results": results, "action_count": len(tasks)}

    def _evaluate_condition(self, condition: str, context_info: ContextInfo) -> bool:
        """Evaluate a condition expression safely without using eval().

        Returns:
        bool: Description of return value.
        """
        try:
            evaluator = ConditionEvaluator(context_info)
            return evaluator.evaluate(condition)
        except Exception as e:
            self.logger.warning("Condition evaluation failed: %s - %s", condition, e)
            return False

    def _load_default_workflows(self) -> None:
        """Load default workflow configurations.

        """
        # Git commit → test → build workflow
        git_workflow = WorkflowChain(
            name="git_commit_validation",
            trigger_contexts=[ContextType.GIT_COMMIT],
            description="Run tests and build after git commit",
            priority=1,
            actions=[
                WorkflowAction(
                    action_type=ActionType.NOTIFICATION,
                    command="Running automated validation after git commit",
                    parameters={"title": "Yesman Automation"},
                ),
                WorkflowAction(
                    action_type=ActionType.SHELL_COMMAND,
                    command="npm test",
                    timeout=120,
                    continue_on_failure=True,
                ),
                WorkflowAction(
                    action_type=ActionType.SHELL_COMMAND,
                    command="npm run build",
                    timeout=180,
                    condition="context_type == 'git_commit'",
                ),
            ],
        )

        # Test failure → retry and report workflow
        test_failure_workflow = WorkflowChain(
            name="test_failure_handling",
            trigger_contexts=[ContextType.TEST_FAILURE],
            description="Handle test failures with retry and reporting",
            priority=2,
            actions=[
                WorkflowAction(
                    action_type=ActionType.NOTIFICATION,
                    command="Test failure detected, attempting retry",
                    parameters={"title": "Test Alert"},
                ),
                WorkflowAction(
                    action_type=ActionType.DELAY,
                    command="5",
                ),
                WorkflowAction(
                    action_type=ActionType.SHELL_COMMAND,
                    command="npm test",
                    timeout=120,
                    retry_count=1,
                ),
            ],
        )

        # Claude idle → status check workflow
        claude_idle_workflow = WorkflowChain(
            name="claude_idle_maintenance",
            trigger_contexts=[ContextType.CLAUDE_IDLE],
            description="Perform maintenance when Claude is idle",
            priority=3,
            actions=[
                WorkflowAction(
                    action_type=ActionType.SHELL_COMMAND,
                    command="git status",
                    timeout=10,
                ),
                WorkflowAction(
                    action_type=ActionType.CONDITION_CHECK,
                    command="confidence > 0.8",
                    parameters={"check_deployment_readiness": True},
                ),
            ],
        )

        self.register_workflow(git_workflow)
        self.register_workflow(test_failure_workflow)
        self.register_workflow(claude_idle_workflow)

    def get_workflow_status(self) -> WorkflowStatusType:
        """Get current workflow engine status.

        Returns:
        WorkflowStatusType: Description of return value.
        """
        return {
            "registered_workflows": len(self.workflows),
            "active_executions": len(self.active_executions),
            "execution_history_count": len(self.execution_history),
            "workflows": {name: workflow.to_dict() for name, workflow in self.workflows.items()},
            "active": {exec_id: execution.to_dict() for exec_id, execution in self.active_executions.items()},
        }

    def save_workflows_config(self, file_path: Path) -> None:
        """Save workflow configurations to file.

        """
        config = {
            "workflows": {name: workflow.to_dict() for name, workflow in self.workflows.items()},
            "saved_at": time.time(),
        }

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

    def load_workflows_config(self, file_path: Path) -> None:
        """Load workflow configurations from file.

        """
        if not file_path.exists():
            return

        with open(file_path, encoding="utf-8") as f:
            config = json.load(f)

        for workflow_data in config.get("workflows", {}).values():
            # Convert back to objects
            actions = []
            for action_data in workflow_data["actions"]:
                action_data["action_type"] = ActionType(action_data["action_type"])
                actions.append(WorkflowAction(**action_data))

            workflow_data["actions"] = actions
            workflow_data["trigger_contexts"] = [ContextType(ctx) for ctx in workflow_data["trigger_contexts"]]

            workflow = WorkflowChain(**workflow_data)
            self.register_workflow(workflow)
