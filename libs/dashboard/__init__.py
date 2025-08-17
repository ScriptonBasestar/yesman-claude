# Copyright notice.

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
try:  # pragma: no cover - optional feature
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
except ModuleNotFoundError:  # pragma: no cover
    AsyncPerformanceOptimizer = OptimizationLevel = PerformanceMetrics = PerformanceOptimizer = (
        PerformanceProfiler
    ) = PerformanceThreshold = get_performance_optimizer = reset_performance_optimizer = None  # type: ignore
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
try:  # pragma: no cover - optional feature
    from .tui_dashboard import DashboardWidget, TUIDashboard, run_tui_dashboard
except ModuleNotFoundError:  # pragma: no cover
    DashboardWidget = TUIDashboard = run_tui_dashboard = None  # type: ignore

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Dashboard modules for project status visualization."""


__all__ = [
    "AsyncPerformanceOptimizer",
    "ColorPalette",
    "DashboardLauncher",
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
]

if TUIDashboard is not None:
    __all__.extend(["DashboardWidget", "TUIDashboard", "run_tui_dashboard"])
