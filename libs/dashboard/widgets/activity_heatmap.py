"""Activity heatmap visualization for session monitoring"""

import time
import math
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque

from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.table import Table


@dataclass
class ActivityPoint:
    """Single activity measurement"""
    timestamp: float
    level: float  # 0.0 - 1.0
    session_name: str
    activity_type: str = "general"


class ActivityHeatmap:
    """Visualizes session activity levels over time as a heatmap"""
    
    def __init__(self, console: Optional[Console] = None, max_history: int = 100):
        self.console = console or Console()
        self.max_history = max_history
        
        # Activity history for each session
        self.activity_history: Dict[str, deque] = {}
        self.current_levels: Dict[str, float] = {}
        
        # Visualization settings
        self.time_window = 300  # 5 minutes in seconds
        self.heatmap_width = 50
        self.heatmap_height = 10
        
        # Activity thresholds
        self.thresholds = {
            "low": 0.2,
            "medium": 0.5,
            "high": 0.8
        }
        
        # Color mapping for activity levels
        self.colors = {
            0: "bright_black",    # ░ Very low
            1: "blue",           # ▒ Low  
            2: "cyan",           # ▓ Medium
            3: "yellow",         # ▓ High
            4: "red"             # █ Very high
        }
        
        self.symbols = ["░", "▒", "▓", "▓", "█"]
    
    def add_activity_point(self, session_name: str, level: float, activity_type: str = "general") -> None:
        """Add a new activity measurement"""
        if session_name not in self.activity_history:
            self.activity_history[session_name] = deque(maxlen=self.max_history)
        
        point = ActivityPoint(
            timestamp=time.time(),
            level=max(0.0, min(1.0, level)),  # Clamp to 0-1
            session_name=session_name,
            activity_type=activity_type
        )
        
        self.activity_history[session_name].append(point)
        self.current_levels[session_name] = level
        
        # Clean old data outside time window
        self._cleanup_old_data()
    
    def _cleanup_old_data(self) -> None:
        """Remove activity points outside the time window"""
        cutoff_time = time.time() - self.time_window
        
        for session_name in self.activity_history:
            history = self.activity_history[session_name]
            # Remove old points from the left
            while history and history[0].timestamp < cutoff_time:
                history.popleft()
    
    def _get_activity_level_color(self, level: float) -> int:
        """Map activity level to color index"""
        if level < 0.1:
            return 0
        elif level < 0.3:
            return 1
        elif level < 0.6:
            return 2
        elif level < 0.8:
            return 3
        else:
            return 4
    
    def render_session_heatmap(self, session_name: str, width: int = 30) -> Text:
        """Render activity heatmap for a single session"""
        text = Text()
        
        if session_name not in self.activity_history:
            text.append("░" * width, style="dim")
            return text
        
        history = list(self.activity_history[session_name])
        if not history:
            text.append("░" * width, style="dim")
            return text
        
        # Create time buckets
        current_time = time.time()
        bucket_duration = self.time_window / width
        
        for i in range(width):
            bucket_start = current_time - self.time_window + (i * bucket_duration)
            bucket_end = bucket_start + bucket_duration
            
            # Find activity points in this time bucket
            bucket_activities = [
                p.level for p in history
                if bucket_start <= p.timestamp < bucket_end
            ]
            
            if bucket_activities:
                avg_activity = sum(bucket_activities) / len(bucket_activities)
            else:
                avg_activity = 0.0
            
            color_idx = self._get_activity_level_color(avg_activity)
            symbol = self.symbols[color_idx]
            color = self.colors[color_idx]
            
            text.append(symbol, style=color)
        
        return text
    
    def render_combined_heatmap(self) -> Panel:
        """Render heatmap for all sessions in a table format"""
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Session", style="cyan", width=15)
        table.add_column("Current", style="white", width=8, justify="center")
        table.add_column("Activity Heatmap (5min)", style="white", width=35)
        table.add_column("Trend", style="white", width=8, justify="center")
        
        # Sort sessions by current activity level
        sorted_sessions = sorted(
            self.current_levels.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        for session_name, current_level in sorted_sessions:
            # Current activity indicator
            current_symbol = self.symbols[self._get_activity_level_color(current_level)]
            current_color = self.colors[self._get_activity_level_color(current_level)]
            current_text = Text(current_symbol * 3, style=current_color)
            
            # Activity heatmap
            heatmap = self.render_session_heatmap(session_name, width=30)
            
            # Trend calculation
            trend = self._calculate_trend(session_name)
            trend_text = self._format_trend(trend)
            
            table.add_row(
                session_name,
                current_text,
                heatmap,
                trend_text
            )
        
        # Add legend
        legend = self._create_legend()
        
        return Panel(
            table,
            title="📊 Session Activity Heatmap",
            subtitle=legend,
            border_style="green"
        )
    
    def _calculate_trend(self, session_name: str) -> float:
        """Calculate activity trend (-1 to 1, negative = decreasing)"""
        if session_name not in self.activity_history:
            return 0.0
        
        history = list(self.activity_history[session_name])
        if len(history) < 2:
            return 0.0
        
        # Compare recent activity to older activity
        recent_count = max(1, len(history) // 3)
        recent_avg = sum(p.level for p in history[-recent_count:]) / recent_count
        older_avg = sum(p.level for p in history[:-recent_count]) / (len(history) - recent_count)
        
        if older_avg == 0:
            return 1.0 if recent_avg > 0 else 0.0
        
        return max(-1.0, min(1.0, (recent_avg - older_avg) / older_avg))
    
    def _format_trend(self, trend: float) -> Text:
        """Format trend value as visual indicator"""
        if trend > 0.2:
            return Text("📈", style="green")
        elif trend < -0.2:
            return Text("📉", style="red")
        else:
            return Text("➡️", style="yellow")
    
    def _create_legend(self) -> str:
        """Create legend for heatmap colors"""
        return "Legend: ░ Idle  ▒ Low  ▓ Medium  █ High"
    
    def render_compact_overview(self) -> Text:
        """Render compact activity overview for status bars"""
        text = Text("Activity: ", style="bold")
        
        if not self.current_levels:
            text.append("No sessions", style="dim")
            return text
        
        # Overall activity level
        avg_activity = sum(self.current_levels.values()) / len(self.current_levels)
        color_idx = self._get_activity_level_color(avg_activity)
        symbol = self.symbols[color_idx]
        color = self.colors[color_idx]
        
        text.append(f"{symbol} {avg_activity:.1%}", style=color)
        
        # Active sessions count
        active_count = sum(1 for level in self.current_levels.values() if level > 0.1)
        text.append(f" ({active_count}/{len(self.current_levels)} active)", style="cyan")
        
        return text
    
    def get_session_summary(self, session_name: str) -> Dict[str, any]:
        """Get detailed activity summary for a session"""
        if session_name not in self.activity_history:
            return {
                "current_level": 0.0,
                "trend": 0.0,
                "peak_time": None,
                "total_active_time": 0.0,
                "points_count": 0
            }
        
        history = list(self.activity_history[session_name])
        if not history:
            return {
                "current_level": 0.0,
                "trend": 0.0,
                "peak_time": None,
                "total_active_time": 0.0,
                "points_count": 0
            }
        
        # Find peak activity
        peak_point = max(history, key=lambda p: p.level)
        
        # Calculate active time (level > threshold)
        active_threshold = 0.2
        active_time = sum(
            1 for p in history if p.level > active_threshold
        ) * (self.time_window / len(history))  # Approximate
        
        return {
            "current_level": self.current_levels.get(session_name, 0.0),
            "trend": self._calculate_trend(session_name),
            "peak_time": peak_point.timestamp,
            "peak_level": peak_point.level,
            "total_active_time": active_time,
            "points_count": len(history)
        }
    
    def clear_session_data(self, session_name: str) -> None:
        """Clear activity data for a session"""
        if session_name in self.activity_history:
            del self.activity_history[session_name]
        if session_name in self.current_levels:
            del self.current_levels[session_name]
    
    def get_activity_data(self, days: int = 90) -> List[Dict[str, any]]:
        """Get activity data for the last N days for web dashboard"""
        from datetime import datetime, timedelta
        import random
        
        # For now, return mock data for the last 90 days
        # In a real implementation, this would query actual activity data
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days-1)
        
        activities = []
        current_date = start_date
        while current_date <= end_date:
            # Generate mock activity data based on current session activity
            if self.current_levels:
                base_activity = sum(self.current_levels.values()) / len(self.current_levels)
                activity_count = int(base_activity * 20) + random.randint(0, 5)
            else:
                activity_count = random.randint(0, 15) if random.random() > 0.3 else 0
            
            activities.append({
                "date": current_date.isoformat(),
                "count": activity_count
            })
            current_date += timedelta(days=1)
        
        return activities