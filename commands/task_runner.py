#!/usr/bin/env python3
"""Task Runner CLI command for automated TODO processing.

Provides automation for processing TODO files in /tasks/todo/ directory.
Implements the TASK_RUNNER.todo prompt workflow:
1. Find next uncompleted task
2. Analyze dependencies and break down if needed
3. Implement task and run tests
4. Commit changes and move completed files
"""

import os
import sys
from pathlib import Path

import click
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn, track

# Add libs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from libs.core.base_command import BaseCommand, CommandError
from libs.task_runner import TaskRunner


class TaskRunnerNextCommand(BaseCommand):
    """Process the next available task."""

    def execute(self, directory: str | None = None, verbose: bool = False, **kwargs) -> dict:
        """Execute the next command."""
        try:
            runner = TaskRunner()
            success = runner.process_next_task(directory)

            if success:
                self.print_success("✅ Task processed successfully")
                return {"success": True, "task_processed": True}
            self.print_info("ℹ️ No more tasks to process")
            return {"success": True, "task_processed": False}

        except Exception as e:
            msg = f"Error processing task: {e}"
            raise CommandError(msg) from e


class TaskRunnerRunCommand(BaseCommand):
    """Run task processor continuously."""

    def execute(
        self,
        directory: str | None = None,
        max_iterations: int = 100,
        dry_run: bool = False,
        **kwargs,
    ) -> dict:
        """Execute the run command."""
        try:
            runner = TaskRunner()

            if dry_run:
                self.print_info("🔍 DRY RUN MODE - No changes will be made")

                # Show what tasks would be processed
                todo_files = runner.find_todo_files(directory)
                self.print_info(f"\nFound {len(todo_files)} todo files:")

                task_count = 0
                # Use progress bar for file analysis
                for file_path in track(
                    todo_files,
                    description="📁 Analyzing todo files...",
                    style="bold cyan",
                ):
                    from libs.task_runner import TodoFile

                    todo_file = TodoFile(str(file_path))
                    incomplete_tasks = [t for t in todo_file.tasks if not t.completed and not t.skipped]
                    if incomplete_tasks:
                        self.print_info(f"  📁 {file_path.relative_to(runner.todo_dir.parent)}: {len(incomplete_tasks)} tasks")
                        task_count += len(incomplete_tasks)

                self.print_info(f"\nTotal tasks to process: {task_count}")
                return {"success": True, "dry_run": True, "task_count": task_count}

            # Add progress indicator for continuous processing
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold green]{task.description}"),
                TimeElapsedColumn(),
                transient=True,
            ) as progress:
                task_id = progress.add_task("🔄 Running task processor continuously...", total=None)
                runner.run_continuously(directory, max_iterations)
                progress.update(task_id, description="✅ Task processing completed")

            return {
                "success": True,
                "directory": directory,
                "max_iterations": max_iterations,
            }

        except KeyboardInterrupt:
            self.print_warning("\n⏹️ Task runner interrupted by user")
            return {"success": True, "interrupted": True}
        except Exception as e:
            msg = f"Error running task processor: {e}"
            raise CommandError(msg) from e


class TaskRunnerStatusCommand(BaseCommand):
    """Show current task status."""

    def execute(self, directory: str | None = None, detailed: bool = False, **kwargs) -> dict:
        """Execute the status command."""
        try:
            runner = TaskRunner()
            todo_files = runner.find_todo_files(directory)

            if not todo_files:
                self.print_info("📭 No todo files found")
                return {"success": True, "todo_files": 0}

            total_files = len(todo_files)
            total_tasks = 0
            completed_tasks = 0
            skipped_tasks = 0
            completed_files = 0

            self.print_info(f"📊 Task Status {'for ' + directory if directory else ''}")
            self.print_info("=" * 50)

            for file_path in todo_files:
                from libs.task_runner import TodoFile

                todo_file = TodoFile(str(file_path))

                file_total = len(todo_file.tasks)
                file_completed = sum(1 for t in todo_file.tasks if t.completed)
                file_skipped = sum(1 for t in todo_file.tasks if t.skipped)

                total_tasks += file_total
                completed_tasks += file_completed
                skipped_tasks += file_skipped

                if todo_file.is_all_completed():
                    completed_files += 1

                # Show file status
                relative_path = file_path.relative_to(runner.todo_dir.parent)
                status_icon = "✅" if todo_file.is_all_completed() else "🔄" if file_completed > 0 else "📝"

                if detailed:
                    completion_pct = (file_completed / file_total * 100) if file_total > 0 else 0
                    self.print_info(f"{status_icon} {relative_path}")
                    self.print_info(f"   Tasks: {file_completed}/{file_total} completed ({completion_pct:.1f}%)")
                    if file_skipped > 0:
                        self.print_info(f"   Skipped: {file_skipped}")
                    self.print_info("")
                else:
                    self.print_info(f"{status_icon} {relative_path}: {file_completed}/{file_total}")

            # Summary
            self.print_info("\n📈 Summary")
            self.print_info("-" * 20)
            self.print_info(f"Files: {completed_files}/{total_files} completed")
            self.print_info(f"Tasks: {completed_tasks}/{total_tasks} completed")
            if skipped_tasks > 0:
                self.print_info(f"Skipped: {skipped_tasks} tasks")

            # Show next task
            result = runner.get_next_task(directory)
            if result:
                todo_file, next_task = result
                relative_path = todo_file.file_path.relative_to(runner.todo_dir.parent)
                self.print_info(f"\n🎯 Next task: {next_task.content}")
                self.print_info(f"   File: {relative_path}")
            else:
                self.print_success("\n🎉 All tasks completed!")

            return {
                "success": True,
                "total_files": total_files,
                "completed_files": completed_files,
                "total_tasks": total_tasks,
                "completed_tasks": completed_tasks,
                "skipped_tasks": skipped_tasks,
            }

        except Exception as e:
            msg = f"Error getting status: {e}"
            raise CommandError(msg) from e


class TaskRunnerAddCommand(BaseCommand):
    """Add a new task to a todo file."""

    def execute(self, task: str | None = None, file_path: str | None = None, **kwargs) -> dict:
        """Execute the add command."""
        if not task or not file_path:
            msg = "Both --task and --file options are required"
            raise CommandError(msg)

        try:
            runner = TaskRunner()

            # Resolve file path
            resolved_path: Path = runner.todo_dir / file_path if not file_path.startswith("/") else Path(file_path)

            if not resolved_path.exists():
                msg = f"File not found: {resolved_path}"
                raise CommandError(msg)

            # Add task to file
            with open(resolved_path, "a", encoding="utf-8") as f:
                f.write(f"\n- [ ] {task}\n")

            self.print_success(f"✅ Added task to {resolved_path.relative_to(runner.todo_dir.parent)}")
            self.print_info(f"   Task: {task}")

            return {"success": True, "task": task, "file_path": str(file_path)}

        except Exception as e:
            msg = f"Error adding task: {e}"
            raise CommandError(msg) from e


@click.group()
def task_runner() -> None:
    """Automated TODO task processor.

    Processes TODO files in tasks/todo/ directory according to TASK_RUNNER.todo workflow.
    Automatically finds next incomplete task, analyzes dependencies, implements solutions,
    runs tests, commits changes, and moves completed files.
    """


@task_runner.command()
@click.option(
    "--dir",
    "-d",
    "directory",
    help="Specific directory to process (e.g. /tasks/todo/phase3)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def next(directory: str | None, verbose: bool) -> None:
    """Process the next available task.

    Finds and processes the next uncompleted task in todo files.
    Tasks are processed in filename order, then by task order within files.

    Examples:
        yesman task-runner next                    # Process next task in any file
        yesman task-runner next -d phase3         # Process next task in phase3/ only
        yesman task-runner next -v               # Verbose output
    """
    command = TaskRunnerNextCommand()
    command.run(directory=directory, verbose=verbose)


@task_runner.command()
@click.option(
    "--dir",
    "-d",
    "directory",
    help="Specific directory to process (e.g. /tasks/todo/phase3)",
)
@click.option(
    "--max-iterations",
    "-m",
    default=100,
    type=int,
    help="Maximum number of tasks to process (default: 100)",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Show what would be processed without making changes",
)
def run(directory: str | None, max_iterations: int, dry_run: bool) -> None:
    """Run task processor continuously.

    Processes all available tasks until none remain or max iterations reached.
    Automatically handles task breakdown, implementation, testing, and file management.

    Examples:
        yesman task-runner run                     # Process all tasks
        yesman task-runner run -d phase3          # Process only phase3 tasks
        yesman task-runner run -m 50              # Limit to 50 iterations
        yesman task-runner run --dry-run          # Preview without changes
    """
    command = TaskRunnerRunCommand()
    command.run(directory=directory, max_iterations=max_iterations, dry_run=dry_run)


@task_runner.command()
@click.option("--dir", "-d", "directory", help="Specific directory to show status for")
@click.option("--detailed", is_flag=True, help="Show detailed task breakdown")
def status(directory: str | None, detailed: bool) -> None:
    """Show current task status.

    Displays overview of todo files and task completion status.
    Shows pending, completed, and skipped tasks across all files.

    Examples:
        yesman task-runner status                  # Overall status
        yesman task-runner status -d phase3       # Phase3 status only
        yesman task-runner status --detailed      # Detailed breakdown
    """
    command = TaskRunnerStatusCommand()
    command.run(directory=directory, detailed=detailed)


@task_runner.command()
@click.option("--task", "-t", help="Task content to add")
@click.option("--file", "-f", "file_path", help="File to add task to")
def add(task: str | None, file_path: str | None) -> None:
    """Add a new task to a todo file.

    Adds a new uncompleted task to the specified todo file.

    Examples:
        yesman task-runner add -t "Implement feature X" -f phase3/01-base-renderer.md
        yesman task-runner add -t "Write tests" -f phase4/01-cli-integration.md
    """
    command = TaskRunnerAddCommand()
    command.run(task=task, file_path=file_path)


if __name__ == "__main__":
    task_runner()
