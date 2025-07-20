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
    "AsyncPerformanceOptimizer",
    "ColorPalette",
    "DashboardLauncher",
    "DashboardWidget",
    "FocusableElement",
    "InterfaceInfo",
    "KeyBinding",
    "KeyModifier",
    "KeyboardNavigationManager",
    "NavigationContext",
    "OptimizationLevel",
    "PerformanceMetrics",
    "PerformanceOptimizer",
    "PerformanceProfiler",
    "PerformanceThreshold",
    "Spacing",
    "SystemThemeDetector",
    "TUIDashboard",
    "Theme",
    "ThemeManager",
    "ThemeMode",
    "Typography",
    "get_keyboard_manager",
    "get_performance_optimizer",
    "get_theme_manager",
    "reset_keyboard_manager",
    "reset_performance_optimizer",
    "reset_theme_manager",
    "run_tui_dashboard",
]
