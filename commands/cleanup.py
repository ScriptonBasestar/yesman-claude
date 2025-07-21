from typing import Any
import os
import shutil
from pathlib import Path
import click
from rich.console import Console
from rich.progress import track
from rich.table import Table
from libs.core.base_command import BaseCommand, ConfigCommandMixin


# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Cache cleanup command for removing excessive cache files."""





class CleanupCommand(BaseCommand, ConfigCommandMixin):
    """Clean up excessive cache files and temporary data."""

    def __init__(self) -> None:
        super().__init__()
        self.console = Console()

    def execute(
        self,
        dry_run: bool = False,  # noqa: FBT001
        force: bool = False,  # noqa: FBT001
        cleanup_all: bool = False,  # noqa: FBT001
        **kwargs: object,  # noqa: ARG002
    ) -> dict:
        """Execute the cleanup command.
        
            Returns:
                Dict containing.
        
                
        """
        # Find cache files to clean
        cache_paths = self._find_cache_files(cleanup_all)
        total_size = sum(size for _, _, size in cache_paths)

        # Display summary
        self._display_summary(cache_paths, total_size)

        if not cache_paths:
            self.print_success("No excessive cache files found")
            return {"cleaned_count": 0, "cleaned_size": 0}

        if dry_run:
            self.print_warning("🔍 Dry run mode - no files will be deleted")
            return {
                "dry_run": True,
                "found_count": len(cache_paths),
                "found_size": total_size,
            }

        # Confirm cleanup
        if not force and not self.confirm_action(f"Delete {len(cache_paths)} cache items ({self._human_readable_size(total_size)})?"):
            self.print_warning("Cleanup cancelled")
            return {"cancelled": True}

        # Perform cleanup
        cleaned_count, cleaned_size, errors = self._perform_cleanup(cache_paths)

        # Show results
        self._display_results(cleaned_count, cleaned_size, errors)

        return {
            "cleaned_count": cleaned_count,
            "cleaned_size": cleaned_size,
            "errors": errors,
            "success": len(errors) == 0,
        }

    def _find_cache_files(self, cleanup_all: bool) -> list[tuple[str, Path, int]]:  # noqa: FBT001
        """Find cache files to clean.

        Returns:
        object: Description of return value.
        """
        cache_paths = []

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

            # Find .pyc files
            for file in files:
                if file.endswith(".pyc"):
                    pyc_path = Path(root) / file
                    if pyc_path.exists():
                        size = pyc_path.stat().st_size
                        cache_paths.append(("pyc", pyc_path, size))

        # Tauri build cache
        tauri_cache = Path("./tauri-dashboard/src-tauri/target")
        if tauri_cache.exists():
            size = sum(f.stat().st_size for f in tauri_cache.rglob("*") if f.is_file())
            cache_paths.append(("tauri-cache", tauri_cache, size))

        # Optional: Log files cleanup
        if cleanup_all:
            log_paths = [
                Path(self.config.get("logging", {}).get("dashboard_log_file", "~/.scripton/yesman/logs/dashboard.log")).expanduser(),
                Path(self.config.get("logging", {}).get("claude_log_file", "~/.scripton/yesman/logs/claude.log")).expanduser(),
                Path(self.config.get("logging", {}).get("session_log_file", "~/.scripton/yesman/logs/session.log")).expanduser(),
            ]

            for log_path in log_paths:
                if log_path.exists() and log_path.stat().st_size > 10 * 1024 * 1024:  # > 10MB
                    size = log_path.stat().st_size
                    cache_paths.append(("log", log_path, size))

        return cache_paths

    def _display_summary(self, cache_paths: list[tuple[str, Path, int]], total_size: int) -> None:
        """Display cache cleanup summary.

        """
        table = Table(title="Cache Cleanup Summary")
        table.add_column("Type", style="cyan")
        table.add_column("Path", style="yellow")
        table.add_column("Size", style="green", justify="right")

        for cache_type, path, size in cache_paths:
            human_size = self._human_readable_size(size)
            table.add_row(cache_type, str(path), human_size)

        self.console.print(table)
        self.console.print(f"\n[bold]Total cache size:[/bold] {self._human_readable_size(total_size)}")

    def _perform_cleanup(self, cache_paths: list[tuple[str, Path, int]]) -> tuple[int, int, list[str]]:
        """Perform the actual cleanup.

        Returns:
        object: Description of return value.
        """
        self.console.print("\n[blue]🧹 Cleaning up cache files...[/blue]")

        cleaned_count = 0
        cleaned_size = 0
        errors = []

        for _cache_type, path, size in track(cache_paths, description="Cleaning...", console=self.console):
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                cleaned_count += 1
                cleaned_size += size
            except Exception as e:
                errors.append(f"{path}: {e}")

        return cleaned_count, cleaned_size, errors

    def _display_results(self, cleaned_count: int, cleaned_size: int, errors: list[str]) -> None:
        """Display cleanup results.

        """
        if cleaned_count > 0:
            self.print_success(f"Cleaned {cleaned_count} items ({self._human_readable_size(cleaned_size)})")

        if errors:
            self.print_error(f"{len(errors)} errors occurred:")
            for error in errors[:5]:  # Show first 5 errors
                self.console.print(f"   {error}")
            if len(errors) > 5:
                self.console.print(f"   ... and {len(errors) - 5} more")

    @staticmethod
    def _human_readable_size(size_bytes: int) -> str:
        """Convert bytes to human readable format.

        Returns:
        str: Description of return value.
        """
        if size_bytes == 0:
            return "0 B"

        size: float = float(size_bytes)
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


@click.command()
@click.option(
    "--dry-run",
    "-n",
    is_flag=True,
    help="Show what would be cleaned without actually deleting",
)
@click.option("--force", "-f", is_flag=True, help="Force cleanup without confirmation")
@click.option("--all", "cleanup_all", is_flag=True, help="Clean all cache types including logs")
def cleanup(dry_run: bool, force: bool, cleanup_all: bool) -> None:  # noqa: FBT001
    """Clean up excessive cache files and temporary data.

    """
    command = CleanupCommand()
    command.run(dry_run=dry_run, force=force, cleanup_all=cleanup_all)


if __name__ == "__main__":
    cleanup()
