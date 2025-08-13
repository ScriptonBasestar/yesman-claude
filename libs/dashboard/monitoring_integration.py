#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Monitoring Dashboard Integration Module.

This module provides comprehensive integration between the performance monitoring
system and visual dashboards, including real-time metrics visualization,
automated alerting, and quality gates integration.
"""

import asyncio
import json
import logging
import time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from libs.core.async_event_bus import AsyncEventBus, Event, EventPriority, EventType, get_event_bus

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of performance metrics."""

    RESPONSE_TIME = "response_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    QUEUE_DEPTH = "queue_depth"
    NETWORK_IO = "network_io"
    ERROR_RATE = "error_rate"


@dataclass
class AlertThreshold:
    """Configuration for alert thresholds."""

    metric_type: MetricType
    component: str
    warning_threshold: float
    error_threshold: float
    critical_threshold: float
    aggregation_window: int = 60  # seconds
    min_occurrences: int = 3  # minimum occurrences before alerting


@dataclass
class PerformanceAlert:
    """Performance alert data structure."""

    timestamp: float
    severity: AlertSeverity
    metric_type: MetricType
    component: str
    current_value: float
    threshold: float
    message: str
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class MonitoringConfig:
    """Monitoring dashboard configuration."""

    # Alert thresholds
    response_time_ms: float = 100.0
    memory_delta_mb: float = 5.0
    cpu_percent: float = 50.0
    queue_utilization: float = 80.0
    network_throughput_mb: float = 1.0
    error_rate_percent: float = 5.0

    # Dashboard settings
    update_interval: float = 1.0  # seconds
    metric_retention: int = 3600  # seconds (1 hour)
    alert_retention: int = 86400  # seconds (24 hours)

    # Quality gates integration
    quality_gates_enabled: bool = True
    performance_regression_threshold: float = 20.0  # percent

    # Alert settings
    alert_cooldown: int = 300  # seconds between same alerts
    alert_aggregation_window: int = 60  # seconds


class MonitoringDashboardIntegration:
    """Main monitoring dashboard integration class."""

    def __init__(
        self,
        config: MonitoringConfig | None = None,
        event_bus: AsyncEventBus | None = None,
    ) -> None:
        """Initialize monitoring dashboard integration.

        Args:
            config: Monitoring configuration
            event_bus: Event bus for system communication
        """
        self.config = config or MonitoringConfig()
        self.event_bus = event_bus or get_event_bus()

        # Metrics storage (component -> metric_type -> deque of (timestamp, value))
        self._metrics_storage: dict[str, dict[MetricType, deque]] = {}

        # Alert management
        self._active_alerts: list[PerformanceAlert] = []
        self._alert_history: deque = deque(maxlen=1000)
        self._last_alert_times: dict[tuple[str, MetricType], float] = {}

        # Alert thresholds configuration
        self._alert_thresholds: list[AlertThreshold] = []
        self._setup_default_thresholds()

        # Performance baselines for regression detection
        self._performance_baselines: dict[str, dict[str, float]] = {}
        self._load_performance_baselines()

        # Dashboard state
        self._is_running = False
        self._dashboard_task: asyncio.Task | None = None
        self._alert_task: asyncio.Task | None = None

        # Alert callbacks
        self._alert_callbacks: list[Callable[[PerformanceAlert], None]] = []

        # Setup event subscriptions
        self._setup_event_subscriptions()

    def _setup_default_thresholds(self) -> None:
        """Setup default alert thresholds."""
        # Component response time thresholds
        components = ["content_capture", "claude_status_check", "prompt_detection", "content_processing", "response_sending", "automation_analysis"]

        for component in components:
            self._alert_thresholds.append(
                AlertThreshold(
                    metric_type=MetricType.RESPONSE_TIME,
                    component=component,
                    warning_threshold=self.config.response_time_ms,
                    error_threshold=self.config.response_time_ms * 2,
                    critical_threshold=self.config.response_time_ms * 5,
                )
            )

            # Memory thresholds
            self._alert_thresholds.append(
                AlertThreshold(
                    metric_type=MetricType.MEMORY_USAGE,
                    component=component,
                    warning_threshold=self.config.memory_delta_mb,
                    error_threshold=self.config.memory_delta_mb * 2,
                    critical_threshold=self.config.memory_delta_mb * 5,
                )
            )

            # CPU thresholds
            self._alert_thresholds.append(
                AlertThreshold(
                    metric_type=MetricType.CPU_USAGE,
                    component=component,
                    warning_threshold=self.config.cpu_percent,
                    error_threshold=self.config.cpu_percent * 1.5,
                    critical_threshold=100.0,
                )
            )

    def _load_performance_baselines(self) -> None:
        """Load performance baselines from file."""
        baseline_path = Path("data/performance_baselines.json")
        if baseline_path.exists():
            try:
                with open(baseline_path, encoding="utf-8") as f:
                    self._performance_baselines = json.load(f)
            except Exception:
                self._performance_baselines = {}

    def _setup_event_subscriptions(self) -> None:
        """Setup event bus subscriptions."""
        self.event_bus.subscribe(EventType.PERFORMANCE_METRICS, self._handle_performance_metrics)
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, self._handle_shutdown)

    async def start(self) -> None:
        """Start the monitoring dashboard integration."""
        if self._is_running:
            return

        self._is_running = True

        # Start dashboard update task
        self._dashboard_task = asyncio.create_task(self._dashboard_update_loop())

        # Start alert monitoring task
        self._alert_task = asyncio.create_task(self._alert_monitoring_loop())

        # Publish startup event
        await self.event_bus.publish(
            Event(
                type=EventType.DASHBOARD_UPDATE,
                data={
                    "update_type": "monitoring_started",
                    "config": {
                        "update_interval": self.config.update_interval,
                        "thresholds": len(self._alert_thresholds),
                    },
                },
                timestamp=time.time(),
                source="monitoring_dashboard",
                priority=EventPriority.HIGH,
            )
        )

    async def stop(self) -> None:
        """Stop the monitoring dashboard integration."""
        if not self._is_running:
            return

        self._is_running = False

        # Cancel tasks
        if self._dashboard_task and not self._dashboard_task.done():
            self._dashboard_task.cancel()
            try:
                await self._dashboard_task
            except asyncio.CancelledError:
                pass

        if self._alert_task and not self._alert_task.done():
            self._alert_task.cancel()
            try:
                await self._alert_task
            except asyncio.CancelledError:
                pass

    async def _handle_performance_metrics(self, event: Event) -> None:
        """Handle incoming performance metrics events.

        Args:
            event: Performance metrics event
        """
        data = event.data
        if not isinstance(data, dict) or "metrics" not in data:
            return

        metrics = data["metrics"]
        component_name = data.get("component", "unknown")

        # Store component metrics
        if "component_response_times" in metrics:
            await self._process_component_metrics(metrics["component_response_times"])

        # Check for performance regressions
        if self.config.quality_gates_enabled:
            await self._check_performance_regression(component_name, metrics)

    async def _process_component_metrics(self, component_metrics: dict[str, dict[str, float]]) -> None:
        """Process and store component metrics.

        Args:
            component_metrics: Component performance metrics
        """
        timestamp = time.time()

        for component, metrics in component_metrics.items():
            if component not in self._metrics_storage:
                self._metrics_storage[component] = {metric_type: deque(maxlen=self.config.metric_retention) for metric_type in MetricType}

            # Store response time metrics
            if "average_ms" in metrics:
                self._metrics_storage[component][MetricType.RESPONSE_TIME].append((timestamp, metrics["average_ms"]))

            # Store memory metrics
            if "avg_memory_delta_mb" in metrics:
                self._metrics_storage[component][MetricType.MEMORY_USAGE].append((timestamp, abs(metrics["avg_memory_delta_mb"])))

            # Store CPU metrics
            if "avg_cpu_percent" in metrics:
                self._metrics_storage[component][MetricType.CPU_USAGE].append((timestamp, metrics["avg_cpu_percent"]))

            # Store error rate
            if "error_rate" in metrics:
                self._metrics_storage[component][MetricType.ERROR_RATE].append((timestamp, metrics["error_rate"] * 100))

            # Store network I/O
            if "avg_throughput_mbps" in metrics:
                self._metrics_storage[component][MetricType.NETWORK_IO].append((timestamp, metrics["avg_throughput_mbps"]))

    async def _check_performance_regression(self, component: str, metrics: dict[str, Any]) -> None:
        """Check for performance regression against baselines.

        Args:
            component: Component name
            metrics: Current metrics
        """
        if component not in self._performance_baselines:
            return

        baseline = self._performance_baselines[component]
        regressions = []

        # Check response time regression
        if "component_response_times" in metrics:
            for comp_name, comp_metrics in metrics["component_response_times"].items():
                if comp_name in baseline and "average_ms" in comp_metrics:
                    baseline_value = baseline.get(f"{comp_name}_avg_ms", 0)
                    if baseline_value > 0:
                        current_value = comp_metrics["average_ms"]
                        regression_percent = ((current_value - baseline_value) / baseline_value) * 100

                        if regression_percent > self.config.performance_regression_threshold:
                            regressions.append(
                                {
                                    "component": comp_name,
                                    "metric": "response_time",
                                    "baseline": baseline_value,
                                    "current": current_value,
                                    "regression_percent": regression_percent,
                                }
                            )

        # Publish regression alerts
        if regressions:
            await self._create_regression_alert(component, regressions)

    async def _create_regression_alert(self, component: str, regressions: list[dict]) -> None:
        """Create performance regression alert.

        Args:
            component: Component name
            regressions: List of detected regressions
        """
        severity = AlertSeverity.WARNING
        if any(r["regression_percent"] > 50 for r in regressions):
            severity = AlertSeverity.ERROR

        alert = PerformanceAlert(
            timestamp=time.time(),
            severity=severity,
            metric_type=MetricType.RESPONSE_TIME,
            component=component,
            current_value=max(r["current"] for r in regressions),
            threshold=max(r["baseline"] for r in regressions),
            message=f"Performance regression detected in {component}",
            context={"regressions": regressions},
        )

        await self._process_alert(alert)

    async def _dashboard_update_loop(self) -> None:
        """Main dashboard update loop."""
        while self._is_running:
            try:
                # Prepare dashboard data
                dashboard_data = await self._prepare_dashboard_data()

                # Publish dashboard update
                await self.event_bus.publish(
                    Event(
                        type=EventType.DASHBOARD_UPDATE,
                        data={
                            "update_type": "metrics_update",
                            "metrics": dashboard_data["metrics"],
                            "alerts": dashboard_data["alerts"],
                            "health_score": dashboard_data["health_score"],
                        },
                        timestamp=time.time(),
                        source="monitoring_dashboard",
                        priority=EventPriority.LOW,
                    )
                )

                await asyncio.sleep(self.config.update_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self.config.update_interval)

    async def _alert_monitoring_loop(self) -> None:
        """Alert monitoring and processing loop."""
        while self._is_running:
            try:
                # Check metrics against thresholds
                await self._check_alert_thresholds()

                # Clean up old alerts
                self._cleanup_old_alerts()

                await asyncio.sleep(self.config.alert_aggregation_window)

            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(self.config.alert_aggregation_window)

    async def _check_alert_thresholds(self) -> None:
        """Check current metrics against alert thresholds."""
        current_time = time.time()

        for threshold in self._alert_thresholds:
            if threshold.component not in self._metrics_storage:
                continue

            metrics = self._metrics_storage[threshold.component].get(threshold.metric_type)
            if not metrics:
                continue

            # Get recent metrics within aggregation window
            recent_metrics = [value for timestamp, value in metrics if current_time - timestamp <= threshold.aggregation_window]

            if len(recent_metrics) < threshold.min_occurrences:
                continue

            # Calculate average value
            avg_value = sum(recent_metrics) / len(recent_metrics)

            # Check against thresholds
            severity = None
            threshold_value = 0

            if avg_value >= threshold.critical_threshold:
                severity = AlertSeverity.CRITICAL
                threshold_value = threshold.critical_threshold
            elif avg_value >= threshold.error_threshold:
                severity = AlertSeverity.ERROR
                threshold_value = threshold.error_threshold
            elif avg_value >= threshold.warning_threshold:
                severity = AlertSeverity.WARNING
                threshold_value = threshold.warning_threshold

            if severity:
                # Check cooldown
                alert_key = (threshold.component, threshold.metric_type)
                last_alert_time = self._last_alert_times.get(alert_key, 0)

                if current_time - last_alert_time >= self.config.alert_cooldown:
                    alert = PerformanceAlert(
                        timestamp=current_time,
                        severity=severity,
                        metric_type=threshold.metric_type,
                        component=threshold.component,
                        current_value=avg_value,
                        threshold=threshold_value,
                        message=f"{threshold.component} {threshold.metric_type.value} exceeded threshold",
                        context={
                            "samples": len(recent_metrics),
                            "window": threshold.aggregation_window,
                        },
                    )

                    await self._process_alert(alert)
                    self._last_alert_times[alert_key] = current_time

    async def _process_alert(self, alert: PerformanceAlert) -> None:
        """Process and distribute an alert.

        Args:
            alert: Performance alert to process
        """
        # Add to active alerts
        self._active_alerts.append(alert)
        self._alert_history.append(alert)

        # Call registered callbacks
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.debug("Alert callback failed: %s", e)

        # Publish alert event
        await self.event_bus.publish(
            Event(
                type=EventType.CUSTOM,
                data={
                    "event_subtype": "performance_alert",
                    "severity": alert.severity.value,
                    "component": alert.component,
                    "metric_type": alert.metric_type.value,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "message": alert.message,
                    "context": alert.context,
                },
                timestamp=alert.timestamp,
                source="monitoring_dashboard",
                priority=EventPriority.HIGH if alert.severity in {AlertSeverity.ERROR, AlertSeverity.CRITICAL} else EventPriority.NORMAL,
            )
        )

    def _cleanup_old_alerts(self) -> None:
        """Remove old alerts from active list."""
        current_time = time.time()
        self._active_alerts = [alert for alert in self._active_alerts if current_time - alert.timestamp < self.config.alert_retention]

    async def _prepare_dashboard_data(self) -> dict[str, Any]:
        """Prepare data for dashboard update.

        Returns:
            Dashboard data dictionary
        """
        current_time = time.time()

        # Prepare metrics summary
        metrics_summary = {}
        for component, metrics in self._metrics_storage.items():
            component_summary = {}

            for metric_type, values in metrics.items():
                if values:
                    recent_values = [
                        value
                        for timestamp, value in values
                        if current_time - timestamp <= 60  # Last minute
                    ]

                    if recent_values:
                        component_summary[metric_type.value] = {
                            "current": recent_values[-1],
                            "average": sum(recent_values) / len(recent_values),
                            "max": max(recent_values),
                            "min": min(recent_values),
                            "samples": len(recent_values),
                        }

            if component_summary:
                metrics_summary[component] = component_summary

        # Calculate health score
        health_score = self._calculate_health_score()

        # Prepare alerts summary
        alerts_summary = {
            "active": len(self._active_alerts),
            "critical": sum(1 for a in self._active_alerts if a.severity == AlertSeverity.CRITICAL),
            "error": sum(1 for a in self._active_alerts if a.severity == AlertSeverity.ERROR),
            "warning": sum(1 for a in self._active_alerts if a.severity == AlertSeverity.WARNING),
            "recent": [
                {
                    "timestamp": alert.timestamp,
                    "severity": alert.severity.value,
                    "component": alert.component,
                    "message": alert.message,
                }
                for alert in self._active_alerts[-5:]  # Last 5 alerts
            ],
        }

        return {
            "metrics": metrics_summary,
            "alerts": alerts_summary,
            "health_score": health_score,
            "timestamp": current_time,
        }

    def _calculate_health_score(self) -> float:
        """Calculate overall system health score.

        Returns:
            Health score between 0 and 100
        """
        score = 100.0

        # Deduct points for active alerts
        for alert in self._active_alerts:
            if alert.severity == AlertSeverity.CRITICAL:
                score -= 20
            elif alert.severity == AlertSeverity.ERROR:
                score -= 10
            elif alert.severity == AlertSeverity.WARNING:
                score -= 5

        # Ensure score stays in range
        return max(0.0, min(100.0, score))

    async def _handle_shutdown(self, event: Event) -> None:
        """Handle system shutdown event.

        Args:
            event: Shutdown event
        """
        await self.stop()

    def register_alert_callback(self, callback: Callable[[PerformanceAlert], None]) -> None:
        """Register a callback for alert notifications.

        Args:
            callback: Function to call when alert is triggered
        """
        self._alert_callbacks.append(callback)

    def add_custom_threshold(self, threshold: AlertThreshold) -> None:
        """Add a custom alert threshold.

        Args:
            threshold: Alert threshold configuration
        """
        self._alert_thresholds.append(threshold)

    def get_metrics_for_component(self, component: str) -> dict[str, list[tuple[float, float]]]:
        """Get all metrics for a specific component.

        Args:
            component: Component name

        Returns:
            Dictionary of metric type to list of (timestamp, value) tuples
        """
        if component not in self._metrics_storage:
            return {}

        return {metric_type.value: list(values) for metric_type, values in self._metrics_storage[component].items()}

    def get_active_alerts(self) -> list[PerformanceAlert]:
        """Get list of active alerts.

        Returns:
            List of active performance alerts
        """
        return self._active_alerts.copy()

    def update_baseline(self, component: str, baseline_data: dict[str, float]) -> None:
        """Update performance baseline for a component.

        Args:
            component: Component name
            baseline_data: New baseline data
        """
        self._performance_baselines[component] = baseline_data

        # Save to file
        baseline_path = Path("data/performance_baselines.json")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)

        with open(baseline_path, "w", encoding="utf-8") as f:
            json.dump(self._performance_baselines, f, indent=2)

    async def publish_test_metrics(self, metrics_data: dict) -> None:
        """Publish test execution metrics to the monitoring system.

        Args:
            metrics_data: Test metrics data dictionary
        """
        # Create test metrics event
        event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "test_execution_metrics",
                "test_metrics": metrics_data,
                "category": "test_performance",
            },
            timestamp=metrics_data.get("timestamp", time.time()),
            source="test_runner",
            priority=EventPriority.LOW,
        )

        # Store test metrics for analysis
        test_name = metrics_data.get("test_name", "unknown")
        if "test_performance" not in self._metrics_storage:
            self._metrics_storage["test_performance"] = {}

        if test_name not in self._metrics_storage["test_performance"]:
            self._metrics_storage["test_performance"][test_name] = deque(maxlen=100)

        # Store test execution metrics
        self._metrics_storage["test_performance"][test_name].append(
            {
                "timestamp": time.time(),
                "duration_ms": metrics_data.get("duration_ms", 0),
                "memory_delta_mb": metrics_data.get("memory_delta_mb", 0),
                "status": metrics_data.get("status", "unknown"),
                "suite": metrics_data.get("suite", "unknown"),
            }
        )

        # Check for test performance regressions
        await self._check_test_performance_regression(test_name, metrics_data)

        # Publish to event bus
        await self.event_bus.publish(event)

    async def _check_test_performance_regression(self, test_name: str, metrics_data: dict) -> None:
        """Check for test performance regression.

        Args:
            test_name: Name of the test
            metrics_data: Current test metrics
        """
        if "test_baselines" not in self._performance_baselines:
            return

        test_baselines = self._performance_baselines["test_baselines"]
        if test_name not in test_baselines:
            return

        baseline = test_baselines[test_name]
        current_duration = metrics_data.get("duration_ms", 0)
        baseline_duration = baseline.get("baseline_duration_ms", 0)

        if baseline_duration > 0 and current_duration > 0:
            regression_percent = ((current_duration - baseline_duration) / baseline_duration) * 100

            # Check if regression exceeds threshold
            threshold = self.config.performance_regression_threshold
            if regression_percent > threshold:
                # Create test performance regression alert
                alert = PerformanceAlert(
                    timestamp=time.time(),
                    severity=AlertSeverity.WARNING if regression_percent < threshold * 2 else AlertSeverity.ERROR,
                    metric_type=MetricType.RESPONSE_TIME,
                    component="test_performance",
                    current_value=current_duration,
                    threshold=baseline_duration * (1 + threshold / 100),
                    message=f"Test performance regression detected: {test_name}",
                    context={
                        "test_name": test_name,
                        "regression_percent": regression_percent,
                        "baseline_duration_ms": baseline_duration,
                        "current_duration_ms": current_duration,
                    },
                )

                await self._process_alert(alert)

    def get_test_performance_summary(self) -> dict[str, Any]:
        """Get test performance summary data.

        Returns:
            Dictionary with test performance summary
        """
        if "test_performance" not in self._metrics_storage:
            return {}

        summary = {}
        for test_name, metrics in self._metrics_storage["test_performance"].items():
            if not metrics:
                continue

            durations = [m["duration_ms"] for m in metrics if m["status"] == "passed"]
            if not durations:
                continue

            summary[test_name] = {
                "total_runs": len(metrics),
                "passed_runs": sum(1 for m in metrics if m["status"] == "passed"),
                "failed_runs": sum(1 for m in metrics if m["status"] == "failed"),
                "avg_duration_ms": sum(durations) / len(durations),
                "min_duration_ms": min(durations),
                "max_duration_ms": max(durations),
                "success_rate": sum(1 for m in metrics if m["status"] == "passed") / len(metrics),
                "last_run_status": metrics[-1]["status"],
                "last_run_duration_ms": metrics[-1]["duration_ms"],
            }

        return summary

    # User Experience Integration Methods

    async def publish_troubleshooting_event(self, event_data: dict) -> None:
        """Publish troubleshooting-related events to the monitoring system.

        Args:
            event_data: Troubleshooting event data
        """
        event = Event(
            type=EventType.CUSTOM,
            data={"event_subtype": "troubleshooting_activity", **event_data},
            timestamp=time.time(),
            source="troubleshooting_system",
            priority=EventPriority.NORMAL,
        )

        await self.event_bus.publish(event)

    async def publish_error_handling_metrics(self, error_data: dict) -> None:
        """Publish error handling metrics and insights.

        Args:
            error_data: Error handling metrics data
        """
        event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "error_handling_metrics",
                "error_code": error_data.get("error_code"),
                "category": error_data.get("category"),
                "severity": error_data.get("severity"),
                "component": error_data.get("component"),
                "auto_fix_available": error_data.get("auto_fix_available", False),
                "user_friendly": True,
                "context": error_data.get("context", {}),
                "timestamp": error_data.get("timestamp", time.time()),
            },
            timestamp=time.time(),
            source="error_handler",
            priority=EventPriority.HIGH,
        )

        await self.event_bus.publish(event)

    async def publish_setup_progress(self, setup_data: dict) -> None:
        """Publish setup/onboarding progress events.

        Args:
            setup_data: Setup progress data
        """
        event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "setup_progress",
                "step_id": setup_data.get("step_id"),
                "status": setup_data.get("status"),
                "progress_percentage": setup_data.get("progress_percentage", 0),
                "estimated_completion": setup_data.get("estimated_completion"),
                "automated": setup_data.get("automated", False),
                "duration": setup_data.get("duration", 0),
            },
            timestamp=time.time(),
            source="setup_assistant",
            priority=EventPriority.LOW,
        )

        await self.event_bus.publish(event)

    def get_troubleshooting_context(self) -> dict[str, Any]:
        """Get comprehensive context for troubleshooting systems.

        Returns:
            Dictionary with troubleshooting-relevant system context
        """
        try:
            # Get current dashboard data without async
            current_time = time.time()

            # Prepare metrics summary for troubleshooting
            metrics_summary = {}
            for component, metrics in self._metrics_storage.items():
                component_summary = {}

                for metric_type, values in metrics.items():
                    if values:
                        recent_values = [
                            value
                            for timestamp, value in values
                            if current_time - timestamp <= 300  # Last 5 minutes
                        ]

                        if recent_values:
                            component_summary[metric_type.value] = {
                                "current": recent_values[-1],
                                "average": sum(recent_values) / len(recent_values),
                                "max": max(recent_values),
                                "min": min(recent_values),
                                "trend": self._calculate_trend(recent_values),
                                "samples": len(recent_values),
                            }

                if component_summary:
                    metrics_summary[component] = component_summary

            # Calculate health indicators
            health_score = self._calculate_health_score()

            # Get active alerts
            active_alerts = [
                {
                    "severity": alert.severity.value,
                    "component": alert.component,
                    "metric_type": alert.metric_type.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                }
                for alert in self._active_alerts
            ]

            return {
                "health_score": health_score,
                "metrics": metrics_summary,
                "active_alerts": active_alerts,
                "active_alerts_count": len(active_alerts),
                "components_monitored": len(metrics_summary),
                "timestamp": current_time,
                "monitoring_active": self._is_running,
                "alerts_by_severity": {
                    "critical": sum(1 for a in active_alerts if a["severity"] == "critical"),
                    "error": sum(1 for a in active_alerts if a["severity"] == "error"),
                    "warning": sum(1 for a in active_alerts if a["severity"] == "warning"),
                    "info": sum(1 for a in active_alerts if a["severity"] == "info"),
                },
                "system_trends": self._get_system_trends(),
                "recent_performance": self._get_recent_performance_summary(),
            }

        except Exception as e:
            # Fallback context if monitoring data is unavailable
            return {
                "health_score": 100,
                "metrics": {},
                "active_alerts": [],
                "active_alerts_count": 0,
                "components_monitored": 0,
                "timestamp": time.time(),
                "monitoring_active": False,
                "error": f"Context unavailable: {str(e)}",
            }

    def _calculate_trend(self, values: list) -> str:
        """Calculate trend direction from a list of values.

        Args:
            values: List of metric values in chronological order

        Returns:
            Trend direction: 'improving', 'degrading', or 'stable'
        """
        if len(values) < 3:
            return "stable"

        # Simple trend calculation using first and last third of values
        first_third = values[: len(values) // 3]
        last_third = values[-len(values) // 3 :]

        first_avg = sum(first_third) / len(first_third)
        last_avg = sum(last_third) / len(last_third)

        change_percent = abs(last_avg - first_avg) / first_avg * 100 if first_avg > 0 else 0

        if change_percent < 5:  # Less than 5% change
            return "stable"
        elif last_avg < first_avg:
            return "improving"  # Assuming lower values are better (response time, errors, etc.)
        else:
            return "degrading"

    def _get_system_trends(self) -> dict[str, Any]:
        """Get system-wide performance trends.

        Returns:
            Dictionary with system trend information
        """
        trends = {"overall": "stable", "components": {}, "concerning_trends": []}

        degrading_count = 0
        improving_count = 0

        for component, metrics in self._metrics_storage.items():
            component_trends = {}
            for metric_type, values in metrics.items():
                if values and len(values) >= 3:
                    recent_values = [v[1] for v in list(values)[-10:]]  # Last 10 values
                    trend = self._calculate_trend(recent_values)
                    component_trends[metric_type.value] = trend

                    if trend == "degrading":
                        degrading_count += 1
                        trends["concerning_trends"].append({"component": component, "metric": metric_type.value, "trend": trend})
                    elif trend == "improving":
                        improving_count += 1

            trends["components"][component] = component_trends

        # Determine overall trend
        if degrading_count > improving_count * 1.5:
            trends["overall"] = "degrading"
        elif improving_count > degrading_count * 1.5:
            trends["overall"] = "improving"

        return trends

    def _get_recent_performance_summary(self) -> dict[str, Any]:
        """Get recent performance summary for troubleshooting context.

        Returns:
            Dictionary with recent performance data
        """
        current_time = time.time()
        summary = {"timeframe_minutes": 5, "avg_response_time": 0, "max_response_time": 0, "total_memory_mb": 0, "avg_cpu_percent": 0, "error_count": 0, "components_with_issues": []}

        response_times = []
        memory_values = []
        cpu_values = []

        for component, metrics in self._metrics_storage.items():
            # Get recent response times
            rt_values = metrics.get(MetricType.RESPONSE_TIME, deque())
            recent_rt = [value for timestamp, value in rt_values if current_time - timestamp <= 300]
            response_times.extend(recent_rt)

            # Get recent memory usage
            mem_values = metrics.get(MetricType.MEMORY_USAGE, deque())
            recent_mem = [value for timestamp, value in mem_values if current_time - timestamp <= 300]
            memory_values.extend(recent_mem)

            # Get recent CPU usage
            cpu_values_metric = metrics.get(MetricType.CPU_USAGE, deque())
            recent_cpu = [value for timestamp, value in cpu_values_metric if current_time - timestamp <= 300]
            cpu_values.extend(recent_cpu)

            # Check for component issues
            has_issues = False
            if recent_rt and max(recent_rt) > 200:  # High response time
                has_issues = True
            if recent_mem and max(recent_mem) > 20:  # High memory usage
                has_issues = True
            if recent_cpu and max(recent_cpu) > 90:  # High CPU usage
                has_issues = True

            if has_issues:
                summary["components_with_issues"].append(
                    {
                        "component": component,
                        "max_response_time": max(recent_rt) if recent_rt else 0,
                        "max_memory_mb": max(recent_mem) if recent_mem else 0,
                        "max_cpu_percent": max(recent_cpu) if recent_cpu else 0,
                    }
                )

        # Calculate summary statistics
        if response_times:
            summary["avg_response_time"] = sum(response_times) / len(response_times)
            summary["max_response_time"] = max(response_times)

        if memory_values:
            summary["total_memory_mb"] = sum(memory_values)

        if cpu_values:
            summary["avg_cpu_percent"] = sum(cpu_values) / len(cpu_values)

        # Count recent errors (from alerts)
        summary["error_count"] = sum(1 for alert in self._active_alerts if current_time - alert.timestamp <= 300 and alert.severity in {AlertSeverity.ERROR, AlertSeverity.CRITICAL})

        return summary

    async def register_user_experience_handlers(self) -> None:
        """Register event handlers for user experience components."""
        # Subscribe to troubleshooting events
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_troubleshooting_event, filter_func=lambda event: event.data.get("event_subtype") == "troubleshooting_activity")

        # Subscribe to error handling events
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_error_metrics_event, filter_func=lambda event: event.data.get("event_subtype") == "error_handling_metrics")

        # Subscribe to setup progress events
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_setup_progress_event, filter_func=lambda event: event.data.get("event_subtype") == "setup_progress")

    async def _handle_troubleshooting_event(self, event: Event) -> None:
        """Handle troubleshooting activity events.

        Args:
            event: Troubleshooting event
        """
        data = event.data

        # Store troubleshooting metrics
        if "troubleshooting_metrics" not in self._metrics_storage:
            self._metrics_storage["troubleshooting_metrics"] = {}

        guide_id = data.get("guide_id", "unknown")
        if guide_id not in self._metrics_storage["troubleshooting_metrics"]:
            self._metrics_storage["troubleshooting_metrics"][guide_id] = deque(maxlen=100)

        # Store troubleshooting execution data
        self._metrics_storage["troubleshooting_metrics"][guide_id].append(
            {
                "timestamp": event.timestamp,
                "execution_time": data.get("execution_time", 0),
                "steps_executed": data.get("steps_executed", 0),
                "steps_failed": data.get("steps_failed", 0),
                "resolution_status": data.get("resolution_status", "unknown"),
                "automated_steps": data.get("automated_steps", 0),
            }
        )

    async def _handle_error_metrics_event(self, event: Event) -> None:
        """Handle error handling metrics events.

        Args:
            event: Error metrics event
        """
        data = event.data

        # Store error handling metrics
        if "error_handling" not in self._metrics_storage:
            self._metrics_storage["error_handling"] = deque(maxlen=1000)

        self._metrics_storage["error_handling"].append(
            {
                "timestamp": event.timestamp,
                "error_code": data.get("error_code"),
                "category": data.get("category"),
                "severity": data.get("severity"),
                "component": data.get("component"),
                "auto_fix_available": data.get("auto_fix_available", False),
                "context_health_score": data.get("context", {}).get("health_score", 100),
            }
        )

    async def _handle_setup_progress_event(self, event: Event) -> None:
        """Handle setup progress events.

        Args:
            event: Setup progress event
        """
        data = event.data

        # Store setup progress metrics
        if "setup_progress" not in self._metrics_storage:
            self._metrics_storage["setup_progress"] = deque(maxlen=200)

        self._metrics_storage["setup_progress"].append(
            {
                "timestamp": event.timestamp,
                "step_id": data.get("step_id"),
                "status": data.get("status"),
                "progress_percentage": data.get("progress_percentage", 0),
                "automated": data.get("automated", False),
                "duration": data.get("duration", 0),
            }
        )

    def get_user_experience_metrics(self) -> dict[str, Any]:
        """Get user experience related metrics.

        Returns:
            Dictionary with UX metrics
        """
        ux_metrics = {
            "troubleshooting": {"total_executions": 0, "success_rate": 0, "avg_execution_time": 0, "most_common_issues": []},
            "error_handling": {"total_errors_handled": 0, "auto_fix_rate": 0, "error_categories": {}, "recent_error_trend": "stable"},
            "setup_progress": {"recent_setups": 0, "avg_setup_time": 0, "success_rate": 0, "most_challenging_steps": []},
        }

        # Troubleshooting metrics
        if "troubleshooting_metrics" in self._metrics_storage:
            all_executions = []
            for guide_executions in self._metrics_storage["troubleshooting_metrics"].values():
                all_executions.extend(guide_executions)

            if all_executions:
                ux_metrics["troubleshooting"]["total_executions"] = len(all_executions)
                successful = sum(1 for e in all_executions if e["resolution_status"] in {"resolved", "manual_intervention_required"})
                ux_metrics["troubleshooting"]["success_rate"] = successful / len(all_executions)
                ux_metrics["troubleshooting"]["avg_execution_time"] = sum(e["execution_time"] for e in all_executions) / len(all_executions)

        # Error handling metrics
        if "error_handling" in self._metrics_storage:
            error_events = list(self._metrics_storage["error_handling"])
            ux_metrics["error_handling"]["total_errors_handled"] = len(error_events)

            if error_events:
                auto_fixable = sum(1 for e in error_events if e["auto_fix_available"])
                ux_metrics["error_handling"]["auto_fix_rate"] = auto_fixable / len(error_events)

                # Category breakdown
                categories = {}
                for error in error_events:
                    cat = error["category"]
                    categories[cat] = categories.get(cat, 0) + 1
                ux_metrics["error_handling"]["error_categories"] = categories

        # Setup progress metrics
        if "setup_progress" in self._metrics_storage:
            setup_events = list(self._metrics_storage["setup_progress"])
            recent_setups = [e for e in setup_events if time.time() - e["timestamp"] < 86400]  # Last 24 hours

            ux_metrics["setup_progress"]["recent_setups"] = len(set(e["timestamp"] for e in recent_setups if e["step_id"] == "system_requirements"))  # Count unique setup sessions

            completed_steps = [e for e in recent_setups if e["status"] == "completed"]
            if completed_steps:
                ux_metrics["setup_progress"]["avg_setup_time"] = sum(e["duration"] for e in completed_steps) / len(completed_steps)

        return ux_metrics


# Singleton instance
_monitoring_dashboard: MonitoringDashboardIntegration | None = None


def get_monitoring_dashboard(
    config: MonitoringConfig | None = None,
    event_bus: AsyncEventBus | None = None,
) -> MonitoringDashboardIntegration:
    """Get or create the monitoring dashboard integration instance.

    Args:
        config: Optional monitoring configuration
        event_bus: Optional event bus instance

    Returns:
        Monitoring dashboard integration instance
    """
    global _monitoring_dashboard  # noqa: PLW0603

    if _monitoring_dashboard is None:
        _monitoring_dashboard = MonitoringDashboardIntegration(config, event_bus)

    return _monitoring_dashboard
