#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Centralized Monitoring Configuration Management.

This module provides centralized configuration management for monitoring thresholds,
alert rules, and dashboard settings with hot-reload capabilities.
"""

import asyncio
import json
import time
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from watchdog.events import FileModifiedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus


class ConfigSection(Enum):
    """Configuration sections."""

    THRESHOLDS = "thresholds"
    ALERTS = "alerts"
    DASHBOARD = "dashboard"
    BASELINES = "baselines"
    QUALITY_GATES = "quality_gates"


@dataclass
class ThresholdConfig:
    """Threshold configuration for a metric."""

    metric: str
    component: str = "all"
    warning: float = 0.0
    error: float = 0.0
    critical: float = 0.0
    enabled: bool = True
    aggregation_window: int = 60
    min_occurrences: int = 3


@dataclass
class AlertRuleConfig:
    """Alert rule configuration."""

    name: str
    description: str
    condition: str  # Expression to evaluate
    severity: str
    cooldown: int = 300
    enabled: bool = True
    actions: list[str] = field(default_factory=list)


@dataclass
class DashboardConfig:
    """Dashboard configuration."""

    update_interval: float = 1.0
    metric_retention: int = 3600
    alert_retention: int = 86400
    chart_max_points: int = 60
    auto_refresh: bool = True
    default_view: str = "overview"
    components_to_monitor: list[str] = field(default_factory=list)


@dataclass
class MonitoringConfiguration:
    """Complete monitoring configuration."""

    version: str = "1.0"
    thresholds: dict[str, ThresholdConfig] = field(default_factory=dict)
    alert_rules: dict[str, AlertRuleConfig] = field(default_factory=dict)
    dashboard: DashboardConfig = field(default_factory=DashboardConfig)
    baselines: dict[str, dict[str, float]] = field(default_factory=dict)
    quality_gates: dict[str, Any] = field(default_factory=dict)
    custom_settings: dict[str, Any] = field(default_factory=dict)


class ConfigFileHandler(FileSystemEventHandler):
    """Handler for configuration file changes."""

    def __init__(self, manager: "MonitoringConfigManager") -> None:
        """Initialize config file handler.

        Args:
            manager: Parent configuration manager
        """
        self.manager = manager

    def on_modified(self, event: FileModifiedEvent) -> None:
        """Handle file modification event.

        Args:
            event: File modification event
        """
        if not event.is_directory and Path(event.src_path) == self.manager.config_path:
            asyncio.create_task(self.manager.reload_config())


class MonitoringConfigManager:
    """Centralized monitoring configuration manager."""

    def __init__(
        self,
        config_path: Path | None = None,
        auto_reload: bool = True,
    ) -> None:
        """Initialize configuration manager.

        Args:
            config_path: Path to configuration file
            auto_reload: Enable automatic configuration reload on file changes
        """
        self.config_path = config_path or Path("config/monitoring_config.json")
        self.auto_reload = auto_reload
        self.event_bus = get_event_bus()

        # Current configuration
        self.config = MonitoringConfiguration()

        # Configuration change callbacks
        self._change_callbacks: dict[ConfigSection, list[Callable]] = {section: [] for section in ConfigSection}

        # File watcher for auto-reload
        self._observer: Observer | None = None
        self._setup_file_watcher()

        # Load initial configuration
        self.load_config()

    def _setup_file_watcher(self) -> None:
        """Setup file watcher for configuration changes."""
        if not self.auto_reload:
            return

        if self.config_path.exists():
            self._observer = Observer()
            handler = ConfigFileHandler(self)
            self._observer.schedule(handler, str(self.config_path.parent), recursive=False)
            self._observer.start()

    def load_config(self) -> bool:
        """Load configuration from file.

        Returns:
            True if configuration loaded successfully
        """
        if not self.config_path.exists():
            # Create default configuration
            self._create_default_config()
            return True

        try:
            with open(self.config_path, encoding="utf-8") as f:
                data = json.load(f)

            # Parse configuration
            self.config = self._parse_config(data)

            # Notify about configuration load
            asyncio.create_task(self._notify_config_loaded())

            return True

        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False

    async def reload_config(self) -> bool:
        """Reload configuration from file.

        Returns:
            True if configuration reloaded successfully
        """
        old_config = self.config

        if self.load_config():
            # Detect changes and notify callbacks
            await self._detect_and_notify_changes(old_config, self.config)

            # Publish configuration reload event
            await self.event_bus.publish(
                Event(
                    type=EventType.CUSTOM,
                    data={
                        "event_subtype": "monitoring_config_reloaded",
                        "config_path": str(self.config_path),
                    },
                    timestamp=time.time(),
                    source="monitoring_config_manager",
                    priority=EventPriority.NORMAL,
                )
            )

            return True

        return False

    def _parse_config(self, data: dict[str, Any]) -> MonitoringConfiguration:
        """Parse configuration from dictionary.

        Args:
            data: Configuration data

        Returns:
            Parsed configuration
        """
        config = MonitoringConfiguration()

        # Parse version
        config.version = data.get("version", "1.0")

        # Parse thresholds
        if "thresholds" in data:
            for key, threshold_data in data["thresholds"].items():
                config.thresholds[key] = ThresholdConfig(**threshold_data)

        # Parse alert rules
        if "alert_rules" in data:
            for key, rule_data in data["alert_rules"].items():
                config.alert_rules[key] = AlertRuleConfig(**rule_data)

        # Parse dashboard settings
        if "dashboard" in data:
            config.dashboard = DashboardConfig(**data["dashboard"])

        # Parse baselines
        config.baselines = data.get("baselines", {})

        # Parse quality gates
        config.quality_gates = data.get("quality_gates", {})

        # Parse custom settings
        config.custom_settings = data.get("custom_settings", {})

        return config

    def _create_default_config(self) -> None:
        """Create default configuration file."""
        default_config = {
            "version": "1.0",
            "thresholds": {
                "response_time_warning": {
                    "metric": "response_time",
                    "component": "all",
                    "warning": 100.0,
                    "error": 200.0,
                    "critical": 500.0,
                    "enabled": True,
                    "aggregation_window": 60,
                    "min_occurrences": 3,
                },
                "memory_usage_warning": {
                    "metric": "memory_usage",
                    "component": "all",
                    "warning": 5.0,
                    "error": 10.0,
                    "critical": 25.0,
                    "enabled": True,
                    "aggregation_window": 60,
                    "min_occurrences": 3,
                },
                "cpu_usage_warning": {"metric": "cpu_usage", "component": "all", "warning": 50.0, "error": 75.0, "critical": 90.0, "enabled": True, "aggregation_window": 60, "min_occurrences": 3},
                "error_rate_warning": {"metric": "error_rate", "component": "all", "warning": 5.0, "error": 10.0, "critical": 25.0, "enabled": True, "aggregation_window": 300, "min_occurrences": 5},
            },
            "alert_rules": {
                "high_response_time": {
                    "name": "High Response Time",
                    "description": "Alert when response time exceeds threshold",
                    "condition": "response_time.p95 > 200",
                    "severity": "warning",
                    "cooldown": 300,
                    "enabled": True,
                    "actions": ["log", "dashboard_notification"],
                },
                "memory_leak": {
                    "name": "Memory Leak Detection",
                    "description": "Alert when memory usage shows consistent growth",
                    "condition": "memory_growth_rate > 1.0",
                    "severity": "error",
                    "cooldown": 600,
                    "enabled": True,
                    "actions": ["log", "dashboard_notification", "email"],
                },
                "performance_regression": {
                    "name": "Performance Regression",
                    "description": "Alert when performance regresses from baseline",
                    "condition": "regression_percent > 20",
                    "severity": "warning",
                    "cooldown": 1800,
                    "enabled": True,
                    "actions": ["log", "dashboard_notification"],
                },
            },
            "dashboard": {
                "update_interval": 1.0,
                "metric_retention": 3600,
                "alert_retention": 86400,
                "chart_max_points": 60,
                "auto_refresh": True,
                "default_view": "overview",
                "components_to_monitor": ["content_capture", "claude_status_check", "prompt_detection", "content_processing", "response_sending", "automation_analysis"],
            },
            "baselines": {},
            "quality_gates": {"performance_regression_threshold": 20.0, "max_response_time_ms": 500.0, "max_memory_growth_mb": 50.0, "max_error_rate_percent": 5.0},
            "custom_settings": {"enable_detailed_logging": False, "export_metrics_interval": 300, "metrics_export_format": "json"},
        }

        # Create config directory if it doesn't exist
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Write default configuration
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2)

        # Parse the default configuration
        self.config = self._parse_config(default_config)

    async def _detect_and_notify_changes(
        self,
        old_config: MonitoringConfiguration,
        new_config: MonitoringConfiguration,
    ) -> None:
        """Detect configuration changes and notify callbacks.

        Args:
            old_config: Previous configuration
            new_config: New configuration
        """
        # Check threshold changes
        if old_config.thresholds != new_config.thresholds:
            await self._notify_section_change(ConfigSection.THRESHOLDS, new_config.thresholds)

        # Check alert rule changes
        if old_config.alert_rules != new_config.alert_rules:
            await self._notify_section_change(ConfigSection.ALERTS, new_config.alert_rules)

        # Check dashboard changes
        if old_config.dashboard != new_config.dashboard:
            await self._notify_section_change(ConfigSection.DASHBOARD, new_config.dashboard)

        # Check baseline changes
        if old_config.baselines != new_config.baselines:
            await self._notify_section_change(ConfigSection.BASELINES, new_config.baselines)

        # Check quality gate changes
        if old_config.quality_gates != new_config.quality_gates:
            await self._notify_section_change(ConfigSection.QUALITY_GATES, new_config.quality_gates)

    async def _notify_section_change(self, section: ConfigSection, new_data: Any) -> None:
        """Notify callbacks about section change.

        Args:
            section: Configuration section that changed
            new_data: New configuration data
        """
        for callback in self._change_callbacks[section]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(new_data)
                else:
                    callback(new_data)
            except Exception as e:
                print(f"Error in configuration change callback: {e}")

    async def _notify_config_loaded(self) -> None:
        """Notify that configuration has been loaded."""
        await self.event_bus.publish(
            Event(
                type=EventType.CUSTOM,
                data={
                    "event_subtype": "monitoring_config_loaded",
                    "config_path": str(self.config_path),
                    "version": self.config.version,
                },
                timestamp=time.time(),
                source="monitoring_config_manager",
                priority=EventPriority.LOW,
            )
        )

    def register_change_callback(
        self,
        section: ConfigSection,
        callback: Callable,
    ) -> None:
        """Register callback for configuration changes.

        Args:
            section: Configuration section to monitor
            callback: Callback function
        """
        self._change_callbacks[section].append(callback)

    def get_threshold(self, threshold_id: str) -> ThresholdConfig | None:
        """Get threshold configuration by ID.

        Args:
            threshold_id: Threshold identifier

        Returns:
            Threshold configuration or None
        """
        return self.config.thresholds.get(threshold_id)

    def get_alert_rule(self, rule_id: str) -> AlertRuleConfig | None:
        """Get alert rule by ID.

        Args:
            rule_id: Alert rule identifier

        Returns:
            Alert rule configuration or None
        """
        return self.config.alert_rules.get(rule_id)

    def get_enabled_thresholds(self) -> dict[str, ThresholdConfig]:
        """Get all enabled thresholds.

        Returns:
            Dictionary of enabled thresholds
        """
        return {key: threshold for key, threshold in self.config.thresholds.items() if threshold.enabled}

    def get_enabled_alert_rules(self) -> dict[str, AlertRuleConfig]:
        """Get all enabled alert rules.

        Returns:
            Dictionary of enabled alert rules
        """
        return {key: rule for key, rule in self.config.alert_rules.items() if rule.enabled}

    def update_threshold(
        self,
        threshold_id: str,
        updates: dict[str, Any],
    ) -> bool:
        """Update threshold configuration.

        Args:
            threshold_id: Threshold identifier
            updates: Updates to apply

        Returns:
            True if update successful
        """
        if threshold_id not in self.config.thresholds:
            return False

        threshold = self.config.thresholds[threshold_id]
        for key, value in updates.items():
            if hasattr(threshold, key):
                setattr(threshold, key, value)

        # Save configuration
        self.save_config()

        return True

    def update_baseline(
        self,
        component: str,
        baseline_data: dict[str, float],
    ) -> None:
        """Update performance baseline.

        Args:
            component: Component name
            baseline_data: New baseline data
        """
        self.config.baselines[component] = baseline_data
        self.save_config()

    def save_config(self) -> bool:
        """Save current configuration to file.

        Returns:
            True if save successful
        """
        try:
            # Convert configuration to dictionary
            config_dict = {
                "version": self.config.version,
                "thresholds": {key: asdict(threshold) for key, threshold in self.config.thresholds.items()},
                "alert_rules": {key: asdict(rule) for key, rule in self.config.alert_rules.items()},
                "dashboard": asdict(self.config.dashboard),
                "baselines": self.config.baselines,
                "quality_gates": self.config.quality_gates,
                "custom_settings": self.config.custom_settings,
            }

            # Write to file
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(config_dict, f, indent=2)

            return True

        except Exception as e:
            print(f"Error saving configuration: {e}")
            return False

    def export_config(self, export_path: Path) -> bool:
        """Export configuration to another file.

        Args:
            export_path: Path to export configuration to

        Returns:
            True if export successful
        """
        try:
            # Read current config file
            with open(self.config_path, encoding="utf-8") as f:
                config_data = json.load(f)

            # Write to export path
            export_path.parent.mkdir(parents=True, exist_ok=True)
            with open(export_path, "w", encoding="utf-8") as f:
                json.dump(config_data, f, indent=2)

            return True

        except Exception as e:
            print(f"Error exporting configuration: {e}")
            return False

    def import_config(self, import_path: Path) -> bool:
        """Import configuration from another file.

        Args:
            import_path: Path to import configuration from

        Returns:
            True if import successful
        """
        try:
            # Read import file
            with open(import_path, encoding="utf-8") as f:
                config_data = json.load(f)

            # Parse and validate
            new_config = self._parse_config(config_data)

            # Update current configuration
            old_config = self.config
            self.config = new_config

            # Save to current config file
            self.save_config()

            # Notify about changes
            asyncio.create_task(self._detect_and_notify_changes(old_config, new_config))

            return True

        except Exception as e:
            print(f"Error importing configuration: {e}")
            return False

    def stop(self) -> None:
        """Stop the configuration manager."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join()


# Singleton instance
_config_manager: MonitoringConfigManager | None = None


def get_monitoring_config_manager(
    config_path: Path | None = None,
    auto_reload: bool = True,
) -> MonitoringConfigManager:
    """Get or create monitoring configuration manager.

    Args:
        config_path: Path to configuration file
        auto_reload: Enable automatic configuration reload

    Returns:
        Configuration manager instance
    """
    global _config_manager  # noqa: PLW0603

    if _config_manager is None:
        _config_manager = MonitoringConfigManager(config_path, auto_reload)

    return _config_manager
