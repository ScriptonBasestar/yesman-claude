# Copyright notice.

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Dashboard Renderers Package Multi-format rendering system for Yesman Claude
dashboard.
"""

from .base_renderer import BaseRenderer, RenderFormat, ThemeColor, WidgetType
from .optimizations import (
    BatchRenderer,
    CacheStats,
    LazyRenderer,
    PerformanceProfiler,
    RenderCache,
    TimingContext,
    cached_layout,
    cached_render,
    clear_all_caches,
    clear_performance_stats,
    get_cache_stats,
    get_performance_stats,
    profile_render,
)
from .registry import RendererRegistry
from .renderer_factory import (
    RendererFactory,
    RendererFactoryError,
    RendererInitializationError,
    UnsupportedFormatError,
    create_renderer,
    get_renderer,
    render_all_formats,
    render_formats,
    render_widget,
)
from .tauri_renderer import TauriRenderer
from .tui_renderer import TUIRenderer
from .web_renderer import WebRenderer
from .widget_adapter import WidgetDataAdapter
from .widget_models import (
    ActivityData,
    ActivityEntry,
    ActivityType,
    ChartData,
    ChartDataPoint,
    HealthCategoryData,
    HealthData,
    HealthLevel,
    MetricCardData,
    ProgressData,
    ProgressPhase,
    SessionData,
    SessionStatus,
    StatusIndicatorData,
    WindowData,
)

__all__ = [
    "ActivityData",
    "ActivityEntry",
    "ActivityType",
    "BaseRenderer",
    "BatchRenderer",
    "CacheStats",
    "ChartData",
    "ChartDataPoint",
    "HealthCategoryData",
    "HealthData",
    "HealthLevel",
    "LazyRenderer",
    "MetricCardData",
    "PerformanceProfiler",
    "ProgressData",
    "ProgressPhase",
    "RenderCache",
    "RenderFormat",
    "RendererFactory",
    "RendererFactoryError",
    "RendererInitializationError",
    "RendererRegistry",
    "SessionData",
    "SessionStatus",
    "StatusIndicatorData",
    "TUIRenderer",
    "TauriRenderer",
    "ThemeColor",
    "TimingContext",
    "UnsupportedFormatError",
    "WebRenderer",
    "WidgetDataAdapter",
    "WidgetType",
    "WindowData",
    "cached_layout",
    "cached_render",
    "clear_all_caches",
    "clear_performance_stats",
    "create_renderer",
    "get_cache_stats",
    "get_performance_stats",
    "get_renderer",
    "profile_render",
    "render_all_formats",
    "render_formats",
    "render_widget",
]
