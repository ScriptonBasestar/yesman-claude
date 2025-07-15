"""AI learning system management commands"""

import time
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from libs.ai.adaptive_response import AdaptiveResponse
from libs.ai.response_analyzer import ResponseAnalyzer


@click.group()
def ai():
    """AI learning system management"""
    pass


@ai.command()
def status():
    """Show AI learning system status"""
    console = Console()

    try:
        # Initialize AI components
        # analyzer = ResponseAnalyzer()  # Not used in this function
        adaptive = AdaptiveResponse()

        # Get statistics
        stats = adaptive.get_learning_statistics()

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
        table.add_row("Confidence Threshold", f"{config.get('min_confidence_threshold', 0.6):.2f}")

        # Runtime info
        runtime = stats.get("runtime_info", {})
        table.add_row("Response Queue", str(runtime.get("response_queue_size", 0)))
        table.add_row("Cache Size", str(runtime.get("cache_size", 0)))

        console.print(table)

        # Response type distribution
        if "response_types" in stats:
            console.print("\\n📊 Response Type Distribution:")
            types_table = Table(show_header=True)
            types_table.add_column("Type", style="yellow")
            types_table.add_column("Count", style="green", justify="right")

            for response_type, count in stats["response_types"].items():
                types_table.add_row(response_type, str(count))

            console.print(types_table)

        # Project distribution
        if "project_distribution" in stats:
            console.print("\\n🏗️ Project Distribution:")
            projects_table = Table(show_header=True)
            projects_table.add_column("Project", style="blue")
            projects_table.add_column("Responses", style="green", justify="right")

            for project, count in stats["project_distribution"].items():
                projects_table.add_row(project, str(count))

            console.print(projects_table)

    except Exception as e:
        console.print(f"[red]Error getting AI status: {e}[/]")


@ai.command()
@click.option("--threshold", "-t", type=float, help="New confidence threshold (0.0-1.0)")
@click.option(
    "--auto-response/--no-auto-response",
    default=None,
    help="Enable/disable auto-response",
)
@click.option("--learning/--no-learning", default=None, help="Enable/disable learning")
def config(threshold, auto_response, learning):
    """Configure AI learning system settings"""
    console = Console()

    try:
        adaptive = AdaptiveResponse()

        changes = []

        if threshold is not None:
            if 0.0 <= threshold <= 1.0:
                adaptive.adjust_confidence_threshold(threshold)
                changes.append(f"Confidence threshold set to {threshold:.2f}")
            else:
                console.print("[red]Error: Threshold must be between 0.0 and 1.0[/]")
                return

        if auto_response is not None:
            adaptive.enable_auto_response(auto_response)
            status = "enabled" if auto_response else "disabled"
            changes.append(f"Auto-response {status}")

        if learning is not None:
            adaptive.enable_learning(learning)
            status = "enabled" if learning else "disabled"
            changes.append(f"Learning {status}")

        if changes:
            console.print("✅ Configuration updated:")
            for change in changes:
                console.print(f"  • {change}")
        else:
            console.print("ℹ️ No configuration changes specified")

    except Exception as e:
        console.print(f"[red]Error updating configuration: {e}[/]")


@ai.command()
@click.option("--limit", "-l", default=10, type=int, help="Number of recent responses to show")
@click.option("--type", "-t", help="Filter by prompt type")
@click.option("--project", "-p", help="Filter by project name")
def history(limit, type, project):
    """Show AI response history"""
    console = Console()

    try:
        analyzer = ResponseAnalyzer()

        # Get filtered response history
        history = analyzer.response_history[-limit:]

        # Apply filters
        if type:
            history = [r for r in history if r.prompt_type == type]
        if project:
            history = [r for r in history if r.project_name == project]

        if not history:
            console.print("📭 No response history found")
            return

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

        console.print(table)

    except Exception as e:
        console.print(f"[red]Error retrieving history: {e}[/]")


@ai.command()
@click.option("--output", "-o", help="Output file path for exported data")
def export(output):
    """Export AI learning data"""
    console = Console()

    try:
        adaptive = AdaptiveResponse()

        if not output:
            timestamp = int(time.time())
            output = f"yesman_ai_export_{timestamp}.json"

        output_path = Path(output)

        if adaptive.export_learning_data(output_path):
            console.print(f"✅ AI learning data exported to: {output_path}")
        else:
            console.print("[red]❌ Failed to export AI learning data[/]")

    except Exception as e:
        console.print(f"[red]Error exporting data: {e}[/]")


@ai.command()
@click.option("--days", "-d", default=30, type=int, help="Days of data to keep (default: 30)")
def cleanup(days):
    """Clean up old AI learning data"""
    console = Console()

    try:
        analyzer = ResponseAnalyzer()

        removed_count = analyzer.cleanup_old_data(days_to_keep=days)

        if removed_count > 0:
            console.print(f"✅ Cleaned up {removed_count} old response records")
            console.print(f"   Kept data from last {days} days")
        else:
            console.print("ℹ️ No old data to clean up")

    except Exception as e:
        console.print(f"[red]Error cleaning up data: {e}[/]")


@ai.command()
@click.argument("prompt_text")
@click.option("--context", "-c", default="", help="Context for the prompt")
@click.option("--project", "-p", help="Project name")
def predict(prompt_text, context, project):
    """Predict response for a given prompt"""
    import asyncio

    console = Console()

    try:
        adaptive = AdaptiveResponse()

        # Get prediction (run async function synchronously)
        should_respond, predicted_response, confidence = asyncio.run(
            adaptive.should_auto_respond(prompt_text, context, project),
        )

        # Create prediction panel
        prediction_text = Text()
        prediction_text.append("Prompt: ", style="bold cyan")
        prediction_text.append(f"{prompt_text}\\n", style="white")

        if context:
            prediction_text.append("Context: ", style="bold yellow")
            prediction_text.append(f"{context}\\n", style="dim")

        if project:
            prediction_text.append("Project: ", style="bold blue")
            prediction_text.append(f"{project}\\n", style="dim")

        prediction_text.append("\\nPredicted Response: ", style="bold green")
        prediction_text.append(f"{predicted_response}\\n", style="green")

        prediction_text.append("Confidence: ", style="bold magenta")
        prediction_text.append(f"{confidence:.2%}\\n", style="magenta")

        prediction_text.append("Auto-respond: ", style="bold")
        if should_respond:
            prediction_text.append("✅ Yes", style="green")
        else:
            prediction_text.append("❌ No", style="red")

        panel = Panel(prediction_text, title="🔮 AI Response Prediction", border_style="blue")
        console.print(panel)

    except Exception as e:
        console.print(f"[red]Error making prediction: {e}[/]")


if __name__ == "__main__":
    ai()
