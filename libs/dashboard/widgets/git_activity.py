"""Git activity visualization and metrics widget"""

import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


@dataclass
class CommitInfo:
    """Information about a git commit"""

    hash: str
    author: str
    date: datetime
    message: str
    files_changed: int
    insertions: int
    deletions: int


@dataclass
class GitStats:
    """Git repository statistics"""

    total_commits: int
    active_contributors: int
    recent_commits: List[CommitInfo]
    daily_activity: Dict[str, int]
    file_changes: Dict[str, int]
    branch_info: Dict[str, Any]


class GitActivityWidget:
    """Git activity and metrics visualization"""

    def __init__(self, console: Optional[Console] = None, repo_path: str = "."):
        self.console = console or Console()
        self.repo_path = repo_path

    def update_git_stats(self) -> GitStats:
        """Update git statistics from repository"""

        try:
            # Get basic repo info
            total_commits = self._get_total_commits()
            recent_commits = self._get_recent_commits(limit=20)
            contributors = self._get_active_contributors()
            daily_activity = self._get_daily_activity(days=30)
            file_changes = self._get_file_change_stats()
            branch_info = self._get_branch_info()

            return GitStats(
                total_commits=total_commits,
                active_contributors=len(contributors),
                recent_commits=recent_commits,
                daily_activity=daily_activity,
                file_changes=file_changes,
                branch_info=branch_info,
            )

        except Exception:
            # Return empty stats on error
            return GitStats(
                total_commits=0,
                active_contributors=0,
                recent_commits=[],
                daily_activity={},
                file_changes={},
                branch_info={},
            )

    def _run_git_command(self, command: List[str]) -> str:
        """Run a git command and return output"""
        try:
            result = subprocess.run(
                ["git"] + command,
                check=False,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.stdout.strip() if result.returncode == 0 else ""
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            return ""

    def _get_total_commits(self) -> int:
        """Get total number of commits"""
        output = self._run_git_command(["rev-list", "--count", "HEAD"])
        return int(output) if output.isdigit() else 0

    def _get_recent_commits(self, limit: int = 20) -> List[CommitInfo]:
        """Get recent commit information"""
        commits = []

        # Get commit information
        format_str = "%H|%an|%ad|%s"
        output = self._run_git_command(
            [
                "log",
                f"--max-count={limit}",
                f"--pretty=format:{format_str}",
                "--date=iso",
            ]
        )

        if not output:
            return commits

        for line in output.split("\\n"):
            if "|" not in line:
                continue

            parts = line.split("|", 3)
            if len(parts) != 4:
                continue

            hash_val, author, date_str, message = parts

            try:
                date = datetime.fromisoformat(date_str.replace(" ", "T", 1))
            except ValueError:
                continue

            # Get diff stats for this commit
            stats_output = self._run_git_command(
                [
                    "show",
                    "--stat",
                    "--format=",
                    hash_val,
                ]
            )

            files_changed, insertions, deletions = self._parse_diff_stats(stats_output)

            commits.append(
                CommitInfo(
                    hash=hash_val[:8],
                    author=author,
                    date=date,
                    message=message,
                    files_changed=files_changed,
                    insertions=insertions,
                    deletions=deletions,
                )
            )

        return commits

    def _parse_diff_stats(self, stats_output: str) -> Tuple[int, int, int]:
        """Parse git diff stats output"""
        files_changed = 0
        insertions = 0
        deletions = 0

        # Look for summary line like: "2 files changed, 15 insertions(+), 3 deletions(-)"
        summary_pattern = r"(\\d+) files? changed(?:, (\\d+) insertions?\\(\\+\\))?(?:, (\\d+) deletions?\\(\\-\\))?"
        match = re.search(summary_pattern, stats_output)

        if match:
            files_changed = int(match.group(1))
            insertions = int(match.group(2)) if match.group(2) else 0
            deletions = int(match.group(3)) if match.group(3) else 0

        return files_changed, insertions, deletions

    def _get_active_contributors(self, days: int = 30) -> Dict[str, int]:
        """Get active contributors in the last N days"""
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        output = self._run_git_command(
            [
                "shortlog",
                "-sn",
                f"--since={since_date}",
            ]
        )

        contributors = {}
        for line in output.split("\\n"):
            if "\\t" in line:
                count, name = line.split("\\t", 1)
                contributors[name] = int(count)

        return contributors

    def _get_daily_activity(self, days: int = 30) -> Dict[str, int]:
        """Get daily commit activity for the last N days"""
        since_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")

        output = self._run_git_command(
            [
                "log",
                f"--since={since_date}",
                "--pretty=format:%ad",
                "--date=short",
            ]
        )

        activity = defaultdict(int)
        for line in output.split("\\n"):
            if line:
                activity[line] += 1

        return dict(activity)

    def _get_file_change_stats(self, limit: int = 10) -> Dict[str, int]:
        """Get most frequently changed files"""
        output = self._run_git_command(
            [
                "log",
                "--name-only",
                "--pretty=format:",
                f"--max-count={limit * 5}",  # Get more commits to find file patterns
            ]
        )

        file_changes = defaultdict(int)
        for raw_line in output.split("\\n"):
            line = raw_line.strip()
            if line and not line.startswith("commit"):
                file_changes[line] += 1

        # Return top files
        sorted_files = sorted(file_changes.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_files[:limit])

    def _get_branch_info(self) -> Dict[str, Any]:
        """Get branch information"""
        info = {}

        # Current branch
        current_branch = self._run_git_command(["branch", "--show-current"])
        info["current_branch"] = current_branch

        # Total branches
        all_branches = self._run_git_command(["branch", "-a"])
        info["total_branches"] = len([b for b in all_branches.split("\\n") if b.strip()])

        # Recent branches
        recent_branches = self._run_git_command(
            [
                "for-each-ref",
                "--sort=-committerdate",
                "--format=%(refname:short)",
                "refs/heads/",
                "--count=5",
            ]
        )
        info["recent_branches"] = recent_branches.split("\\n") if recent_branches else []

        return info

    def render_activity_overview(self) -> Panel:
        """Render git activity overview"""
        stats = self.update_git_stats()

        content = Text()

        # Repository stats
        content.append("📊 Repository Overview\\n", style="bold cyan")
        content.append(f"  Total Commits: {stats.total_commits:,}\\n", style="white")
        content.append(f"  Active Contributors: {stats.active_contributors}\\n", style="white")
        content.append(f"  Current Branch: {stats.branch_info.get('current_branch', 'unknown')}\\n", style="yellow")
        content.append(f"  Total Branches: {stats.branch_info.get('total_branches', 0)}\\n\\n", style="white")

        # Recent activity
        if stats.daily_activity:
            recent_days = sorted(stats.daily_activity.items(), reverse=True)[:7]
            content.append("📈 Recent Activity (7 days)\\n", style="bold yellow")

            for date, count in recent_days:
                bar_length = min(count, 20)  # Max bar length
                bar = "█" * bar_length + "░" * (20 - bar_length)
                content.append(f"  {date}: {bar} {count}\\n", style="green")

        return Panel(content, title="🔀 Git Activity", border_style="blue")

    def render_recent_commits(self, limit: int = 5) -> Panel:
        """Render recent commits table"""
        stats = self.update_git_stats()

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Hash", style="yellow", width=8)
        table.add_column("Author", style="cyan", width=15)
        table.add_column("Date", style="white", width=12)
        table.add_column("Message", style="white", width=40)
        table.add_column("Changes", style="green", width=8, justify="center")

        for commit in stats.recent_commits[:limit]:
            # Format date
            date_str = commit.date.strftime("%m-%d %H:%M")

            # Truncate message
            message = commit.message[:37] + "..." if len(commit.message) > 40 else commit.message

            # Format changes
            changes = f"+{commit.insertions}/-{commit.deletions}"

            table.add_row(
                commit.hash,
                commit.author,
                date_str,
                message,
                changes,
            )

        return Panel(table, title="📝 Recent Commits", border_style="green")

    def render_file_activity(self) -> Panel:
        """Render file change activity"""
        stats = self.update_git_stats()

        if not stats.file_changes:
            return Panel(Text("No file activity data", style="dim"), title="📁 File Activity")

        content = Text()
        content.append("📁 Most Changed Files\\n", style="bold cyan")

        max_changes = max(stats.file_changes.values()) if stats.file_changes else 1

        for file_path, changes in list(stats.file_changes.items())[:8]:
            # Create visual bar
            bar_length = int((changes / max_changes) * 20)
            bar = "█" * bar_length + "░" * (20 - bar_length)

            # Truncate filename
            filename = file_path.split("/")[-1] if "/" in file_path else file_path
            if len(filename) > 25:
                filename = filename[:22] + "..."

            content.append(f"  {filename:<25} {bar} {changes}\\n", style="white")

        return Panel(content, title="📁 File Activity", border_style="yellow")

    def render_contributors(self) -> Panel:
        """Render contributor activity"""
        contributors = self._get_active_contributors(days=30)

        if not contributors:
            return Panel(Text("No contributor data", style="dim"), title="👥 Contributors")

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Contributor", style="cyan", width=20)
        table.add_column("Commits (30d)", style="green", width=12, justify="center")
        table.add_column("Activity", style="white", width=20)

        max_commits = max(contributors.values()) if contributors else 1

        for author, commits in sorted(contributors.items(), key=lambda x: x[1], reverse=True):
            # Activity bar
            bar_length = int((commits / max_commits) * 15)
            activity_bar = "█" * bar_length + "░" * (15 - bar_length)

            table.add_row(author, str(commits), activity_bar)

        return Panel(table, title="👥 Contributors (30 days)", border_style="cyan")

    def render_compact_status(self) -> Text:
        """Render compact git status for status bars"""
        stats = self.update_git_stats()

        text = Text()
        text.append("Git: ", style="bold")

        # Recent activity
        if stats.daily_activity:
            today = datetime.now().strftime("%Y-%m-%d")
            today_commits = stats.daily_activity.get(today, 0)
            text.append(f"{today_commits} today", style="green")
        else:
            text.append("No activity", style="dim")

        # Current branch
        current_branch = stats.branch_info.get("current_branch", "unknown")
        text.append(f" ({current_branch})", style="yellow")

        return text

    def get_activity_metrics(self) -> Dict[str, Any]:
        """Get git activity metrics as data"""
        stats = self.update_git_stats()

        # Calculate trends
        if len(stats.daily_activity) >= 7:
            recent_week = list(sorted(stats.daily_activity.items()))[-7:]
            prev_week = list(sorted(stats.daily_activity.items()))[-14:-7]

            recent_total = sum(count for _, count in recent_week)
            prev_total = sum(count for _, count in prev_week)

            trend = ((recent_total - prev_total) / prev_total * 100) if prev_total > 0 else 0
        else:
            trend = 0

        return {
            "total_commits": stats.total_commits,
            "active_contributors": stats.active_contributors,
            "commits_this_week": sum(stats.daily_activity.values()),
            "trend_percentage": trend,
            "current_branch": stats.branch_info.get("current_branch"),
            "most_active_file": max(stats.file_changes.items(), key=lambda x: x[1])[0] if stats.file_changes else None,
            "last_commit": stats.recent_commits[0].date.isoformat() if stats.recent_commits else None,
        }
