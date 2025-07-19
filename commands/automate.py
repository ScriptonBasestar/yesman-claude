"""Context-aware automation and workflow management commands."""

import asyncio
import json
import time
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from rich.table import Table

from libs.automation.automation_manager import AutomationManager
from libs.automation.context_detector import ContextType
from libs.core.base_command import BaseCommand, CommandError, ConfigCommandMixin


class AutomateStatusCommand(BaseCommand):
    """Show automation system status."""

    def __init__(self):
        super().__init__()
        self.console = Console()

    def execute(self, project_path: str = ".", **kwargs) -> dict[str, Any]:
        """Execute the status command."""
        try:
            project_path_obj = Path(project_path).resolve()
            automation_manager = AutomationManager(project_path_obj)

            # Get current status
            stats = automation_manager.stats

            # Create status overview
            overview = Panel(
                f"Project: {project_path_obj.name}\n"
                f"Monitoring: {'✅ Active' if automation_manager.is_monitoring else '❌ Inactive'}\n"
                f"Uptime: {self._format_duration(time.time() - stats['start_time'])}\n"
                f"Contexts Detected: {stats['contexts_detected']}\n"
                f"Workflows Triggered: {stats['workflows_triggered']}\n"
                f"Workflows Completed: {stats['workflows_completed']}",
                title="🤖 Automation Status",
                border_style="blue",
            )
            self.console.print(overview)

            # Show available context types
            context_table = Table(title="📊 Context Detection Capabilities", show_header=True)
            context_table.add_column("Context Type", style="cyan")
            context_table.add_column("Description", style="white")
            context_table.add_column("Triggers", style="yellow")

            context_info = {
                ContextType.GIT_COMMIT: (
                    "Git Commit",
                    "Detects new commits",
                    "commit hooks, git log",
                ),
                ContextType.TEST_FAILURE: (
                    "Test Failure",
                    "Detects failing tests",
                    "test output, CI status",
                ),
                ContextType.BUILD_FAILURE: (
                    "Build Failure",
                    "Detects build failures",
                    "build scripts, CI",
                ),
                ContextType.DEPENDENCY_UPDATE: (
                    "Dependencies",
                    "Detects dependency changes",
                    "package files",
                ),
                ContextType.ERROR_DETECTED: (
                    "Error",
                    "Detects runtime errors",
                    "log analysis",
                ),
                ContextType.FILE_CHANGE: (
                    "File Change",
                    "Detects file modifications",
                    "file system events",
                ),
                ContextType.DEPLOYMENT_READY: (
                    "Deployment Ready",
                    "Detects deployment readiness",
                    "deploy scripts",
                ),
                ContextType.CODE_REVIEW: (
                    "Code Review",
                    "Detects review requests",
                    "PR/MR events",
                ),
            }

            for _context_type, (name, desc, triggers) in context_info.items():
                context_table.add_row(name, desc, triggers)

            self.console.print(context_table)

            # Show workflow chains
            workflows = automation_manager.workflow_engine.workflows
            if workflows:
                self.console.print("\n🔗 Available Workflow Chains:")
                for chain_name in workflows:
                    self.console.print(f"  • {chain_name}")
            else:
                self.console.print("\n📝 No workflow chains configured")

            return stats

        except Exception as e:
            raise CommandError(f"Error getting automation status: {e}") from e

    def _format_duration(self, seconds: float) -> str:
        """Format duration in human readable format."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds / 60)}m {int(seconds % 60)}s"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            return f"{hours}h {minutes}m"


class AutomateMonitorCommand(BaseCommand):
    """Start context monitoring and automation."""

    def __init__(self):
        super().__init__()
        self.console = Console()

    def execute(self, project_path: str = ".", interval: int = 10, **kwargs) -> dict[str, Any]:
        """Execute the monitor command."""
        try:
            project_path_obj = Path(project_path).resolve()
            automation_manager = AutomationManager(project_path_obj)

            self.console.print(f"🚀 Starting automation monitoring for {project_path_obj.name}")
            self.console.print(f"Detection interval: {interval} seconds")
            self.console.print("Press Ctrl+C to stop monitoring")
            self.console.print("=" * 60)

            # Add callback for events
            def on_context_detected(context_info):
                self.console.print(f"[yellow]🔍 Context detected: {context_info.context_type.value}[/]")
                self.console.print(f"   Details: {context_info.description}")

            def on_workflow_triggered(workflow_name, context):
                self.console.print(f"[cyan]⚡ Workflow triggered: {workflow_name}[/]")
                self.console.print(f"   Context: {context.context_type.value}")

            def on_workflow_completed(workflow_name, success, results):
                status = "✅ Success" if success else "❌ Failed"
                self.console.print(f"[green]{status}: {workflow_name}[/]")
                if results:
                    self.console.print(f"   Results: {results}")

            automation_manager.add_callback("context_detected", on_context_detected)
            automation_manager.add_callback("workflow_triggered", on_workflow_triggered)
            automation_manager.add_callback("workflow_completed", on_workflow_completed)

            # Start monitoring
            async def run_monitoring():
                await automation_manager.start_monitoring(monitor_interval=interval)

            asyncio.run(run_monitoring())
            return {"monitoring_started": True}

        except KeyboardInterrupt:
            self.print_warning("Automation monitoring stopped")
            return {"monitoring_started": False, "stopped": True}
        except Exception as e:
            raise CommandError(f"Error during monitoring: {e}") from e


class AutomateTriggerCommand(BaseCommand):
    """Manually trigger automation for a specific context."""

    def __init__(self):
        super().__init__()
        self.console = Console()

    def execute(
        self,
        project_path: str = ".",
        context_type: str = None,
        description: str = "Manual trigger",
        **kwargs,
    ) -> dict[str, Any]:
        """Execute the trigger command."""
        if not context_type:
            raise CommandError("Context type is required")

        try:
            project_path_obj = Path(project_path).resolve()
            automation_manager = AutomationManager(project_path_obj)

            # Convert string to enum
            context_enum = ContextType(context_type)

            self.console.print(f"🎯 Manually triggering automation for context: {context_type}")
            self.console.print(f"Description: {description}")

            # Simulate context detection
            async def trigger_automation():
                import time

                from libs.automation.context_detector import ContextInfo

                # Create a context info object
                context_info = ContextInfo(context_type=context_enum, confidence=1.0, details={"description": description, "manual": True}, timestamp=time.time())

                # Trigger workflows for this context
                triggered_workflows = automation_manager.workflow_engine.trigger_workflows(context_info)
                return {"triggered_workflows": triggered_workflows}

            result = asyncio.run(trigger_automation())

            if result:
                self.print_success("Automation triggered successfully")
                self.console.print(f"Workflows executed: {len(result)}")
                for workflow_name, success in result.items():
                    status = "✅" if success else "❌"
                    self.console.print(f"  {status} {workflow_name}")
            else:
                self.print_warning("No workflows triggered for this context")

            return {"result": result, "triggered": bool(result)}

        except Exception as e:
            raise CommandError(f"Error triggering automation: {e}") from e


class AutomateExecuteCommand(BaseCommand):
    """Execute a specific workflow chain."""

    def __init__(self):
        super().__init__()
        self.console = Console()

    def execute(self, workflow_name: str = None, project_path: str = ".", **kwargs) -> dict[str, Any]:
        """Execute the workflow command."""
        # Handle workflow_name from kwargs if not provided as positional argument
        if workflow_name is None:
            workflow_name = kwargs.get("workflow_name")

        if not workflow_name:
            raise CommandError("workflow_name is required")

        try:
            project_path_obj = Path(project_path).resolve()
            automation_manager = AutomationManager(project_path_obj)

            self.console.print(f"⚡ Executing workflow: {workflow_name}")

            async def run_workflow():
                import time

                from libs.automation.context_detector import ContextInfo, ContextType

                # Create a dummy context for manual execution
                context_info = ContextInfo(context_type=ContextType.UNKNOWN, confidence=1.0, details={"manual_execution": True, "workflow_name": workflow_name}, timestamp=time.time())

                # Use manual trigger workflow
                execution_id = await automation_manager.manual_trigger_workflow(workflow_name, context_info)

                if execution_id:
                    return True, {"execution_id": execution_id}
                else:
                    return False, {"error": "Failed to start workflow"}

            success, results = asyncio.run(run_workflow())

            if success:
                self.print_success(f"Workflow '{workflow_name}' completed successfully")
            else:
                self.print_error(f"Workflow '{workflow_name}' failed")

            if results:
                self.console.print("Results:")
                for step, result in results.items():
                    self.console.print(f"  {step}: {result}")

            return {"success": success, "results": results}

        except Exception as e:
            raise CommandError(f"Error executing workflow: {e}") from e


class AutomateDetectCommand(BaseCommand):
    """Run context detection once and show results."""

    def __init__(self):
        super().__init__()
        self.console = Console()

    def execute(self, project_path: str = ".", **kwargs) -> dict[str, Any]:
        """Execute the detect command."""
        try:
            project_path_obj = Path(project_path).resolve()
            automation_manager = AutomationManager(project_path_obj)

            # Add progress indicator for context detection
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold yellow]{task.description}"),
                TimeElapsedColumn(),
                transient=True,
            ) as progress:
                detection_task = progress.add_task(
                    f"🔍 Running context detection for {project_path_obj.name}...",
                    total=None,
                )

                async def run_detection():
                    contexts = await automation_manager._detect_all_contexts()
                    return contexts

                contexts = asyncio.run(run_detection())
                progress.update(detection_task, description="✅ Context detection completed")

            if not contexts:
                self.print_info("No contexts detected")
                return {"contexts": []}

            # Display detected contexts
            table = Table(title="🎯 Detected Contexts", show_header=True)
            table.add_column("Type", style="cyan")
            table.add_column("Description", style="white")
            table.add_column("Confidence", style="green", justify="center")
            table.add_column("Data", style="yellow")

            for context in contexts:
                data_summary = str(context.details)[:50] + "..." if len(str(context.details)) > 50 else str(context.details)
                table.add_row(
                    context.context_type.value,
                    context.details.get("description", "No description"),
                    f"{context.confidence:.1%}",
                    data_summary,
                )

            self.console.print(table)

            # Show potential workflows
            self.console.print("\n🔗 Potential Workflows:")
            for context in contexts:
                # Find workflows that match this context type
                matching_workflows = []
                for workflow_name, workflow in automation_manager.workflow_engine.workflows.items():
                    if context.context_type in workflow.trigger_contexts:
                        matching_workflows.append(workflow_name)

                if matching_workflows:
                    self.console.print(f"  {context.context_type.value}: {', '.join(matching_workflows)}")
                else:
                    self.console.print(f"  {context.context_type.value}: No workflows configured")

            return {"contexts": contexts}

        except Exception as e:
            raise CommandError(f"Error during context detection: {e}") from e


class AutomateConfigCommand(BaseCommand, ConfigCommandMixin):
    """Generate workflow configuration template."""

    def __init__(self):
        super().__init__()
        self.console = Console()

    def execute(self, project_path: str = ".", output: str | None = None, **kwargs) -> dict[str, Any]:
        """Execute the config command."""
        try:
            # Generate sample workflow configuration
            sample_config = {
                "workflows": {
                    "git-commit-workflow": {
                        "triggers": ["git_commit"],
                        "steps": [
                            {
                                "name": "run_tests",
                                "command": "npm test",
                                "on_failure": "notify",
                            },
                            {
                                "name": "check_build",
                                "command": "npm run build",
                                "depends_on": ["run_tests"],
                            },
                            {
                                "name": "deploy_if_green",
                                "command": "npm run deploy",
                                "depends_on": ["run_tests", "check_build"],
                                "condition": "all_success",
                            },
                        ],
                    },
                    "test-failure-workflow": {
                        "triggers": ["test_failure"],
                        "steps": [
                            {
                                "name": "analyze_failure",
                                "command": "npm run test:analyze",
                            },
                            {
                                "name": "notify_team",
                                "command": "slack-notify 'Tests failing'",
                            },
                        ],
                    },
                    "dependency-update-workflow": {
                        "triggers": ["dependency_update"],
                        "steps": [
                            {
                                "name": "backup_lockfile",
                                "command": "cp package-lock.json package-lock.json.bak",
                            },
                            {
                                "name": "run_tests",
                                "command": "npm test",
                            },
                            {
                                "name": "rollback_if_fail",
                                "command": "mv package-lock.json.bak package-lock.json",
                                "condition": "previous_failed",
                            },
                        ],
                    },
                },
            }

            config_json = json.dumps(sample_config, indent=2)

            if output:
                output_path = Path(output)
                output_path.write_text(config_json)
                self.print_success(f"Workflow configuration written to: {output_path}")
            else:
                self.console.print("📝 Sample Workflow Configuration:")
                self.console.print(config_json)

            return {"config": sample_config, "output": output}

        except Exception as e:
            raise CommandError(f"Error generating configuration: {e}") from e


@click.group()
def automate():
    """Context-aware automation and workflow management."""
    pass


@automate.command()
@click.option("--project-path", "-p", default=".", help="Project directory path")
def status(project_path):
    """Show automation system status."""
    command = AutomateStatusCommand()
    command.run(project_path=project_path)


@automate.command()
@click.option("--project-path", "-p", default=".", help="Project directory path")
@click.option("--interval", "-i", default=10, type=int, help="Detection interval in seconds")
def monitor(project_path, interval):
    """Start context monitoring and automation."""
    command = AutomateMonitorCommand()
    command.run(project_path=project_path, interval=interval)


@automate.command()
@click.option("--project-path", "-p", default=".", help="Project directory path")
@click.option(
    "--context-type",
    "-c",
    required=True,
    type=click.Choice([ct.value for ct in ContextType]),
    help="Context type to simulate",
)
@click.option("--description", "-d", default="Manual trigger", help="Context description")
def trigger(project_path, context_type, description):
    """Manually trigger automation for a specific context."""
    command = AutomateTriggerCommand()
    command.run(project_path=project_path, context_type=context_type, description=description)


@automate.command()
@click.argument("workflow_name")
@click.option("--project-path", "-p", default=".", help="Project directory path")
def execute(workflow_name, project_path):
    """Execute a specific workflow chain."""
    command = AutomateExecuteCommand()
    command.run(workflow_name=workflow_name, project_path=project_path)


@automate.command()
@click.option("--project-path", "-p", default=".", help="Project directory path")
def detect(project_path):
    """Run context detection once and show results."""
    command = AutomateDetectCommand()
    command.run(project_path=project_path)


@automate.command()
@click.option("--project-path", "-p", default=".", help="Project directory path")
@click.option("--output", "-o", help="Output file for workflow configuration")
def config(project_path, output):
    """Generate workflow configuration template."""
    command = AutomateConfigCommand()
    command.run(project_path=project_path, output=output)


if __name__ == "__main__":
    automate()
