from typing import Any
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from .base_renderer import BaseRenderer, RenderFormat, WidgetType
from .registry import RendererRegistry
from .tauri_renderer import TauriRenderer
from .tui_renderer import TUIRenderer
from .web_renderer import WebRenderer

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Renderer Factory
Factory pattern for creating and managing dashboard renderers.
"""




class RendererFactoryError(Exception):
    """Base exception for renderer factory errors."""


class UnsupportedFormatError(RendererFactoryError):
    """Raised when unsupported format is requested."""


class RendererInitializationError(RendererFactoryError):
    """Raised when renderer initialization fails."""


class RendererFactory:
    """Factory for creating and managing dashboard renderers.

    Provides centralized creation, registration, and management of renderers
    with support for multiple output formats and thread-safe operations.
    """

    # Registered renderer classes
    _renderer_classes: dict[RenderFormat, type[BaseRenderer]] = {
        RenderFormat.TUI: TUIRenderer,
        RenderFormat.WEB: WebRenderer,
        RenderFormat.TAURI: TauriRenderer,
    }

    # Thread safety
    _lock = threading.Lock()
    _instances: dict[RenderFormat, BaseRenderer] = {}
    _initialized = False

    @classmethod
    def initialize(cls) -> None:
        """Initialize the factory and register all renderers."""
        with cls._lock:
            if cls._initialized:
                return

            try:
                cls.register_all()
                cls._initialized = True
            except Exception as e:
                msg = f"Failed to initialize renderer factory: {e}"
                raise RendererInitializationError(msg) from e

    @classmethod
    def register_all(cls) -> None:
        """Register all available renderers in the global registry."""
        registry = RendererRegistry()

        for render_format, renderer_class in cls._renderer_classes.items():
            try:
                # Register the class itself
                registry.register(render_format, renderer_class)
            except Exception as e:
                msg = f"Failed to register {render_format.value} renderer: {e}"
                raise RendererInitializationError(
                    msg,
                ) from e

    @classmethod
    def register_renderer(cls, render_format: RenderFormat, renderer_class: type[BaseRenderer]) -> None:
        """Register a new renderer class.

        Args:
            render_format: Format this renderer handles
            renderer_class: Renderer class to register
        """
        with cls._lock:
            cls._renderer_classes[render_format] = renderer_class

            # Update global registry if initialized
            if cls._initialized:
                try:
                    registry = RendererRegistry()
                    registry.register(render_format, renderer_class)
                except Exception as e:
                    msg = f"Failed to register {render_format.value} renderer: {e}"
                    raise RendererInitializationError(
                        msg,
                    ) from e

    @classmethod
    def create(cls, render_format: RenderFormat, **kwargs: dict[str, object]) -> BaseRenderer:
        """Create a renderer instance for the specified format.

        Args:
            render_format: Output format for rendering
            **kwargs: Arguments to pass to renderer constructor

        Returns:
            Configured renderer instance

        Raises:
            UnsupportedFormatError: If format is not supported
            RendererInitializationError: If renderer creation fails
        """
        if not cls._initialized:
            cls.initialize()

        if render_format not in cls._renderer_classes:
            msg = f"Unsupported render format: {render_format.value}. Available formats: {list(cls._renderer_classes.keys())}"
            raise UnsupportedFormatError(
                msg,
            )

        try:
            renderer_class = cls._renderer_classes[render_format]
            return renderer_class(**kwargs: dict[str, object])
        except Exception as e:
            msg = f"Failed to create {render_format.value} renderer: {e}"
            raise RendererInitializationError(
                msg,
            ) from e

    @classmethod
    def get_singleton(cls, render_format: RenderFormat, **kwargs: dict[str, object]) -> BaseRenderer:
        """Get or create a singleton renderer instance.

        Args:
            render_format: Output format for rendering
            **kwargs: Arguments to pass to renderer constructor (only on first creation)

        Returns:
            Singleton renderer instance
        """
        with cls._lock:
            if render_format not in cls._instances:
                cls._instances[render_format] = cls.create(render_format, **kwargs: dict[str, object])
            return cls._instances[render_format]

    @classmethod
    def render_universal(
        cls,
        widget_type: WidgetType,
        data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
        render_format: RenderFormat | None = None,
        options: dict[str, str | int | float | bool] | None = None,
    ) -> str | dict[str, str | int | float | bool] | list[str | int | float | bool] | dict[RenderFormat, str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
        """Universal rendering method with format selection.

        Args:
            widget_type: Type of widget to render
            data: Widget data to render
            render_format: Specific format to render (None for all formats)
            options: Rendering options

        Returns:
            Single result if format specified, dict of all results otherwise
        """
        if not cls._initialized:
            cls.initialize()

        options = options or {}

        if render_format:
            # Render with specific format
            renderer = cls.get_singleton(render_format)
            try:
                return renderer.render_widget(widget_type, data, options)
            except Exception as e:
                msg = f"Rendering failed for {render_format.value}: {e}"
                raise RendererFactoryError(
                    msg,
                ) from e
        else:
            # Render with all available formats
            results = {}
            errors = []

            for fmt in cls._renderer_classes:
                try:
                    renderer = cls.get_singleton(fmt)
                    results[fmt] = renderer.render_widget(widget_type, data, options)
                except Exception as e:
                    errors.append(f"{fmt.value}: {e}")

            if errors and not results:
                msg = f"All renderers failed: {'; '.join(errors)}"
                raise RendererFactoryError(msg)

            return results

    @classmethod
    def render_parallel(
        cls,
        widget_type: WidgetType,
        data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
        formats: list[RenderFormat] | None = None,
        options: dict[str, str | int | float | bool] | None = None,
        max_workers: int = 3,
    ) -> dict[RenderFormat, str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
        """Render widget with multiple formats in parallel.

        Args:
            widget_type: Type of widget to render
            data: Widget data to render
            formats: Specific formats to render (None for all)
            options: Rendering options
            max_workers: Maximum number of parallel workers

        Returns:
            Dict mapping formats to their rendered results
        """
        if not cls._initialized:
            cls.initialize()

        formats = formats or list(cls._renderer_classes.keys())
        options = options or {}
        results = {}
        errors = []

        def render_format(fmt: RenderFormat) -> tuple[RenderFormat, str | dict[str, str | int | float | bool] | list[str | int | float | bool] | None, str | None]:
            try:
                renderer = cls.get_singleton(fmt)
                result = renderer.render_widget(widget_type, data, options)
                return fmt, result, None
            except Exception as e:
                return fmt, None, str(e)

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_format = {executor.submit(render_format, fmt): fmt for fmt in formats}

            for future in as_completed(future_to_format):
                fmt, result, error = future.result()
                if error:
                    errors.append(f"{fmt.value}: {error}")
                else:
                    results[fmt] = result

        if errors and not results:
            msg = f"All parallel renders failed: {'; '.join(errors)}"
            raise RendererFactoryError(msg)

        return results

    @classmethod
    def get_supported_formats(cls) -> list[RenderFormat]:
        """Get list of supported render formats."""
        return list(cls._renderer_classes.keys())

    @classmethod
    def is_format_supported(cls, render_format: RenderFormat) -> bool:
        """Check if a render format is supported."""
        return render_format in cls._renderer_classes

    @classmethod
    def clear_instances(cls) -> None:
        """Clear all singleton instances (useful for testing)."""
        with cls._lock:
            cls._instances.clear()

    @classmethod
    def reset(cls) -> None:
        """Reset factory to uninitialized state (useful for testing)."""
        with cls._lock:
            cls._instances.clear()
            cls._initialized = False


# Convenience functions for easier usage


def render_widget(
    widget_type: WidgetType,
    data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
    render_format: RenderFormat,
    options: dict[str, str | int | float | bool] | None = None,
) -> str | dict[str, str | int | float | bool] | list[str | int | float | bool]:
    """Render a single widget with specified format.

    Args:
        widget_type: Type of widget to render
        data: Widget data to render
        render_format: Output format for rendering
        options: Rendering options

    Returns:
        Rendered widget output
    """
    return RendererFactory.render_universal(widget_type, data, render_format, options)


def render_all_formats(
    widget_type: WidgetType,
    data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
    options: dict[str, str | int | float | bool] | None = None,
) -> dict[RenderFormat, str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
    """Render a widget with all available formats.

    Args:
        widget_type: Type of widget to render
        data: Widget data to render
        options: Rendering options

    Returns:
        Dict mapping formats to their rendered outputs
    """
    return RendererFactory.render_universal(widget_type, data, None, options)


def render_formats(
    widget_type: WidgetType,
    data: dict[str, str | int | float | bool | list[str]] | list[str | int | float | bool] | str | int | float | bool,  # noqa: FBT001
    formats: list[RenderFormat],
    options: dict[str, str | int | float | bool] | None = None,
    parallel: bool = False,  # noqa: FBT001
) -> dict[RenderFormat, str | dict[str, str | int | float | bool] | list[str | int | float | bool]]:
    """Render a widget with specific formats.

    Args:
        widget_type: Type of widget to render
        data: Widget data to render
        formats: List of formats to render
        options: Rendering options
        parallel: Whether to render in parallel

    Returns:
        Dict mapping formats to their rendered outputs
    """
    if parallel:
        return RendererFactory.render_parallel(widget_type, data, formats, options)
    results = {}
    for fmt in formats:
        results[fmt] = render_widget(widget_type, data, fmt, options)
    return results


def create_renderer(render_format: RenderFormat, **kwargs: dict[str, object]) -> BaseRenderer:
    """Create a new renderer instance.

    Args:
        render_format: Format for the renderer
        **kwargs: Constructor arguments

    Returns:
        New renderer instance
    """
    return RendererFactory.create(render_format, **kwargs: dict[str, object])


def get_renderer(render_format: RenderFormat, **kwargs: dict[str, object]) -> BaseRenderer:
    """Get singleton renderer instance.

    Args:
        render_format: Format for the renderer
        **kwargs: Constructor arguments (only used on first creation)

    Returns:
        Singleton renderer instance
    """
    return RendererFactory.get_singleton(render_format, **kwargs: dict[str, object])
