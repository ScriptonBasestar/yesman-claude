#!/usr/bin/env python3

# Copyright notice.

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from rich.console import Console
from rich.progress import (

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Progress indicator utilities for long-running commands.

Provides standardized progress indicators using Rich library
for consistent user experience across all commands.
"""


    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    track,
)


class ProgressStyle:
    """Standard progress indicator styles."""

    # Spinner styles for long-running operations without known duration
    STARTUP = "bold blue"
    PROCESSING = "bold green"
    ANALYZING = "bold yellow"
    CLEANUP = "bold cyan"
    ERROR = "bold red"
    SUCCESS = "bold green"

    # Bar styles for operations with known progress
    FILE_OPERATIONS = "blue"
    NETWORK_OPERATIONS = "cyan"
    DATA_PROCESSING = "green"


@contextmanager
def spinner_progress(description: str, style: str = ProgressStyle.PROCESSING) -> Iterator[Callable[[str], None]]:
    """Create a spinner progress indicator for indefinite operations.

    Args:
        description: Initial description text
        style: Rich style for the text (default: ProgressStyle.PROCESSING)

    Yields:
        update_function: Function to update the description

    Example:
        with spinner_progress("🔄 Processing files...") as update:
            do_work()
            update("📊 Analyzing results...")
            more_work()
    """
    with Progress(
        SpinnerColumn(),
        TextColumn(f"[{style}]{{task.description}}[/]"),
        TimeElapsedColumn(),
        transient=True,
        console=Console(),
    ) as progress:
        task_id = progress.add_task(description, total=None)

        def update_description(new_description: str) -> None:
            progress.update(task_id, description=new_description)

        yield update_description


@contextmanager
def bar_progress(description: str, total: int, style: str = ProgressStyle.DATA_PROCESSING) -> Iterator[Callable[[int, str | None], None]]:
    """Create a progress bar for operations with known total.

    Args:
        description: Description text
        total: Total number of items to process
        style: Rich style for the text

    Yields:
        update_function: Function to update progress (advance, new_description)

    Example:
        items = get_items()
        with bar_progress("Processing items", len(items)) as update:
            for i, item in enumerate(items):
                process_item(item)
                update(1, f"Processed {item.name}")
    """
    with Progress(
        TextColumn(f"[{style}]{{task.description}}[/]"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=Console(),
    ) as progress:
        task_id = progress.add_task(description, total=total)

        def update_progress(advance: int = 1, new_description: str | None = None) -> None:
            progress.update(task_id, advance=advance)
            if new_description:
                progress.update(task_id, description=new_description)

        yield update_progress


def track_items(items: list[object], description: str, style: str = ProgressStyle.DATA_PROCESSING) -> object:
    """Track progress through a list of items with rich progress bar.

    Args:
        items: List of items to process
        description: Description for the progress bar
        style: Rich style for the text

    Yields:
        Each item from the list

    Example:
        files = get_files()
        for file_path in track_items(files, "🔧 Processing files", ProgressStyle.FILE_OPERATIONS):
            process_file(file_path)

    Returns:
        Description of Any return value
    """
    return track(items, description=f"[{style}]{description}[/]")


@contextmanager
def multi_stage_progress(stages: list[str], style: str = ProgressStyle.PROCESSING) -> Iterator[Callable[[int, str | None], None]]:
    """Create a multi-stage progress indicator.

    Args:
        stages: List of stage descriptions
        style: Rich style for the text

    Yields:
        next_stage_function: Function to advance to next stage (stage_index, custom_description)

    Example:
        stages = ["Initializing", "Processing", "Finalizing"]
        with multi_stage_progress(stages) as next_stage:
            # Stage 0: Initializing
            initialize()
            next_stage(1)  # Move to Processing

            process_data()
            next_stage(2, "🏁 Finishing up...")  # Custom description

            finalize()
    """
    with Progress(
        TextColumn(f"[{style}]{{task.description}}[/]"),
        BarColumn(bar_width=None),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TextColumn("({task.completed}/{task.total})"),
        TimeElapsedColumn(),
        console=Console(),
    ) as progress:
        task_id = progress.add_task(stages[0], total=len(stages), completed=0)

        def next_stage(stage_index: int, custom_description: str | None = None) -> None:
            description = custom_description or stages[stage_index] if stage_index < len(stages) else "✅ Completed"
            progress.update(task_id, completed=stage_index, description=description)

        yield next_stage


class ProgressManager:
    """High-level progress manager for complex operations.

    Provides easy-to-use methods for common progress patterns
    """

    @staticmethod
    def startup_sequence(operations: list[tuple[str, Callable]], style: str = ProgressStyle.STARTUP) -> dict[str]:
        """Execute a sequence of startup operations with progress tracking.

        Args:
            operations: List of (description, function) tuples
            style: Rich style for progress text

        Returns:
            Dictionary with results from each operation

        Example:
            operations = [
                ("🔧 Loading configuration", load_config),
                ("🚀 Starting services", start_services),
                ("✅ Ready", lambda: None),
            ]
            results = ProgressManager.startup_sequence(operations)
        """
        results = {}

        with multi_stage_progress([desc for desc, _ in operations], style) as next_stage:
            for i, (description, operation) in enumerate(operations):
                next_stage(i, description)
                try:
                    result = operation()
                    results[f"stage_{i}"] = {"success": True, "result": result}
                except Exception as e:
                    results[f"stage_{i}"] = {"success": False, "error": str(e)}
                    raise

        return results

    @staticmethod
    def file_batch_operation(
        files: list[object],
        operation: Callable[[object]],
        description: str = "🔧 Processing files",
        style: str = ProgressStyle.FILE_OPERATIONS,
    ) -> list[object]:
        """Process a batch of files with progress tracking.

        Args:
            files: List of files to process
            operation: Function to apply to each file
            description: Progress description
            style: Rich style for progress text

        Returns:
            List of results from each operation

        Example:
            files = Path("/some/dir").glob("*.txt")
            results = ProgressManager.file_batch_operation(
                files,
                lambda f: f.read_text(),
                "📖 Reading text files"
            )
        """
        results = []

        for file_item in track_items(list(files), description, style):
            try:
                result = operation(file_item)
                results.append({"success": True, "result": result, "file": str(file_item)})
            except Exception as e:
                results.append({"success": False, "error": str(e), "file": str(file_item)})

        return results


# Convenience functions for common patterns
def with_startup_progress(description: str) -> object:
    """Decorator for startup operations."""
    return spinner_progress(description, ProgressStyle.STARTUP)


def with_processing_progress(description: str) -> object:
    """Decorator for processing operations."""
    return spinner_progress(description, ProgressStyle.PROCESSING)


def with_analysis_progress(description: str) -> object:
    """Decorator for analysis operations."""
    return spinner_progress(description, ProgressStyle.ANALYZING)
