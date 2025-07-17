"""Dashboard modules for project status visualization."""

from .dashboard_launcher import DashboardLauncher, InterfaceInfo
from .keyboard_navigation import (
    FocusableElement,
    KeyBinding,
    KeyboardNavigationManager,
    KeyModifier,
    NavigationContext,
    get_keyboard_manager,
    reset_keyboard_manager,
)
from .performance_optimizer import (
    AsyncPerformanceOptimizer,
    OptimizationLevel,
    PerformanceMetrics,
    PerformanceOptimizer,
    PerformanceProfiler,
    PerformanceThreshold,
    get_performance_optimizer,
    reset_performance_optimizer,
)
from .theme_system import (
    ColorPalette,
    Spacing,
    SystemThemeDetector,
    Theme,
    ThemeManager,
    ThemeMode,
    Typography,
    get_theme_manager,
    reset_theme_manager,
)
from .tui_dashboard import DashboardWidget, TUIDashboard, run_tui_dashboard

__all__ = [
    "DashboardLauncher",
    "InterfaceInfo",
    "TUIDashboard",
    "DashboardWidget",
    "run_tui_dashboard",
    "KeyboardNavigationManager",
    "KeyBinding",
    "KeyModifier",
    "NavigationContext",
    "FocusableElement",
    "get_keyboard_manager",
    "reset_keyboard_manager",
    "ThemeManager",
    "Theme",
    "ThemeMode",
    "ColorPalette",
    "Typography",
    "Spacing",
    "SystemThemeDetector",
    "get_theme_manager",
    "reset_theme_manager",
    "PerformanceOptimizer",
    "AsyncPerformanceOptimizer",
    "PerformanceMetrics",
    "OptimizationLevel",
    "PerformanceThreshold",
    "PerformanceProfiler",
    "get_performance_optimizer",
    "reset_performance_optimizer",
]
