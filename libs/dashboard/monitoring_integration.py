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
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Optional

from libs.core.async_event_bus import AsyncEventBus, Event, EventPriority, EventType, get_event_bus


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
        config: Optional[MonitoringConfig] = None,
        event_bus: Optional[AsyncEventBus] = None,
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
        self._dashboard_task: Optional[asyncio.Task] = None
        self._alert_task: Optional[asyncio.Task] = None
        
        # Alert callbacks
        self._alert_callbacks: list[Callable[[PerformanceAlert], None]] = []
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _setup_default_thresholds(self) -> None:
        """Setup default alert thresholds."""
        # Component response time thresholds
        components = [
            'content_capture', 'claude_status_check', 'prompt_detection',
            'content_processing', 'response_sending', 'automation_analysis'
        ]
        
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
                with open(baseline_path) as f:
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
                    }
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
                self._metrics_storage[component] = {
                    metric_type: deque(maxlen=self.config.metric_retention)
                    for metric_type in MetricType
                }
            
            # Store response time metrics
            if "average_ms" in metrics:
                self._metrics_storage[component][MetricType.RESPONSE_TIME].append(
                    (timestamp, metrics["average_ms"])
                )
            
            # Store memory metrics
            if "avg_memory_delta_mb" in metrics:
                self._metrics_storage[component][MetricType.MEMORY_USAGE].append(
                    (timestamp, abs(metrics["avg_memory_delta_mb"]))
                )
            
            # Store CPU metrics
            if "avg_cpu_percent" in metrics:
                self._metrics_storage[component][MetricType.CPU_USAGE].append(
                    (timestamp, metrics["avg_cpu_percent"])
                )
            
            # Store error rate
            if "error_rate" in metrics:
                self._metrics_storage[component][MetricType.ERROR_RATE].append(
                    (timestamp, metrics["error_rate"] * 100)
                )
            
            # Store network I/O
            if "avg_throughput_mbps" in metrics:
                self._metrics_storage[component][MetricType.NETWORK_IO].append(
                    (timestamp, metrics["avg_throughput_mbps"])
                )
    
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
                            regressions.append({
                                "component": comp_name,
                                "metric": "response_time",
                                "baseline": baseline_value,
                                "current": current_value,
                                "regression_percent": regression_percent,
                            })
        
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
            recent_metrics = [
                value for timestamp, value in metrics
                if current_time - timestamp <= threshold.aggregation_window
            ]
            
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
            except Exception:
                pass
        
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
                priority=EventPriority.HIGH if alert.severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL] else EventPriority.NORMAL,
            )
        )
    
    def _cleanup_old_alerts(self) -> None:
        """Remove old alerts from active list."""
        current_time = time.time()
        self._active_alerts = [
            alert for alert in self._active_alerts
            if current_time - alert.timestamp < self.config.alert_retention
        ]
    
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
                        value for timestamp, value in values
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
        
        return {
            metric_type.value: list(values)
            for metric_type, values in self._metrics_storage[component].items()
        }
    
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
        
        with open(baseline_path, "w") as f:
            json.dump(self._performance_baselines, f, indent=2)


# Singleton instance
_monitoring_dashboard: Optional[MonitoringDashboardIntegration] = None


def get_monitoring_dashboard(
    config: Optional[MonitoringConfig] = None,
    event_bus: Optional[AsyncEventBus] = None,
) -> MonitoringDashboardIntegration:
    """Get or create the monitoring dashboard integration instance.
    
    Args:
        config: Optional monitoring configuration
        event_bus: Optional event bus instance
        
    Returns:
        Monitoring dashboard integration instance
    """
    global _monitoring_dashboard
    
    if _monitoring_dashboard is None:
        _monitoring_dashboard = MonitoringDashboardIntegration(config, event_bus)
    
    return _monitoring_dashboard