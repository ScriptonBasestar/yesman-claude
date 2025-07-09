"""Project health status visualization widget"""

import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich.progress import Progress, BarColumn, TextColumn, SpinnerColumn
from rich.tree import Tree
from rich.columns import Columns

from ..health_calculator import HealthCalculator, HealthLevel, HealthCategory


@dataclass
class ProjectStatus:
    """Project status information"""
    name: str
    health_score: float
    health_level: HealthLevel
    categories: Dict[str, Dict[str, Any]]
    last_updated: float
    build_status: str = "unknown"
    test_status: str = "unknown"
    git_status: str = "unknown"


class ProjectHealthWidget:
    """Project health visualization widget"""
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self.health_calculator = HealthCalculator()
        
    def update_project_health(self, project_path: str, project_name: str = None) -> ProjectStatus:
        """Update health information for a project"""
        if not project_name:
            project_name = Path(project_path).name
        
        try:
            # Calculate health metrics
            health_report = self.health_calculator.calculate_comprehensive_health()
            overall_score = health_report.get("overall_score", 0)
            health_level = HealthLevel.from_score(int(overall_score))
            
            # Extract category details
            categories = {}
            for category in HealthCategory:
                cat_data = health_report.get("categories", {}).get(category.value, {})
                categories[category.value] = {
                    "score": cat_data.get("score", 0),
                    "status": cat_data.get("status", "unknown"),
                    "details": cat_data.get("details", []),
                    "issues": cat_data.get("issues", [])
                }
            
            # Create status object
            status = ProjectStatus(
                name=project_name,
                health_score=overall_score,
                health_level=health_level,
                categories=categories,
                last_updated=time.time(),
                build_status=categories.get("build", {}).get("status", "unknown"),
                test_status=categories.get("tests", {}).get("status", "unknown"),
                git_status=categories.get("git", {}).get("status", "unknown")
            )
            
            self.project_cache[project_name] = status
            return status
            
        except Exception as e:
            # Create fallback status
            status = ProjectStatus(
                name=project_name,
                health_score=0,
                health_level=HealthLevel.UNKNOWN,
                categories={},
                last_updated=time.time(),
                build_status="error",
                test_status="error",
                git_status="error"
            )
            self.project_cache[project_name] = status
            return status
    
    def render_health_overview(self, project_name: str) -> Panel:
        """Render project health overview"""
        if project_name not in self.project_cache:
            return Panel(Text("Project not found", style="red"), title="Health Overview")
        
        status = self.project_cache[project_name]
        
        # Create overview content
        content = Text()
        
        # Header with project name and overall score
        content.append(f"🎯 {status.name}\\n", style="bold cyan")
        content.append(f"Overall Health: ", style="bold")
        content.append(f"{status.health_level.emoji} {status.health_score:.0f}% ", style="bold")
        content.append(f"({status.health_level.label.title()})\\n\\n", style=f"bold {self._get_score_color(status.health_score)}")
        
        # Key metrics
        content.append("📊 Key Metrics:\\n", style="bold yellow")
        
        key_categories = ["build", "tests", "dependencies", "security"]
        for category in key_categories:
            if category in status.categories:
                cat_data = status.categories[category]
                score = cat_data["score"]
                emoji = HealthLevel.from_score(score).emoji
                
                content.append(f"  {emoji} {category.title()}: ", style="white")
                content.append(f"{score}%\\n", style=self._get_score_color(score))
        
        # Recent activity
        import time
        time_ago = time.time() - status.last_updated
        if time_ago < 60:
            time_str = f"{int(time_ago)}s ago"
        elif time_ago < 3600:
            time_str = f"{int(time_ago/60)}m ago"
        else:
            time_str = f"{int(time_ago/3600)}h ago"
        
        content.append(f"\\n🕒 Last updated: {time_str}", style="dim")
        
        return Panel(content, title="📈 Project Health Overview", border_style="green")
    
    def render_detailed_breakdown(self, project_name: str) -> Panel:
        """Render detailed health breakdown by category"""
        if project_name not in self.project_cache:
            return Panel(Text("Project not found", style="red"), title="Health Breakdown")
        
        status = self.project_cache[project_name]
        
        # Create detailed table
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan", width=15)
        table.add_column("Score", style="white", width=8, justify="center")
        table.add_column("Status", style="white", width=12, justify="center")
        table.add_column("Issues", style="yellow", width=40)
        
        for category_name, cat_data in status.categories.items():
            score = cat_data["score"]
            status_text = cat_data["status"]
            issues = cat_data.get("issues", [])
            
            # Format score with color
            score_text = Text(f"{score}%", style=self._get_score_color(score))
            
            # Format status with emoji
            level = HealthLevel.from_score(score)
            status_display = f"{level.emoji} {status_text}"
            
            # Format issues (show first 2)
            if issues:
                issues_text = "; ".join(issues[:2])
                if len(issues) > 2:
                    issues_text += f" (+{len(issues)-2} more)"
            else:
                issues_text = "None"
            
            table.add_row(
                category_name.replace("_", " ").title(),
                score_text,
                status_display,
                issues_text
            )
        
        return Panel(table, title="🔍 Detailed Health Breakdown", border_style="blue")
    
    def render_progress_tracker(self, project_name: str) -> Panel:
        """Render TODO progress tracking"""
        if project_name not in self.project_cache:
            return Panel(Text("Project not found", style="red"), title="Progress Tracker")
        
        # Simulated TODO progress (in real implementation, integrate with TODO system)
        progress_data = {
            "total_todos": 12,
            "completed_todos": 8,
            "in_progress": 2,
            "pending": 2,
            "today_completed": 3
        }
        
        content = Text()
        
        # Progress bar
        completion_rate = progress_data["completed_todos"] / progress_data["total_todos"]
        bar_length = 20
        filled = int(completion_rate * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)
        
        content.append("📋 TODO Progress:\\n", style="bold cyan")
        content.append(f"  {bar} {completion_rate:.1%}\\n", style="green")
        content.append(f"  {progress_data['completed_todos']}/{progress_data['total_todos']} completed\\n\\n", style="white")
        
        # Status breakdown
        content.append("📊 Status Breakdown:\\n", style="bold yellow")
        content.append(f"  ✅ Completed: {progress_data['completed_todos']}\\n", style="green")
        content.append(f"  🔄 In Progress: {progress_data['in_progress']}\\n", style="yellow")
        content.append(f"  ⏳ Pending: {progress_data['pending']}\\n", style="blue")
        
        # Today's activity
        content.append(f"\\n🎯 Today: {progress_data['today_completed']} completed", style="bright_green")
        
        return Panel(content, title="📊 Progress Tracker", border_style="cyan")
    
    def render_compact_status(self, project_name: str) -> Text:
        """Render compact status for status bars"""
        if project_name not in self.project_cache:
            return Text(f"{project_name}: Unknown", style="dim")
        
        status = self.project_cache[project_name]
        
        text = Text()
        text.append(f"{status.name}: ", style="white")
        text.append(f"{status.health_level.emoji} {status.health_score:.0f}%", 
                   style=self._get_score_color(status.health_score))
        
        # Add key status indicators
        if status.build_status == "success":
            text.append(" 🏗️", style="green")
        elif status.build_status == "failed":
            text.append(" 🚫", style="red")
        
        if status.test_status == "passing":
            text.append(" ✅", style="green")
        elif status.test_status == "failing":
            text.append(" ❌", style="red")
        
        return text
    
    def render_multi_project_grid(self, project_names: List[str]) -> Panel:
        """Render health status for multiple projects in a grid"""
        if not project_names:
            return Panel(Text("No projects to display", style="dim"), title="Project Grid")
        
        # Create cards for each project
        cards = []
        for project_name in project_names:
            if project_name in self.project_cache:
                card = self._create_project_card(self.project_cache[project_name])
            else:
                card = Panel(
                    Text(f"{project_name}\\nNot monitored", style="dim"),
                    title="❓ Unknown",
                    width=25,
                    height=8
                )
            cards.append(card)
        
        return Panel(
            Columns(cards, equal=True, expand=True),
            title="🏗️ Multi-Project Health Overview",
            border_style="blue"
        )
    
    def _create_project_card(self, status: ProjectStatus) -> Panel:
        """Create a compact project status card"""
        content = Text()
        
        # Health score and level
        content.append(f"{status.health_level.emoji} {status.health_score:.0f}%\\n", 
                      style=f"bold {self._get_score_color(status.health_score)}")
        
        # Key status indicators
        indicators = []
        if status.build_status == "success":
            indicators.append("🏗️ Pass")
        elif status.build_status == "failed":
            indicators.append("🚫 Fail")
        
        if status.test_status == "passing":
            indicators.append("✅ Tests")
        elif status.test_status == "failing":
            indicators.append("❌ Tests")
        
        content.append("\\n".join(indicators), style="white")
        
        # Border color based on health
        if status.health_score >= 80:
            border_style = "green"
        elif status.health_score >= 60:
            border_style = "yellow"
        else:
            border_style = "red"
        
        return Panel(
            content,
            title=status.name,
            width=25,
            height=8,
            border_style=border_style
        )
    
    def _get_score_color(self, score: float) -> str:
        """Get Rich color for a health score"""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        elif score >= 40:
            return "red"
        else:
            return "bright_red"
    
    def get_project_summary(self, project_name: str) -> Dict[str, Any]:
        """Get project health summary as data"""
        if project_name not in self.project_cache:
            return {"error": "Project not found"}
        
        status = self.project_cache[project_name]
        return {
            "name": status.name,
            "health_score": status.health_score,
            "health_level": status.health_level.label,
            "categories": {
                name: {
                    "score": data["score"],
                    "status": data["status"],
                    "issue_count": len(data.get("issues", []))
                }
                for name, data in status.categories.items()
            },
            "last_updated": status.last_updated,
            "build_status": status.build_status,
            "test_status": status.test_status,
            "git_status": status.git_status
        }