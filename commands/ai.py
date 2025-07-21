# Copyright notice.

import asyncio
import time
from pathlib import Path
from typing import Any
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from libs.ai.adaptive_response import AdaptiveResponse
from libs.ai.response_analyzer import ResponseAnalyzer
from libs.core.base_command import BaseCommand, CommandError, ConfigCommandMixin

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""AI learning system management commands."""





class AIStatusCommand(BaseCommand):
    """Show AI learning system status."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()
        self.adaptive: AdaptiveResponse | None = None

    def validate_preconditions(self) -> None:
        """Validate command preconditions.

        """
        super().validate_preconditions()
        try:
            self.adaptive = AdaptiveResponse()
        except Exception as e:
            msg = f"Failed to initialize AI components: {e}"
            raise CommandError(msg) from e

    def execute(self, **kwargs: dict[str, object]) -> dict:  # noqa: ARG002
        """Execute the status command.

        Returns:
        dict: Description of return value.
        """
        try:
            # Get statistics
            stats: dict[str, object] = self.adaptive.get_learning_statistics()

            # Create status table
            table = Table(title="🤖 AI Learning System Status", show_header=True)
            table.add_column("Component", style="cyan", width=25)
            table.add_column("Status", style="white", width=40)

            # Basic info
            table.add_row("Total Responses", str(stats.get("total_responses", 0)))
            table.add_row("Learned Patterns", str(stats.get("total_patterns", 0)))
            table.add_row("Recent Activity (7 days)", str(stats.get("recent_activity", 0)))

            # Configuration
            config = stats.get("adaptive_config", {})
            table.add_row(
                "Auto-Response",
                "✅ Enabled" if config.get("auto_response_enabled") else "❌ Disabled",
            )
            table.add_row(
                "Learning",
                "✅ Enabled" if config.get("learning_enabled") else "❌ Disabled",
            )
            table.add_row(
                "Confidence Threshold",
                f"{config.get('min_confidence_threshold', 0.6):.2f}",
            )

            # Runtime info
            runtime = stats.get("runtime_info", {})
            table.add_row("Response Queue", str(runtime.get("response_queue_size", 0)))
            table.add_row("Cache Size", str(runtime.get("cache_size", 0)))

            self.console.print(table)

            # Response type distribution
            if "response_types" in stats:
                self.console.print("\n📊 Response Type Distribution:")
                types_table = Table(show_header=True)
                types_table.add_column("Type", style="yellow")
                types_table.add_column("Count", style="green", justify="right")

                for response_type, count in stats["response_types"].items():
                    types_table.add_row(response_type, str(count))

                self.console.print(types_table)

            # Project distribution
            if "project_distribution" in stats:
                self.console.print("\n🏗️ Project Distribution:")
                projects_table = Table(show_header=True)
                projects_table.add_column("Project", style="blue")
                projects_table.add_column("Responses", style="green", justify="right")

                for project, count in stats["project_distribution"].items():
                    projects_table.add_row(project, str(count))

                self.console.print(projects_table)

            return stats

        except Exception as e:
            msg = f"Error getting AI status: {e}"
            raise CommandError(msg) from e


class AIConfigCommand(BaseCommand, ConfigCommandMixin):
    """Configure AI learning system settings."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()
        self.adaptive: AdaptiveResponse | None = None

    def validate_preconditions(self) -> None:
        """Validate command preconditions.

        """
        super().validate_preconditions()
        try:
            self.adaptive = AdaptiveResponse()
        except Exception as e:
            msg = f"Failed to initialize AI components: {e}"
            raise CommandError(msg) from e

    def execute(self, **kwargs: dict[str, object]) -> dict:
        """Execute the command.

        Returns:
        dict: Description of return value.
        """
        # Extract parameters from kwargs

        threshold = kwargs.get("threshold")

        auto_response = kwargs.get("auto_response")

        learning = kwargs.get("learning")
        """Execute the config command."""
        changes = []

        if threshold is not None:
            if 0.0 <= threshold <= 1.0:
                self.adaptive.adjust_confidence_threshold(threshold)
                changes.append(f"Confidence threshold set to {threshold:.2f}")
            else:
                msg = "Threshold must be between 0.0 and 1.0"
                raise CommandError(msg)

        if auto_response is not None:
            self.adaptive.enable_auto_response(auto_response)
            status = "enabled" if auto_response else "disabled"
            changes.append(f"Auto-response {status}")

        if learning is not None:
            self.adaptive.enable_learning(learning)
            status = "enabled" if learning else "disabled"
            changes.append(f"Learning {status}")

        if changes:
            self.print_success("Configuration updated:")
            for change in changes:
                self.console.print(f"  • {change}")
        else:
            self.print_info("No configuration changes specified")

        return {"changes": changes}


class AIHistoryCommand(BaseCommand):
    """Show AI response history."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()
        self.analyzer: ResponseAnalyzer | None = None

    def validate_preconditions(self) -> None:
        """Validate command preconditions.

        """
        super().validate_preconditions()
        try:
            self.analyzer = ResponseAnalyzer()
        except Exception as e:
            msg = f"Failed to initialize AI components: {e}"
            raise CommandError(msg) from e

    def execute(self, **kwargs: dict[str, object]) -> dict:
        """Execute the command.

        Returns:
        dict: Description of return value.
        """
        # Extract parameters from kwargs

        limit = kwargs.get("limit", 10)

        type = kwargs.get("type")

        project = kwargs.get("project")
        """Execute the history command."""
        # Get filtered response history
        history = self.analyzer.response_history[-limit:]

        # Apply filters
        if type:
            history = [r for r in history if r.prompt_type == type]
        if project:
            history = [r for r in history if r.project_name == project]

        if not history:
            self.console.print("📭 No response history found")
            return {"history": []}

        # Create history table
        table = Table(title=f"📚 AI Response History (last {len(history)})", show_header=True)
        table.add_column("Time", style="dim", width=12)
        table.add_column("Type", style="yellow", width=15)
        table.add_column("Prompt", style="white", width=40)
        table.add_column("Response", style="green", width=10)
        table.add_column("Project", style="blue", width=15)

        for record in reversed(history):  # Show most recent first
            time_str = time.strftime("%H:%M:%S", time.localtime(record.timestamp))

            # Truncate long prompts
            prompt = record.prompt_text[:37] + "..." if len(record.prompt_text) > 40 else record.prompt_text

            table.add_row(
                time_str,
                record.prompt_type,
                prompt,
                record.user_response,
                record.project_name or "global",
            )

        self.console.print(table)
        return {"history": history}


class AIExportCommand(BaseCommand):
    """Export AI learning data."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()
        self.adaptive: AdaptiveResponse | None = None

    def validate_preconditions(self) -> None:
        """Validate command preconditions.

        """
        super().validate_preconditions()
        try:
            self.adaptive = AdaptiveResponse()
        except Exception as e:
            msg = f"Failed to initialize AI components: {e}"
            raise CommandError(msg) from e

    def execute(self, **kwargs: dict[str, object]) -> dict:
        """Execute the command.

        Returns:
        dict: Description of return value.
        """
        # Extract parameters from kwargs

        output = kwargs.get("output")
        """Execute the export command."""
        if not output:
            timestamp = int(time.time())
            output = f"yesman_ai_export_{timestamp}.json"

        output_path = Path(output)

        if self.adaptive.export_learning_data(output_path):
            self.print_success(f"AI learning data exported to: {output_path}")
            return {"output_path": str(output_path), "success": True}
        msg = "Failed to export AI learning data"
        raise CommandError(msg) from None


class AICleanupCommand(BaseCommand):
    """Clean up old AI learning data."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()
        self.analyzer: ResponseAnalyzer | None = None

    def validate_preconditions(self) -> None:
        """Validate command preconditions.

        """
        super().validate_preconditions()
        try:
            self.analyzer = ResponseAnalyzer()
        except Exception as e:
            msg = f"Failed to initialize AI components: {e}"
            raise CommandError(msg) from e

    def execute(self, **kwargs: dict[str, object]) -> dict:
        """Execute the command.

        Returns:
        dict: Description of return value.
        """
        # Extract parameters from kwargs

        days = kwargs.get("days", 30)
        """Execute the cleanup command."""
        removed_count = self.analyzer.cleanup_old_data(days_to_keep=days)

        if removed_count > 0:
            self.print_success(f"Cleaned up {removed_count} old response records")
            self.console.print(f"   Kept data from last {days} days")
        else:
            self.print_info("No old data to clean up")

        return {"removed_count": removed_count, "days_kept": days}


class AIPredictCommand(BaseCommand):
    """Predict response for a given prompt."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()
        self.adaptive: AdaptiveResponse | None = None

    def validate_preconditions(self) -> None:
        """Validate command preconditions.

        """
        super().validate_preconditions()
        try:
            self.adaptive = AdaptiveResponse()
        except Exception as e:
            msg = f"Failed to initialize AI components: {e}"
            raise CommandError(msg) from e

    def execute(self, **kwargs: dict[str, object]) -> dict:
        """Execute the command.

        Returns:
        dict: Description of return value.
        """
        # Extract parameters from kwargs

        prompt_text = kwargs["prompt_text"]

        context = kwargs.get("context", "")

        project = kwargs.get("project")
        """Execute the predict command."""
        # Get prediction (run async function synchronously)
        should_respond, predicted_response, confidence = asyncio.run(
            self.adaptive.should_auto_respond(prompt_text, context, project),
        )

        # Create prediction panel
        prediction_text = Text()
        prediction_text.append("Prompt: ", style="bold cyan")
        prediction_text.append(f"{prompt_text}\n", style="white")

        if context:
            prediction_text.append("Context: ", style="bold yellow")
            prediction_text.append(f"{context}\n", style="dim")

        if project:
            prediction_text.append("Project: ", style="bold blue")
            prediction_text.append(f"{project}\n", style="dim")

        prediction_text.append("\nPredicted Response: ", style="bold green")
        prediction_text.append(f"{predicted_response}\n", style="green")

        prediction_text.append("Confidence: ", style="bold magenta")
        prediction_text.append(f"{confidence:.2%}\n", style="magenta")

        prediction_text.append("Auto-respond: ", style="bold")
        if should_respond:
            prediction_text.append("✅ Yes", style="green")
        else:
            prediction_text.append("❌ No", style="red")

        panel = Panel(prediction_text, title="🔮 AI Response Prediction", border_style="blue")
        self.console.print(panel)

        return {
            "should_respond": should_respond,
            "predicted_response": predicted_response,
            "confidence": confidence,
        }


@click.group()
def ai() -> None:
    """AI learning system management.

    """


@ai.command()
def status() -> None:
    """Show AI learning system status.

    """
    command = AIStatusCommand()
    command.run()


@ai.command()
@click.option("--threshold", "-t", type=float, help="New confidence threshold (0.0-1.0)")
@click.option(
    "--auto-response/--no-auto-response",
    default=None,
    help="Enable/disable auto-response",
)
@click.option("--learning/--no-learning", default=None, help="Enable/disable learning")
def config(threshold: float | None, auto_response: bool | None, learning: bool | None) -> None:  # noqa: FBT001
    """Configure AI learning system settings.

    """
    command = AIConfigCommand()
    command.run(threshold=threshold, auto_response=auto_response, learning=learning)


@ai.command()
@click.option("--limit", "-l", default=10, type=int, help="Number of recent responses to show")
@click.option("--type", "-t", help="Filter by prompt type")
@click.option("--project", "-p", help="Filter by project name")
def history(limit: int, type: str | None, project: str | None) -> None:
    """Show AI response history.

    """
    command = AIHistoryCommand()
    command.run(limit=limit, type=type, project=project)


@ai.command()
@click.option("--output", "-o", help="Output file path for exported data")
def export(output: str | None) -> None:
    """Export AI learning data.

    """
    command = AIExportCommand()
    command.run(output=output)


@ai.command()
@click.option("--days", "-d", default=30, type=int, help="Days of data to keep (default: 30)")
def cleanup(days: int) -> None:
    """Clean up old AI learning data.

    """
    command = AICleanupCommand()
    command.run(days=days)


@ai.command()
@click.argument("prompt_text")
@click.option("--context", "-c", default="", help="Context for the prompt")
@click.option("--project", "-p", help="Project name")
def predict(prompt_text: str, context: str, project: str | None) -> None:
    """Predict response for a given prompt.

    """
    command = AIPredictCommand()
    command.run(prompt_text=prompt_text, context=context, project=project)


if __name__ == "__main__":
    ai()
