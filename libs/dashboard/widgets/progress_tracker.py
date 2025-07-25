# Copyright notice.

import datetime
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""TODO progress tracking and visualization widget."""


class TodoStatus(Enum):
    """TODO item status."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


@dataclass
class TodoItem:
    """Individual TODO item."""

    id: str
    content: str
    status: TodoStatus
    priority: str
    created_at: float
    updated_at: float
    project: str | None = None
    category: str | None = None
    estimated_hours: float | None = None
    actual_hours: float | None = None


@dataclass
class ProgressStats:
    """Progress tracking statistics."""

    total_items: int
    completed_items: int
    in_progress_items: int
    pending_items: int
    completion_rate: float
    velocity: float  # items per day
    estimated_completion: float | None = None


class ProgressTracker:
    """TODO progress tracking and visualization."""

    def __init__(self, console: Console | None = None) -> None:
        self.console = console or Console()
        self.todos: list[TodoItem] = []

    def load_todos_from_file(self, file_path: str) -> bool:
        """Load TODO items from markdown file.

        Returns:
        Boolean indicating.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False

            content = path.read_text(encoding="utf-8")
            self.todos = self._parse_markdown_todos(content)
            return True

        except Exception:
            return False

    def load_todos_from_api(self, api_endpoint: str) -> bool:  # noqa: ARG002
        """Load TODO items from API (placeholder for future implementation).

        Returns:
        Boolean indicating.
        """
        # This would integrate with the yesman todo system when available
        # For now, return empty list
        self.todos = []
        return True

    def _parse_markdown_todos(self, content: str) -> list[TodoItem]:
        """Parse TODO items from markdown content.

        Returns:
        List of.
        """
        todos = []
        current_time = time.time()

        # Simple regex patterns for TODO items
        patterns = [
            r"^\\s*-\\s*\\[([x\\s])\\]\\s*(.+)$",  # - [ ] or - [x] format
            r"^\\s*\\*\\s*\\[([x\\s])\\]\\s*(.+)$",  # * [ ] or * [x] format
            r"^\\s*\\d+\\.\\s*\\[([x\\s])\\]\\s*(.+)$",  # 1. [ ] format
        ]

        lines = content.split("\\n")
        todo_counter = 1

        for line_num, line in enumerate(lines):
            for pattern in patterns:
                match = re.match(pattern, line, re.IGNORECASE)
                if match:
                    checkbox, todo_text = match.groups()

                    # Determine status
                    if "x" in checkbox.lower():
                        status = TodoStatus.COMPLETED
                    elif "🔄" in todo_text or "in progress" in todo_text.lower():
                        status = TodoStatus.IN_PROGRESS
                    else:
                        status = TodoStatus.PENDING

                    # Extract priority (if specified)
                    priority = "medium"
                    if "!!!" in todo_text or "urgent" in todo_text.lower() or "!" in todo_text or "important" in todo_text.lower():
                        priority = "high"
                    elif "low" in todo_text.lower() or "nice to have" in todo_text.lower():
                        priority = "low"

                    # Clean up todo text
                    clean_text = re.sub(r"[!]+|\\(urgent\\)|\\(important\\)", "", todo_text).strip()

                    todo = TodoItem(
                        id=f"todo_{todo_counter}",
                        content=clean_text,
                        status=status,
                        priority=priority,
                        created_at=current_time - (line_num * 3600),  # Rough estimate
                        updated_at=current_time,
                        project=self._extract_project_from_text(clean_text),
                        category=self._extract_category_from_text(clean_text),
                    )

                    todos.append(todo)
                    todo_counter += 1
                    break

        return todos

    @staticmethod
    def _extract_project_from_text(text: str) -> str | None:
        """Extract project name from TODO text.

        Returns:
        Str | None object.
        """
        # Look for patterns like "IMPROVE-001:", "Fix:", etc.
        project_patterns = [
            r"^([A-Z]+-\\d+):",  # IMPROVE-001:
            r"^(\\w+):\\s",  # Fix: or Add:
            r"\\(([^)]+)\\)",  # (project-name)
        ]

        for pattern in project_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)

        return None

    @staticmethod
    def _extract_category_from_text(text: str) -> str | None:
        """Extract category from TODO text.

        Returns:
        Str | None object.
        """
        categories = {
            "performance": ["performance", "optimization", "cache", "speed"],
            "ui": ["ui", "interface", "dashboard", "visualization"],
            "ai": ["ai", "learning", "intelligence", "adaptive"],
            "automation": ["automation", "workflow", "auto"],
            "testing": ["test", "testing", "unit test", "integration"],
            "documentation": ["doc", "documentation", "readme", "guide"],
            "bug": ["bug", "fix", "error", "issue"],
        }

        text_lower = text.lower()
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category

        return "general"

    def calculate_progress_stats(self) -> ProgressStats:
        """Calculate progress statistics.

        Returns:
        Progressstats object.
        """
        total = len(self.todos)
        if total == 0:
            return ProgressStats(0, 0, 0, 0, 0.0, 0.0)

        # Count by status
        completed = len([t for t in self.todos if t.status == TodoStatus.COMPLETED])
        in_progress = len([t for t in self.todos if t.status == TodoStatus.IN_PROGRESS])
        pending = len([t for t in self.todos if t.status == TodoStatus.PENDING])

        completion_rate = completed / total

        # Calculate velocity (completed items per day)
        completed_todos = [t for t in self.todos if t.status == TodoStatus.COMPLETED]
        if completed_todos:
            # Find oldest and newest completion
            oldest_completion = min(t.updated_at for t in completed_todos)
            newest_completion = max(t.updated_at for t in completed_todos)

            days_span = max(1, (newest_completion - oldest_completion) / 86400)  # Convert to days
            velocity = len(completed_todos) / days_span
        else:
            velocity = 0.0

        # Estimate completion time
        estimated_completion = None
        if velocity > 0 and pending > 0:
            current_time = time.time()
            days_remaining = pending / velocity
            estimated_completion = current_time + (days_remaining * 86400)

        return ProgressStats(
            total_items=total,
            completed_items=completed,
            in_progress_items=in_progress,
            pending_items=pending,
            completion_rate=completion_rate,
            velocity=velocity,
            estimated_completion=estimated_completion,
        )

    def render_progress_overview(self) -> Panel:
        """Render progress overview panel.

        Returns:
        Panel object.
        """
        stats = self.calculate_progress_stats()

        if stats.total_items == 0:
            return Panel(
                Text("No TODO items found", style="dim"),
                title="📊 Progress Overview",
            )

        content = Text()

        # Progress bar
        bar_length = 30
        filled = int(stats.completion_rate * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        content.append("📊 Overall Progress\\n", style="bold cyan")
        content.append(f"  {bar} {stats.completion_rate:.1%}\\n", style="green")
        content.append(
            f"  {stats.completed_items}/{stats.total_items} completed\\n\\n",
            style="white",
        )

        # Status breakdown
        content.append("📋 Status Breakdown\\n", style="bold yellow")
        content.append(f"  ✅ Completed: {stats.completed_items}\\n", style="green")
        content.append(f"  🔄 In Progress: {stats.in_progress_items}\\n", style="yellow")
        content.append(f"  ⏳ Pending: {stats.pending_items}\\n\\n", style="blue")

        # Velocity and estimates
        content.append("⚡ Performance Metrics\\n", style="bold magenta")
        content.append(f"  Velocity: {stats.velocity:.1f} items/day\\n", style="white")

        if stats.estimated_completion:
            eta = datetime.datetime.fromtimestamp(stats.estimated_completion)
            content.append(f"  ETA: {eta.strftime('%Y-%m-%d')}\\n", style="cyan")
        else:
            content.append("  ETA: Not available\\n", style="dim")

        return Panel(content, title="📊 Progress Overview", border_style="green")

    def render_todo_list(self, status_filter: TodoStatus | None = None, limit: int = 10) -> Panel:
        """Render TODO list with optional filtering.

        Returns:
        List of items.
        """
        todos = self.todos

        if status_filter:
            todos = [t for t in todos if t.status == status_filter]
            title = f"📝 {status_filter.value.replace('_', ' ').title()} Items"
        else:
            title = "📝 All TODO Items"

        if not todos:
            return Panel(Text("No items found", style="dim"), title=title)

        # Sort by priority and creation time
        priority_order = {"high": 0, "medium": 1, "low": 2}
        todos = sorted(
            todos,
            key=lambda t: (
                priority_order.get(t.priority, 1),
                -t.created_at,
            ),
        )

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Priority", style="white", width=8, justify="center")
        table.add_column("Status", style="white", width=12, justify="center")
        table.add_column("Item", style="white", width=50)
        table.add_column("Project", style="cyan", width=15)

        for todo in todos[:limit]:
            # Priority emoji
            priority_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢",
            }.get(todo.priority, "⚪")

            # Status emoji
            status_emoji = {
                TodoStatus.COMPLETED: "✅",
                TodoStatus.IN_PROGRESS: "🔄",
                TodoStatus.PENDING: "⏳",
                TodoStatus.CANCELLED: "❌",
            }.get(todo.status, "❓")

            # Truncate content
            content = todo.content[:47] + "..." if len(todo.content) > 50 else todo.content

            table.add_row(
                priority_emoji,
                status_emoji,
                content,
                todo.project or "general",
            )

        return Panel(table, title=title, border_style="blue")

    def render_category_breakdown(self) -> Panel:
        """Render TODO breakdown by category.

        Returns:
        Panel object.
        """
        if not self.todos:
            return Panel(Text("No data available", style="dim"), title="📊 Category Breakdown")

        # Group by category
        categories = {}
        for todo in self.todos:
            category = todo.category or "general"
            if category not in categories:
                categories[category] = {"total": 0, "completed": 0}

            categories[category]["total"] += 1
            if todo.status == TodoStatus.COMPLETED:
                categories[category]["completed"] += 1

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan", width=15)
        table.add_column("Progress", style="white", width=20)
        table.add_column("Completion", style="green", width=10, justify="center")

        for category, data in sorted(categories.items()):
            total = data["total"]
            completed = data["completed"]
            rate = completed / total if total > 0 else 0

            # Progress bar
            bar_length = 15
            filled = int(rate * bar_length)
            bar = "█" * filled + "░" * (bar_length - filled)

            table.add_row(
                category.replace("_", " ").title(),
                bar,
                f"{rate:.1%}",
            )

        return Panel(table, title="📊 Category Breakdown", border_style="cyan")

    def render_compact_progress(self) -> Text:
        """Render compact progress for status bars.

        Returns:
        Text object.
        """
        stats = self.calculate_progress_stats()

        if stats.total_items == 0:
            return Text("TODO: No items", style="dim")

        text = Text()
        text.append("TODO: ", style="bold")
        text.append(f"{stats.completed_items}/{stats.total_items}", style="green")
        text.append(f" ({stats.completion_rate:.0%})", style="white")

        if stats.in_progress_items > 0:
            text.append(f" 🔄{stats.in_progress_items}", style="yellow")

        return text

    def get_progress_data(self) -> dict[str, object]:
        """Get progress data for external use.

        Returns:
        Dict containing the requested data.
        """
        stats = self.calculate_progress_stats()

        # Category breakdown
        categories = {}
        for todo in self.todos:
            category = todo.category or "general"
            if category not in categories:
                categories[category] = {"total": 0, "completed": 0, "pending": 0}

            categories[category]["total"] += 1
            if todo.status == TodoStatus.COMPLETED:
                categories[category]["completed"] += 1
            elif todo.status == TodoStatus.PENDING:
                categories[category]["pending"] += 1

        return {
            "total_items": stats.total_items,
            "completed_items": stats.completed_items,
            "in_progress_items": stats.in_progress_items,
            "pending_items": stats.pending_items,
            "completion_rate": stats.completion_rate,
            "velocity": stats.velocity,
            "estimated_completion": stats.estimated_completion,
            "categories": categories,
            "recent_todos": [
                {
                    "content": todo.content,
                    "status": todo.status.value,
                    "priority": todo.priority,
                    "project": todo.project,
                }
                for todo in sorted(self.todos, key=lambda t: t.updated_at, reverse=True)[:5]
            ],
        }
