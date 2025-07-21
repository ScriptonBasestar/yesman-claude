from typing import Any
from .base_renderer import BaseRenderer, RenderFormat

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Renderer Registry
Central registry for managing renderer instances and types.
"""



class RendererRegistry:
    """Registry for managing renderer classes and instances.

    Provides a centralized way to register, retrieve, and manage
    different renderer implementations for various formats.
    """

    def __init__(self) -> None:
        """Initialize the registry."""
        self._renderers: dict[RenderFormat, type[BaseRenderer]] = {}
        self._instances: dict[RenderFormat, BaseRenderer] = {}
        self._default_format: RenderFormat | None = None

    def register(self, format_type: RenderFormat, renderer_class: type[BaseRenderer]) -> None:
        """Register a renderer class for a specific format.

        Args:
            format_type: The format this renderer handles
            renderer_class: The renderer class to register

        Raises:
            ValueError: If renderer_class is not a subclass of BaseRenderer
        """
        if not issubclass(renderer_class, BaseRenderer):
            msg = f"Renderer class must be a subclass of BaseRenderer, got {renderer_class}"
            raise ValueError(msg)

        self._renderers[format_type] = renderer_class

        # Set as default if it's the first registered renderer
        if self._default_format is None:
            self._default_format = format_type

    def unregister(self, format_type: RenderFormat) -> None:
        """Unregister a renderer for a specific format.

        Args:
            format_type: The format to unregister
        """
        if format_type in self._renderers:
            del self._renderers[format_type]

        if format_type in self._instances:
            del self._instances[format_type]

        # Update default if necessary
        if self._default_format == format_type:
            self._default_format = next(iter(self._renderers.keys())) if self._renderers else None

    def get_renderer_class(self, format_type: RenderFormat) -> type[BaseRenderer] | None:
        """Get the renderer class for a specific format.

        Args:
            format_type: The format to get renderer class for

        Returns:
            Renderer class or None if not found
        """
        return self._renderers.get(format_type)

    def get_renderer(self, format_type: RenderFormat, **kwargs) -> BaseRenderer | None:
        """Get a renderer instance for a specific format.

        Args:
            format_type: The format to get renderer for
            **kwargs: Additional arguments to pass to renderer constructor

        Returns:
            Renderer instance or None if not found
        """
        if format_type not in self._renderers:
            return None

        # Return cached instance if available and no kwargs provided
        if format_type in self._instances and not kwargs:
            return self._instances[format_type]

        # Create new instance
        renderer_class = self._renderers[format_type]
        instance = renderer_class(format_type, **kwargs)

        # Cache instance if no custom kwargs
        if not kwargs:
            self._instances[format_type] = instance

        return instance

    def get_default_renderer(self, **kwargs) -> BaseRenderer | None:
        """Get the default renderer instance.

        Args:
            **kwargs: Additional arguments to pass to renderer constructor

        Returns:
            Default renderer instance or None if no default set
        """
        if self._default_format is None:
            return None

        return self.get_renderer(self._default_format, **kwargs)

    def set_default_format(self, format_type: RenderFormat) -> None:
        """Set the default renderer format.

        Args:
            format_type: The format to set as default

        Raises:
            ValueError: If the format is not registered
        """
        if format_type not in self._renderers:
            msg = f"Format {format_type} is not registered"
            raise ValueError(msg)

        self._default_format = format_type

    def get_default_format(self) -> RenderFormat | None:
        """Get the current default format.

        Returns:
            Default format or None if not set
        """
        return self._default_format

    def get_registered_formats(self) -> list[RenderFormat]:
        """Get list of all registered formats.

        Returns:
            List of registered formats
        """
        return list(self._renderers.keys())

    def is_registered(self, format_type: RenderFormat) -> bool:
        """Check if a format is registered.

        Args:
            format_type: The format to check

        Returns:
            True if registered, False otherwise
        """
        return format_type in self._renderers

    def clear(self) -> None:
        """Clear all registered renderers and instances."""
        self._renderers.clear()
        self._instances.clear()
        self._default_format = None

    def __len__(self) -> int:
        """Get number of registered renderers."""
        return len(self._renderers)

    def __contains__(self, format_type: RenderFormat) -> bool:
        """Check if format is registered."""
        return format_type in self._renderers

    def __repr__(self) -> str:
        """String representation of registry."""
        formats = ", ".join(f.value for f in self._renderers)
        default = self._default_format.value if self._default_format else "None"
        return f"RendererRegistry(formats=[{formats}], default={default})"


# Global registry instance
registry = RendererRegistry()


def register_renderer(format_type: RenderFormat, renderer_class: type[BaseRenderer]) -> None:
    """Convenience function to register a renderer globally.

    Args:
        format_type: The format this renderer handles
        renderer_class: The renderer class to register
    """
    registry.register(format_type, renderer_class)


def get_renderer(format_type: RenderFormat, **kwargs) -> BaseRenderer | None:
    """Convenience function to get a renderer from global registry.

    Args:
        format_type: The format to get renderer for
        **kwargs: Additional arguments to pass to renderer constructor

    Returns:
        Renderer instance or None if not found
    """
    return registry.get_renderer(format_type, **kwargs)


def get_default_renderer(**kwargs) -> BaseRenderer | None:
    """Convenience function to get default renderer from global registry.

    Args:
        **kwargs: Additional arguments to pass to renderer constructor

    Returns:
        Default renderer instance or None if no default set
    """
    return registry.get_default_renderer(**kwargs)
