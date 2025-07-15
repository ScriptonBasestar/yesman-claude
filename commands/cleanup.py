"""Cache cleanup command for removing excessive cache files"""

import os
import shutil
from pathlib import Path

import click
from rich.console import Console
from rich.progress import track
from rich.table import Table

from libs.yesman_config import YesmanConfig


@click.command()
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be cleaned without actually deleting",
)
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
@click.option("--all", "cleanup_all", is_flag=True, help="Clean all cache types including logs")
def cleanup(dry_run: bool, force: bool, cleanup_all: bool):
    """Clean up excessive cache files and temporary data"""

    console = Console()

    # Find cache files to clean
    cache_paths = []
    total_size = 0

    # Python cache files (__pycache__, *.pyc)
    for root, dirs, files in os.walk("."):
        # Skip .venv directory
        if ".venv" in dirs:
            dirs.remove(".venv")

        # Find __pycache__ directories
        if "__pycache__" in dirs:
            pycache_path = Path(root) / "__pycache__"
            if pycache_path.exists():
                size = sum(f.stat().st_size for f in pycache_path.rglob("*") if f.is_file())
                cache_paths.append(("__pycache__", pycache_path, size))
                total_size += size

        # Find .pyc files
        for file in files:
            if file.endswith(".pyc"):
                pyc_path = Path(root) / file
                if pyc_path.exists():
                    size = pyc_path.stat().st_size
                    cache_paths.append(("pyc", pyc_path, size))
                    total_size += size

    # Tauri build cache
    tauri_cache = Path("./tauri-dashboard/src-tauri/target")
    if tauri_cache.exists():
        size = sum(f.stat().st_size for f in tauri_cache.rglob("*") if f.is_file())
        cache_paths.append(("tauri-cache", tauri_cache, size))
        total_size += size

    # Optional: Log files cleanup
    if cleanup_all:
        config = YesmanConfig()
        log_paths = [
            Path(config.get("logging", {}).get("dashboard_log_file", "~/.yesman/logs/dashboard.log")).expanduser(),
            Path(config.get("logging", {}).get("claude_log_file", "~/.yesman/logs/claude.log")).expanduser(),
            Path(config.get("logging", {}).get("session_log_file", "~/.yesman/logs/session.log")).expanduser(),
        ]

        for log_path in log_paths:
            if log_path.exists() and log_path.stat().st_size > 10 * 1024 * 1024:  # > 10MB
                size = log_path.stat().st_size
                cache_paths.append(("log", log_path, size))
                total_size += size

    # Display summary
    table = Table(title="Cache Cleanup Summary")
    table.add_column("Type", style="cyan")
    table.add_column("Path", style="yellow")
    table.add_column("Size", style="green", justify="right")

    for cache_type, path, size in cache_paths:
        human_size = _human_readable_size(size)
        table.add_row(cache_type, str(path), human_size)

    console.print(table)
    console.print(f"\n[bold]Total cache size:[/bold] {_human_readable_size(total_size)}")

    if not cache_paths:
        console.print("[green]✅ No excessive cache files found[/green]")
        return

    if dry_run:
        console.print("\n[yellow]🔍 Dry run mode - no files will be deleted[/yellow]")
        return

    # Confirm cleanup
    if not force:
        confirm = click.confirm(f"\nDelete {len(cache_paths)} cache items ({_human_readable_size(total_size)})?")
        if not confirm:
            console.print("[yellow]❌ Cleanup cancelled[/yellow]")
            return

    # Perform cleanup
    console.print("\n[blue]🧹 Cleaning up cache files...[/blue]")

    cleaned_count = 0
    cleaned_size = 0
    errors = []

    for _cache_type, path, size in track(cache_paths, description="Cleaning..."):
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            cleaned_count += 1
            cleaned_size += size
        except Exception as e:
            errors.append(f"{path}: {e}")

    # Show results
    if cleaned_count > 0:
        console.print(f"\n[green]✅ Cleaned {cleaned_count} items ({_human_readable_size(cleaned_size)})[/green]")

    if errors:
        console.print(f"\n[red]❌ {len(errors)} errors occurred:[/red]")
        for error in errors[:5]:  # Show first 5 errors
            console.print(f"   {error}")
        if len(errors) > 5:
            console.print(f"   ... and {len(errors) - 5} more")


def _human_readable_size(size_bytes: int) -> str:
    """Convert bytes to human readable format"""
    if size_bytes == 0:
        return "0 B"

    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


if __name__ == "__main__":
    cleanup()
