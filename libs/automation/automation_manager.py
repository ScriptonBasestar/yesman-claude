"""Automation manager that integrates context detection and workflow execution."""

import asyncio
import contextlib
import logging
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .context_detector import ContextDetector, ContextInfo, ContextType
from .workflow_engine import WorkflowChain, WorkflowEngine


class AutomationManager:
    """Manages context-aware automation for yesman-claude."""

    def __init__(self, project_path: Path | None = None):
        self.project_path = project_path or Path.cwd()
        self.logger = logging.getLogger("yesman.automation_manager")

        # Initialize components
        self.context_detector = ContextDetector(self.project_path)
        self.workflow_engine = WorkflowEngine(self.project_path)

        # Monitoring state
        self.is_monitoring = False
        self._monitor_task: asyncio.Task | None = None
        self._callbacks: dict[str, list[Callable]] = {
            "context_detected": [],
            "workflow_triggered": [],
            "workflow_completed": [],
        }

        # Statistics
        self.stats = {
            "contexts_detected": 0,
            "workflows_triggered": 0,
            "workflows_completed": 0,
            "start_time": time.time(),
        }

    def add_callback(self, event_type: str, callback: Callable) -> None:
        """Add callback for automation events."""
        if event_type in self._callbacks:
            self._callbacks[event_type].append(callback)

    def remove_callback(self, event_type: str, callback: Callable) -> None:
        """Remove callback for automation events."""
        if event_type in self._callbacks and callback in self._callbacks[event_type]:
            self._callbacks[event_type].remove(callback)

    async def start_monitoring(self, monitor_interval: int = 5) -> bool:
        """Start monitoring for contexts and triggering workflows."""
        if self.is_monitoring:
            self.logger.warning("Automation monitoring already running")
            return False

        self.is_monitoring = True
        self.stats["start_time"] = time.time()

        self._monitor_task = asyncio.create_task(
            self._monitoring_loop(monitor_interval),
        )

        self.logger.info("Started automation monitoring")
        return True

    async def stop_monitoring(self) -> bool:
        """Stop monitoring for contexts."""
        if not self.is_monitoring:
            self.logger.warning("Automation monitoring not running")
            return False

        self.is_monitoring = False

        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task

        self.logger.info("Stopped automation monitoring")
        return True

    async def _monitoring_loop(self, interval: int) -> None:
        """Main monitoring loop for context detection."""
        self.logger.info(f"Starting automation monitoring loop (interval: {interval}s)")

        try:
            while self.is_monitoring:
                await asyncio.sleep(interval)

                # Detect various contexts
                contexts = await self._detect_all_contexts()

                for context in contexts:
                    await self._handle_detected_context(context)

        except asyncio.CancelledError:
            self.logger.info("Monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)

    async def _detect_all_contexts(self) -> list[ContextInfo]:
        """Detect all possible contexts."""
        detected_contexts = []

        try:
            # Git context
            git_context = self.context_detector.detect_git_context()
            if git_context:
                detected_contexts.append(git_context)

            # File changes
            file_changes = self.context_detector.detect_file_changes()
            detected_contexts.extend(file_changes)

            # Deployment readiness
            deployment_context = self.context_detector.detect_deployment_ready_context()
            if deployment_context:
                detected_contexts.append(deployment_context)

        except Exception as e:
            self.logger.debug(f"Context detection error: {e}")

        return detected_contexts

    async def _handle_detected_context(self, context: ContextInfo) -> None:
        """Handle a detected context by triggering appropriate workflows."""
        self.stats["contexts_detected"] += 1

        self.logger.info(
            f"Context detected: {context.context_type.value} (confidence: {context.confidence:.2f})",
        )

        # Notify callbacks
        for callback in self._callbacks["context_detected"]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(context)
                else:
                    callback(context)
            except Exception as e:
                self.logger.error(f"Callback error: {e}")

        # Trigger workflows
        triggered_executions = self.workflow_engine.trigger_workflows(context)

        if triggered_executions:
            self.stats["workflows_triggered"] += len(triggered_executions)

            # Notify workflow triggered callbacks
            for callback in self._callbacks["workflow_triggered"]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(context, triggered_executions)
                    else:
                        callback(context, triggered_executions)
                except Exception as e:
                    self.logger.error(f"Workflow trigger callback error: {e}")

    def analyze_content_for_context(self, content: str, session_name: str = None) -> list[ContextInfo]:
        """Analyze content (e.g., tmux pane output) for context clues."""
        return self.context_detector.detect_context_from_content(content, session_name)

    def analyze_claude_idle(self, last_activity_time: float, idle_threshold: int = 30) -> ContextInfo | None:
        """Analyze Claude idle state for potential automation."""
        return self.context_detector.detect_claude_idle_context(last_activity_time, idle_threshold)

    def register_custom_workflow(self, workflow: WorkflowChain) -> None:
        """Register a custom workflow chain."""
        self.workflow_engine.register_workflow(workflow)

    def get_automation_status(self) -> dict[str, Any]:
        """Get comprehensive automation status."""
        workflow_status = self.workflow_engine.get_workflow_status()
        context_summary = self.context_detector.get_current_context_summary()

        return {
            "monitoring": {
                "is_monitoring": self.is_monitoring,
                "uptime": (time.time() - self.stats["start_time"] if self.is_monitoring else 0),
            },
            "statistics": self.stats.copy(),
            "workflows": workflow_status,
            "current_context": context_summary,
            "project_path": str(self.project_path),
        }

    async def manual_trigger_workflow(self, workflow_name: str, context_info: ContextInfo) -> str | None:
        """Manually trigger a specific workflow."""
        if workflow_name not in self.workflow_engine.workflows:
            self.logger.error(f"Workflow not found: {workflow_name}")
            return None

        workflow = self.workflow_engine.workflows[workflow_name]
        execution_ids = self.workflow_engine.trigger_workflows(context_info)

        if execution_ids:
            self.logger.info(f"Manually triggered workflow: {workflow_name}")
            return execution_ids[0]
        else:
            self.logger.warning(f"Failed to trigger workflow: {workflow_name}")
            return None

    def save_automation_config(self, config_path: Path = None) -> None:
        """Save automation configuration to file."""
        if not config_path:
            config_path = Path.home() / ".scripton" / "yesman" / "automation_config.json"

        config_path.parent.mkdir(parents=True, exist_ok=True)
        self.workflow_engine.save_workflows_config(config_path)

        self.logger.info(f"Saved automation config to: {config_path}")

    def load_automation_config(self, config_path: Path = None) -> None:
        """Load automation configuration from file."""
        if not config_path:
            config_path = Path.home() / ".scripton" / "yesman" / "automation_config.json"

        if config_path.exists():
            self.workflow_engine.load_workflows_config(config_path)
            self.logger.info(f"Loaded automation config from: {config_path}")
        else:
            self.logger.debug(f"No automation config found at: {config_path}")

    def get_execution_history(self, limit: int = 20) -> list[dict[str, Any]]:
        """Get recent workflow execution history."""
        history = self.workflow_engine.execution_history[-limit:]
        return [execution.to_dict() for execution in history]

    async def test_automation_chain(self, context_type: ContextType, test_details: dict[str, Any] = None) -> dict[str, Any]:
        """Test automation chain with simulated context."""
        test_context = ContextInfo(
            context_type=context_type,
            confidence=0.9,
            details=test_details or {"test": True, "simulated": True},
            timestamp=time.time(),
            project_path=str(self.project_path),
            session_name="test_session",
        )

        # Count workflows before trigger
        initial_executions = len(self.workflow_engine.active_executions)

        # Trigger workflows
        triggered_executions = self.workflow_engine.trigger_workflows(test_context)

        # Wait a moment for executions to start
        await asyncio.sleep(0.1)

        result = {
            "test_context": test_context.to_dict(),
            "triggered_executions": triggered_executions,
            "execution_count": len(triggered_executions),
            "active_executions_before": initial_executions,
            "active_executions_after": len(self.workflow_engine.active_executions),
        }

        self.logger.info(f"Automation test completed: {context_type.value} -> {len(triggered_executions)} workflows")

        return result

    def get_workflow_recommendations(self, context_info: ContextInfo) -> list[str]:
        """Get recommendations for workflows based on context."""
        recommendations = []

        # Analyze context and suggest appropriate workflows
        if context_info.context_type == ContextType.TEST_FAILURE:
            recommendations.extend(
                [
                    "Consider adding retry logic with delay",
                    "Add notification to team chat",
                    "Automatically run specific failed tests only",
                    "Check for flaky test patterns",
                ]
            )

        elif context_info.context_type == ContextType.GIT_COMMIT:
            recommendations.extend(
                [
                    "Run full test suite",
                    "Trigger build and deployment pipeline",
                    "Update documentation if needed",
                    "Run security scans",
                ]
            )

        elif context_info.context_type == ContextType.BUILD_FAILURE:
            recommendations.extend(
                [
                    "Retry build with clean cache",
                    "Check dependency updates",
                    "Run diagnostic commands",
                    "Rollback to last known good state",
                ]
            )

        return recommendations
