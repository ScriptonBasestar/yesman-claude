#!/usr/bin/env python3
"""
Task Runner CLI command for automated TODO processing

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

# Add libs to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from libs.task_runner import TaskRunner


@click.group()
def task_runner():
    """Automated TODO task processor

    Processes TODO files in tasks/todo/ directory according to TASK_RUNNER.todo workflow.
    Automatically finds next incomplete task, analyzes dependencies, implements solutions,
    runs tests, commits changes, and moves completed files.
    """
    pass


@task_runner.command()
@click.option(
    "--dir",
    "-d",
    "directory",
    help="Specific directory to process (e.g. /tasks/todo/phase3)",
)
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
def next(directory, verbose):
    """Process the next available task

    Finds and processes the next uncompleted task in todo files.
    Tasks are processed in filename order, then by task order within files.

    Examples:
        yesman task-runner next                    # Process next task in any file
        yesman task-runner next -d phase3         # Process next task in phase3/ only
        yesman task-runner next -v               # Verbose output
    """
    runner = TaskRunner()

    try:
        success = runner.process_next_task(directory)
        if success:
            click.echo("✅ Task processed successfully")
        else:
            click.echo("ℹ️ No more tasks to process")

    except Exception as e:
        click.echo(f"❌ Error processing task: {e}", err=True)
        sys.exit(1)


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
def run(directory, max_iterations, dry_run):
    """Run task processor continuously

    Processes all available tasks until none remain or max iterations reached.
    Automatically handles task breakdown, implementation, testing, and file management.

    Examples:
        yesman task-runner run                     # Process all tasks
        yesman task-runner run -d phase3          # Process only phase3 tasks
        yesman task-runner run -m 50              # Limit to 50 iterations
        yesman task-runner run --dry-run          # Preview without changes
    """
    runner = TaskRunner()

    if dry_run:
        click.echo("🔍 DRY RUN MODE - No changes will be made")
        # Show what tasks would be processed
        todo_files = runner.find_todo_files(directory)
        click.echo(f"\nFound {len(todo_files)} todo files:")

        task_count = 0
        for file_path in todo_files:
            from libs.task_runner import TodoFile

            todo_file = TodoFile(file_path)
            incomplete_tasks = [t for t in todo_file.tasks if not t.completed and not t.skipped]
            if incomplete_tasks:
                click.echo(f"  📁 {file_path.relative_to(runner.todo_dir.parent)}: {len(incomplete_tasks)} tasks")
                task_count += len(incomplete_tasks)

        click.echo(f"\nTotal tasks to process: {task_count}")
        return

    try:
        runner.run_continuously(directory, max_iterations)

    except KeyboardInterrupt:
        click.echo("\n⏹️ Task runner interrupted by user")
        sys.exit(0)
    except Exception as e:
        click.echo(f"❌ Error running task processor: {e}", err=True)
        sys.exit(1)


@task_runner.command()
@click.option("--dir", "-d", "directory", help="Specific directory to show status for")
@click.option("--detailed", is_flag=True, help="Show detailed task breakdown")
def status(directory, detailed):
    """Show current task status

    Displays overview of todo files and task completion status.
    Shows pending, completed, and skipped tasks across all files.

    Examples:
        yesman task-runner status                  # Overall status
        yesman task-runner status -d phase3       # Phase3 status only
        yesman task-runner status --detailed      # Detailed breakdown
    """
    runner = TaskRunner()

    try:
        todo_files = runner.find_todo_files(directory)

        if not todo_files:
            click.echo("📭 No todo files found")
            return

        total_files = len(todo_files)
        total_tasks = 0
        completed_tasks = 0
        skipped_tasks = 0
        completed_files = 0

        click.echo(f"📊 Task Status {'for ' + directory if directory else ''}")
        click.echo("=" * 50)

        for file_path in todo_files:
            from libs.task_runner import TodoFile

            todo_file = TodoFile(file_path)

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
                click.echo(f"{status_icon} {relative_path}")
                click.echo(f"   Tasks: {file_completed}/{file_total} completed ({completion_pct:.1f}%)")
                if file_skipped > 0:
                    click.echo(f"   Skipped: {file_skipped}")
                click.echo()
            else:
                click.echo(f"{status_icon} {relative_path}: {file_completed}/{file_total}")

        # Summary
        click.echo("\n📈 Summary")
        click.echo("-" * 20)
        click.echo(f"Files: {completed_files}/{total_files} completed")
        click.echo(f"Tasks: {completed_tasks}/{total_tasks} completed")
        if skipped_tasks > 0:
            click.echo(f"Skipped: {skipped_tasks} tasks")

        # Show next task
        result = runner.get_next_task(directory)
        if result:
            todo_file, next_task = result
            relative_path = todo_file.file_path.relative_to(runner.todo_dir.parent)
            click.echo(f"\n🎯 Next task: {next_task.content}")
            click.echo(f"   File: {relative_path}")
        else:
            click.echo("\n🎉 All tasks completed!")

    except Exception as e:
        click.echo(f"❌ Error getting status: {e}", err=True)
        sys.exit(1)


@task_runner.command()
@click.option("--task", "-t", help="Task content to add")
@click.option("--file", "-f", "file_path", help="File to add task to")
def add(task, file_path):
    """Add a new task to a todo file

    Adds a new uncompleted task to the specified todo file.

    Examples:
        yesman task-runner add -t "Implement feature X" -f phase3/01-base-renderer.md
        yesman task-runner add -t "Write tests" -f phase4/01-cli-integration.md
    """
    if not task or not file_path:
        click.echo("❌ Both --task and --file options are required", err=True)
        sys.exit(1)

    runner = TaskRunner()

    # Resolve file path
    file_path = runner.todo_dir / file_path if not file_path.startswith("/") else Path(file_path)

    if not file_path.exists():
        click.echo(f"❌ File not found: {file_path}", err=True)
        sys.exit(1)

    try:
        # Add task to file
        with open(file_path, "a", encoding="utf-8") as f:
            f.write(f"\n- [ ] {task}\n")

        click.echo(f"✅ Added task to {file_path.relative_to(runner.todo_dir.parent)}")
        click.echo(f"   Task: {task}")

    except Exception as e:
        click.echo(f"❌ Error adding task: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    task_runner()
