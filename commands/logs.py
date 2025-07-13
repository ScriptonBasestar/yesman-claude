"""Log management and analysis commands"""

import json
import logging
import time
from pathlib import Path
from typing import Any, Dict

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from libs.logging import AsyncLogger, AsyncLoggerConfig, LogLevel


@click.group()
def logs():
    """Log management and analysis"""
    pass


@logs.command()
@click.option("--output-dir", "-o", default="~/.yesman/logs", help="Log output directory")
@click.option("--format", "-f", default="json", type=click.Choice(["json", "text"]), help="Log format")
@click.option("--compression", "-c", is_flag=True, help="Enable gzip compression")
@click.option("--buffer-size", "-b", default=1000, type=int, help="Buffer size for batching")
def configure(output_dir, format, compression, buffer_size):
    """Configure async logging system"""
    console = Console()

    try:
        # Expand home directory
        output_path = Path(output_dir).expanduser()
        output_path.mkdir(parents=True, exist_ok=True)

        # Create configuration
        config = AsyncLoggerConfig(
            output_directory=output_path,
            log_format=format,
            enable_compression=compression,
            buffer_size=buffer_size,
            flush_interval=5.0,
        )

        # Initialize logger to test configuration
        async_logger = AsyncLogger(config)

        console.print("✅ Async logging configured successfully")
        console.print(f"  Output directory: {output_path}")
        console.print(f"  Format: {format}")
        console.print(f"  Compression: {'enabled' if compression else 'disabled'}")
        console.print(f"  Buffer size: {buffer_size}")

        # Test log entry
        async_logger.log(
            LogLevel.INFO,
            "Async logging system configured",
            extra_data={
                "config_test": True,
                "timestamp": time.time(),
            },
        )

        console.print("\\n🔍 Test log entry written")

    except Exception as e:
        console.print(f"[red]Error configuring logging: {e}[/]")


@logs.command()
@click.option("--log-dir", "-d", default="~/.yesman/logs", help="Log directory to analyze")
@click.option("--last-hours", "-h", default=24, type=int, help="Analyze last N hours")
@click.option("--level", "-l", help="Filter by log level")
def analyze(log_dir, last_hours, level):
    """Analyze log files and show statistics"""
    console = Console()

    try:
        log_path = Path(log_dir).expanduser()

        if not log_path.exists():
            console.print(f"[red]Log directory not found: {log_path}[/]")
            return

        # Find log files
        log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.jsonl")) + list(log_path.glob("*.log.gz"))

        if not log_files:
            console.print("[yellow]No log files found[/]")
            return

        # Analyze logs
        stats = _analyze_log_files(log_files, last_hours, level)

        # Display statistics
        _display_log_statistics(console, stats)

    except Exception as e:
        console.print(f"[red]Error analyzing logs: {e}[/]")


@logs.command()
@click.option("--log-dir", "-d", default="~/.yesman/logs", help="Log directory")
@click.option("--level", "-l", default="INFO", help="Log level filter")
@click.option("--follow", "-f", is_flag=True, help="Follow log output")
@click.option("--last-lines", "-n", default=50, type=int, help="Show last N lines")
def tail(log_dir, level, follow, last_lines):
    """Tail log files (like tail -f)"""
    console = Console()

    try:
        log_path = Path(log_dir).expanduser()

        if not log_path.exists():
            console.print(f"[red]Log directory not found: {log_path}[/]")
            return

        # Find most recent log file
        log_files = list(log_path.glob("*.log")) + list(log_path.glob("*.jsonl"))
        if not log_files:
            console.print("[yellow]No log files found[/]")
            return

        # Get most recent file
        latest_log = max(log_files, key=lambda f: f.stat().st_mtime)

        if follow:
            _follow_log_file(console, latest_log, level)
        else:
            _show_recent_logs(console, latest_log, last_lines, level)

    except KeyboardInterrupt:
        console.print("\\n[yellow]Log tail stopped[/]")
    except Exception as e:
        console.print(f"[red]Error tailing logs: {e}[/]")


@logs.command()
@click.option("--log-dir", "-d", default="~/.yesman/logs", help="Log directory")
@click.option("--days", default=7, type=int, help="Days of logs to keep")
def cleanup(log_dir, days):
    """Clean up old log files"""
    console = Console()

    try:
        log_path = Path(log_dir).expanduser()

        if not log_path.exists():
            console.print(f"[yellow]Log directory not found: {log_path}[/]")
            return

        # Find old log files
        cutoff_time = time.time() - (days * 24 * 3600)
        old_files = []
        total_size = 0

        for log_file in log_path.rglob("*.log*"):
            if log_file.stat().st_mtime < cutoff_time:
                old_files.append(log_file)
                total_size += log_file.stat().st_size

        if not old_files:
            console.print(f"[green]No log files older than {days} days found[/]")
            return

        # Confirm deletion
        size_mb = total_size / (1024 * 1024)
        console.print(f"Found {len(old_files)} log files older than {days} days ({size_mb:.1f} MB)")

        if click.confirm("Delete these files?"):
            for log_file in old_files:
                log_file.unlink()

            console.print(f"✅ Deleted {len(old_files)} old log files ({size_mb:.1f} MB freed)")
        else:
            console.print("Cleanup cancelled")

    except Exception as e:
        console.print(f"[red]Error cleaning up logs: {e}[/]")


def _analyze_log_files(log_files: list, last_hours: int, level_filter: str = None) -> Dict[str, Any]:
    """Analyze log files and return statistics"""
    import gzip
    from collections import defaultdict

    stats = {
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

                        stats["total_entries"] += 1
                        stats["level_counts"][level] += 1

                        # Hourly distribution
                        hour = int(timestamp // 3600)
                        stats["hourly_counts"][hour] += 1

                        # Collect errors
                        if level in ["ERROR", "CRITICAL"] and len(stats["error_messages"]) < 10:
                            stats["error_messages"].append(entry.get("message", ""))

                    except json.JSONDecodeError:
                        # Handle text format
                        stats["total_entries"] += 1

        except Exception as e:
            logging.warning(f"Failed to process log file {log_file}: {e}")
            continue  # Skip problematic files

    return stats


def _display_log_statistics(console: Console, stats: Dict[str, Any]):
    """Display log analysis statistics"""
    # Overview
    overview = Panel(
        f"Total Entries: {stats['total_entries']:,}\\nTime Range: Last {24} hours\\nError Count: {stats['level_counts']['ERROR'] + stats['level_counts']['CRITICAL']}",
        title="📊 Log Overview",
        border_style="blue",
    )
    console.print(overview)

    # Level distribution
    if stats["level_counts"]:
        level_table = Table(title="📈 Log Level Distribution", show_header=True)
        level_table.add_column("Level", style="cyan")
        level_table.add_column("Count", style="green", justify="right")
        level_table.add_column("Percentage", style="yellow", justify="right")

        total = sum(stats["level_counts"].values())
        for level, count in sorted(stats["level_counts"].items()):
            percentage = (count / total * 100) if total > 0 else 0
            level_table.add_row(level, str(count), f"{percentage:.1f}%")

        console.print(level_table)

    # Recent errors
    if stats["error_messages"]:
        console.print("\\n🚨 Recent Errors:")
        for i, error in enumerate(stats["error_messages"][:5], 1):
            console.print(f"  {i}. {error[:80]}{'...' if len(error) > 80 else ''}")


def _follow_log_file(console: Console, log_file: Path, level_filter: str = None):
    """Follow a log file like tail -f"""
    import time

    console.print(f"📋 Following {log_file.name} (Press Ctrl+C to stop)")
    console.print("=" * 60)

    # Start from end of file
    with open(log_file) as f:
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

                    timestamp = time.strftime("%H:%M:%S", time.localtime(entry.get("timestamp", time.time())))
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
                    console.print(f"[dim]{timestamp}[/] [{level_color}]{level:8}[/] {message}")

                except json.JSONDecodeError:
                    # Handle text format
                    if not level_filter:
                        console.print(line)
            else:
                time.sleep(0.1)


def _show_recent_logs(console: Console, log_file: Path, lines: int, level_filter: str = None):
    """Show recent log entries"""
    console.print(f"📋 Last {lines} entries from {log_file.name}")
    console.print("=" * 60)

    try:
        with open(log_file) as f:
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

                    timestamp = time.strftime("%H:%M:%S", time.localtime(entry.get("timestamp", time.time())))
                    message = entry.get("message", "")

                    level_colors = {
                        "ERROR": "red",
                        "CRITICAL": "bright_red",
                        "WARNING": "yellow",
                        "INFO": "white",
                        "DEBUG": "dim",
                    }

                    level_color = level_colors.get(level, "white")
                    console.print(f"[dim]{timestamp}[/] [{level_color}]{level:8}[/] {message}")

                except json.JSONDecodeError:
                    if not level_filter:
                        console.print(line)

    except Exception as e:
        console.print(f"[red]Error reading log file: {e}[/]")


if __name__ == "__main__":
    logs()
