"""
Dashboard Renderers Package
Multi-format rendering system for Yesman Claude dashboard
"""

from .base_renderer import BaseRenderer, RenderFormat, WidgetType, ThemeColor
from .registry import RendererRegistry
from .tui_renderer import TUIRenderer
from .web_renderer import WebRenderer
from .tauri_renderer import TauriRenderer
from .renderer_factory import (
    RendererFactory, RendererFactoryError, UnsupportedFormatError,
    RendererInitializationError, render_widget, render_all_formats,
    render_formats, create_renderer, get_renderer
)
from .optimizations import (
    RenderCache, CacheStats, cached_render, cached_layout,
    LazyRenderer, BatchRenderer, PerformanceProfiler, TimingContext,
    profile_render, get_cache_stats, clear_all_caches,
    get_performance_stats, clear_performance_stats
)
from .widget_models import (
    SessionData, SessionStatus, WindowData,
    HealthData, HealthCategoryData, HealthLevel,
    ActivityData, ActivityEntry, ActivityType,
    ProgressData, ProgressPhase,
    MetricCardData, StatusIndicatorData,
    ChartData, ChartDataPoint
)
from .widget_adapter import WidgetDataAdapter

__all__ = [
    'BaseRenderer',
    'RenderFormat', 
    'WidgetType',
    'ThemeColor',
    'RendererRegistry',
    'TUIRenderer',
    'WebRenderer',
    'TauriRenderer',
    'RendererFactory',
    'RendererFactoryError',
    'UnsupportedFormatError', 
    'RendererInitializationError',
    'render_widget',
    'render_all_formats',
    'render_formats',
    'create_renderer',
    'get_renderer',
    'RenderCache',
    'CacheStats',
    'cached_render',
    'cached_layout',
    'LazyRenderer',
    'BatchRenderer',
    'PerformanceProfiler',
    'TimingContext',
    'profile_render',
    'get_cache_stats',
    'clear_all_caches',
    'get_performance_stats',
    'clear_performance_stats',
    'SessionData',
    'SessionStatus',
    'WindowData', 
    'HealthData',
    'HealthCategoryData',
    'HealthLevel',
    'ActivityData',
    'ActivityEntry',
    'ActivityType',
    'ProgressData', 
    'ProgressPhase',
    'MetricCardData',
    'StatusIndicatorData',
    'ChartData',
    'ChartDataPoint',
    'WidgetDataAdapter'
]