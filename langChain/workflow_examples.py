#!/usr/bin/env python3
"""Workflow Examples for LangChain-Claude CLI Integration.

This module provides common workflow patterns and examples for integrating
LangChain with Claude CLI for various development tasks.
"""

import asyncio
from typing import Any

from langchain_claude_integration import ClaudeAgent


class WorkflowTemplates:
    """Collection of common workflow templates."""

    @staticmethod
    def code_review_workflow() -> list[dict[str, Any]]:
        """Workflow for automated code review."""
        return [
            {
                "id": "security_scan",
                "type": "analysis",
                "prompt": "Scan codebase for security vulnerabilities and potential issues",
                "context": {"focus": "security", "severity": "all"},
            },
            {
                "id": "code_quality",
                "type": "analysis",
                "prompt": "Analyze code quality, style consistency, and best practices",
                "context": {"standards": ["pep8", "clean_code"], "metrics": True},
            },
            {
                "id": "test_coverage",
                "type": "testing",
                "prompt": "Check test coverage and identify untested code paths",
                "context": {"coverage_threshold": 80, "generate_missing": True},
            },
            {
                "id": "documentation_review",
                "type": "analysis",
                "prompt": "Review documentation completeness and accuracy",
                "context": {"check_api_docs": True, "update_readme": True},
            },
        ]

    @staticmethod
    def feature_development_workflow() -> list[dict[str, Any]]:
        """Workflow for new feature development."""
        return [
            {
                "id": "requirements_analysis",
                "type": "analysis",
                "prompt": "Analyze feature requirements and create implementation plan",
                "context": {"create_tasks": True, "estimate_effort": True},
            },
            {
                "id": "design_review",
                "type": "analysis",
                "prompt": "Review system design and architecture for the new feature",
                "context": {"check_compatibility": True, "suggest_patterns": True},
            },
            {
                "id": "implementation",
                "type": "implementation",
                "prompt": "Implement the feature following best practices and design patterns",
                "context": {"follow_conventions": True, "add_logging": True},
            },
            {
                "id": "unit_tests",
                "type": "testing",
                "prompt": "Create comprehensive unit tests for the new feature",
                "context": {"coverage_target": 95, "edge_cases": True},
            },
            {
                "id": "integration_tests",
                "type": "testing",
                "prompt": "Create integration tests and verify system compatibility",
                "context": {"test_endpoints": True, "verify_contracts": True},
            },
        ]

    @staticmethod
    def refactoring_workflow() -> list[dict[str, Any]]:
        """Workflow for code refactoring."""
        return [
            {
                "id": "identify_hotspots",
                "type": "analysis",
                "prompt": "Identify code hotspots and areas needing refactoring",
                "context": {"complexity_analysis": True, "technical_debt": True},
            },
            {
                "id": "extract_methods",
                "type": "implementation",
                "prompt": "Extract methods and improve code organization",
                "context": {"preserve_behavior": True, "improve_readability": True},
            },
            {
                "id": "remove_duplicates",
                "type": "implementation",
                "prompt": "Remove code duplication and create reusable components",
                "context": {"dry_principle": True, "create_utilities": True},
            },
            {
                "id": "verify_behavior",
                "type": "testing",
                "prompt": "Verify that refactoring preserves original behavior",
                "context": {"regression_tests": True, "performance_check": True},
            },
        ]

    @staticmethod
    def deployment_workflow() -> list[dict[str, Any]]:
        """Workflow for deployment preparation."""
        return [
            {
                "id": "pre_deployment_checks",
                "type": "testing",
                "prompt": "Run all pre-deployment checks and validations",
                "context": {"full_test_suite": True, "integration_tests": True},
            },
            {
                "id": "build_artifacts",
                "type": "implementation",
                "prompt": "Build deployment artifacts and verify integrity",
                "context": {"optimize_build": True, "security_scan": True},
            },
            {
                "id": "environment_setup",
                "type": "implementation",
                "prompt": "Prepare deployment environment and configurations",
                "context": {"environment": "production", "rollback_plan": True},
            },
            {
                "id": "health_checks",
                "type": "testing",
                "prompt": "Verify deployment health and system status",
                "context": {"monitoring": True, "alerts": True},
            },
        ]


class WorkflowExecutor:
    """Advanced workflow executor with error handling and recovery."""

    def __init__(self, project_path: str) -> None:
        self.agent = ClaudeAgent(project_path)
        self.execution_history = []
        self.checkpoints = {}

    async def execute_with_checkpoints(self, workflow: list[dict[str, Any]], checkpoint_interval: int = 2) -> dict[str, Any]:
        """Execute workflow with checkpoint saving."""
        results = {}

        for i, step in enumerate(workflow):
            try:
                # Execute step
                result = await self._execute_step(step)
                results[step["id"]] = result

                # Save checkpoint periodically
                if i % checkpoint_interval == 0:
                    await self._save_checkpoint(i, results, workflow)

                # Log progress
                self._log_progress(step, result)

            except Exception as e:
                # Handle error and attempt recovery
                recovery_result = await self._handle_error(step, e, results)

                if recovery_result:
                    results[step["id"]] = recovery_result
                else:
                    # Save failure state and exit
                    await self._save_failure_state(step, e, results)
                    raise

        return results

    async def _execute_step(self, step: dict[str, Any]) -> str:
        """Execute a single workflow step."""
        step_type = step.get("type", "general")
        prompt = step["prompt"]
        step.get("context", {})

        # Prepare custom prompt based on step type
        custom_prompts = {
            "analysis": "Perform detailed analysis with comprehensive insights",
            "implementation": "Implement following best practices and conventions",
            "testing": "Create thorough tests with good coverage",
            "deployment": "Prepare for production deployment with safety checks",
        }

        custom_prompt = custom_prompts.get(step_type, "Execute the requested task")

        # Execute through Claude CLI
        result = self.agent.claude_tool._run(prompt=prompt, custom_prompt=custom_prompt)

        return result

    async def _save_checkpoint(self, step_index: int, results: dict[str, Any], workflow: list[dict[str, Any]]) -> None:
        """Save execution checkpoint."""
        checkpoint = {
            "step_index": step_index,
            "results": results,
            "workflow": workflow,
            "timestamp": asyncio.get_event_loop().time(),
            "session_state": self.agent.session.current_context,
        }

        self.checkpoints[step_index] = checkpoint

    async def _handle_error(self, step: dict[str, Any], error: Exception, partial_results: dict[str, Any]) -> str:
        """Handle execution errors with recovery attempts."""
        # Log error
        error_info = {
            "step": step["id"],
            "error": str(error),
            "context": step.get("context", {}),
            "partial_results": len(partial_results),
        }

        self.execution_history.append(error_info)

        # Attempt recovery strategies
        recovery_strategies = [
            self._retry_with_simplified_prompt,
            self._retry_with_context_reset,
            self._skip_step_with_warning,
        ]

        for strategy in recovery_strategies:
            try:
                result = await strategy(step, error)
                if result:
                    return result
            except Exception as strategy_error:
                print(f"⚠️ Recovery strategy {strategy.__name__} failed: {strategy_error}")
                continue

        return None

    async def _retry_with_simplified_prompt(self, step: dict[str, Any], error: Exception) -> str:
        """Retry with a simplified version of the prompt."""
        simplified_prompt = f"Simple version: {step['prompt']}"

        result = self.agent.claude_tool._run(prompt=simplified_prompt, custom_prompt="Keep it simple and focused")

        return result

    async def _retry_with_context_reset(self, step: dict[str, Any], error: Exception) -> str:
        """Retry with fresh context (no session continuity)."""
        result = self.agent.claude_tool._run(prompt=step["prompt"], continue_session=False)

        return result

    async def _skip_step_with_warning(self, step: dict[str, Any], error: Exception) -> str:
        """Skip step with warning message."""
        return f"SKIPPED: {step['id']} - {str(error)}"

    async def _save_failure_state(
        self,
        failed_step: dict[str, Any],
        error: Exception,
        partial_results: dict[str, Any],
    ) -> None:
        """Save failure state for debugging."""
        failure_state = {
            "failed_step": failed_step,
            "error": str(error),
            "partial_results": partial_results,
            "session_state": self.agent.session.current_context,
            "execution_history": self.execution_history,
        }

        # Save to file for analysis
        import json

        with open("workflow_failure.json", "w", encoding="utf-8") as f:
            json.dump(failure_state, f, indent=2, default=str)

    def _log_progress(self, step: dict[str, Any], result: str) -> None:
        """Log workflow progress."""
        progress_info = {
            "step_id": step["id"],
            "step_type": step.get("type", "general"),
            "success": bool(result and "Error:" not in result),
            "result_length": len(result) if result else 0,
        }

        self.execution_history.append(progress_info)


# Example usage functions
async def run_code_review() -> None:
    """Run automated code review workflow."""
    executor = WorkflowExecutor("/path/to/your/project")
    workflow = WorkflowTemplates.code_review_workflow()

    results = await executor.execute_with_checkpoints(workflow)
    return results


async def run_feature_development() -> None:
    """Run feature development workflow."""
    executor = WorkflowExecutor("/path/to/your/project")
    workflow = WorkflowTemplates.feature_development_workflow()

    results = await executor.execute_with_checkpoints(workflow)
    return results


async def run_refactoring() -> None:
    """Run refactoring workflow."""
    executor = WorkflowExecutor("/path/to/your/project")
    workflow = WorkflowTemplates.refactoring_workflow()

    results = await executor.execute_with_checkpoints(workflow)
    return results


if __name__ == "__main__":
    # Example: Run code review workflow
    asyncio.run(run_code_review())
