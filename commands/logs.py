# Copyright notice.

import gzip
import json
import time
from collections import defaultdict
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from libs.core.base_command import BaseCommand, CommandError
from libs.logging import AsyncLogger, AsyncLoggerConfig, LogLevel

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Log management and analysis commands."""


class LogsConfigureCommand(BaseCommand):
    """Configure async logging system."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()

    def execute(
        self,
        output_dir: str = "~/.scripton/yesman/logs",
        format: str = "json",
        compression: bool = False,
        buffer_size: int = 1000,
        **kwargs: Any,
    ) -> dict:
        """Execute the configure command.

        Returns:
            Dict containing.
        """
        try:
            # Expand home directory
            output_path = Path(output_dir).expanduser()
            output_path.mkdir(parents=True, exist_ok=True)

            # Create configuration
            config = AsyncLoggerConfig(
                output_dir=output_path,
                log_format=format,
                flush_interval=5.0,
            )

            # Initialize logger to test configuration
            async_logger = AsyncLogger(config)

            self.print_success("Async logging configured successfully")
            self.print_info(f"  Output directory: {output_path}")
            self.print_info(f"  Format: {format}")
            self.print_info(f"  Compression: {'enabled' if compression else 'disabled'}")
            self.print_info(f"  Buffer size: {buffer_size}")

            # Test log entry
            async_logger.log(
                LogLevel.INFO,
                "Async logging system configured",
                extra_data={
                    "config_test": True,
                    "timestamp": time.time(),
                },
            )

            self.print_info("\n🔍 Test log entry written")

            return {
                "output_directory": str(output_path),
                "format": format,
                "compression": compression,
                "buffer_size": buffer_size,
                "success": True,
            }

        except Exception as e:
            msg = f"Error configuring logging: {e}"
            raise CommandError(msg) from e


class LogsAnalyzeCommand(BaseCommand):
    """Analyze log files and show statistics."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()

    def execute(
        self,
        log_dir: str = "~/.scripton/yesman/logs",
        last_hours: int = 24,
        level: str | None = None,
        **kwargs: Any,
    ) -> dict:
        """Execute the analyze command.

        Returns:
            Dict containing.
        """
        try:
            log_path = Path(log_dir).expanduser()

            if not log_path.exists():
                msg = f"Log directory not found: {log_path}"
                raise CommandError(msg)

            # Find log files
            log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.jsonl")) + list(log_path.glob("*.log.gz"))

            if not log_files:
                self.print_warning("No log files found")
                return {"files_found": 0, "stats": {}}

            # Analyze logs
            stats = self._analyze_log_files(log_files, last_hours, level)

            # Display statistics
            self._display_log_statistics(stats)

            return {"files_found": len(log_files), "stats": stats}

        except Exception as e:
            msg = f"Error analyzing logs: {e}"
            raise CommandError(msg) from e

    def _analyze_log_files(self, log_files: list[Path], last_hours: int, level_filter: str | None = None) -> dict[str, object]:
        """Analyze log files and return statistics.

        Returns:
        object: Description of return value.
        """
        stats: dict[str, object] = {
            "total_entries": 0,
            "level_counts": defaultdict(int),
            "hourly_counts": defaultdict(int),
            "error_messages": [],
            "performance_metrics": [],
        }

        cutoff_time = time.time() - (last_hours * 3600)

        for log_file in log_files:
            try:
                # Handle compressed files
                opener = gzip.open if log_file.suffix == ".gz" else open

                with opener(log_file, "rt", encoding="utf-8") as f:
                    for raw_line in f:
                        line = raw_line.strip()
                        if not line:
                            continue

                        try:
                            # Try to parse as JSON
                            entry = json.loads(line)
                            timestamp = entry.get("timestamp", 0)

                            # Filter by time
                            if timestamp < cutoff_time:
                                continue

                            level = entry.get("level", "UNKNOWN")

                            # Filter by level
                            if level_filter and level != level_filter:
                                continue

                            current_total = stats["total_entries"]
                            stats["total_entries"] = (int(current_total) if isinstance(current_total, (int, str)) else 0) + 1
                            level_counts = stats["level_counts"]
                            if isinstance(level_counts, dict):
                                level_counts[level] = level_counts.get(level, 0) + 1

                            # Hourly distribution
                            hour = int(timestamp // 3600)
                            hourly_counts = stats["hourly_counts"]
                            if isinstance(hourly_counts, dict):
                                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1

                            # Collect errors
                            error_messages = stats["error_messages"]
                            if isinstance(error_messages, list) and level in {"ERROR", "CRITICAL"} and len(error_messages) < 10:
                                error_messages.append(entry.get("message", ""))

                        except json.JSONDecodeError:
                            # Handle text format
                            current_total = stats["total_entries"]
                            stats["total_entries"] = (int(current_total) if isinstance(current_total, (int, str)) else 0) + 1

            except Exception as e:
                self.logger.warning(f"Failed to process log file {log_file}: {e}")
                continue  # Skip problematic files

        return stats

    def _display_log_statistics(self, stats: dict[str, object]) -> None:
        """Display log analysis statistics."""
        # Overview
        level_counts = stats["level_counts"] if isinstance(stats["level_counts"], dict) else {}
        error_count = level_counts.get("ERROR", 0) + level_counts.get("CRITICAL", 0)
        overview = Panel(
            f"Total Entries: {stats['total_entries']:,}\nTime Range: Last 24 hours\nError Count: {error_count}",
            title="📊 Log Overview",
            border_style="blue",
        )
        self.console.print(overview)

        # Level distribution
        if stats["level_counts"]:
            level_table = Table(title="📈 Log Level Distribution", show_header=True)
            level_table.add_column("Level", style="cyan")
            level_table.add_column("Count", style="green", justify="right")
            level_table.add_column("Percentage", style="yellow", justify="right")

            level_counts_obj = stats["level_counts"]
            if not isinstance(level_counts_obj, dict):
                return
            level_counts = level_counts_obj
            total = sum(level_counts.values())
            for level, count in sorted(level_counts.items()):
                percentage = (count / total * 100) if total > 0 else 0
                level_table.add_row(level, str(count), f"{percentage:.1f}%")

            self.console.print(level_table)

        # Recent errors
        if stats["error_messages"]:
            self.console.print("\n🚨 Recent Errors:")
            error_messages_obj = stats["error_messages"]
            error_messages = list(error_messages_obj) if isinstance(error_messages_obj, list) else []
            for i, error in enumerate(error_messages[:5], 1):
                self.console.print(f"  {i}. {error[:80]}{'...' if len(error) > 80 else ''}")


class LogsTailCommand(BaseCommand):
    """Execute the tail command.

    Returns:
        Dict containing.
    """

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()

    def execute(
        self,
        log_dir: str = "~/.scripton/yesman/logs",
        level: str = "INFO",
        follow: bool = False,
        last_lines: int = 50,
        **kwargs: Any,
    ) -> dict:
        """Execute the tail command."""
        try:
            log_path = Path(log_dir).expanduser()

            if not log_path.exists():
                msg = f"Log directory not found: {log_path}"
                raise CommandError(msg)

            # Find most recent log file
            log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.jsonl"))
            if not log_files:
                self.print_warning("No log files found")
                return {"success": False, "files_found": 0}

            # Get most recent file
            latest_log = max(log_files, key=lambda f: f.stat().st_mtime)

            if follow:
                self._follow_log_file(latest_log, level)
            else:
                self._show_recent_logs(latest_log, last_lines, level)

            return {"success": True, "log_file": str(latest_log)}

        except KeyboardInterrupt:
            self.print_warning("\nLog tail stopped")
            return {"success": True, "stopped_by_user": True}
        except Exception as e:
            msg = f"Error tailing logs: {e}"
            raise CommandError(msg) from e

    def _follow_log_file(self, log_file: Path, level_filter: str | None = None) -> None:
        """Follow a log file like tail -f."""
        self.console.print(f"📋 Following {log_file.name} (Press Ctrl+C to stop)")
        self.console.print("=" * 60)

        # Start from end of file
        with open(log_file, encoding="utf-8") as f:
            f.seek(0, 2)  # Seek to end

            while True:
                line = f.readline()
                if line:
                    line = line.strip()

                    try:
                        # Try to parse as JSON
                        entry = json.loads(line)
                        level = entry.get("level", "INFO")

                        if level_filter and level != level_filter:
                            continue

                        timestamp = time.strftime(
                            "%H:%M:%S",
                            time.localtime(entry.get("timestamp", time.time())),
                        )
                        message = entry.get("message", "")

                        # Color code by level
                        level_colors = {
                            "ERROR": "red",
                            "CRITICAL": "bright_red",
                            "WARNING": "yellow",
                            "INFO": "white",
                            "DEBUG": "dim",
                        }

                        level_color = level_colors.get(level, "white")
                        self.console.print(f"[dim]{timestamp}[/] [{level_color}]{level:8}[/] {message}")

                    except json.JSONDecodeError:
                        # Handle text format
                        if not level_filter:
                            self.console.print(line)
                else:
                    time.sleep(0.1)

    def _show_recent_logs(self, log_file: Path, lines: int, level_filter: str | None = None) -> None:
        """Show recent log entries."""
        self.console.print(f"📋 Last {lines} entries from {log_file.name}")
        self.console.print("=" * 60)

        try:
            with open(log_file, encoding="utf-8") as f:
                all_lines = f.readlines()
                recent_lines = all_lines[-lines:]

                for raw_line in recent_lines:
                    line = raw_line.strip()
                    if not line:
                        continue

                    try:
                        entry = json.loads(line)
                        level = entry.get("level", "INFO")

                        if level_filter and level != level_filter:
                            continue

                        timestamp = time.strftime(
                            "%H:%M:%S",
                            time.localtime(entry.get("timestamp", time.time())),
                        )
                        message = entry.get("message", "")

                        level_colors = {
                            "ERROR": "red",
                            "CRITICAL": "bright_red",
                            "WARNING": "yellow",
                            "INFO": "white",
                            "DEBUG": "dim",
                        }

                        level_color = level_colors.get(level, "white")
                        self.console.print(f"[dim]{timestamp}[/] [{level_color}]{level:8}[/] {message}")

                    except json.JSONDecodeError:
                        if not level_filter:
                            self.console.print(line)

        except Exception as e:
            self.console.print(f"[red]Error reading log file: {e}[/]")


class LogsCleanupCommand(BaseCommand):
    """Clean up old log files."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()

    def execute(self, log_dir: str = "~/.scripton/yesman/logs", days: int = 7, **kwargs: Any) -> dict:
        """Execute the cleanup command.

        Returns:
        dict: Description of return value.
        """
        try:
            log_path = Path(log_dir).expanduser()

            if not log_path.exists():
                self.print_warning(f"Log directory not found: {log_path}")
                return {"success": False, "files_deleted": 0}

            # Find old log files
            cutoff_time = time.time() - (days * 24 * 3600)
            old_files = []
            total_size = 0

            for log_file in log_path.rglob("*.log*"):
                if log_file.stat().st_mtime < cutoff_time:
                    old_files.append(log_file)
                    total_size += log_file.stat().st_size

            if not old_files:
                self.print_success(f"No log files older than {days} days found")
                return {"success": True, "files_deleted": 0}

            # Confirm deletion
            size_mb = total_size / (1024 * 1024)
            self.console.print(f"Found {len(old_files)} log files older than {days} days ({size_mb:.1f} MB)")

            if self.confirm_action("Delete these files?"):
                for log_file in old_files:
                    log_file.unlink()

                self.print_success(f"Deleted {len(old_files)} old log files ({size_mb:.1f} MB freed)")
                return {
                    "success": True,
                    "files_deleted": len(old_files),
                    "size_freed": total_size,
                }
            self.print_info("Cleanup cancelled")
            return {"success": False, "cancelled": True}

        except Exception as e:
            msg = f"Error cleaning up logs: {e}"
            raise CommandError(msg) from e


@click.group()
def logs() -> None:
    """Log management and analysis."""


@logs.command()
@click.option("--output-dir", "-o", default="~/.scripton/yesman/logs", help="Log output directory")
@click.option(
    "--format",
    "-f",
    default="json",
    type=click.Choice(["json", "text"]),
    help="Log format",
)
@click.option("--compression", "-c", is_flag=True, help="Enable gzip compression")
@click.option("--buffer-size", "-b", default=1000, type=int, help="Buffer size for batching")
def configure(output_dir: str, format: str, compression: bool, buffer_size: int) -> None:
    """Configure async logging system."""
    command = LogsConfigureCommand()
    command.run(
        output_dir=output_dir,
        format=format,
        compression=compression,
        buffer_size=buffer_size,
    )


@logs.command()
@click.option(
    "--log-dir",
    "-d",
    default="~/.scripton/yesman/logs",
    help="Log directory to analyze",
)
@click.option("--last-hours", "-h", default=24, type=int, help="Analyze last N hours")
@click.option("--level", "-l", help="Filter by log level")
def analyze(log_dir: str, last_hours: int, level: str | None) -> None:
    """Analyze log files and show statistics."""
    command = LogsAnalyzeCommand()
    command.run(log_dir=log_dir, last_hours=last_hours, level=level)


@logs.command()
@click.option("--log-dir", "-d", default="~/.scripton/yesman/logs", help="Log directory")
@click.option("--level", "-l", default="INFO", help="Log level filter")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--last-lines", "-n", default=50, type=int, help="Show last N lines")
def tail(log_dir: str, level: str, follow: bool, last_lines: int) -> None:
    """Tail log files (like tail -f)."""
    command = LogsTailCommand()
    command.run(log_dir=log_dir, level=level, follow=follow, last_lines=last_lines)


@logs.command()
@click.option("--log-dir", "-d", default="~/.scripton/yesman/logs", help="Log directory")
@click.option("--days", default=7, type=int, help="Days of logs to keep")
def cleanup(log_dir: str, days: int) -> None:
    """Clean up old log files."""
    command = LogsCleanupCommand()
    command.run(log_dir=log_dir, days=days)


if __name__ == "__main__":
    logs()
