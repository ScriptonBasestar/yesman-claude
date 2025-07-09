# 🔧 Phase 3: 공통 렌더러 시스템

**Phase ID**: COMMON-RENDERER  
**예상 시간**: 1주 (5일)  
**선행 조건**: Phase 1, 2 완료  
**후행 Phase**: PHASE-4 통합 및 고급 기능

## 🎯 Phase 목표

3가지 인터페이스(TUI, Web, Tauri)에서 동일한 위젯 데이터를 렌더링할 수 있는 통합 렌더러 시스템을 구축한다.

## 📋 상세 작업 계획

### Day 1: 렌더러 아키텍처 설계

#### 1.1 기본 렌더러 인터페이스
**파일**: `libs/dashboard/renderers/base_renderer.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import json
from datetime import datetime

class RenderFormat(Enum):
    """렌더링 포맷"""
    TUI = "tui"          # Rich 터미널 UI
    WEB = "web"          # HTML/JavaScript
    TAURI = "tauri"      # Tauri 네이티브
    JSON = "json"        # 순수 JSON 데이터
    MARKDOWN = "markdown" # Markdown 포맷

class WidgetType(Enum):
    """위젯 타입"""
    SESSION_BROWSER = "session_browser"
    HEALTH_METER = "health_meter"
    ACTIVITY_HEATMAP = "activity_heatmap"
    PROGRESS_TRACKER = "progress_tracker"
    LOG_VIEWER = "log_viewer"
    GIT_ACTIVITY = "git_activity"
    METRICS_CHART = "metrics_chart"
    STATUS_CARD = "status_card"

class BaseRenderer(ABC):
    """기본 렌더러 추상 클래스"""
    
    def __init__(self, format: RenderFormat):
        self.format = format
        self.theme = self.get_default_theme()
        self.config = self.get_default_config()
        
    @abstractmethod
    def render_widget(self, widget_type: WidgetType, data: Dict[str, Any], 
                     options: Optional[Dict[str, Any]] = None) -> Any:
        """위젯 렌더링"""
        pass
        
    @abstractmethod
    def render_layout(self, layout: Dict[str, Any], widgets: List[Dict[str, Any]]) -> Any:
        """레이아웃 렌더링"""
        pass
        
    @abstractmethod
    def render_container(self, title: str, content: Any, 
                        options: Optional[Dict[str, Any]] = None) -> Any:
        """컨테이너 렌더링"""
        pass
        
    def render(self, component_type: str, data: Dict[str, Any], 
              options: Optional[Dict[str, Any]] = None) -> Any:
        """통합 렌더링 메서드"""
        if component_type == "widget":
            return self.render_widget(
                WidgetType(data.get("type")), 
                data.get("data", {}), 
                options
            )
        elif component_type == "layout":
            return self.render_layout(
                data.get("layout", {}), 
                data.get("widgets", [])
            )
        elif component_type == "container":
            return self.render_container(
                data.get("title", ""), 
                data.get("content"), 
                options
            )
        else:
            raise ValueError(f"Unknown component type: {component_type}")
            
    def get_default_theme(self) -> Dict[str, Any]:
        """기본 테마 설정"""
        return {
            "colors": {
                "primary": "#3B82F6",      # blue-500
                "secondary": "#10B981",    # green-500
                "warning": "#F59E0B",      # yellow-500
                "error": "#EF4444",        # red-500
                "info": "#06B6D4",         # cyan-500
                "background": "#F3F4F6",   # gray-100
                "surface": "#FFFFFF",      # white
                "text": "#1F2937",         # gray-800
                "text_secondary": "#6B7280" # gray-500
            },
            "spacing": {
                "xs": 2,
                "sm": 4,
                "md": 8,
                "lg": 16,
                "xl": 32
            },
            "typography": {
                "font_family": "system-ui",
                "font_size_base": 14,
                "font_size_sm": 12,
                "font_size_lg": 16,
                "font_size_xl": 20
            }
        }
        
    def get_default_config(self) -> Dict[str, Any]:
        """기본 설정"""
        return {
            "animations": True,
            "compact_mode": False,
            "show_icons": True,
            "date_format": "%Y-%m-%d %H:%M:%S",
            "number_format": "{:,.2f}"
        }
        
    def apply_theme(self, theme: Dict[str, Any]):
        """테마 적용"""
        self.theme.update(theme)
        
    def apply_config(self, config: Dict[str, Any]):
        """설정 적용"""
        self.config.update(config)
        
    # 공통 유틸리티 메서드
    def format_number(self, value: Union[int, float]) -> str:
        """숫자 포맷팅"""
        return self.config["number_format"].format(value)
        
    def format_date(self, date: Union[str, datetime]) -> str:
        """날짜 포맷팅"""
        if isinstance(date, str):
            date = datetime.fromisoformat(date)
        return date.strftime(self.config["date_format"])
        
    def format_percentage(self, value: float) -> str:
        """퍼센트 포맷팅"""
        return f"{value:.1f}%"
        
    def get_color(self, color_name: str) -> str:
        """테마 색상 가져오기"""
        return self.theme["colors"].get(color_name, "#000000")
        
    def get_spacing(self, size: str) -> int:
        """테마 간격 가져오기"""
        return self.theme["spacing"].get(size, 8)

class RendererRegistry:
    """렌더러 레지스트리"""
    
    def __init__(self):
        self._renderers: Dict[RenderFormat, BaseRenderer] = {}
        
    def register(self, format: RenderFormat, renderer: BaseRenderer):
        """렌더러 등록"""
        self._renderers[format] = renderer
        
    def get(self, format: RenderFormat) -> BaseRenderer:
        """렌더러 조회"""
        if format not in self._renderers:
            raise ValueError(f"No renderer registered for format: {format}")
        return self._renderers[format]
        
    def render(self, format: RenderFormat, component_type: str, 
              data: Dict[str, Any], options: Optional[Dict[str, Any]] = None) -> Any:
        """특정 포맷으로 렌더링"""
        renderer = self.get(format)
        return renderer.render(component_type, data, options)
        
    def render_all(self, component_type: str, data: Dict[str, Any], 
                  options: Optional[Dict[str, Any]] = None) -> Dict[RenderFormat, Any]:
        """모든 포맷으로 렌더링"""
        results = {}
        for format, renderer in self._renderers.items():
            try:
                results[format] = renderer.render(component_type, data, options)
            except Exception as e:
                results[format] = {"error": str(e)}
        return results

# 전역 레지스트리
renderer_registry = RendererRegistry()
```

#### 1.2 위젯 데이터 모델
**파일**: `libs/dashboard/renderers/widget_models.py`
```python
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class SessionStatus(Enum):
    """세션 상태"""
    ACTIVE = "active"
    IDLE = "idle"
    STOPPED = "stopped"
    ERROR = "error"

@dataclass
class SessionData:
    """세션 데이터 모델"""
    name: str
    id: str
    status: SessionStatus
    created_at: datetime
    last_activity: Optional[datetime] = None
    windows: List[Dict[str, Any]] = field(default_factory=list)
    panes: int = 0
    claude_active: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "name": self.name,
            "id": self.id,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "windows": self.windows,
            "panes": self.panes,
            "claude_active": self.claude_active,
            "metadata": self.metadata
        }

@dataclass
class HealthData:
    """건강도 데이터 모델"""
    overall_score: float
    categories: Dict[str, float]
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_status(self) -> str:
        """건강 상태 반환"""
        if self.overall_score >= 80:
            return "excellent"
        elif self.overall_score >= 60:
            return "good"
        elif self.overall_score >= 40:
            return "fair"
        else:
            return "poor"
            
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "overall_score": self.overall_score,
            "categories": self.categories,
            "status": self.get_status(),
            "issues": self.issues,
            "suggestions": self.suggestions,
            "last_updated": self.last_updated.isoformat()
        }

@dataclass
class ActivityData:
    """활동 데이터 모델"""
    date: datetime
    activity_count: int
    details: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "date": self.date.isoformat(),
            "activity_count": self.activity_count,
            "details": self.details
        }

@dataclass
class ProgressData:
    """진행률 데이터 모델"""
    title: str
    current: float
    total: float
    unit: str = ""
    status: str = "in_progress"
    
    @property
    def percentage(self) -> float:
        """퍼센트 계산"""
        if self.total == 0:
            return 0
        return (self.current / self.total) * 100
        
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리 변환"""
        return {
            "title": self.title,
            "current": self.current,
            "total": self.total,
            "percentage": self.percentage,
            "unit": self.unit,
            "status": self.status
        }

class WidgetDataAdapter:
    """위젯 데이터 어댑터"""
    
    @staticmethod
    def adapt_session_data(raw_data: Dict[str, Any]) -> SessionData:
        """세션 데이터 변환"""
        return SessionData(
            name=raw_data.get("session_name", ""),
            id=raw_data.get("session_id", ""),
            status=SessionStatus(raw_data.get("status", "active")),
            created_at=datetime.fromisoformat(raw_data.get("created_at", datetime.now().isoformat())),
            last_activity=datetime.fromisoformat(raw_data["last_activity"]) if raw_data.get("last_activity") else None,
            windows=raw_data.get("windows", []),
            panes=raw_data.get("panes", 0),
            claude_active=raw_data.get("claude_active", False),
            metadata=raw_data.get("metadata", {})
        )
        
    @staticmethod
    def adapt_health_data(raw_data: Dict[str, Any]) -> HealthData:
        """건강도 데이터 변환"""
        return HealthData(
            overall_score=raw_data.get("overall_score", 0),
            categories=raw_data.get("categories", {}),
            issues=raw_data.get("issues", []),
            suggestions=raw_data.get("suggestions", []),
            last_updated=datetime.fromisoformat(raw_data.get("last_updated", datetime.now().isoformat()))
        )
        
    @staticmethod
    def adapt_activity_data(raw_data: Dict[str, Any]) -> ActivityData:
        """활동 데이터 변환"""
        return ActivityData(
            date=datetime.fromisoformat(raw_data.get("date", datetime.now().isoformat())),
            activity_count=raw_data.get("activity_count", 0),
            details=raw_data.get("details", [])
        )
        
    @staticmethod
    def adapt_progress_data(raw_data: Dict[str, Any]) -> ProgressData:
        """진행률 데이터 변환"""
        return ProgressData(
            title=raw_data.get("title", ""),
            current=raw_data.get("current", 0),
            total=raw_data.get("total", 100),
            unit=raw_data.get("unit", ""),
            status=raw_data.get("status", "in_progress")
        )
```

### Day 2: TUI 렌더러 구현

#### 2.1 TUI 렌더러
**파일**: `libs/dashboard/renderers/tui_renderer.py`
```python
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.text import Text
from rich.tree import Tree
from rich.columns import Columns
from rich.align import Align
from rich import box
from typing import Dict, Any, List, Optional

from .base_renderer import BaseRenderer, RenderFormat, WidgetType
from .widget_models import SessionData, HealthData, ActivityData, ProgressData, WidgetDataAdapter

class TUIRenderer(BaseRenderer):
    """Rich 기반 TUI 렌더러"""
    
    def __init__(self, console: Optional[Console] = None):
        super().__init__(RenderFormat.TUI)
        self.console = console or Console()
        
    def render_widget(self, widget_type: WidgetType, data: Dict[str, Any], 
                     options: Optional[Dict[str, Any]] = None) -> Any:
        """위젯 렌더링"""
        options = options or {}
        
        renderers = {
            WidgetType.SESSION_BROWSER: self._render_session_browser,
            WidgetType.HEALTH_METER: self._render_health_meter,
            WidgetType.ACTIVITY_HEATMAP: self._render_activity_heatmap,
            WidgetType.PROGRESS_TRACKER: self._render_progress_tracker,
            WidgetType.LOG_VIEWER: self._render_log_viewer,
            WidgetType.GIT_ACTIVITY: self._render_git_activity,
            WidgetType.METRICS_CHART: self._render_metrics_chart,
            WidgetType.STATUS_CARD: self._render_status_card
        }
        
        renderer = renderers.get(widget_type)
        if not renderer:
            raise ValueError(f"No renderer for widget type: {widget_type}")
            
        return renderer(data, options)
        
    def render_layout(self, layout: Dict[str, Any], widgets: List[Dict[str, Any]]) -> Layout:
        """레이아웃 렌더링"""
        rich_layout = Layout()
        
        # 레이아웃 구조 생성
        if layout.get("type") == "split":
            rich_layout.split(
                *[Layout(name=w["name"]) for w in widgets],
                direction=layout.get("direction", "vertical")
            )
        elif layout.get("type") == "grid":
            # 그리드 레이아웃 처리
            rows = layout.get("rows", 1)
            cols = layout.get("cols", 1)
            # 구현 필요
            
        # 위젯 렌더링 및 배치
        for widget in widgets:
            widget_content = self.render_widget(
                WidgetType(widget["type"]),
                widget["data"],
                widget.get("options")
            )
            rich_layout[widget["name"]].update(widget_content)
            
        return rich_layout
        
    def render_container(self, title: str, content: Any, 
                        options: Optional[Dict[str, Any]] = None) -> Panel:
        """컨테이너 렌더링"""
        options = options or {}
        
        return Panel(
            content,
            title=title,
            title_align=options.get("title_align", "left"),
            border_style=options.get("border_style", "blue"),
            box=getattr(box, options.get("box_type", "ROUNDED"), box.ROUNDED),
            expand=options.get("expand", True)
        )
        
    # 위젯별 렌더링 메서드
    def _render_session_browser(self, data: Dict[str, Any], options: Dict[str, Any]) -> Any:
        """세션 브라우저 렌더링"""
        sessions = [WidgetDataAdapter.adapt_session_data(s) for s in data.get("sessions", [])]
        view_mode = options.get("view_mode", "table")
        
        if view_mode == "table":
            return self._render_session_table(sessions)
        elif view_mode == "tree":
            return self._render_session_tree(sessions)
        elif view_mode == "cards":
            return self._render_session_cards(sessions)
        else:
            return self._render_session_table(sessions)
            
    def _render_session_table(self, sessions: List[SessionData]) -> Table:
        """세션 테이블 렌더링"""
        table = Table(
            title="Active Sessions",
            box=box.ROUNDED,
            show_header=True,
            header_style="bold magenta"
        )
        
        # 컬럼 추가
        table.add_column("Status", style="cyan", width=8)
        table.add_column("Name", style="green")
        table.add_column("Windows", justify="right")
        table.add_column("Panes", justify="right")
        table.add_column("Claude", justify="center")
        table.add_column("Last Activity")
        
        # 행 추가
        for session in sessions:
            status_icon = "🟢" if session.status == SessionStatus.ACTIVE else "🔴"
            claude_icon = "✓" if session.claude_active else "✗"
            last_activity = session.last_activity.strftime("%H:%M:%S") if session.last_activity else "-"
            
            table.add_row(
                status_icon,
                session.name,
                str(len(session.windows)),
                str(session.panes),
                claude_icon,
                last_activity
            )
            
        return table
        
    def _render_session_tree(self, sessions: List[SessionData]) -> Tree:
        """세션 트리 렌더링"""
        tree = Tree("Sessions")
        
        for session in sessions:
            status_color = "green" if session.status == SessionStatus.ACTIVE else "red"
            session_branch = tree.add(
                f"[{status_color}]{session.name}[/{status_color}]"
            )
            
            # 윈도우 추가
            for window in session.windows:
                window_branch = session_branch.add(f"Window: {window.get('name', 'unnamed')}")
                
                # 페인 추가
                for pane in window.get("panes", []):
                    pane_info = f"Pane {pane.get('index', '?')}: {pane.get('command', 'shell')}"
                    window_branch.add(pane_info)
                    
        return tree
        
    def _render_session_cards(self, sessions: List[SessionData]) -> Columns:
        """세션 카드 렌더링"""
        cards = []
        
        for session in sessions:
            status_color = "green" if session.status == SessionStatus.ACTIVE else "red"
            
            card_content = f"""[{status_color}]● {session.status.value}[/{status_color}]
Windows: {len(session.windows)}
Panes: {session.panes}
Claude: {'Active' if session.claude_active else 'Inactive'}
Last Activity: {session.last_activity.strftime('%H:%M:%S') if session.last_activity else '-'}"""
            
            card = Panel(
                card_content,
                title=session.name,
                border_style=status_color,
                width=30
            )
            cards.append(card)
            
        return Columns(cards, equal=True, expand=True)
        
    def _render_health_meter(self, data: Dict[str, Any], options: Dict[str, Any]) -> Panel:
        """건강도 미터 렌더링"""
        health = WidgetDataAdapter.adapt_health_data(data)
        
        # 전체 점수 색상
        score_color = self._get_score_color(health.overall_score)
        
        # 건강도 바
        health_bar = self._create_progress_bar(
            health.overall_score, 
            100, 
            f"Overall Health: {health.overall_score:.1f}%",
            score_color
        )
        
        # 카테고리별 점수
        category_bars = []
        for category, score in health.categories.items():
            cat_color = self._get_score_color(score)
            cat_bar = self._create_progress_bar(
                score, 
                100, 
                f"{category.replace('_', ' ').title()}: {score:.1f}%",
                cat_color,
                width=40
            )
            category_bars.append(cat_bar)
            
        # 제안사항
        suggestions_text = "\n".join([f"• {s}" for s in health.suggestions[:3]])
        
        # 전체 구성
        content = f"{health_bar}\n\n"
        content += "\n".join(category_bars)
        
        if suggestions_text:
            content += f"\n\n[yellow]Suggestions:[/yellow]\n{suggestions_text}"
            
        return Panel(
            content,
            title="Project Health",
            border_style=score_color
        )
        
    def _render_activity_heatmap(self, data: Dict[str, Any], options: Dict[str, Any]) -> Panel:
        """활동 히트맵 렌더링"""
        activities = [WidgetDataAdapter.adapt_activity_data(a) for a in data.get("activities", [])]
        
        # 주별로 그룹화
        weeks = self._group_activities_by_week(activities)
        
        # 히트맵 생성
        heatmap_rows = []
        
        # 요일 헤더
        day_headers = "   " + " ".join(["Su", "Mo", "Tu", "We", "Th", "Fr", "Sa"])
        heatmap_rows.append(day_headers)
        
        # 주별 행
        for week_num, week_activities in enumerate(weeks[-12:]):  # 최근 12주
            week_row = f"W{week_num+1:2d} "
            
            for day in range(7):
                if day < len(week_activities):
                    activity = week_activities[day]
                    week_row += self._get_activity_block(activity.activity_count) + " "
                else:
                    week_row += "  "
                    
            heatmap_rows.append(week_row)
            
        # 범례
        legend = "\nLess " + "".join([
            self._get_activity_block(i) for i in [0, 2, 5, 10, 20]
        ]) + " More"
        
        heatmap_rows.append(legend)
        
        return Panel(
            "\n".join(heatmap_rows),
            title="Activity Heatmap",
            border_style="green"
        )
        
    def _render_progress_tracker(self, data: Dict[str, Any], options: Dict[str, Any]) -> Panel:
        """진행률 트래커 렌더링"""
        progresses = [WidgetDataAdapter.adapt_progress_data(p) for p in data.get("progresses", [])]
        
        progress_bars = []
        for progress in progresses:
            color = self._get_progress_color(progress.status)
            bar = self._create_progress_bar(
                progress.current,
                progress.total,
                f"{progress.title}: {progress.current}/{progress.total} {progress.unit}",
                color
            )
            progress_bars.append(bar)
            
        return Panel(
            "\n".join(progress_bars),
            title="Progress Tracker",
            border_style="blue"
        )
        
    def _render_log_viewer(self, data: Dict[str, Any], options: Dict[str, Any]) -> Panel:
        """로그 뷰어 렌더링"""
        logs = data.get("logs", [])
        max_lines = options.get("max_lines", 20)
        
        log_lines = []
        for log in logs[-max_lines:]:
            level = log.get("level", "info")
            timestamp = log.get("timestamp", "")
            message = log.get("message", "")
            
            level_color = {
                "debug": "dim",
                "info": "blue",
                "warning": "yellow",
                "error": "red"
            }.get(level, "white")
            
            log_line = f"[{level_color}]{timestamp} [{level.upper()}] {message}[/{level_color}]"
            log_lines.append(log_line)
            
        return Panel(
            "\n".join(log_lines),
            title="Logs",
            border_style="cyan"
        )
        
    def _render_git_activity(self, data: Dict[str, Any], options: Dict[str, Any]) -> Panel:
        """Git 활동 렌더링"""
        commits = data.get("commits", [])
        
        table = Table(box=box.SIMPLE_HEAD)
        table.add_column("Hash", style="cyan", width=8)
        table.add_column("Author", style="green")
        table.add_column("Message")
        table.add_column("Date", style="dim")
        
        for commit in commits[:10]:
            table.add_row(
                commit.get("hash", "")[:8],
                commit.get("author", ""),
                Text(commit.get("message", ""), overflow="ellipsis"),
                commit.get("date", "")
            )
            
        return Panel(table, title="Recent Commits", border_style="magenta")
        
    def _render_metrics_chart(self, data: Dict[str, Any], options: Dict[str, Any]) -> Panel:
        """메트릭 차트 렌더링 (간단한 ASCII 차트)"""
        metrics = data.get("metrics", [])
        chart_type = options.get("chart_type", "line")
        
        if not metrics:
            return Panel("No metrics data", title="Metrics")
            
        # 간단한 스파크라인 생성
        values = [m.get("value", 0) for m in metrics]
        max_val = max(values) if values else 1
        min_val = min(values) if values else 0
        
        # 정규화
        normalized = [(v - min_val) / (max_val - min_val) * 7 for v in values]
        
        # 스파크라인 문자
        spark_chars = " ▁▂▃▄▅▆▇█"
        sparkline = "".join([spark_chars[int(n)] for n in normalized[-20:]])
        
        content = f"Latest: {values[-1] if values else 0:.2f}\n"
        content += f"Range: {min_val:.2f} - {max_val:.2f}\n"
        content += f"Trend: {sparkline}"
        
        return Panel(content, title="Metrics", border_style="blue")
        
    def _render_status_card(self, data: Dict[str, Any], options: Dict[str, Any]) -> Panel:
        """상태 카드 렌더링"""
        title = data.get("title", "Status")
        value = data.get("value", "-")
        status = data.get("status", "normal")
        icon = data.get("icon", "●")
        
        status_colors = {
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "blue",
            "normal": "white"
        }
        
        color = status_colors.get(status, "white")
        
        content = Align.center(
            f"[{color}]{icon}[/{color}]\n\n[bold {color}]{value}[/bold {color}]",
            vertical="middle"
        )
        
        return Panel(
            content,
            title=title,
            border_style=color,
            width=20,
            height=7
        )
        
    # 유틸리티 메서드
    def _get_score_color(self, score: float) -> str:
        """점수에 따른 색상 반환"""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        else:
            return "red"
            
    def _get_progress_color(self, status: str) -> str:
        """진행 상태에 따른 색상 반환"""
        return {
            "completed": "green",
            "in_progress": "blue",
            "paused": "yellow",
            "failed": "red"
        }.get(status, "white")
        
    def _create_progress_bar(self, current: float, total: float, 
                            description: str, color: str, width: int = 50) -> str:
        """프로그레스 바 생성"""
        percentage = (current / total) * 100 if total > 0 else 0
        filled = int((percentage / 100) * width)
        
        bar = "█" * filled + "░" * (width - filled)
        
        return f"[{color}]{description}\n{bar} {percentage:.1f}%[/{color}]"
        
    def _get_activity_block(self, count: int) -> str:
        """활동 수에 따른 블록 반환"""
        if count == 0:
            return "⬜"
        elif count <= 2:
            return "🟩"
        elif count <= 5:
            return "🟧"
        elif count <= 10:
            return "🟥"
        else:
            return "🟪"
            
    def _group_activities_by_week(self, activities: List[ActivityData]) -> List[List[ActivityData]]:
        """활동을 주별로 그룹화"""
        # 간단한 구현 - 실제로는 더 정교한 날짜 처리 필요
        weeks = []
        current_week = []
        
        for i, activity in enumerate(activities):
            current_week.append(activity)
            
            if len(current_week) == 7:
                weeks.append(current_week)
                current_week = []
                
        if current_week:
            weeks.append(current_week)
            
        return weeks
```

### Day 3: Web 렌더러 구현

#### 3.1 Web 렌더러
**파일**: `libs/dashboard/renderers/web_renderer.py`
```python
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base_renderer import BaseRenderer, RenderFormat, WidgetType
from .widget_models import SessionData, HealthData, ActivityData, ProgressData, WidgetDataAdapter

class WebRenderer(BaseRenderer):
    """HTML/JavaScript 웹 렌더러"""
    
    def __init__(self):
        super().__init__(RenderFormat.WEB)
        self.component_id_counter = 0
        
    def render_widget(self, widget_type: WidgetType, data: Dict[str, Any], 
                     options: Optional[Dict[str, Any]] = None) -> str:
        """위젯을 HTML/JS로 렌더링"""
        options = options or {}
        
        renderers = {
            WidgetType.SESSION_BROWSER: self._render_session_browser,
            WidgetType.HEALTH_METER: self._render_health_meter,
            WidgetType.ACTIVITY_HEATMAP: self._render_activity_heatmap,
            WidgetType.PROGRESS_TRACKER: self._render_progress_tracker,
            WidgetType.LOG_VIEWER: self._render_log_viewer,
            WidgetType.GIT_ACTIVITY: self._render_git_activity,
            WidgetType.METRICS_CHART: self._render_metrics_chart,
            WidgetType.STATUS_CARD: self._render_status_card
        }
        
        renderer = renderers.get(widget_type)
        if not renderer:
            raise ValueError(f"No renderer for widget type: {widget_type}")
            
        return renderer(data, options)
        
    def render_layout(self, layout: Dict[str, Any], widgets: List[Dict[str, Any]]) -> str:
        """레이아웃을 HTML로 렌더링"""
        layout_type = layout.get("type", "grid")
        
        if layout_type == "grid":
            return self._render_grid_layout(layout, widgets)
        elif layout_type == "flex":
            return self._render_flex_layout(layout, widgets)
        elif layout_type == "tabs":
            return self._render_tabs_layout(layout, widgets)
        else:
            return self._render_grid_layout(layout, widgets)
            
    def render_container(self, title: str, content: str, 
                        options: Optional[Dict[str, Any]] = None) -> str:
        """컨테이너를 HTML로 렌더링"""
        options = options or {}
        container_id = self._generate_id("container")
        
        classes = ["dashboard-container"]
        if options.get("rounded", True):
            classes.append("rounded-lg")
        if options.get("shadow", True):
            classes.append("shadow")
            
        style = options.get("style", "")
        
        return f"""
        <div id="{container_id}" class="{' '.join(classes)} bg-white dark:bg-gray-800 p-4" style="{style}">
            {f'<h3 class="text-lg font-semibold mb-4">{title}</h3>' if title else ''}
            <div class="container-content">
                {content}
            </div>
        </div>
        """
        
    # 레이아웃 렌더링 메서드
    def _render_grid_layout(self, layout: Dict[str, Any], widgets: List[Dict[str, Any]]) -> str:
        """그리드 레이아웃 렌더링"""
        cols = layout.get("cols", 1)
        gap = layout.get("gap", 4)
        
        grid_html = f'<div class="grid grid-cols-{cols} gap-{gap}">'
        
        for widget in widgets:
            widget_html = self.render_widget(
                WidgetType(widget["type"]),
                widget["data"],
                widget.get("options")
            )
            grid_html += f'<div class="grid-item">{widget_html}</div>'
            
        grid_html += '</div>'
        
        return grid_html
        
    def _render_flex_layout(self, layout: Dict[str, Any], widgets: List[Dict[str, Any]]) -> str:
        """Flexbox 레이아웃 렌더링"""
        direction = "flex-row" if layout.get("direction") == "horizontal" else "flex-col"
        gap = layout.get("gap", 4)
        
        flex_html = f'<div class="flex {direction} gap-{gap}">'
        
        for widget in widgets:
            flex_grow = widget.get("grow", 1)
            widget_html = self.render_widget(
                WidgetType(widget["type"]),
                widget["data"],
                widget.get("options")
            )
            flex_html += f'<div class="flex-{flex_grow}">{widget_html}</div>'
            
        flex_html += '</div>'
        
        return flex_html
        
    def _render_tabs_layout(self, layout: Dict[str, Any], widgets: List[Dict[str, Any]]) -> str:
        """탭 레이아웃 렌더링"""
        tabs_id = self._generate_id("tabs")
        
        tabs_html = f'<div id="{tabs_id}" class="tabs-container">'
        
        # 탭 헤더
        tabs_html += '<div class="tabs-header flex border-b">'
        for i, widget in enumerate(widgets):
            active_class = "active" if i == 0 else ""
            tabs_html += f'''
                <button class="tab-button px-4 py-2 {active_class}" 
                        onclick="switchTab('{tabs_id}', {i})">
                    {widget.get("title", f"Tab {i+1}")}
                </button>
            '''
        tabs_html += '</div>'
        
        # 탭 컨텐츠
        tabs_html += '<div class="tabs-content">'
        for i, widget in enumerate(widgets):
            display = "block" if i == 0 else "none"
            widget_html = self.render_widget(
                WidgetType(widget["type"]),
                widget["data"],
                widget.get("options")
            )
            tabs_html += f'<div class="tab-pane" style="display: {display}">{widget_html}</div>'
            
        tabs_html += '</div></div>'
        
        # 탭 전환 스크립트
        tabs_html += f"""
        <script>
        function switchTab(containerId, tabIndex) {{
            const container = document.getElementById(containerId);
            const buttons = container.querySelectorAll('.tab-button');
            const panes = container.querySelectorAll('.tab-pane');
            
            buttons.forEach((btn, idx) => {{
                btn.classList.toggle('active', idx === tabIndex);
            }});
            
            panes.forEach((pane, idx) => {{
                pane.style.display = idx === tabIndex ? 'block' : 'none';
            }});
        }}
        </script>
        """
        
        return tabs_html
        
    # 위젯별 렌더링 메서드
    def _render_session_browser(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """세션 브라우저 HTML 렌더링"""
        sessions = [WidgetDataAdapter.adapt_session_data(s) for s in data.get("sessions", [])]
        component_id = self._generate_id("session-browser")
        view_mode = options.get("view_mode", "list")
        
        html = f'<div id="{component_id}" class="session-browser" data-view-mode="{view_mode}">'
        
        # 뷰 모드 선택 버튼
        html += '''
        <div class="view-mode-selector mb-4">
            <button onclick="changeSessionView('list')" class="px-3 py-1 mr-2 bg-blue-500 text-white rounded">List</button>
            <button onclick="changeSessionView('grid')" class="px-3 py-1 mr-2 bg-blue-500 text-white rounded">Grid</button>
            <button onclick="changeSessionView('tree')" class="px-3 py-1 bg-blue-500 text-white rounded">Tree</button>
        </div>
        '''
        
        # 세션 컨테이너
        html += '<div class="sessions-container">'
        
        if view_mode == "list":
            html += self._render_session_list(sessions)
        elif view_mode == "grid":
            html += self._render_session_grid(sessions)
        elif view_mode == "tree":
            html += self._render_session_tree_html(sessions)
            
        html += '</div></div>'
        
        # JavaScript 데이터
        html += f"""
        <script>
        window.sessionData = window.sessionData || {{}};
        window.sessionData['{component_id}'] = {json.dumps([s.to_dict() for s in sessions])};
        
        function changeSessionView(mode) {{
            const container = document.getElementById('{component_id}');
            container.dataset.viewMode = mode;
            // 실제 구현에서는 뷰 재렌더링
        }}
        </script>
        """
        
        return html
        
    def _render_session_list(self, sessions: List[SessionData]) -> str:
        """세션 리스트 뷰"""
        html = '<div class="space-y-2">'
        
        for session in sessions:
            status_color = "green" if session.status == SessionStatus.ACTIVE else "gray"
            html += f'''
            <div class="session-item flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700 rounded">
                <div class="flex items-center space-x-3">
                    <div class="w-3 h-3 bg-{status_color}-500 rounded-full"></div>
                    <span class="font-medium">{session.name}</span>
                    <span class="text-sm text-gray-500">{len(session.windows)} windows</span>
                </div>
                <div class="flex space-x-2">
                    <button class="px-2 py-1 text-xs bg-blue-500 text-white rounded">Enter</button>
                    <button class="px-2 py-1 text-xs bg-red-500 text-white rounded">Stop</button>
                </div>
            </div>
            '''
            
        html += '</div>'
        return html
        
    def _render_health_meter(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """건강도 미터 HTML 렌더링"""
        health = WidgetDataAdapter.adapt_health_data(data)
        component_id = self._generate_id("health-meter")
        
        score_color = self._get_score_color_class(health.overall_score)
        
        html = f'<div id="{component_id}" class="health-meter">'
        
        # 전체 점수
        html += f'''
        <div class="overall-score text-center mb-6">
            <div class="text-4xl font-bold {score_color}">{health.overall_score:.0f}/100</div>
            <div class="text-sm text-gray-500">Overall Health Score</div>
        </div>
        '''
        
        # 카테고리별 점수
        html += '<div class="categories space-y-3">'
        for category, score in health.categories.items():
            cat_color = self._get_score_color_class(score)
            html += f'''
            <div class="category-item">
                <div class="flex justify-between mb-1">
                    <span class="text-sm font-medium">{category.replace("_", " ").title()}</span>
                    <span class="text-sm {cat_color}">{score:.0f}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full bg-{self._get_score_color(score)}-500" 
                         style="width: {score}%"></div>
                </div>
            </div>
            '''
        html += '</div>'
        
        # 제안사항
        if health.suggestions:
            html += '''
            <div class="suggestions mt-4 p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded">
                <h4 class="text-sm font-medium text-yellow-800 dark:text-yellow-200 mb-2">Suggestions</h4>
                <ul class="text-sm text-yellow-700 dark:text-yellow-300">
            '''
            for suggestion in health.suggestions[:3]:
                html += f'<li>• {suggestion}</li>'
            html += '</ul></div>'
            
        html += '</div>'
        
        return html
        
    def _render_activity_heatmap(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """활동 히트맵 HTML 렌더링"""
        activities = data.get("activities", [])
        component_id = self._generate_id("activity-heatmap")
        
        html = f'<div id="{component_id}" class="activity-heatmap">'
        
        # 히트맵 그리드
        html += '<div class="heatmap-grid">'
        
        # 요일 헤더
        html += '<div class="day-labels grid grid-cols-7 text-xs text-gray-500 mb-1">'
        for day in ['S', 'M', 'T', 'W', 'T', 'F', 'S']:
            html += f'<div class="text-center">{day}</div>'
        html += '</div>'
        
        # 활동 그리드
        html += '<div class="activity-grid grid grid-cols-53 gap-1">'
        
        for activity in activities:
            count = activity.get("activity_count", 0)
            date = activity.get("date", "")
            color_class = self._get_activity_color_class(count)
            
            html += f'''
            <div class="activity-cell w-3 h-3 {color_class} rounded-sm cursor-pointer" 
                 title="{date}: {count} activities"
                 data-date="{date}"
                 data-count="{count}">
            </div>
            '''
            
        html += '</div>'
        
        # 범례
        html += '''
        <div class="legend flex items-center justify-center mt-4 text-xs text-gray-500">
            <span class="mr-2">Less</span>
            <div class="flex space-x-1">
                <div class="w-3 h-3 bg-gray-200 rounded-sm"></div>
                <div class="w-3 h-3 bg-green-200 rounded-sm"></div>
                <div class="w-3 h-3 bg-green-400 rounded-sm"></div>
                <div class="w-3 h-3 bg-green-600 rounded-sm"></div>
                <div class="w-3 h-3 bg-green-800 rounded-sm"></div>
            </div>
            <span class="ml-2">More</span>
        </div>
        '''
        
        html += '</div></div>'
        
        return html
        
    def _render_progress_tracker(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """진행률 트래커 HTML 렌더링"""
        progresses = [WidgetDataAdapter.adapt_progress_data(p) for p in data.get("progresses", [])]
        component_id = self._generate_id("progress-tracker")
        
        html = f'<div id="{component_id}" class="progress-tracker space-y-4">'
        
        for progress in progresses:
            status_color = self._get_progress_color(progress.status)
            html += f'''
            <div class="progress-item">
                <div class="flex justify-between mb-1">
                    <span class="text-sm font-medium">{progress.title}</span>
                    <span class="text-sm text-{status_color}-600">
                        {progress.current}/{progress.total} {progress.unit}
                    </span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="h-2 rounded-full bg-{status_color}-500 transition-all duration-300" 
                         style="width: {progress.percentage}%"></div>
                </div>
            </div>
            '''
            
        html += '</div>'
        
        return html
        
    def _render_log_viewer(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """로그 뷰어 HTML 렌더링"""
        logs = data.get("logs", [])
        component_id = self._generate_id("log-viewer")
        max_height = options.get("max_height", "400px")
        
        html = f'''
        <div id="{component_id}" class="log-viewer">
            <div class="log-controls mb-2 flex justify-between">
                <select class="text-sm border rounded px-2 py-1">
                    <option value="all">All Levels</option>
                    <option value="debug">Debug</option>
                    <option value="info">Info</option>
                    <option value="warning">Warning</option>
                    <option value="error">Error</option>
                </select>
                <button class="text-sm bg-gray-500 text-white px-2 py-1 rounded">Clear</button>
            </div>
            <div class="log-container bg-gray-900 text-gray-100 p-2 rounded font-mono text-xs overflow-y-auto" 
                 style="max-height: {max_height}">
        '''
        
        for log in logs:
            level = log.get("level", "info")
            timestamp = log.get("timestamp", "")
            message = log.get("message", "")
            
            level_colors = {
                "debug": "text-gray-400",
                "info": "text-blue-400",
                "warning": "text-yellow-400",
                "error": "text-red-400"
            }
            
            color_class = level_colors.get(level, "text-gray-100")
            
            html += f'''
            <div class="log-entry {color_class}">
                <span class="text-gray-500">{timestamp}</span>
                <span class="level-badge">[{level.upper()}]</span>
                <span class="message">{self._escape_html(message)}</span>
            </div>
            '''
            
        html += '</div></div>'
        
        return html
        
    def _render_git_activity(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """Git 활동 HTML 렌더링"""
        commits = data.get("commits", [])
        component_id = self._generate_id("git-activity")
        
        html = f'<div id="{component_id}" class="git-activity">'
        
        html += '''
        <table class="w-full text-sm">
            <thead>
                <tr class="border-b">
                    <th class="text-left py-2">Commit</th>
                    <th class="text-left py-2">Author</th>
                    <th class="text-left py-2">Message</th>
                    <th class="text-left py-2">Date</th>
                </tr>
            </thead>
            <tbody>
        '''
        
        for commit in commits[:10]:
            html += f'''
            <tr class="border-b hover:bg-gray-50 dark:hover:bg-gray-700">
                <td class="py-2 text-blue-600 font-mono">{commit.get("hash", "")[:8]}</td>
                <td class="py-2">{commit.get("author", "")}</td>
                <td class="py-2 truncate max-w-xs">{commit.get("message", "")}</td>
                <td class="py-2 text-gray-500">{commit.get("date", "")}</td>
            </tr>
            '''
            
        html += '</tbody></table></div>'
        
        return html
        
    def _render_metrics_chart(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """메트릭 차트 HTML 렌더링"""
        metrics = data.get("metrics", [])
        component_id = self._generate_id("metrics-chart")
        chart_type = options.get("chart_type", "line")
        
        html = f'<div id="{component_id}" class="metrics-chart">'
        
        # Canvas 요소
        html += f'<canvas id="{component_id}-canvas" width="400" height="200"></canvas>'
        
        # Chart.js 스크립트
        html += f"""
        <script>
        (function() {{
            const ctx = document.getElementById('{component_id}-canvas').getContext('2d');
            const data = {json.dumps(metrics)};
            
            new Chart(ctx, {{
                type: '{chart_type}',
                data: {{
                    labels: data.map(d => d.label || d.date),
                    datasets: [{{
                        label: 'Metrics',
                        data: data.map(d => d.value),
                        borderColor: 'rgb(59, 130, 246)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        tension: 0.1
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }}
                }}
            }});
        }})();
        </script>
        """
        
        html += '</div>'
        
        return html
        
    def _render_status_card(self, data: Dict[str, Any], options: Dict[str, Any]) -> str:
        """상태 카드 HTML 렌더링"""
        title = data.get("title", "Status")
        value = data.get("value", "-")
        status = data.get("status", "normal")
        icon = data.get("icon", "")
        
        component_id = self._generate_id("status-card")
        
        status_colors = {
            "success": "green",
            "warning": "yellow",
            "error": "red",
            "info": "blue",
            "normal": "gray"
        }
        
        color = status_colors.get(status, "gray")
        
        html = f'''
        <div id="{component_id}" class="status-card bg-white dark:bg-gray-800 rounded-lg shadow p-4 text-center">
            <div class="text-{color}-500 text-3xl mb-2">{icon}</div>
            <h4 class="text-sm text-gray-500 mb-1">{title}</h4>
            <div class="text-2xl font-bold text-{color}-600">{value}</div>
        </div>
        '''
        
        return html
        
    # 유틸리티 메서드
    def _generate_id(self, prefix: str) -> str:
        """고유 ID 생성"""
        self.component_id_counter += 1
        return f"{prefix}-{self.component_id_counter}"
        
    def _escape_html(self, text: str) -> str:
        """HTML 이스케이프"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
        
    def _get_score_color(self, score: float) -> str:
        """점수에 따른 색상"""
        if score >= 80:
            return "green"
        elif score >= 60:
            return "yellow"
        else:
            return "red"
            
    def _get_score_color_class(self, score: float) -> str:
        """점수에 따른 CSS 클래스"""
        color = self._get_score_color(score)
        return f"text-{color}-500"
        
    def _get_activity_color_class(self, count: int) -> str:
        """활동 수에 따른 CSS 클래스"""
        if count == 0:
            return "bg-gray-200"
        elif count <= 2:
            return "bg-green-200"
        elif count <= 5:
            return "bg-green-400"
        elif count <= 10:
            return "bg-green-600"
        else:
            return "bg-green-800"
            
    def _get_progress_color(self, status: str) -> str:
        """진행 상태에 따른 색상"""
        return {
            "completed": "green",
            "in_progress": "blue",
            "paused": "yellow",
            "failed": "red"
        }.get(status, "gray")
```

### Day 4: Tauri 렌더러 및 통합

#### 4.1 Tauri 렌더러
**파일**: `libs/dashboard/renderers/tauri_renderer.py`
```python
import json
from typing import Dict, Any, List, Optional

from .base_renderer import BaseRenderer, RenderFormat, WidgetType
from .widget_models import SessionData, HealthData, ActivityData, ProgressData, WidgetDataAdapter

class TauriRenderer(BaseRenderer):
    """Tauri 네이티브 렌더러 (JSON 기반)"""
    
    def __init__(self):
        super().__init__(RenderFormat.TAURI)
        
    def render_widget(self, widget_type: WidgetType, data: Dict[str, Any], 
                     options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """위젯을 Tauri 컴포넌트 데이터로 렌더링"""
        options = options or {}
        
        # 기본 위젯 구조
        widget_data = {
            "type": widget_type.value,
            "id": self._generate_id(widget_type.value),
            "data": data,
            "options": options,
            "metadata": {
                "rendered_at": datetime.now().isoformat(),
                "renderer": "tauri"
            }
        }
        
        # 위젯 타입별 특수 처리
        processors = {
            WidgetType.SESSION_BROWSER: self._process_session_browser,
            WidgetType.HEALTH_METER: self._process_health_meter,
            WidgetType.ACTIVITY_HEATMAP: self._process_activity_heatmap,
            WidgetType.PROGRESS_TRACKER: self._process_progress_tracker,
            WidgetType.LOG_VIEWER: self._process_log_viewer,
            WidgetType.GIT_ACTIVITY: self._process_git_activity,
            WidgetType.METRICS_CHART: self._process_metrics_chart,
            WidgetType.STATUS_CARD: self._process_status_card
        }
        
        processor = processors.get(widget_type)
        if processor:
            widget_data = processor(widget_data)
            
        return widget_data
        
    def render_layout(self, layout: Dict[str, Any], widgets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """레이아웃을 Tauri 레이아웃 데이터로 렌더링"""
        return {
            "type": "layout",
            "layout_type": layout.get("type", "grid"),
            "properties": {
                "cols": layout.get("cols", 1),
                "rows": layout.get("rows", 1),
                "gap": layout.get("gap", 4),
                "padding": layout.get("padding", 4)
            },
            "children": [
                self.render_widget(
                    WidgetType(widget["type"]),
                    widget["data"],
                    widget.get("options")
                ) for widget in widgets
            ],
            "metadata": {
                "rendered_at": datetime.now().isoformat(),
                "renderer": "tauri"
            }
        }
        
    def render_container(self, title: str, content: Any, 
                        options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """컨테이너를 Tauri 컨테이너 데이터로 렌더링"""
        options = options or {}
        
        return {
            "type": "container",
            "id": self._generate_id("container"),
            "title": title,
            "content": content,
            "style": {
                "background": options.get("background", "surface"),
                "border": options.get("border", True),
                "shadow": options.get("shadow", True),
                "rounded": options.get("rounded", True),
                "padding": options.get("padding", 16)
            },
            "metadata": {
                "rendered_at": datetime.now().isoformat(),
                "renderer": "tauri"
            }
        }
        
    # 위젯별 데이터 처리 메서드
    def _process_session_browser(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """세션 브라우저 데이터 처리"""
        sessions = widget_data["data"].get("sessions", [])
        
        # 세션 데이터 변환
        processed_sessions = []
        for session in sessions:
            session_model = WidgetDataAdapter.adapt_session_data(session)
            processed_sessions.append({
                **session_model.to_dict(),
                "actions": [
                    {"id": "enter", "label": "Enter", "icon": "login"},
                    {"id": "stop", "label": "Stop", "icon": "stop"},
                    {"id": "restart", "label": "Restart", "icon": "refresh"}
                ]
            })
            
        widget_data["data"]["sessions"] = processed_sessions
        widget_data["view_modes"] = ["list", "grid", "tree"]
        widget_data["default_view"] = widget_data["options"].get("view_mode", "list")
        
        return widget_data
        
    def _process_health_meter(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """건강도 미터 데이터 처리"""
        health = WidgetDataAdapter.adapt_health_data(widget_data["data"])
        
        widget_data["data"] = {
            **health.to_dict(),
            "chart_data": {
                "type": "radar",
                "labels": list(health.categories.keys()),
                "values": list(health.categories.values())
            },
            "color_scheme": self._get_health_color_scheme(health.overall_score)
        }
        
        return widget_data
        
    def _process_activity_heatmap(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """활동 히트맵 데이터 처리"""
        activities = widget_data["data"].get("activities", [])
        
        # 히트맵 매트릭스 생성
        matrix = self._create_activity_matrix(activities)
        
        widget_data["data"]["matrix"] = matrix
        widget_data["data"]["color_scale"] = [
            {"threshold": 0, "color": "#ebedf0"},
            {"threshold": 1, "color": "#9be9a8"},
            {"threshold": 5, "color": "#40c463"},
            {"threshold": 10, "color": "#30a14e"},
            {"threshold": 20, "color": "#216e39"}
        ]
        
        return widget_data
        
    def _process_progress_tracker(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """진행률 트래커 데이터 처리"""
        progresses = widget_data["data"].get("progresses", [])
        
        processed_progresses = []
        for progress in progresses:
            progress_model = WidgetDataAdapter.adapt_progress_data(progress)
            processed_progresses.append({
                **progress_model.to_dict(),
                "color": self._get_progress_color(progress_model.status),
                "animated": True
            })
            
        widget_data["data"]["progresses"] = processed_progresses
        
        return widget_data
        
    def _process_log_viewer(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """로그 뷰어 데이터 처리"""
        logs = widget_data["data"].get("logs", [])
        
        # 로그 레벨별 그룹화
        grouped_logs = {}
        for log in logs:
            level = log.get("level", "info")
            if level not in grouped_logs:
                grouped_logs[level] = []
            grouped_logs[level].append(log)
            
        widget_data["data"]["grouped_logs"] = grouped_logs
        widget_data["data"]["filters"] = {
            "levels": ["debug", "info", "warning", "error"],
            "search_enabled": True,
            "date_range_enabled": True
        }
        
        return widget_data
        
    def _process_git_activity(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """Git 활동 데이터 처리"""
        commits = widget_data["data"].get("commits", [])
        
        # 커밋 통계 생성
        stats = {
            "total_commits": len(commits),
            "authors": list(set(c.get("author", "") for c in commits)),
            "date_range": {
                "start": min(c.get("date", "") for c in commits) if commits else None,
                "end": max(c.get("date", "") for c in commits) if commits else None
            }
        }
        
        widget_data["data"]["stats"] = stats
        widget_data["data"]["chart_data"] = self._create_commit_chart_data(commits)
        
        return widget_data
        
    def _process_metrics_chart(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """메트릭 차트 데이터 처리"""
        metrics = widget_data["data"].get("metrics", [])
        chart_type = widget_data["options"].get("chart_type", "line")
        
        # 차트 라이브러리용 데이터 변환
        chart_data = {
            "type": chart_type,
            "datasets": [{
                "label": "Metrics",
                "data": [{"x": m.get("date", ""), "y": m.get("value", 0)} for m in metrics],
                "borderColor": self.get_color("primary"),
                "backgroundColor": self._hex_to_rgba(self.get_color("primary"), 0.1)
            }],
            "options": {
                "responsive": True,
                "animations": widget_data["options"].get("animated", True),
                "interaction": {
                    "mode": "index",
                    "intersect": False
                }
            }
        }
        
        widget_data["data"]["chart_data"] = chart_data
        
        return widget_data
        
    def _process_status_card(self, widget_data: Dict[str, Any]) -> Dict[str, Any]:
        """상태 카드 데이터 처리"""
        status = widget_data["data"].get("status", "normal")
        
        # 상태별 스타일 정의
        status_styles = {
            "success": {"color": "green", "icon": "check-circle"},
            "warning": {"color": "yellow", "icon": "alert-triangle"},
            "error": {"color": "red", "icon": "x-circle"},
            "info": {"color": "blue", "icon": "info-circle"},
            "normal": {"color": "gray", "icon": "circle"}
        }
        
        style = status_styles.get(status, status_styles["normal"])
        widget_data["data"]["style"] = style
        
        return widget_data
        
    # 유틸리티 메서드
    def _generate_id(self, prefix: str) -> str:
        """고유 ID 생성"""
        import uuid
        return f"{prefix}-{uuid.uuid4().hex[:8]}"
        
    def _get_health_color_scheme(self, score: float) -> str:
        """건강도 점수에 따른 색상 스키마"""
        if score >= 80:
            return "success"
        elif score >= 60:
            return "warning"
        else:
            return "danger"
            
    def _get_progress_color(self, status: str) -> str:
        """진행 상태에 따른 색상"""
        colors = {
            "completed": "#10b981",
            "in_progress": "#3b82f6",
            "paused": "#f59e0b",
            "failed": "#ef4444"
        }
        return colors.get(status, "#6b7280")
        
    def _create_activity_matrix(self, activities: List[Dict[str, Any]]) -> List[List[int]]:
        """활동 데이터를 매트릭스로 변환"""
        # 52주 x 7일 매트릭스 생성
        matrix = [[0 for _ in range(7)] for _ in range(52)]
        
        # 활동 데이터 매핑
        for activity in activities:
            date = datetime.fromisoformat(activity.get("date", datetime.now().isoformat()))
            week_of_year = date.isocalendar()[1] - 1
            day_of_week = date.weekday()
            
            if 0 <= week_of_year < 52 and 0 <= day_of_week < 7:
                matrix[week_of_year][day_of_week] = activity.get("activity_count", 0)
                
        return matrix
        
    def _create_commit_chart_data(self, commits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """커밋 데이터를 차트 데이터로 변환"""
        # 일별 커밋 수 집계
        daily_commits = {}
        
        for commit in commits:
            date = commit.get("date", "").split("T")[0]
            daily_commits[date] = daily_commits.get(date, 0) + 1
            
        return {
            "labels": list(daily_commits.keys()),
            "values": list(daily_commits.values())
        }
        
    def _hex_to_rgba(self, hex_color: str, alpha: float) -> str:
        """HEX 색상을 RGBA로 변환"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"rgba({r}, {g}, {b}, {alpha})"
```

#### 4.2 렌더러 팩토리 및 통합
**파일**: `libs/dashboard/renderers/renderer_factory.py`
```python
from typing import Dict, Any, Optional, Type

from .base_renderer import BaseRenderer, RenderFormat, renderer_registry
from .tui_renderer import TUIRenderer
from .web_renderer import WebRenderer
from .tauri_renderer import TauriRenderer

class RendererFactory:
    """렌더러 팩토리"""
    
    # 렌더러 클래스 매핑
    _renderer_classes: Dict[RenderFormat, Type[BaseRenderer]] = {
        RenderFormat.TUI: TUIRenderer,
        RenderFormat.WEB: WebRenderer,
        RenderFormat.TAURI: TauriRenderer
    }
    
    @classmethod
    def create(cls, format: RenderFormat, **kwargs) -> BaseRenderer:
        """렌더러 생성"""
        renderer_class = cls._renderer_classes.get(format)
        if not renderer_class:
            raise ValueError(f"Unknown render format: {format}")
            
        return renderer_class(**kwargs)
        
    @classmethod
    def register_all(cls):
        """모든 렌더러를 레지스트리에 등록"""
        for format, renderer_class in cls._renderer_classes.items():
            renderer = renderer_class()
            renderer_registry.register(format, renderer)
            
    @classmethod
    def get_renderer(cls, format: RenderFormat) -> BaseRenderer:
        """렌더러 조회"""
        return renderer_registry.get(format)
        
    @classmethod
    def render_universal(cls, widget_type: str, data: Dict[str, Any], 
                        format: Optional[RenderFormat] = None,
                        options: Optional[Dict[str, Any]] = None) -> Any:
        """범용 렌더링 메서드"""
        if format:
            # 특정 포맷으로 렌더링
            renderer = cls.get_renderer(format)
            return renderer.render("widget", {
                "type": widget_type,
                "data": data
            }, options)
        else:
            # 모든 포맷으로 렌더링
            results = {}
            for fmt in RenderFormat:
                try:
                    renderer = cls.get_renderer(fmt)
                    results[fmt.value] = renderer.render("widget", {
                        "type": widget_type,
                        "data": data
                    }, options)
                except Exception as e:
                    results[fmt.value] = {"error": str(e)}
            return results

# 초기화 시 모든 렌더러 등록
RendererFactory.register_all()

# 간편 함수
def render_widget(widget_type: str, data: Dict[str, Any], 
                 format: RenderFormat, options: Optional[Dict[str, Any]] = None) -> Any:
    """위젯 렌더링 간편 함수"""
    return RendererFactory.render_universal(widget_type, data, format, options)

def render_all_formats(widget_type: str, data: Dict[str, Any], 
                      options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """모든 포맷으로 렌더링하는 간편 함수"""
    return RendererFactory.render_universal(widget_type, data, None, options)
```

### Day 5: 테스트 및 최적화

#### 5.1 렌더러 테스트
**파일**: `tests/test_renderers.py`
```python
import pytest
from rich.console import Console

from libs.dashboard.renderers.base_renderer import RenderFormat, WidgetType
from libs.dashboard.renderers.renderer_factory import RendererFactory, render_widget, render_all_formats
from libs.dashboard.renderers.widget_models import SessionData, HealthData, SessionStatus

class TestRenderers:
    """렌더러 테스트"""
    
    @pytest.fixture
    def sample_session_data(self):
        """샘플 세션 데이터"""
        return {
            "sessions": [{
                "session_name": "test-session",
                "session_id": "12345",
                "status": "active",
                "created_at": "2024-01-01T10:00:00",
                "windows": [
                    {"name": "main", "panes": [{"index": 0, "command": "vim"}]}
                ],
                "panes": 1,
                "claude_active": True
            }]
        }
        
    @pytest.fixture
    def sample_health_data(self):
        """샘플 건강도 데이터"""
        return {
            "overall_score": 85.5,
            "categories": {
                "build": 90,
                "tests": 80,
                "dependencies": 85,
                "security": 88
            },
            "suggestions": [
                "Update outdated dependencies",
                "Increase test coverage"
            ]
        }
        
    def test_tui_renderer(self, sample_session_data):
        """TUI 렌더러 테스트"""
        result = render_widget(
            WidgetType.SESSION_BROWSER.value,
            sample_session_data,
            RenderFormat.TUI
        )
        
        assert result is not None
        # TUI 렌더러는 Rich 객체를 반환
        assert hasattr(result, '__rich__') or hasattr(result, '__rich_console__')
        
    def test_web_renderer(self, sample_health_data):
        """웹 렌더러 테스트"""
        result = render_widget(
            WidgetType.HEALTH_METER.value,
            sample_health_data,
            RenderFormat.WEB
        )
        
        assert isinstance(result, str)
        assert '<div' in result
        assert 'health-meter' in result
        assert '85.5' in result or '86' in result  # 반올림 처리
        
    def test_tauri_renderer(self, sample_session_data):
        """Tauri 렌더러 테스트"""
        result = render_widget(
            WidgetType.SESSION_BROWSER.value,
            sample_session_data,
            RenderFormat.TAURI
        )
        
        assert isinstance(result, dict)
        assert result["type"] == "session_browser"
        assert "data" in result
        assert "sessions" in result["data"]
        assert len(result["data"]["sessions"]) == 1
        
    def test_render_all_formats(self, sample_health_data):
        """모든 포맷 렌더링 테스트"""
        results = render_all_formats(
            WidgetType.HEALTH_METER.value,
            sample_health_data
        )
        
        assert len(results) == 3
        assert RenderFormat.TUI.value in results
        assert RenderFormat.WEB.value in results
        assert RenderFormat.TAURI.value in results
        
    def test_renderer_factory(self):
        """렌더러 팩토리 테스트"""
        # TUI 렌더러 생성
        tui_renderer = RendererFactory.create(RenderFormat.TUI)
        assert tui_renderer.format == RenderFormat.TUI
        
        # 웹 렌더러 생성
        web_renderer = RendererFactory.create(RenderFormat.WEB)
        assert web_renderer.format == RenderFormat.WEB
        
        # Tauri 렌더러 생성
        tauri_renderer = RendererFactory.create(RenderFormat.TAURI)
        assert tauri_renderer.format == RenderFormat.TAURI
        
    def test_widget_data_adapter(self):
        """위젯 데이터 어댑터 테스트"""
        from libs.dashboard.renderers.widget_models import WidgetDataAdapter
        
        raw_session = {
            "session_name": "test",
            "session_id": "123",
            "status": "active",
            "created_at": "2024-01-01T10:00:00"
        }
        
        session = WidgetDataAdapter.adapt_session_data(raw_session)
        assert isinstance(session, SessionData)
        assert session.name == "test"
        assert session.status == SessionStatus.ACTIVE
        
    def test_renderer_options(self, sample_session_data):
        """렌더러 옵션 테스트"""
        # 뷰 모드 옵션
        options = {"view_mode": "grid"}
        
        result = render_widget(
            WidgetType.SESSION_BROWSER.value,
            sample_session_data,
            RenderFormat.WEB,
            options
        )
        
        assert 'data-view-mode="grid"' in result
        
    def test_error_handling(self):
        """에러 처리 테스트"""
        with pytest.raises(ValueError):
            # 잘못된 위젯 타입
            render_widget(
                "invalid_widget",
                {},
                RenderFormat.TUI
            )
            
    @pytest.mark.benchmark
    def test_renderer_performance(self, benchmark, sample_health_data):
        """렌더러 성능 테스트"""
        def render_health():
            return render_widget(
                WidgetType.HEALTH_METER.value,
                sample_health_data,
                RenderFormat.WEB
            )
            
        result = benchmark(render_health)
        assert result is not None
```

#### 5.2 성능 최적화
**파일**: `libs/dashboard/renderers/optimizations.py`
```python
from functools import lru_cache
from typing import Dict, Any, Tuple
import hashlib
import json

class RenderCache:
    """렌더링 캐시"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, Any] = {}
        
    def get_key(self, widget_type: str, data: Dict[str, Any], 
                format: str, options: Dict[str, Any] = None) -> str:
        """캐시 키 생성"""
        # 데이터를 정규화하여 일관된 키 생성
        normalized = {
            "widget_type": widget_type,
            "data": self._normalize_data(data),
            "format": format,
            "options": options or {}
        }
        
        # JSON 직렬화 후 해시
        serialized = json.dumps(normalized, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()
        
    def _normalize_data(self, data: Any) -> Any:
        """데이터 정규화"""
        if isinstance(data, dict):
            return {k: self._normalize_data(v) for k, v in sorted(data.items())}
        elif isinstance(data, list):
            return [self._normalize_data(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            return str(data)
            
    def get(self, key: str) -> Any:
        """캐시에서 조회"""
        return self._cache.get(key)
        
    def set(self, key: str, value: Any):
        """캐시에 저장"""
        # 크기 제한 확인
        if len(self._cache) >= self.max_size:
            # FIFO 방식으로 오래된 항목 제거
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            
        self._cache[key] = value
        
    def clear(self):
        """캐시 초기화"""
        self._cache.clear()

# 전역 캐시 인스턴스
render_cache = RenderCache()

def cached_render(func):
    """렌더링 캐시 데코레이터"""
    def wrapper(self, widget_type, data, options=None):
        # 캐시 키 생성
        cache_key = render_cache.get_key(
            widget_type.value if hasattr(widget_type, 'value') else widget_type,
            data,
            self.format.value if hasattr(self.format, 'value') else str(self.format),
            options
        )
        
        # 캐시 조회
        cached_result = render_cache.get(cache_key)
        if cached_result is not None:
            return cached_result
            
        # 실제 렌더링
        result = func(self, widget_type, data, options)
        
        # 캐시 저장
        render_cache.set(cache_key, result)
        
        return result
        
    return wrapper

class LazyRenderer:
    """지연 렌더링"""
    
    def __init__(self, renderer, widget_type, data, options=None):
        self.renderer = renderer
        self.widget_type = widget_type
        self.data = data
        self.options = options
        self._result = None
        
    def render(self):
        """실제 렌더링 수행"""
        if self._result is None:
            self._result = self.renderer.render_widget(
                self.widget_type,
                self.data,
                self.options
            )
        return self._result
        
    def __str__(self):
        """문자열 변환 시 렌더링"""
        return str(self.render())
        
    def __repr__(self):
        """표현 문자열"""
        return f"<LazyRenderer {self.widget_type}>"

class BatchRenderer:
    """배치 렌더링"""
    
    def __init__(self, renderer):
        self.renderer = renderer
        self.batch = []
        
    def add(self, widget_type, data, options=None):
        """배치에 추가"""
        self.batch.append({
            "widget_type": widget_type,
            "data": data,
            "options": options
        })
        
    def render_all(self):
        """배치 렌더링 수행"""
        results = []
        
        for item in self.batch:
            result = self.renderer.render_widget(
                item["widget_type"],
                item["data"],
                item["options"]
            )
            results.append(result)
            
        self.batch.clear()
        return results
```

## ✅ Phase 3 완료 기준

### 기능적 요구사항
- [ ] TUI 렌더러 완전 구현
- [ ] Web 렌더러 완전 구현
- [ ] Tauri 렌더러 완전 구현
- [ ] 모든 위젯 타입 지원
- [ ] 레이아웃 시스템 구현
- [ ] 테마 시스템 구현

### 기술적 요구사항
- [ ] 통합 렌더러 인터페이스
- [ ] 위젯 데이터 모델
- [ ] 렌더러 팩토리
- [ ] 캐싱 시스템
- [ ] 성능 최적화

### 품질 요구사항
- [ ] 단위 테스트 커버리지 90%
- [ ] 렌더링 성능 < 50ms
- [ ] 메모리 효율성
- [ ] 코드 재사용성 80%

## 🔧 테스트 명령어

```bash
# 렌더러 테스트
python -m pytest tests/test_renderers.py -v

# 성능 테스트
python -m pytest tests/test_renderers.py -v --benchmark-only

# 통합 테스트
python test_integration/test_renderer_integration.py
```

---

**다음 단계**: Phase 3 완료 후 `04-integration-advanced-features.md` 진행