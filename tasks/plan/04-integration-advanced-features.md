# 🚀 Phase 4: 통합 및 고급 기능

**Phase ID**: INTEGRATION-ADVANCED  
**예상 시간**: 1주 (5일)  
**선행 조건**: Phase 1, 2, 3 완료  
**후행 Phase**: 프로젝트 완료

## 🎯 Phase 목표

3가지 대시보드 인터페이스(TUI, Web, Tauri)를 통합 CLI로 관리하고, 고급 기능(키보드 네비게이션, 테마 시스템, 성능 최적화)을 구현한다.

## 📋 상세 작업 계획

### Day 1: 통합 CLI 인터페이스

#### 1.1 통합 대시보드 명령어
**파일**: `commands/dashboard.py` (업데이트)
```python
import click
import asyncio
import webbrowser
import subprocess
import sys
from typing import Optional
from enum import Enum

from libs.dashboard.renderers.base_renderer import RenderFormat
from libs.dashboard.renderers.renderer_factory import RendererFactory
from libs.dashboard.dashboard_server import DashboardServer
from libs.dashboard.dashboard_launcher import DashboardLauncher
from rich.console import Console
from rich.prompt import Prompt, Confirm

console = Console()

class DashboardInterface(Enum):
    """대시보드 인터페이스 타입"""
    TUI = "tui"
    WEB = "web" 
    TAURI = "tauri"
    AUTO = "auto"

@click.command()
@click.option('--interface', '-i', 
              type=click.Choice(['tui', 'web', 'tauri', 'auto']),
              default='auto',
              help='Dashboard interface to use')
@click.option('--port', '-p', 
              type=int,
              default=8080,
              help='Port for web dashboard')
@click.option('--host', '-h',
              default='localhost',
              help='Host for web dashboard')
@click.option('--dev', 
              is_flag=True,
              help='Development mode')
@click.option('--theme', '-t',
              type=click.Choice(['light', 'dark', 'auto']),
              default='auto',
              help='Theme preference')
@click.option('--detach', '-d',
              is_flag=True,
              help='Run in background (web/tauri only)')
def dashboard(interface: str, port: int, host: str, dev: bool, theme: str, detach: bool):
    """
    Launch the yesman-claude dashboard.
    
    Interfaces:
    - tui: Terminal UI dashboard (Rich-based)
    - web: Web browser dashboard
    - tauri: Native desktop application
    - auto: Automatically select best interface
    """
    try:
        launcher = DashboardLauncher()
        
        # 인터페이스 자동 선택
        if interface == 'auto':
            interface = launcher.detect_best_interface()
            console.print(f"[blue]Auto-selected interface: {interface}[/blue]")
        
        # 인터페이스별 실행
        if interface == DashboardInterface.TUI.value:
            launch_tui_dashboard(theme, dev)
        elif interface == DashboardInterface.WEB.value:
            launch_web_dashboard(host, port, theme, dev, detach)
        elif interface == DashboardInterface.TAURI.value:
            launch_tauri_dashboard(theme, dev, detach)
        else:
            console.print(f"[red]Unknown interface: {interface}[/red]")
            sys.exit(1)
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error launching dashboard: {e}[/red]")
        sys.exit(1)

def launch_tui_dashboard(theme: str, dev: bool):
    """TUI 대시보드 실행"""
    from libs.dashboard.tui_dashboard import TUIDashboard
    
    console.print("[green]Launching TUI dashboard...[/green]")
    
    # TUI 대시보드 인스턴스 생성
    tui = TUIDashboard(theme=theme, dev_mode=dev)
    
    # 실행
    tui.run()

def launch_web_dashboard(host: str, port: int, theme: str, dev: bool, detach: bool):
    """웹 대시보드 실행"""
    console.print(f"[green]Launching web dashboard on {host}:{port}...[/green]")
    
    # 웹 서버 시작
    server = DashboardServer(host=host, port=port, theme=theme, dev_mode=dev)
    
    if detach:
        # 백그라운드 실행
        server.start_background()
        console.print(f"[blue]Web dashboard running in background[/blue]")
        console.print(f"[blue]Access at: http://{host}:{port}[/blue]")
    else:
        # 브라우저 열기
        url = f"http://{host}:{port}"
        webbrowser.open(url)
        
        # 서버 실행
        console.print(f"[blue]Web dashboard available at: {url}[/blue]")
        console.print("[yellow]Press Ctrl+C to stop[/yellow]")
        
        asyncio.run(server.start())

def launch_tauri_dashboard(theme: str, dev: bool, detach: bool):
    """Tauri 대시보드 실행"""
    console.print("[green]Launching Tauri desktop dashboard...[/green]")
    
    tauri_dir = "tauri-dashboard"
    
    if dev:
        # 개발 모드
        cmd = ["npm", "run", "tauri", "dev"]
    else:
        # 프로덕션 모드 - 빌드된 앱 실행
        if sys.platform == "darwin":
            app_path = f"{tauri_dir}/src-tauri/target/release/bundle/macos/Yesman Claude.app"
            cmd = ["open", app_path]
        elif sys.platform == "win32":
            app_path = f"{tauri_dir}/src-tauri/target/release/yesman-claude.exe"
            cmd = [app_path]
        else:  # Linux
            app_path = f"{tauri_dir}/src-tauri/target/release/yesman-claude"
            cmd = [app_path]
    
    # 환경 변수 설정
    env = os.environ.copy()
    env["YESMAN_THEME"] = theme
    
    if detach:
        # 백그라운드 실행
        subprocess.Popen(cmd, cwd=tauri_dir, env=env)
        console.print("[blue]Tauri dashboard launched in background[/blue]")
    else:
        # 포그라운드 실행
        subprocess.run(cmd, cwd=tauri_dir, env=env)

# 추가 서브커맨드들
@click.group()
def dashboard_group():
    """Dashboard management commands"""
    pass

@dashboard_group.command()
def list_interfaces():
    """List available dashboard interfaces"""
    launcher = DashboardLauncher()
    available = launcher.get_available_interfaces()
    
    console.print("[bold]Available Dashboard Interfaces:[/bold]")
    for interface in available:
        info = launcher.get_interface_info(interface)
        console.print(f"  • {interface}: {info['description']}")
        console.print(f"    Status: {'✓ Available' if info['available'] else '✗ Not available'}")
        if not info['available']:
            console.print(f"    Reason: {info['reason']}")

@dashboard_group.command()
@click.option('--interface', '-i', required=True,
              type=click.Choice(['web', 'tauri']))
def build(interface: str):
    """Build dashboard for production"""
    if interface == 'web':
        build_web_dashboard()
    elif interface == 'tauri':
        build_tauri_dashboard()

def build_web_dashboard():
    """웹 대시보드 빌드"""
    console.print("[blue]Building web dashboard...[/blue]")
    
    # 의존성 설치
    subprocess.run(["npm", "install"], cwd="web-dashboard", check=True)
    
    # 빌드
    subprocess.run(["npm", "run", "build"], cwd="web-dashboard", check=True)
    
    console.print("[green]Web dashboard built successfully![/green]")

def build_tauri_dashboard():
    """Tauri 대시보드 빌드"""
    console.print("[blue]Building Tauri dashboard...[/blue]")
    
    # 의존성 설치
    subprocess.run(["npm", "install"], cwd="tauri-dashboard", check=True)
    
    # Tauri 빌드
    subprocess.run(["npm", "run", "tauri", "build"], cwd="tauri-dashboard", check=True)
    
    console.print("[green]Tauri dashboard built successfully![/green]")
```

#### 1.2 대시보드 런처
**파일**: `libs/dashboard/dashboard_launcher.py`
```python
import os
import sys
import shutil
import subprocess
from typing import List, Dict, Any, Optional
from enum import Enum

class DashboardLauncher:
    """대시보드 런처 - 최적 인터페이스 감지 및 실행"""
    
    def detect_best_interface(self) -> str:
        """최적의 대시보드 인터페이스 자동 감지"""
        
        # 1. 환경 변수 확인
        if os.environ.get('YESMAN_DASHBOARD_INTERFACE'):
            return os.environ['YESMAN_DASHBOARD_INTERFACE']
        
        # 2. GUI 환경 확인
        if self._is_gui_available():
            # Tauri 앱이 설치되어 있으면 우선 사용
            if self._is_tauri_available():
                return "tauri"
            # 아니면 웹 대시보드
            return "web"
        
        # 3. SSH/터미널 환경
        if self._is_ssh_session():
            # SSH 포트 포워딩이 가능하면 웹
            if self._can_use_port_forwarding():
                return "web"
            # 아니면 TUI
            return "tui"
        
        # 4. 기본값: TUI
        return "tui"
    
    def get_available_interfaces(self) -> List[str]:
        """사용 가능한 인터페이스 목록"""
        available = []
        
        # TUI는 항상 사용 가능
        available.append("tui")
        
        # 웹 서버 실행 가능 여부
        if self._check_web_dependencies():
            available.append("web")
        
        # Tauri 앱 사용 가능 여부
        if self._is_tauri_available():
            available.append("tauri")
        
        return available
    
    def get_interface_info(self, interface: str) -> Dict[str, Any]:
        """인터페이스 정보 조회"""
        info = {
            "tui": {
                "name": "Terminal UI",
                "description": "Rich-based terminal dashboard",
                "requirements": ["Python 3.8+", "Rich library"],
                "available": True,
                "reason": None
            },
            "web": {
                "name": "Web Dashboard",
                "description": "Browser-based dashboard",
                "requirements": ["Python 3.8+", "FastAPI", "Modern browser"],
                "available": self._check_web_dependencies(),
                "reason": None if self._check_web_dependencies() else "Missing web dependencies"
            },
            "tauri": {
                "name": "Desktop App",
                "description": "Native desktop application",
                "requirements": ["Tauri app installed", "GUI environment"],
                "available": self._is_tauri_available(),
                "reason": None if self._is_tauri_available() else "Tauri app not found"
            }
        }
        
        return info.get(interface, {})
    
    def _is_gui_available(self) -> bool:
        """GUI 환경 사용 가능 여부"""
        # macOS
        if sys.platform == "darwin":
            return True
        
        # Windows
        if sys.platform == "win32":
            return True
        
        # Linux - X11 또는 Wayland 확인
        if sys.platform.startswith("linux"):
            return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
        
        return False
    
    def _is_ssh_session(self) -> bool:
        """SSH 세션 여부 확인"""
        return bool(os.environ.get("SSH_CLIENT") or os.environ.get("SSH_TTY"))
    
    def _can_use_port_forwarding(self) -> bool:
        """포트 포워딩 가능 여부"""
        # SSH 설정 파일에서 포트 포워딩 허용 여부 확인
        # 간단히 구현 - 실제로는 더 정교한 확인 필요
        return not os.environ.get("YESMAN_NO_PORT_FORWARD")
    
    def _is_tauri_available(self) -> bool:
        """Tauri 앱 사용 가능 여부"""
        if sys.platform == "darwin":
            app_path = "tauri-dashboard/src-tauri/target/release/bundle/macos/Yesman Claude.app"
            return os.path.exists(app_path)
        elif sys.platform == "win32":
            app_path = "tauri-dashboard/src-tauri/target/release/yesman-claude.exe"
            return os.path.exists(app_path)
        else:  # Linux
            app_path = "tauri-dashboard/src-tauri/target/release/yesman-claude"
            return os.path.exists(app_path)
    
    def _check_web_dependencies(self) -> bool:
        """웹 대시보드 의존성 확인"""
        try:
            import fastapi
            import uvicorn
            import jinja2
            return True
        except ImportError:
            return False
    
    def check_system_requirements(self) -> Dict[str, bool]:
        """시스템 요구사항 확인"""
        requirements = {
            "python_version": sys.version_info >= (3, 8),
            "pip_available": shutil.which("pip") is not None,
            "npm_available": shutil.which("npm") is not None,
            "rust_available": shutil.which("rustc") is not None,
            "git_available": shutil.which("git") is not None
        }
        
        return requirements
    
    def install_dependencies(self, interface: str) -> bool:
        """인터페이스별 의존성 설치"""
        try:
            if interface == "web":
                # Python 의존성
                subprocess.run([sys.executable, "-m", "pip", "install", 
                              "fastapi", "uvicorn", "jinja2", "aiofiles"], 
                              check=True)
                
                # JavaScript 의존성
                subprocess.run(["npm", "install"], cwd="web-dashboard", check=True)
                
            elif interface == "tauri":
                # Tauri 의존성
                subprocess.run(["npm", "install"], cwd="tauri-dashboard", check=True)
                
            return True
            
        except subprocess.CalledProcessError:
            return False
```

### Day 2: TUI 대시보드 통합

#### 2.1 통합 TUI 대시보드
**파일**: `libs/dashboard/tui_dashboard.py`
```python
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.align import Align
from rich.text import Text
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Input, ListView, ListItem
from textual.reactive import reactive
from textual import events
import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional

from libs.dashboard.renderers.tui_renderer import TUIRenderer
from libs.dashboard.renderers.base_renderer import WidgetType
from libs.dashboard.widgets.session_browser import SessionBrowser
from libs.dashboard.widgets.project_health import ProjectHealth
from libs.dashboard.widgets.activity_heatmap import ActivityHeatmap
from libs.core.session_manager import SessionManager

class DashboardWidget(Static):
    """대시보드 위젯 베이스 클래스"""
    
    def __init__(self, widget_type: WidgetType, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.widget_type = widget_type
        self.renderer = TUIRenderer()
        self.data = {}
        
    async def update_data(self, data: Dict[str, Any]):
        """데이터 업데이트"""
        self.data = data
        await self.refresh()
        
    def render(self) -> Any:
        """위젯 렌더링"""
        return self.renderer.render_widget(self.widget_type, self.data)

class TUIDashboard(App):
    """Textual 기반 TUI 대시보드"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        background: $primary;
    }
    
    #sidebar {
        width: 30;
        background: $panel;
        border-right: solid $primary;
    }
    
    #main-content {
        background: $surface;
    }
    
    .widget-container {
        height: 100%;
        border: solid $primary;
        margin: 1;
        padding: 1;
    }
    
    Button {
        margin: 1;
    }
    
    Button:hover {
        background: $primary;
    }
    
    ListView {
        background: $panel;
        border: solid $primary;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("d", "toggle_dark", "Toggle Dark Mode"),
        ("r", "refresh", "Refresh"),
        ("s", "switch_view", "Switch View"),
        ("h", "show_help", "Help"),
        ("1", "view_sessions", "Sessions"),
        ("2", "view_health", "Health"),
        ("3", "view_activity", "Activity"),
        ("4", "view_logs", "Logs"),
    ]
    
    def __init__(self, theme: str = "auto", dev_mode: bool = False):
        super().__init__()
        self.theme = theme
        self.dev_mode = dev_mode
        self.session_manager = SessionManager()
        self.current_view = "sessions"
        self.widgets: Dict[str, DashboardWidget] = {}
        self.auto_refresh = True
        self.refresh_interval = 2.0  # seconds
        
    def compose(self) -> ComposeResult:
        """UI 구성"""
        yield Header(show_clock=True)
        
        with Horizontal():
            # 사이드바
            with Vertical(id="sidebar"):
                yield Static("📊 Dashboard", classes="sidebar-title")
                yield Button("Sessions", id="btn-sessions", variant="primary")
                yield Button("Health", id="btn-health")
                yield Button("Activity", id="btn-activity")
                yield Button("Logs", id="btn-logs")
                yield Button("Settings", id="btn-settings")
                
                # 상태 표시
                yield Static("", id="status-indicator", classes="status")
                
            # 메인 컨텐츠
            with Container(id="main-content"):
                # 세션 위젯
                yield DashboardWidget(
                    WidgetType.SESSION_BROWSER,
                    id="widget-sessions",
                    classes="widget-container"
                )
                
                # 건강도 위젯
                yield DashboardWidget(
                    WidgetType.HEALTH_METER,
                    id="widget-health",
                    classes="widget-container",
                    display=False
                )
                
                # 활동 위젯
                yield DashboardWidget(
                    WidgetType.ACTIVITY_HEATMAP,
                    id="widget-activity",
                    classes="widget-container",
                    display=False
                )
                
                # 로그 위젯
                yield DashboardWidget(
                    WidgetType.LOG_VIEWER,
                    id="widget-logs",
                    classes="widget-container",
                    display=False
                )
                
        yield Footer()
    
    async def on_mount(self) -> None:
        """마운트 시 초기화"""
        # 위젯 참조 저장
        self.widgets = {
            "sessions": self.query_one("#widget-sessions"),
            "health": self.query_one("#widget-health"),
            "activity": self.query_one("#widget-activity"),
            "logs": self.query_one("#widget-logs")
        }
        
        # 초기 데이터 로드
        await self.load_initial_data()
        
        # 자동 새로고침 시작
        if self.auto_refresh:
            self.set_interval(self.refresh_interval, self.auto_refresh_data)
    
    async def load_initial_data(self) -> None:
        """초기 데이터 로드"""
        # 세션 데이터
        sessions = self.session_manager.get_cached_sessions_list()
        await self.widgets["sessions"].update_data({"sessions": sessions})
        
        # 건강도 데이터
        health_calc = ProjectHealth()
        health_data = health_calc.calculate_health()
        await self.widgets["health"].update_data(health_data)
        
        # 활동 데이터
        activity_widget = ActivityHeatmap()
        activity_data = activity_widget.get_activity_data()
        await self.widgets["activity"].update_data({"activities": activity_data})
        
        # 상태 업데이트
        self.update_status(f"Loaded {len(sessions)} sessions")
    
    async def auto_refresh_data(self) -> None:
        """자동 데이터 새로고침"""
        if self.current_view == "sessions":
            sessions = self.session_manager.get_cached_sessions_list()
            await self.widgets["sessions"].update_data({"sessions": sessions})
        elif self.current_view == "health":
            health_calc = ProjectHealth()
            health_data = health_calc.calculate_health()
            await self.widgets["health"].update_data(health_data)
        # 다른 뷰들도 필요시 추가
        
        self.update_status(f"Updated at {datetime.now().strftime('%H:%M:%S')}")
    
    def update_status(self, message: str) -> None:
        """상태 메시지 업데이트"""
        status = self.query_one("#status-indicator")
        status.update(f"✓ {message}")
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """버튼 클릭 처리"""
        button_id = event.button.id
        
        if button_id == "btn-sessions":
            await self.switch_to_view("sessions")
        elif button_id == "btn-health":
            await self.switch_to_view("health")
        elif button_id == "btn-activity":
            await self.switch_to_view("activity")
        elif button_id == "btn-logs":
            await self.switch_to_view("logs")
        elif button_id == "btn-settings":
            await self.show_settings()
    
    async def switch_to_view(self, view_name: str) -> None:
        """뷰 전환"""
        # 모든 위젯 숨기기
        for widget in self.widgets.values():
            widget.display = False
        
        # 선택된 위젯 표시
        if view_name in self.widgets:
            self.widgets[view_name].display = True
            self.current_view = view_name
            
            # 버튼 스타일 업데이트
            for btn_id in ["btn-sessions", "btn-health", "btn-activity", "btn-logs"]:
                btn = self.query_one(f"#{btn_id}")
                if btn_id == f"btn-{view_name}":
                    btn.variant = "primary"
                else:
                    btn.variant = "default"
    
    async def action_toggle_dark(self) -> None:
        """다크 모드 토글"""
        self.dark = not self.dark
        
    async def action_refresh(self) -> None:
        """수동 새로고침"""
        await self.load_initial_data()
        self.update_status("Manually refreshed")
    
    async def action_switch_view(self) -> None:
        """뷰 순환 전환"""
        views = ["sessions", "health", "activity", "logs"]
        current_index = views.index(self.current_view)
        next_index = (current_index + 1) % len(views)
        await self.switch_to_view(views[next_index])
    
    async def action_show_help(self) -> None:
        """도움말 표시"""
        help_text = """
        Keyboard Shortcuts:
        
        1-4: Switch between views
        q: Quit
        d: Toggle dark mode
        r: Refresh data
        s: Cycle through views
        h: Show this help
        
        Mouse:
        Click buttons to switch views
        """
        
        self.push_screen(HelpScreen(help_text))
    
    # 특정 뷰로 직접 전환하는 액션들
    async def action_view_sessions(self) -> None:
        await self.switch_to_view("sessions")
    
    async def action_view_health(self) -> None:
        await self.switch_to_view("health")
    
    async def action_view_activity(self) -> None:
        await self.switch_to_view("activity")
    
    async def action_view_logs(self) -> None:
        await self.switch_to_view("logs")
    
    async def show_settings(self) -> None:
        """설정 화면 표시"""
        self.push_screen(SettingsScreen(self))

class HelpScreen(Screen):
    """도움말 화면"""
    
    def __init__(self, help_text: str):
        super().__init__()
        self.help_text = help_text
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static(self.help_text, id="help-content"),
            Button("Close", id="close-help"),
            id="help-container"
        )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close-help":
            self.app.pop_screen()

class SettingsScreen(Screen):
    """설정 화면"""
    
    def __init__(self, dashboard: TUIDashboard):
        super().__init__()
        self.dashboard = dashboard
    
    def compose(self) -> ComposeResult:
        yield Container(
            Static("Settings", classes="title"),
            
            # 자동 새로고침
            Horizontal(
                Static("Auto Refresh:"),
                Button(
                    "ON" if self.dashboard.auto_refresh else "OFF",
                    id="toggle-refresh"
                )
            ),
            
            # 새로고침 간격
            Horizontal(
                Static("Refresh Interval:"),
                Input(
                    str(self.dashboard.refresh_interval),
                    id="refresh-interval"
                )
            ),
            
            # 테마
            Horizontal(
                Static("Theme:"),
                Button(self.dashboard.theme, id="toggle-theme")
            ),
            
            Button("Save", id="save-settings", variant="primary"),
            Button("Cancel", id="cancel-settings"),
            
            id="settings-container"
        )
    
    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "save-settings":
            # 설정 저장
            await self.save_settings()
            self.app.pop_screen()
        elif event.button.id == "cancel-settings":
            self.app.pop_screen()
        elif event.button.id == "toggle-refresh":
            # 자동 새로고침 토글
            self.dashboard.auto_refresh = not self.dashboard.auto_refresh
            event.button.label = "ON" if self.dashboard.auto_refresh else "OFF"
        elif event.button.id == "toggle-theme":
            # 테마 순환
            themes = ["auto", "light", "dark"]
            current_index = themes.index(self.dashboard.theme)
            self.dashboard.theme = themes[(current_index + 1) % len(themes)]
            event.button.label = self.dashboard.theme
    
    async def save_settings(self) -> None:
        """설정 저장"""
        # 새로고침 간격 업데이트
        interval_input = self.query_one("#refresh-interval")
        try:
            self.dashboard.refresh_interval = float(interval_input.value)
        except ValueError:
            pass
```

### Day 3: 키보드 네비게이션 시스템

#### 3.1 통합 키보드 네비게이션
**파일**: `libs/dashboard/keyboard_navigation.py`
```python
from typing import Dict, List, Callable, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json

class KeyModifier(Enum):
    """키 수정자"""
    NONE = ""
    CTRL = "ctrl"
    ALT = "alt"
    SHIFT = "shift"
    META = "meta"  # Command on macOS, Windows key on Windows

@dataclass
class KeyBinding:
    """키 바인딩"""
    key: str
    modifiers: List[KeyModifier]
    action: str
    description: str
    context: Optional[str] = None  # 특정 컨텍스트에서만 활성화
    
    def to_string(self) -> str:
        """키 바인딩을 문자열로 변환"""
        parts = [m.value for m in self.modifiers if m != KeyModifier.NONE]
        parts.append(self.key)
        return "+".join(parts)
    
    @classmethod
    def from_string(cls, binding_str: str, action: str, description: str) -> "KeyBinding":
        """문자열에서 키 바인딩 생성"""
        parts = binding_str.lower().split("+")
        key = parts[-1]
        
        modifiers = []
        for part in parts[:-1]:
            try:
                modifiers.append(KeyModifier(part))
            except ValueError:
                pass
                
        return cls(key, modifiers, action, description)

class KeyboardNavigationManager:
    """키보드 네비게이션 관리자"""
    
    def __init__(self):
        self.bindings: Dict[str, KeyBinding] = {}
        self.actions: Dict[str, Callable] = {}
        self.contexts: List[str] = ["global"]
        self.current_focus: Optional[str] = None
        self.focusable_elements: List[str] = []
        self.vim_mode: bool = False
        
        # 기본 바인딩 등록
        self._register_default_bindings()
        
    def _register_default_bindings(self):
        """기본 키 바인딩 등록"""
        # 전역 네비게이션
        self.register_binding("tab", [], "focus_next", "Focus next element")
        self.register_binding("tab", [KeyModifier.SHIFT], "focus_prev", "Focus previous element")
        self.register_binding("escape", [], "unfocus", "Clear focus")
        
        # 방향키 네비게이션
        self.register_binding("up", [], "navigate_up", "Navigate up")
        self.register_binding("down", [], "navigate_down", "Navigate down")
        self.register_binding("left", [], "navigate_left", "Navigate left")
        self.register_binding("right", [], "navigate_right", "Navigate right")
        
        # Vim 스타일 네비게이션
        self.register_binding("h", [], "navigate_left", "Navigate left (Vim)", context="vim")
        self.register_binding("j", [], "navigate_down", "Navigate down (Vim)", context="vim")
        self.register_binding("k", [], "navigate_up", "Navigate up (Vim)", context="vim")
        self.register_binding("l", [], "navigate_right", "Navigate right (Vim)", context="vim")
        
        # 액션
        self.register_binding("enter", [], "activate", "Activate focused element")
        self.register_binding("space", [], "toggle", "Toggle focused element")
        
        # 단축키
        self.register_binding("r", [KeyModifier.CTRL], "refresh", "Refresh")
        self.register_binding("q", [KeyModifier.CTRL], "quit", "Quit")
        self.register_binding("s", [KeyModifier.CTRL], "save", "Save")
        self.register_binding("f", [KeyModifier.CTRL], "find", "Find")
        
        # 뷰 전환
        self.register_binding("1", [KeyModifier.ALT], "view_1", "Switch to view 1")
        self.register_binding("2", [KeyModifier.ALT], "view_2", "Switch to view 2")
        self.register_binding("3", [KeyModifier.ALT], "view_3", "Switch to view 3")
        self.register_binding("4", [KeyModifier.ALT], "view_4", "Switch to view 4")
        
    def register_binding(self, key: str, modifiers: List[KeyModifier], 
                        action: str, description: str, context: Optional[str] = None):
        """키 바인딩 등록"""
        binding = KeyBinding(key, modifiers, action, description, context)
        binding_key = self._get_binding_key(key, modifiers, context)
        self.bindings[binding_key] = binding
        
    def register_action(self, action: str, handler: Callable):
        """액션 핸들러 등록"""
        self.actions[action] = handler
        
    def add_focusable_element(self, element_id: str):
        """포커스 가능한 요소 추가"""
        if element_id not in self.focusable_elements:
            self.focusable_elements.append(element_id)
            
    def remove_focusable_element(self, element_id: str):
        """포커스 가능한 요소 제거"""
        if element_id in self.focusable_elements:
            self.focusable_elements.remove(element_id)
            if self.current_focus == element_id:
                self.current_focus = None
                
    def handle_key_event(self, key: str, modifiers: List[KeyModifier]) -> bool:
        """키 이벤트 처리"""
        # 현재 컨텍스트에서 바인딩 찾기
        for context in reversed(self.contexts):
            binding_key = self._get_binding_key(key, modifiers, context)
            if binding_key in self.bindings:
                binding = self.bindings[binding_key]
                return self._execute_action(binding.action)
                
        # 전역 컨텍스트에서 찾기
        binding_key = self._get_binding_key(key, modifiers, None)
        if binding_key in self.bindings:
            binding = self.bindings[binding_key]
            return self._execute_action(binding.action)
            
        return False
        
    def _execute_action(self, action: str) -> bool:
        """액션 실행"""
        if action in self.actions:
            try:
                self.actions[action]()
                return True
            except Exception as e:
                print(f"Error executing action {action}: {e}")
                return False
        return False
        
    def _get_binding_key(self, key: str, modifiers: List[KeyModifier], 
                        context: Optional[str]) -> str:
        """바인딩 키 생성"""
        mod_str = "+".join(sorted(m.value for m in modifiers if m != KeyModifier.NONE))
        key_str = f"{mod_str}+{key}" if mod_str else key
        return f"{context}:{key_str}" if context else key_str
        
    def push_context(self, context: str):
        """컨텍스트 추가"""
        self.contexts.append(context)
        
    def pop_context(self):
        """컨텍스트 제거"""
        if len(self.contexts) > 1:
            self.contexts.pop()
            
    def set_vim_mode(self, enabled: bool):
        """Vim 모드 설정"""
        self.vim_mode = enabled
        if enabled:
            self.push_context("vim")
        else:
            if "vim" in self.contexts:
                self.contexts.remove("vim")
                
    def focus_next(self):
        """다음 요소로 포커스 이동"""
        if not self.focusable_elements:
            return
            
        if self.current_focus is None:
            self.current_focus = self.focusable_elements[0]
        else:
            try:
                current_index = self.focusable_elements.index(self.current_focus)
                next_index = (current_index + 1) % len(self.focusable_elements)
                self.current_focus = self.focusable_elements[next_index]
            except ValueError:
                self.current_focus = self.focusable_elements[0]
                
    def focus_prev(self):
        """이전 요소로 포커스 이동"""
        if not self.focusable_elements:
            return
            
        if self.current_focus is None:
            self.current_focus = self.focusable_elements[-1]
        else:
            try:
                current_index = self.focusable_elements.index(self.current_focus)
                prev_index = (current_index - 1) % len(self.focusable_elements)
                self.current_focus = self.focusable_elements[prev_index]
            except ValueError:
                self.current_focus = self.focusable_elements[-1]
                
    def get_bindings_for_context(self, context: Optional[str] = None) -> List[KeyBinding]:
        """특정 컨텍스트의 바인딩 목록"""
        bindings = []
        for key, binding in self.bindings.items():
            if binding.context == context or (context is None and binding.context is None):
                bindings.append(binding)
        return sorted(bindings, key=lambda b: b.to_string())
        
    def export_bindings(self) -> Dict[str, Any]:
        """바인딩을 딕셔너리로 내보내기"""
        return {
            "bindings": [
                {
                    "key": b.key,
                    "modifiers": [m.value for m in b.modifiers],
                    "action": b.action,
                    "description": b.description,
                    "context": b.context
                }
                for b in self.bindings.values()
            ],
            "vim_mode": self.vim_mode
        }
        
    def import_bindings(self, data: Dict[str, Any]):
        """딕셔너리에서 바인딩 가져오기"""
        self.bindings.clear()
        
        for binding_data in data.get("bindings", []):
            modifiers = [KeyModifier(m) for m in binding_data["modifiers"]]
            self.register_binding(
                binding_data["key"],
                modifiers,
                binding_data["action"],
                binding_data["description"],
                binding_data.get("context")
            )
            
        self.vim_mode = data.get("vim_mode", False)

class WebKeyboardHandler:
    """웹 대시보드용 키보드 핸들러"""
    
    @staticmethod
    def generate_javascript() -> str:
        """키보드 처리 JavaScript 코드 생성"""
        return """
        class KeyboardNavigationManager {
            constructor() {
                this.bindings = new Map();
                this.focusableElements = [];
                this.currentFocusIndex = -1;
                this.vimMode = false;
                
                this.registerDefaultBindings();
                this.attachEventListeners();
            }
            
            registerDefaultBindings() {
                // Tab navigation
                this.registerBinding('Tab', [], 'focusNext');
                this.registerBinding('Tab', ['shift'], 'focusPrev');
                
                // Arrow navigation
                this.registerBinding('ArrowUp', [], 'navigateUp');
                this.registerBinding('ArrowDown', [], 'navigateDown');
                this.registerBinding('ArrowLeft', [], 'navigateLeft');
                this.registerBinding('ArrowRight', [], 'navigateRight');
                
                // Vim navigation
                this.registerBinding('h', [], 'navigateLeft', 'vim');
                this.registerBinding('j', [], 'navigateDown', 'vim');
                this.registerBinding('k', [], 'navigateUp', 'vim');
                this.registerBinding('l', [], 'navigateRight', 'vim');
                
                // Actions
                this.registerBinding('Enter', [], 'activate');
                this.registerBinding(' ', [], 'toggle');
                
                // Shortcuts
                this.registerBinding('r', ['ctrl'], 'refresh');
                this.registerBinding('f', ['ctrl'], 'find');
                this.registerBinding('s', ['ctrl'], 'save');
                
                // View switching
                this.registerBinding('1', ['alt'], 'switchView1');
                this.registerBinding('2', ['alt'], 'switchView2');
                this.registerBinding('3', ['alt'], 'switchView3');
                this.registerBinding('4', ['alt'], 'switchView4');
            }
            
            registerBinding(key, modifiers = [], action, context = null) {
                const bindingKey = this.getBindingKey(key, modifiers, context);
                this.bindings.set(bindingKey, { key, modifiers, action, context });
            }
            
            getBindingKey(key, modifiers, context) {
                const modStr = modifiers.sort().join('+');
                const keyStr = modStr ? `${modStr}+${key}` : key;
                return context ? `${context}:${keyStr}` : keyStr;
            }
            
            attachEventListeners() {
                document.addEventListener('keydown', (e) => this.handleKeyDown(e));
                
                // Track focusable elements
                this.updateFocusableElements();
                
                // Update on DOM changes
                const observer = new MutationObserver(() => this.updateFocusableElements());
                observer.observe(document.body, { childList: true, subtree: true });
            }
            
            handleKeyDown(event) {
                const modifiers = [];
                if (event.ctrlKey) modifiers.push('ctrl');
                if (event.altKey) modifiers.push('alt');
                if (event.shiftKey) modifiers.push('shift');
                if (event.metaKey) modifiers.push('meta');
                
                // Check context-specific bindings first
                const contexts = this.vimMode ? ['vim', null] : [null];
                
                for (const context of contexts) {
                    const bindingKey = this.getBindingKey(event.key, modifiers, context);
                    const binding = this.bindings.get(bindingKey);
                    
                    if (binding) {
                        event.preventDefault();
                        this.executeAction(binding.action);
                        return;
                    }
                }
            }
            
            executeAction(action) {
                const actionMap = {
                    focusNext: () => this.focusNext(),
                    focusPrev: () => this.focusPrev(),
                    navigateUp: () => this.navigate('up'),
                    navigateDown: () => this.navigate('down'),
                    navigateLeft: () => this.navigate('left'),
                    navigateRight: () => this.navigate('right'),
                    activate: () => this.activate(),
                    toggle: () => this.toggle(),
                    refresh: () => window.location.reload(),
                    find: () => this.showFindDialog(),
                    save: () => this.save(),
                    switchView1: () => this.switchView(1),
                    switchView2: () => this.switchView(2),
                    switchView3: () => this.switchView(3),
                    switchView4: () => this.switchView(4),
                };
                
                const handler = actionMap[action];
                if (handler) {
                    handler();
                }
            }
            
            updateFocusableElements() {
                this.focusableElements = Array.from(
                    document.querySelectorAll(
                        'a, button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
                    )
                ).filter(el => !el.disabled && el.offsetParent !== null);
            }
            
            focusNext() {
                if (this.focusableElements.length === 0) return;
                
                this.currentFocusIndex = (this.currentFocusIndex + 1) % this.focusableElements.length;
                this.focusableElements[this.currentFocusIndex].focus();
            }
            
            focusPrev() {
                if (this.focusableElements.length === 0) return;
                
                this.currentFocusIndex = this.currentFocusIndex <= 0 
                    ? this.focusableElements.length - 1 
                    : this.currentFocusIndex - 1;
                this.focusableElements[this.currentFocusIndex].focus();
            }
            
            navigate(direction) {
                // Implement spatial navigation
                const current = document.activeElement;
                if (!current) return;
                
                const rect = current.getBoundingClientRect();
                const candidates = this.focusableElements.filter(el => el !== current);
                
                let best = null;
                let bestScore = Infinity;
                
                candidates.forEach(candidate => {
                    const candidateRect = candidate.getBoundingClientRect();
                    const score = this.calculateNavigationScore(
                        rect, candidateRect, direction
                    );
                    
                    if (score < bestScore) {
                        bestScore = score;
                        best = candidate;
                    }
                });
                
                if (best) {
                    best.focus();
                }
            }
            
            calculateNavigationScore(from, to, direction) {
                const dx = to.left - from.left;
                const dy = to.top - from.top;
                
                switch (direction) {
                    case 'up':
                        return dy < 0 ? -dy + Math.abs(dx) * 0.5 : Infinity;
                    case 'down':
                        return dy > 0 ? dy + Math.abs(dx) * 0.5 : Infinity;
                    case 'left':
                        return dx < 0 ? -dx + Math.abs(dy) * 0.5 : Infinity;
                    case 'right':
                        return dx > 0 ? dx + Math.abs(dy) * 0.5 : Infinity;
                    default:
                        return Infinity;
                }
            }
            
            activate() {
                const current = document.activeElement;
                if (current) {
                    current.click();
                }
            }
            
            toggle() {
                const current = document.activeElement;
                if (current && (current.type === 'checkbox' || current.type === 'radio')) {
                    current.checked = !current.checked;
                    current.dispatchEvent(new Event('change'));
                }
            }
            
            switchView(index) {
                const viewButtons = document.querySelectorAll('[data-view-index]');
                if (viewButtons[index - 1]) {
                    viewButtons[index - 1].click();
                }
            }
            
            showFindDialog() {
                // Implement find functionality
                const query = prompt('Find:');
                if (query) {
                    window.find(query);
                }
            }
            
            save() {
                // Trigger save event
                document.dispatchEvent(new CustomEvent('dashboard:save'));
            }
            
            setVimMode(enabled) {
                this.vimMode = enabled;
                document.body.classList.toggle('vim-mode', enabled);
            }
        }
        
        // Initialize on DOM ready
        document.addEventListener('DOMContentLoaded', () => {
            window.keyboardNav = new KeyboardNavigationManager();
        });
        """
```

### Day 4: 테마 시스템

#### 4.1 통합 테마 시스템
**파일**: `libs/dashboard/theme_system.py`
```python
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import json
import os
from pathlib import Path

class ThemeMode(Enum):
    """테마 모드"""
    LIGHT = "light"
    DARK = "dark"
    AUTO = "auto"
    CUSTOM = "custom"

@dataclass
class ColorPalette:
    """색상 팔레트"""
    primary: str = "#3B82F6"      # blue-500
    secondary: str = "#10B981"    # green-500
    accent: str = "#8B5CF6"       # purple-500
    warning: str = "#F59E0B"      # yellow-500
    error: str = "#EF4444"        # red-500
    info: str = "#06B6D4"         # cyan-500
    success: str = "#10B981"      # green-500
    
    # 배경색
    background: str = "#FFFFFF"
    surface: str = "#F9FAFB"      # gray-50
    panel: str = "#F3F4F6"        # gray-100
    
    # 텍스트색
    text: str = "#111827"         # gray-900
    text_secondary: str = "#6B7280" # gray-500
    text_disabled: str = "#9CA3AF"  # gray-400
    
    # 테두리색
    border: str = "#E5E7EB"       # gray-200
    border_focus: str = "#3B82F6"  # blue-500
    
    # 그림자
    shadow: str = "rgba(0, 0, 0, 0.1)"
    
    def to_dict(self) -> Dict[str, str]:
        """딕셔너리로 변환"""
        return {
            key: value for key, value in self.__dict__.items()
            if not key.startswith('_')
        }

@dataclass
class Typography:
    """타이포그래피 설정"""
    font_family: str = "system-ui, -apple-system, sans-serif"
    font_family_mono: str = "ui-monospace, monospace"
    
    # 폰트 크기
    font_size_xs: int = 12
    font_size_sm: int = 14
    font_size_base: int = 16
    font_size_lg: int = 18
    font_size_xl: int = 20
    font_size_2xl: int = 24
    font_size_3xl: int = 30
    
    # 폰트 굵기
    font_weight_normal: int = 400
    font_weight_medium: int = 500
    font_weight_semibold: int = 600
    font_weight_bold: int = 700
    
    # 줄 높이
    line_height_tight: float = 1.25
    line_height_normal: float = 1.5
    line_height_relaxed: float = 1.75
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return self.__dict__.copy()

@dataclass
class Spacing:
    """간격 설정"""
    xs: int = 2
    sm: int = 4
    md: int = 8
    lg: int = 16
    xl: int = 24
    xxl: int = 32
    
    def to_dict(self) -> Dict[str, int]:
        """딕셔너리로 변환"""
        return self.__dict__.copy()

@dataclass
class Theme:
    """테마 정의"""
    name: str
    mode: ThemeMode
    colors: ColorPalette = field(default_factory=ColorPalette)
    typography: Typography = field(default_factory=Typography)
    spacing: Spacing = field(default_factory=Spacing)
    custom_css: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "name": self.name,
            "mode": self.mode.value,
            "colors": self.colors.to_dict(),
            "typography": self.typography.to_dict(),
            "spacing": self.spacing.to_dict(),
            "custom_css": self.custom_css
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Theme":
        """딕셔너리에서 생성"""
        theme = cls(
            name=data["name"],
            mode=ThemeMode(data["mode"])
        )
        
        # 색상 팔레트
        if "colors" in data:
            for key, value in data["colors"].items():
                setattr(theme.colors, key, value)
                
        # 타이포그래피
        if "typography" in data:
            for key, value in data["typography"].items():
                setattr(theme.typography, key, value)
                
        # 간격
        if "spacing" in data:
            for key, value in data["spacing"].items():
                setattr(theme.spacing, key, value)
                
        # 커스텀 CSS
        theme.custom_css = data.get("custom_css", "")
        
        return theme

class ThemeManager:
    """테마 관리자"""
    
    def __init__(self, config_dir: Optional[str] = None):
        self.config_dir = Path(config_dir or os.path.expanduser("~/.yesman/themes"))
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.themes: Dict[str, Theme] = {}
        self.current_theme: Optional[Theme] = None
        self.mode: ThemeMode = ThemeMode.AUTO
        
        # 기본 테마 로드
        self._load_default_themes()
        # 사용자 테마 로드
        self._load_user_themes()
        
    def _load_default_themes(self):
        """기본 테마 로드"""
        # 라이트 테마
        light_theme = Theme(
            name="Default Light",
            mode=ThemeMode.LIGHT,
            colors=ColorPalette()
        )
        self.themes["default-light"] = light_theme
        
        # 다크 테마
        dark_colors = ColorPalette(
            background="#0F172A",      # slate-900
            surface="#1E293B",         # slate-800
            panel="#334155",           # slate-700
            text="#F1F5F9",           # slate-100
            text_secondary="#94A3B8",  # slate-400
            text_disabled="#64748B",   # slate-500
            border="#334155",          # slate-700
            border_focus="#3B82F6"     # blue-500
        )
        dark_theme = Theme(
            name="Default Dark",
            mode=ThemeMode.DARK,
            colors=dark_colors
        )
        self.themes["default-dark"] = dark_theme
        
        # 고대비 테마
        high_contrast_colors = ColorPalette(
            primary="#0066CC",
            secondary="#008000",
            accent="#6600CC",
            warning="#CC6600",
            error="#CC0000",
            info="#0099CC",
            success="#008000",
            background="#FFFFFF",
            surface="#FFFFFF",
            panel="#F0F0F0",
            text="#000000",
            text_secondary="#333333",
            text_disabled="#666666",
            border="#000000",
            border_focus="#0066CC"
        )
        high_contrast_theme = Theme(
            name="High Contrast",
            mode=ThemeMode.LIGHT,
            colors=high_contrast_colors
        )
        self.themes["high-contrast"] = high_contrast_theme
        
    def _load_user_themes(self):
        """사용자 테마 로드"""
        theme_files = self.config_dir.glob("*.json")
        
        for theme_file in theme_files:
            try:
                with open(theme_file, "r") as f:
                    theme_data = json.load(f)
                    theme = Theme.from_dict(theme_data)
                    theme_id = theme_file.stem
                    self.themes[theme_id] = theme
            except Exception as e:
                print(f"Failed to load theme {theme_file}: {e}")
                
    def save_theme(self, theme_id: str, theme: Theme):
        """테마 저장"""
        theme_file = self.config_dir / f"{theme_id}.json"
        
        with open(theme_file, "w") as f:
            json.dump(theme.to_dict(), f, indent=2)
            
        self.themes[theme_id] = theme
        
    def delete_theme(self, theme_id: str):
        """테마 삭제"""
        if theme_id.startswith("default-"):
            raise ValueError("Cannot delete default themes")
            
        theme_file = self.config_dir / f"{theme_id}.json"
        if theme_file.exists():
            theme_file.unlink()
            
        if theme_id in self.themes:
            del self.themes[theme_id]
            
    def get_theme(self, theme_id: str) -> Optional[Theme]:
        """테마 조회"""
        return self.themes.get(theme_id)
        
    def list_themes(self) -> List[Dict[str, Any]]:
        """테마 목록"""
        return [
            {
                "id": theme_id,
                "name": theme.name,
                "mode": theme.mode.value,
                "is_default": theme_id.startswith("default-")
            }
            for theme_id, theme in self.themes.items()
        ]
        
    def set_current_theme(self, theme_id: str):
        """현재 테마 설정"""
        if theme_id in self.themes:
            self.current_theme = self.themes[theme_id]
        else:
            raise ValueError(f"Theme {theme_id} not found")
            
    def set_mode(self, mode: ThemeMode):
        """테마 모드 설정"""
        self.mode = mode
        
        if mode == ThemeMode.AUTO:
            # 시스템 테마 감지
            if self._is_dark_mode():
                self.set_current_theme("default-dark")
            else:
                self.set_current_theme("default-light")
        elif mode == ThemeMode.DARK:
            self.set_current_theme("default-dark")
        elif mode == ThemeMode.LIGHT:
            self.set_current_theme("default-light")
            
    def _is_dark_mode(self) -> bool:
        """시스템 다크 모드 감지"""
        # 플랫폼별 구현
        if sys.platform == "darwin":
            # macOS
            try:
                import subprocess
                result = subprocess.run(
                    ["defaults", "read", "-g", "AppleInterfaceStyle"],
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip() == "Dark"
            except:
                return False
        elif sys.platform == "win32":
            # Windows
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0
            except:
                return False
        else:
            # Linux - 환경 변수 확인
            return os.environ.get("GTK_THEME", "").lower().endswith("dark")
            
    def export_css(self, theme: Optional[Theme] = None) -> str:
        """테마를 CSS로 내보내기"""
        theme = theme or self.current_theme
        if not theme:
            theme = self.themes["default-light"]
            
        css = f"""
/* Theme: {theme.name} */
:root {{
    /* Colors */
    --color-primary: {theme.colors.primary};
    --color-secondary: {theme.colors.secondary};
    --color-accent: {theme.colors.accent};
    --color-warning: {theme.colors.warning};
    --color-error: {theme.colors.error};
    --color-info: {theme.colors.info};
    --color-success: {theme.colors.success};
    
    --color-background: {theme.colors.background};
    --color-surface: {theme.colors.surface};
    --color-panel: {theme.colors.panel};
    
    --color-text: {theme.colors.text};
    --color-text-secondary: {theme.colors.text_secondary};
    --color-text-disabled: {theme.colors.text_disabled};
    
    --color-border: {theme.colors.border};
    --color-border-focus: {theme.colors.border_focus};
    
    --color-shadow: {theme.colors.shadow};
    
    /* Typography */
    --font-family: {theme.typography.font_family};
    --font-family-mono: {theme.typography.font_family_mono};
    
    --font-size-xs: {theme.typography.font_size_xs}px;
    --font-size-sm: {theme.typography.font_size_sm}px;
    --font-size-base: {theme.typography.font_size_base}px;
    --font-size-lg: {theme.typography.font_size_lg}px;
    --font-size-xl: {theme.typography.font_size_xl}px;
    --font-size-2xl: {theme.typography.font_size_2xl}px;
    --font-size-3xl: {theme.typography.font_size_3xl}px;
    
    --font-weight-normal: {theme.typography.font_weight_normal};
    --font-weight-medium: {theme.typography.font_weight_medium};
    --font-weight-semibold: {theme.typography.font_weight_semibold};
    --font-weight-bold: {theme.typography.font_weight_bold};
    
    --line-height-tight: {theme.typography.line_height_tight};
    --line-height-normal: {theme.typography.line_height_normal};
    --line-height-relaxed: {theme.typography.line_height_relaxed};
    
    /* Spacing */
    --spacing-xs: {theme.spacing.xs}px;
    --spacing-sm: {theme.spacing.sm}px;
    --spacing-md: {theme.spacing.md}px;
    --spacing-lg: {theme.spacing.lg}px;
    --spacing-xl: {theme.spacing.xl}px;
    --spacing-xxl: {theme.spacing.xxl}px;
}}

/* Base styles */
body {{
    background-color: var(--color-background);
    color: var(--color-text);
    font-family: var(--font-family);
    font-size: var(--font-size-base);
    line-height: var(--line-height-normal);
}}

.surface {{
    background-color: var(--color-surface);
}}

.panel {{
    background-color: var(--color-panel);
    border: 1px solid var(--color-border);
    border-radius: var(--spacing-sm);
    padding: var(--spacing-md);
}}

/* Custom CSS */
{theme.custom_css}
"""
        
        return css
        
    def export_rich_theme(self, theme: Optional[Theme] = None) -> Dict[str, Any]:
        """테마를 Rich 스타일로 내보내기"""
        theme = theme or self.current_theme
        if not theme:
            theme = self.themes["default-light"]
            
        return {
            "background": theme.colors.background,
            "panel": theme.colors.panel,
            "primary": theme.colors.primary,
            "secondary": theme.colors.secondary,
            "warning": theme.colors.warning,
            "error": theme.colors.error,
            "info": theme.colors.info,
            "success": theme.colors.success,
            "text": theme.colors.text,
            "text.secondary": theme.colors.text_secondary,
            "border": theme.colors.border
        }

# 전역 테마 관리자
theme_manager = ThemeManager()

def get_current_theme() -> Theme:
    """현재 테마 가져오기"""
    return theme_manager.current_theme or theme_manager.themes["default-light"]

def apply_theme(theme_id: str):
    """테마 적용"""
    theme_manager.set_current_theme(theme_id)
```

### Day 5: 성능 최적화 및 통합 테스트

#### 5.1 성능 최적화
**파일**: `libs/dashboard/performance_optimizer.py`
```python
import time
import psutil
import asyncio
from typing import Dict, Any, List, Callable, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import threading
from collections import deque
import gc

@dataclass
class PerformanceMetrics:
    """성능 메트릭"""
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    render_time: float = 0.0
    update_frequency: float = 0.0
    widget_count: int = 0
    active_connections: int = 0
    cache_hit_rate: float = 0.0
    
    # 시계열 데이터
    cpu_history: deque = field(default_factory=lambda: deque(maxlen=60))
    memory_history: deque = field(default_factory=lambda: deque(maxlen=60))
    render_time_history: deque = field(default_factory=lambda: deque(maxlen=60))

class PerformanceOptimizer:
    """성능 최적화 관리자"""
    
    def __init__(self):
        self.metrics = PerformanceMetrics()
        self.monitoring = False
        self.optimization_enabled = True
        self.thresholds = {
            "cpu_high": 80.0,
            "memory_high": 80.0,
            "render_time_slow": 100.0,  # ms
            "update_frequency_low": 0.5  # Hz
        }
        self.optimizations = []
        self._monitor_thread = None
        
    def start_monitoring(self):
        """성능 모니터링 시작"""
        if not self.monitoring:
            self.monitoring = True
            self._monitor_thread = threading.Thread(target=self._monitor_loop)
            self._monitor_thread.daemon = True
            self._monitor_thread.start()
            
    def stop_monitoring(self):
        """성능 모니터링 중지"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join()
            
    def _monitor_loop(self):
        """모니터링 루프"""
        process = psutil.Process()
        
        while self.monitoring:
            try:
                # CPU 사용률
                cpu_percent = process.cpu_percent(interval=1)
                self.metrics.cpu_usage = cpu_percent
                self.metrics.cpu_history.append({
                    "timestamp": datetime.now(),
                    "value": cpu_percent
                })
                
                # 메모리 사용률
                memory_info = process.memory_info()
                memory_percent = process.memory_percent()
                self.metrics.memory_usage = memory_percent
                self.metrics.memory_history.append({
                    "timestamp": datetime.now(),
                    "value": memory_percent,
                    "rss": memory_info.rss,
                    "vms": memory_info.vms
                })
                
                # 최적화 체크
                if self.optimization_enabled:
                    self._check_optimizations()
                    
                time.sleep(1)
                
            except Exception as e:
                print(f"Monitoring error: {e}")
                
    def _check_optimizations(self):
        """최적화 필요 여부 체크"""
        optimizations_needed = []
        
        # CPU 사용률 체크
        if self.metrics.cpu_usage > self.thresholds["cpu_high"]:
            optimizations_needed.append("reduce_update_frequency")
            optimizations_needed.append("enable_lazy_loading")
            
        # 메모리 사용률 체크
        if self.metrics.memory_usage > self.thresholds["memory_high"]:
            optimizations_needed.append("clear_caches")
            optimizations_needed.append("reduce_widget_count")
            
        # 렌더링 시간 체크
        if self.metrics.render_time > self.thresholds["render_time_slow"]:
            optimizations_needed.append("simplify_rendering")
            optimizations_needed.append("enable_virtualization")
            
        # 최적화 적용
        for optimization in optimizations_needed:
            self.apply_optimization(optimization)
            
    def apply_optimization(self, optimization: str):
        """최적화 적용"""
        if optimization in self.optimizations:
            return  # 이미 적용됨
            
        optimization_map = {
            "reduce_update_frequency": self._reduce_update_frequency,
            "enable_lazy_loading": self._enable_lazy_loading,
            "clear_caches": self._clear_caches,
            "reduce_widget_count": self._reduce_widget_count,
            "simplify_rendering": self._simplify_rendering,
            "enable_virtualization": self._enable_virtualization
        }
        
        handler = optimization_map.get(optimization)
        if handler:
            handler()
            self.optimizations.append(optimization)
            
    def _reduce_update_frequency(self):
        """업데이트 빈도 감소"""
        # 업데이트 간격을 2배로 증가
        from libs.dashboard.dashboard_server import DashboardServer
        DashboardServer.update_interval *= 2
        
    def _enable_lazy_loading(self):
        """지연 로딩 활성화"""
        # 위젯 지연 로딩 활성화
        from libs.dashboard.renderers.optimizations import LazyRenderer
        # 구현 필요
        
    def _clear_caches(self):
        """캐시 정리"""
        from libs.dashboard.renderers.optimizations import render_cache
        render_cache.clear()
        gc.collect()
        
    def _reduce_widget_count(self):
        """위젯 수 감소"""
        # 비활성 위젯 제거
        # 구현 필요
        pass
        
    def _simplify_rendering(self):
        """렌더링 단순화"""
        # 애니메이션 비활성화
        # 복잡한 시각효과 제거
        # 구현 필요
        pass
        
    def _enable_virtualization(self):
        """가상화 활성화"""
        # 긴 목록에 대한 가상 스크롤링
        # 구현 필요
        pass
        
    def measure_render_time(self, func: Callable) -> Callable:
        """렌더링 시간 측정 데코레이터"""
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            render_time = (time.time() - start_time) * 1000  # ms
            
            self.metrics.render_time = render_time
            self.metrics.render_time_history.append({
                "timestamp": datetime.now(),
                "value": render_time,
                "function": func.__name__
            })
            
            return result
        return wrapper
        
    def get_performance_report(self) -> Dict[str, Any]:
        """성능 리포트 생성"""
        return {
            "current": {
                "cpu_usage": f"{self.metrics.cpu_usage:.1f}%",
                "memory_usage": f"{self.metrics.memory_usage:.1f}%",
                "render_time": f"{self.metrics.render_time:.1f}ms",
                "widget_count": self.metrics.widget_count,
                "active_connections": self.metrics.active_connections,
                "cache_hit_rate": f"{self.metrics.cache_hit_rate:.1f}%"
            },
            "averages": {
                "cpu_avg": self._calculate_average(self.metrics.cpu_history),
                "memory_avg": self._calculate_average(self.metrics.memory_history),
                "render_time_avg": self._calculate_average(self.metrics.render_time_history)
            },
            "optimizations": {
                "enabled": self.optimization_enabled,
                "applied": self.optimizations,
                "thresholds": self.thresholds
            },
            "recommendations": self._get_recommendations()
        }
        
    def _calculate_average(self, history: deque) -> float:
        """평균 계산"""
        if not history:
            return 0.0
        values = [item["value"] for item in history]
        return sum(values) / len(values)
        
    def _get_recommendations(self) -> List[str]:
        """성능 개선 권장사항"""
        recommendations = []
        
        avg_cpu = self._calculate_average(self.metrics.cpu_history)
        if avg_cpu > 70:
            recommendations.append("Consider reducing update frequency")
            
        avg_memory = self._calculate_average(self.metrics.memory_history)
        if avg_memory > 70:
            recommendations.append("Consider implementing pagination for large datasets")
            
        avg_render = self._calculate_average(self.metrics.render_time_history)
        if avg_render > 50:
            recommendations.append("Consider simplifying widget rendering")
            
        if self.metrics.cache_hit_rate < 80:
            recommendations.append("Consider increasing cache size")
            
        return recommendations

class AsyncPerformanceOptimizer:
    """비동기 성능 최적화"""
    
    def __init__(self):
        self.semaphores = {
            "render": asyncio.Semaphore(5),     # 동시 렌더링 제한
            "update": asyncio.Semaphore(10),    # 동시 업데이트 제한
            "websocket": asyncio.Semaphore(100) # 동시 WebSocket 연결 제한
        }
        self.rate_limiters = {}
        
    async def with_semaphore(self, name: str, coro):
        """세마포어로 동시 실행 제한"""
        async with self.semaphores.get(name, asyncio.Semaphore(10)):
            return await coro
            
    async def rate_limit(self, key: str, rate: float, coro):
        """Rate limiting"""
        if key not in self.rate_limiters:
            self.rate_limiters[key] = asyncio.Lock()
            
        async with self.rate_limiters[key]:
            result = await coro
            await asyncio.sleep(1.0 / rate)  # Rate limit
            return result
            
    async def batch_process(self, items: List[Any], processor: Callable, 
                          batch_size: int = 10) -> List[Any]:
        """배치 처리"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_results = await asyncio.gather(
                *[processor(item) for item in batch]
            )
            results.extend(batch_results)
            
        return results

# 전역 성능 최적화 인스턴스
performance_optimizer = PerformanceOptimizer()
async_optimizer = AsyncPerformanceOptimizer()

def optimize_performance(func):
    """성능 최적화 데코레이터"""
    def wrapper(*args, **kwargs):
        # 렌더링 시간 측정
        func_with_timing = performance_optimizer.measure_render_time(func)
        return func_with_timing(*args, **kwargs)
    return wrapper

async def optimize_async(func):
    """비동기 성능 최적화 데코레이터"""
    async def wrapper(*args, **kwargs):
        # Rate limiting
        return await async_optimizer.rate_limit(
            func.__name__,
            10,  # 초당 10회
            func(*args, **kwargs)
        )
    return wrapper
```

#### 5.2 통합 테스트
**파일**: `tests/test_integration.py`
```python
import pytest
import asyncio
from unittest.mock import Mock, patch
import time

from libs.dashboard.dashboard_launcher import DashboardLauncher
from libs.dashboard.renderers.renderer_factory import RendererFactory, RenderFormat
from libs.dashboard.theme_system import ThemeManager, ThemeMode
from libs.dashboard.keyboard_navigation import KeyboardNavigationManager, KeyModifier
from libs.dashboard.performance_optimizer import PerformanceOptimizer

class TestDashboardIntegration:
    """대시보드 통합 테스트"""
    
    @pytest.fixture
    def launcher(self):
        """대시보드 런처"""
        return DashboardLauncher()
        
    @pytest.fixture
    def theme_manager(self):
        """테마 관리자"""
        return ThemeManager()
        
    @pytest.fixture
    def keyboard_manager(self):
        """키보드 네비게이션 관리자"""
        return KeyboardNavigationManager()
        
    def test_interface_detection(self, launcher):
        """인터페이스 자동 감지 테스트"""
        # GUI 환경 시뮬레이션
        with patch.object(launcher, '_is_gui_available', return_value=True):
            with patch.object(launcher, '_is_tauri_available', return_value=True):
                assert launcher.detect_best_interface() == "tauri"
                
            with patch.object(launcher, '_is_tauri_available', return_value=False):
                assert launcher.detect_best_interface() == "web"
                
        # SSH 환경 시뮬레이션
        with patch.object(launcher, '_is_gui_available', return_value=False):
            with patch.object(launcher, '_is_ssh_session', return_value=True):
                assert launcher.detect_best_interface() == "tui"
                
    def test_multi_format_rendering(self):
        """다중 포맷 렌더링 테스트"""
        sample_data = {
            "sessions": [{
                "session_name": "test",
                "session_id": "123",
                "status": "active",
                "created_at": "2024-01-01T10:00:00"
            }]
        }
        
        # 모든 포맷으로 렌더링
        for format in RenderFormat:
            renderer = RendererFactory.get_renderer(format)
            result = renderer.render("widget", {
                "type": "session_browser",
                "data": sample_data
            })
            
            assert result is not None
            
    def test_theme_switching(self, theme_manager):
        """테마 전환 테스트"""
        # 라이트 테마
        theme_manager.set_mode(ThemeMode.LIGHT)
        assert theme_manager.current_theme.name == "Default Light"
        
        # 다크 테마
        theme_manager.set_mode(ThemeMode.DARK)
        assert theme_manager.current_theme.name == "Default Dark"
        
        # CSS 내보내기
        css = theme_manager.export_css()
        assert "--color-primary" in css
        assert "--font-family" in css
        
    def test_keyboard_navigation(self, keyboard_manager):
        """키보드 네비게이션 테스트"""
        # 액션 등록
        action_called = False
        def test_action():
            nonlocal action_called
            action_called = True
            
        keyboard_manager.register_action("test_action", test_action)
        keyboard_manager.register_binding("t", [KeyModifier.CTRL], "test_action", "Test")
        
        # 키 이벤트 처리
        handled = keyboard_manager.handle_key_event("t", [KeyModifier.CTRL])
        assert handled
        assert action_called
        
        # Vim 모드
        keyboard_manager.set_vim_mode(True)
        assert "vim" in keyboard_manager.contexts
        
    def test_performance_monitoring(self):
        """성능 모니터링 테스트"""
        optimizer = PerformanceOptimizer()
        optimizer.start_monitoring()
        
        # 모니터링 데이터 수집 대기
        time.sleep(2)
        
        # 메트릭 확인
        assert optimizer.metrics.cpu_usage >= 0
        assert optimizer.metrics.memory_usage >= 0
        assert len(optimizer.metrics.cpu_history) > 0
        
        # 성능 리포트
        report = optimizer.get_performance_report()
        assert "current" in report
        assert "averages" in report
        assert "recommendations" in report
        
        optimizer.stop_monitoring()
        
    @pytest.mark.asyncio
    async def test_concurrent_rendering(self):
        """동시 렌더링 테스트"""
        from libs.dashboard.performance_optimizer import async_optimizer
        
        # 동시 렌더링 작업
        async def render_widget(index):
            await asyncio.sleep(0.1)  # 렌더링 시뮬레이션
            return f"Widget {index}"
            
        # 세마포어로 제한된 동시 실행
        tasks = []
        for i in range(20):
            task = async_optimizer.with_semaphore(
                "render",
                render_widget(i)
            )
            tasks.append(task)
            
        results = await asyncio.gather(*tasks)
        assert len(results) == 20
        
    def test_end_to_end_dashboard_launch(self, launcher):
        """종단간 대시보드 실행 테스트"""
        # 사용 가능한 인터페이스 확인
        available = launcher.get_available_interfaces()
        assert "tui" in available  # TUI는 항상 사용 가능
        
        # 시스템 요구사항 확인
        requirements = launcher.check_system_requirements()
        assert requirements["python_version"]  # Python 3.8+
        
    def test_theme_persistence(self, theme_manager, tmp_path):
        """테마 지속성 테스트"""
        # 임시 설정 디렉토리
        theme_manager.config_dir = tmp_path
        
        # 커스텀 테마 생성
        from libs.dashboard.theme_system import Theme, ColorPalette
        
        custom_colors = ColorPalette(primary="#FF0000")
        custom_theme = Theme(
            name="Custom Red",
            mode=ThemeMode.CUSTOM,
            colors=custom_colors
        )
        
        # 테마 저장
        theme_manager.save_theme("custom-red", custom_theme)
        
        # 새 인스턴스에서 로드
        new_manager = ThemeManager(config_dir=str(tmp_path))
        loaded_theme = new_manager.get_theme("custom-red")
        
        assert loaded_theme is not None
        assert loaded_theme.name == "Custom Red"
        assert loaded_theme.colors.primary == "#FF0000"
        
    @pytest.mark.benchmark
    def test_rendering_performance(self, benchmark):
        """렌더링 성능 벤치마크"""
        from libs.dashboard.renderers.web_renderer import WebRenderer
        
        renderer = WebRenderer()
        sample_data = {
            "sessions": [
                {
                    "session_name": f"session-{i}",
                    "session_id": str(i),
                    "status": "active",
                    "created_at": "2024-01-01T10:00:00"
                }
                for i in range(100)
            ]
        }
        
        def render():
            return renderer.render_widget(
                WidgetType.SESSION_BROWSER,
                sample_data
            )
            
        result = benchmark(render)
        assert result is not None
        
        # 성능 기준: 100개 세션 렌더링이 50ms 이내
        assert benchmark.stats["mean"] < 0.05
```

## ✅ Phase 4 완료 기준

### 기능적 요구사항
- [ ] 통합 CLI 인터페이스 (`--interface` 옵션)
- [ ] 자동 인터페이스 감지
- [ ] TUI 대시보드 완전 통합
- [ ] 키보드 네비게이션 (모든 인터페이스)
- [ ] 테마 시스템 (라이트/다크/커스텀)
- [ ] 성능 최적화 자동 적용

### 기술적 요구사항
- [ ] 대시보드 런처 구현
- [ ] Textual 기반 TUI
- [ ] 통합 키보드 네비게이션
- [ ] 테마 관리 시스템
- [ ] 성능 모니터링 및 최적화

### 성능 요구사항
- [ ] 인터페이스 전환 < 1초
- [ ] 메모리 사용량 < 200MB
- [ ] CPU 사용률 < 10% (idle)
- [ ] 동시 렌더링 지원
- [ ] 캐시 적중률 > 80%

### 품질 요구사항
- [ ] 통합 테스트 완료
- [ ] 성능 벤치마크 통과
- [ ] 사용자 문서 작성
- [ ] 설정 가이드 제공

## 🎉 프로젝트 완료

모든 Phase가 완료되면:

1. **최종 테스트**
   ```bash
   # 전체 테스트 실행
   python -m pytest tests/ -v
   
   # 통합 테스트
   python -m pytest tests/test_integration.py -v
   
   # 성능 테스트
   python -m pytest tests/ -v --benchmark-only
   ```

2. **빌드 및 배포**
   ```bash
   # 웹 대시보드 빌드
   cd web-dashboard && npm run build
   
   # Tauri 앱 빌드
   cd tauri-dashboard && npm run tauri build
   
   # Python 패키지
   python setup.py sdist bdist_wheel
   ```

3. **문서화**
   - README 업데이트
   - 사용자 가이드 작성
   - API 문서 생성
   - 스크린샷/데모 추가

4. **릴리스**
   - 버전 태그 생성
   - 변경사항 정리
   - 릴리스 노트 작성
   - 배포 자동화

---

**프로젝트 완료!** 🚀