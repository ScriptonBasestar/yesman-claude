#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Security Metrics Integration Module.

This module extends the monitoring dashboard with security metrics,
providing real-time security status monitoring, vulnerability tracking,
and security-performance correlation analysis.
"""

import asyncio
import json
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from libs.core.async_event_bus import AsyncEventBus, Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_integration import (
    AlertSeverity,
    AlertThreshold,
    MetricType,
    MonitoringDashboardIntegration,
    PerformanceAlert,
)


class SecurityMetricType(Enum):
    """Types of security metrics."""
    
    SECURITY_SCAN_TIME = "security_scan_time"
    SECURITY_VIOLATIONS = "security_violations"
    SECURITY_FALSE_POSITIVES = "security_false_positives"
    VULNERABILITY_COUNT = "vulnerability_count"
    SECURITY_SCAN_COVERAGE = "security_scan_coverage"
    AUTHENTICATION_FAILURES = "authentication_failures"
    AUTHORIZATION_VIOLATIONS = "authorization_violations"
    ENCRYPTION_STRENGTH = "encryption_strength"
    COMPLIANCE_SCORE = "compliance_score"


class VulnerabilitySeverity(Enum):
    """Vulnerability severity levels."""
    
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityMetrics:
    """Security metrics data structure."""
    
    scan_duration_ms: float
    violations_found: int
    false_positive_rate: float
    vulnerability_severity_counts: Dict[str, int]
    scan_coverage_percent: float
    authentication_failures: int = 0
    authorization_violations: int = 0
    encryption_issues: int = 0
    compliance_violations: int = 0
    timestamp: float = field(default_factory=time.time)


@dataclass
class SecurityEvent:
    """Security event data structure."""
    
    event_type: str  # 'scan_completed', 'violation_detected', 'baseline_updated'
    timestamp: float
    component: str
    data: Dict[str, Any]
    severity: VulnerabilitySeverity = VulnerabilitySeverity.LOW


@dataclass
class SecurityPerformanceCorrelation:
    """Security-performance correlation data."""
    
    component: str
    security_impact_on_performance: float  # Percentage impact
    performance_during_scan: Dict[str, float]  # Metrics during security scan
    scan_overhead_ms: float
    correlation_coefficient: float
    timestamp: float


class SecurityMetricsIntegration:
    """Security metrics integration for monitoring dashboard."""
    
    def __init__(
        self,
        monitoring_dashboard: Optional[MonitoringDashboardIntegration] = None,
        event_bus: Optional[AsyncEventBus] = None,
    ) -> None:
        """Initialize security metrics integration.
        
        Args:
            monitoring_dashboard: Monitoring dashboard instance
            event_bus: Event bus for system communication
        """
        self.monitoring_dashboard = monitoring_dashboard
        self.event_bus = event_bus or get_event_bus()
        
        # Security metrics storage
        self._security_metrics: Dict[str, deque] = {}
        self._security_events: deque = deque(maxlen=1000)
        self._vulnerability_inventory: Dict[str, List[Dict[str, Any]]] = {}
        
        # Correlation analysis
        self._correlation_data: deque = deque(maxlen=100)
        self._performance_impact_cache: Dict[str, float] = {}
        
        # Security baselines
        self._security_baselines: Dict[str, Dict[str, float]] = {}
        self._load_security_baselines()
        
        # Security thresholds
        self._security_thresholds: List[AlertThreshold] = []
        self._setup_security_thresholds()
        
        # Integration state
        self._is_running = False
        self._correlation_task: Optional[asyncio.Task] = None
        
        # Setup event subscriptions
        self._setup_event_subscriptions()
    
    def _setup_security_thresholds(self) -> None:
        """Setup default security alert thresholds."""
        # Scan time thresholds
        self._security_thresholds.append(
            AlertThreshold(
                metric_type=MetricType.RESPONSE_TIME,  # Reuse for scan time
                component="security_scan",
                warning_threshold=100.0,  # 100ms
                error_threshold=500.0,    # 500ms
                critical_threshold=1000.0,  # 1s
                aggregation_window=60,
                min_occurrences=2,
            )
        )
        
        # Violation count thresholds
        self._security_thresholds.append(
            AlertThreshold(
                metric_type=MetricType.ERROR_RATE,  # Reuse for violations
                component="security_violations",
                warning_threshold=5,
                error_threshold=10,
                critical_threshold=20,
                aggregation_window=300,  # 5 minutes
                min_occurrences=1,
            )
        )
        
        # False positive rate thresholds
        self._security_thresholds.append(
            AlertThreshold(
                metric_type=MetricType.ERROR_RATE,
                component="false_positives",
                warning_threshold=10.0,  # 10%
                error_threshold=25.0,    # 25%
                critical_threshold=50.0,  # 50%
                aggregation_window=3600,  # 1 hour
                min_occurrences=5,
            )
        )
    
    def _load_security_baselines(self) -> None:
        """Load security baselines from file."""
        baseline_path = Path("data/security_baselines.json")
        if baseline_path.exists():
            try:
                with open(baseline_path) as f:
                    self._security_baselines = json.load(f)
            except Exception:
                self._security_baselines = {}
    
    def _setup_event_subscriptions(self) -> None:
        """Setup event bus subscriptions for security events."""
        # Subscribe to security-specific events
        self.event_bus.subscribe(EventType.CUSTOM, self._handle_security_event)
        
        # Subscribe to performance metrics for correlation
        self.event_bus.subscribe(EventType.PERFORMANCE_METRICS, self._handle_performance_for_correlation)
    
    async def start(self) -> None:
        """Start the security metrics integration."""
        if self._is_running:
            return
        
        self._is_running = True
        
        # Start correlation analysis task
        self._correlation_task = asyncio.create_task(self._correlation_analysis_loop())
        
        # Register security thresholds with monitoring dashboard
        if self.monitoring_dashboard:
            for threshold in self._security_thresholds:
                self.monitoring_dashboard.add_custom_threshold(threshold)
        
        # Publish startup event
        await self.event_bus.publish(
            Event(
                type=EventType.CUSTOM,
                data={
                    "event_subtype": "security_monitoring_started",
                    "thresholds": len(self._security_thresholds),
                },
                timestamp=time.time(),
                source="security_metrics",
                priority=EventPriority.HIGH,
            )
        )
    
    async def stop(self) -> None:
        """Stop the security metrics integration."""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Cancel correlation task
        if self._correlation_task and not self._correlation_task.done():
            self._correlation_task.cancel()
            try:
                await self._correlation_task
            except asyncio.CancelledError:
                pass
    
    async def _handle_security_event(self, event: Event) -> None:
        """Handle incoming security events.
        
        Args:
            event: Security event
        """
        data = event.data
        if not isinstance(data, dict) or data.get("event_subtype") != "security":
            return
        
        security_event = SecurityEvent(
            event_type=data.get("security_event_type", "unknown"),
            timestamp=event.timestamp,
            component=data.get("component", "unknown"),
            data=data.get("metrics", {}),
            severity=VulnerabilitySeverity(data.get("severity", "low")),
        )
        
        # Store security event
        self._security_events.append(security_event)
        
        # Process based on event type
        if security_event.event_type == "scan_completed":
            await self._process_scan_completed(security_event)
        elif security_event.event_type == "violation_detected":
            await self._process_violation_detected(security_event)
        elif security_event.event_type == "baseline_updated":
            await self._process_baseline_updated(security_event)
    
    async def _process_scan_completed(self, event: SecurityEvent) -> None:
        """Process security scan completion event.
        
        Args:
            event: Security scan completion event
        """
        component = event.component
        metrics_data = event.data
        
        # Extract security metrics
        security_metrics = SecurityMetrics(
            scan_duration_ms=metrics_data.get("scan_duration_ms", 0),
            violations_found=metrics_data.get("violations_found", 0),
            false_positive_rate=metrics_data.get("false_positive_rate", 0),
            vulnerability_severity_counts=metrics_data.get("vulnerability_counts", {}),
            scan_coverage_percent=metrics_data.get("scan_coverage", 100),
            authentication_failures=metrics_data.get("auth_failures", 0),
            authorization_violations=metrics_data.get("authz_violations", 0),
            encryption_issues=metrics_data.get("encryption_issues", 0),
            compliance_violations=metrics_data.get("compliance_violations", 0),
            timestamp=event.timestamp,
        )
        
        # Store metrics
        if component not in self._security_metrics:
            self._security_metrics[component] = deque(maxlen=1000)
        self._security_metrics[component].append(security_metrics)
        
        # Check for security performance impact
        await self._analyze_security_performance_impact(component, security_metrics)
        
        # Update monitoring dashboard if integrated
        if self.monitoring_dashboard:
            await self._update_monitoring_dashboard(component, security_metrics)
        
        # Check security thresholds
        await self._check_security_thresholds(component, security_metrics)
    
    async def _process_violation_detected(self, event: SecurityEvent) -> None:
        """Process security violation detection event.
        
        Args:
            event: Security violation event
        """
        component = event.component
        violation_data = event.data
        
        # Store violation in inventory
        if component not in self._vulnerability_inventory:
            self._vulnerability_inventory[component] = []
        
        self._vulnerability_inventory[component].append({
            "timestamp": event.timestamp,
            "severity": event.severity.value,
            "type": violation_data.get("violation_type", "unknown"),
            "description": violation_data.get("description", ""),
            "remediation": violation_data.get("remediation", ""),
            "false_positive": violation_data.get("false_positive", False),
        })
        
        # Create alert for critical violations
        if event.severity in [VulnerabilitySeverity.HIGH, VulnerabilitySeverity.CRITICAL]:
            await self._create_security_alert(component, event)
    
    async def _process_baseline_updated(self, event: SecurityEvent) -> None:
        """Process security baseline update event.
        
        Args:
            event: Baseline update event
        """
        component = event.component
        baseline_data = event.data
        
        # Update security baselines
        if component not in self._security_baselines:
            self._security_baselines[component] = {}
        
        self._security_baselines[component].update(baseline_data)
        
        # Save baselines to file
        baseline_path = Path("data/security_baselines.json")
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(baseline_path, "w") as f:
            json.dump(self._security_baselines, f, indent=2)
    
    async def _handle_performance_for_correlation(self, event: Event) -> None:
        """Handle performance metrics for correlation analysis.
        
        Args:
            event: Performance metrics event
        """
        if not self._is_running:
            return
        
        data = event.data
        if not isinstance(data, dict) or "metrics" not in data:
            return
        
        # Store for correlation analysis
        self._correlation_data.append({
            "timestamp": event.timestamp,
            "component": data.get("component", "unknown"),
            "metrics": data["metrics"],
        })
    
    async def _analyze_security_performance_impact(
        self,
        component: str,
        security_metrics: SecurityMetrics,
    ) -> None:
        """Analyze the performance impact of security operations.
        
        Args:
            component: Component name
            security_metrics: Security metrics data
        """
        # Look for performance metrics during security scan window
        scan_start = security_metrics.timestamp - (security_metrics.scan_duration_ms / 1000)
        scan_end = security_metrics.timestamp
        
        performance_during_scan = []
        baseline_performance = []
        
        for data in self._correlation_data:
            if data["component"] == component:
                if scan_start <= data["timestamp"] <= scan_end:
                    performance_during_scan.append(data["metrics"])
                elif data["timestamp"] < scan_start:
                    baseline_performance.append(data["metrics"])
        
        if not performance_during_scan or not baseline_performance:
            return
        
        # Calculate performance impact
        impact = self._calculate_performance_impact(
            baseline_performance,
            performance_during_scan,
        )
        
        # Store correlation data
        correlation = SecurityPerformanceCorrelation(
            component=component,
            security_impact_on_performance=impact["impact_percent"],
            performance_during_scan=impact["during_scan_metrics"],
            scan_overhead_ms=security_metrics.scan_duration_ms,
            correlation_coefficient=impact["correlation"],
            timestamp=security_metrics.timestamp,
        )
        
        # Cache performance impact
        self._performance_impact_cache[component] = impact["impact_percent"]
        
        # Publish correlation insight
        await self._publish_correlation_insight(correlation)
    
    def _calculate_performance_impact(
        self,
        baseline: List[Dict],
        during_scan: List[Dict],
    ) -> Dict[str, Any]:
        """Calculate performance impact of security operations.
        
        Args:
            baseline: Baseline performance metrics
            during_scan: Performance metrics during security scan
            
        Returns:
            Performance impact analysis
        """
        # Calculate average response times
        baseline_rt = self._extract_metric_average(baseline, "component_response_times")
        scan_rt = self._extract_metric_average(during_scan, "component_response_times")
        
        # Calculate impact percentage
        impact_percent = 0
        if baseline_rt > 0:
            impact_percent = ((scan_rt - baseline_rt) / baseline_rt) * 100
        
        # Simple correlation coefficient
        correlation = min(1.0, abs(impact_percent) / 100)
        
        return {
            "impact_percent": impact_percent,
            "during_scan_metrics": {
                "response_time": scan_rt,
                "baseline_response_time": baseline_rt,
            },
            "correlation": correlation,
        }
    
    def _extract_metric_average(
        self,
        metrics_list: List[Dict],
        metric_key: str,
    ) -> float:
        """Extract average value from metrics list.
        
        Args:
            metrics_list: List of metrics dictionaries
            metric_key: Key to extract
            
        Returns:
            Average value
        """
        values = []
        for metrics in metrics_list:
            if metric_key in metrics:
                component_metrics = metrics[metric_key]
                if isinstance(component_metrics, dict):
                    for comp_data in component_metrics.values():
                        if isinstance(comp_data, dict) and "average_ms" in comp_data:
                            values.append(comp_data["average_ms"])
        
        return sum(values) / len(values) if values else 0
    
    async def _update_monitoring_dashboard(
        self,
        component: str,
        security_metrics: SecurityMetrics,
    ) -> None:
        """Update monitoring dashboard with security metrics.
        
        Args:
            component: Component name
            security_metrics: Security metrics data
        """
        # Convert security metrics to monitoring dashboard format
        dashboard_event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "security_metrics_update",
                "component": component,
                "metrics": {
                    "security_scan_time": security_metrics.scan_duration_ms,
                    "security_violations": security_metrics.violations_found,
                    "false_positive_rate": security_metrics.false_positive_rate,
                    "scan_coverage": security_metrics.scan_coverage_percent,
                    "vulnerability_counts": security_metrics.vulnerability_severity_counts,
                },
                "timestamp": security_metrics.timestamp,
            },
            timestamp=security_metrics.timestamp,
            source="security_metrics",
            priority=EventPriority.NORMAL,
        )
        
        await self.event_bus.publish(dashboard_event)
    
    async def _check_security_thresholds(
        self,
        component: str,
        security_metrics: SecurityMetrics,
    ) -> None:
        """Check security metrics against thresholds.
        
        Args:
            component: Component name
            security_metrics: Security metrics data
        """
        # Check scan time threshold
        if security_metrics.scan_duration_ms > 1000:  # 1 second
            await self._create_performance_alert(
                component,
                "security_scan_time",
                security_metrics.scan_duration_ms,
                1000,
                AlertSeverity.WARNING,
            )
        
        # Check violation count threshold
        if security_metrics.violations_found > 20:
            await self._create_performance_alert(
                component,
                "security_violations",
                security_metrics.violations_found,
                20,
                AlertSeverity.CRITICAL,
            )
        
        # Check false positive rate
        if security_metrics.false_positive_rate > 25:
            await self._create_performance_alert(
                component,
                "false_positive_rate",
                security_metrics.false_positive_rate,
                25,
                AlertSeverity.ERROR,
            )
    
    async def _create_security_alert(
        self,
        component: str,
        event: SecurityEvent,
    ) -> None:
        """Create security alert.
        
        Args:
            component: Component name
            event: Security event
        """
        severity_map = {
            VulnerabilitySeverity.LOW: AlertSeverity.INFO,
            VulnerabilitySeverity.MEDIUM: AlertSeverity.WARNING,
            VulnerabilitySeverity.HIGH: AlertSeverity.ERROR,
            VulnerabilitySeverity.CRITICAL: AlertSeverity.CRITICAL,
        }
        
        alert_event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "security_alert",
                "severity": severity_map[event.severity].value,
                "component": component,
                "message": f"Security violation detected in {component}",
                "details": event.data,
            },
            timestamp=event.timestamp,
            source="security_metrics",
            priority=EventPriority.HIGH,
        )
        
        await self.event_bus.publish(alert_event)
    
    async def _create_performance_alert(
        self,
        component: str,
        metric: str,
        value: float,
        threshold: float,
        severity: AlertSeverity,
    ) -> None:
        """Create performance alert for security metrics.
        
        Args:
            component: Component name
            metric: Metric name
            value: Current value
            threshold: Threshold value
            severity: Alert severity
        """
        alert_event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "performance_alert",
                "severity": severity.value,
                "component": component,
                "metric_type": metric,
                "current_value": value,
                "threshold": threshold,
                "message": f"Security {metric} exceeded threshold in {component}",
                "context": {
                    "security_related": True,
                },
            },
            timestamp=time.time(),
            source="security_metrics",
            priority=EventPriority.HIGH if severity in [AlertSeverity.ERROR, AlertSeverity.CRITICAL] else EventPriority.NORMAL,
        )
        
        await self.event_bus.publish(alert_event)
    
    async def _publish_correlation_insight(
        self,
        correlation: SecurityPerformanceCorrelation,
    ) -> None:
        """Publish security-performance correlation insight.
        
        Args:
            correlation: Correlation data
        """
        insight_event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "correlation_insight",
                "component": correlation.component,
                "security_impact_percent": correlation.security_impact_on_performance,
                "scan_overhead_ms": correlation.scan_overhead_ms,
                "correlation_coefficient": correlation.correlation_coefficient,
                "performance_during_scan": correlation.performance_during_scan,
                "message": f"Security scan impacts {correlation.component} performance by {correlation.security_impact_on_performance:.1f}%",
            },
            timestamp=correlation.timestamp,
            source="security_metrics",
            priority=EventPriority.LOW,
        )
        
        await self.event_bus.publish(insight_event)
    
    async def _correlation_analysis_loop(self) -> None:
        """Main correlation analysis loop."""
        while self._is_running:
            try:
                # Analyze correlations every minute
                await asyncio.sleep(60)
                
                # Perform correlation analysis
                correlations = self._analyze_all_correlations()
                
                # Publish correlation summary
                if correlations:
                    await self._publish_correlation_summary(correlations)
                
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)
    
    def _analyze_all_correlations(self) -> List[Dict[str, Any]]:
        """Analyze all security-performance correlations.
        
        Returns:
            List of correlation analyses
        """
        correlations = []
        
        for component, impact in self._performance_impact_cache.items():
            if abs(impact) > 10:  # Significant impact threshold
                correlations.append({
                    "component": component,
                    "impact": impact,
                    "recommendation": self._generate_optimization_recommendation(component, impact),
                })
        
        return correlations
    
    def _generate_optimization_recommendation(
        self,
        component: str,
        impact: float,
    ) -> str:
        """Generate optimization recommendation based on impact.
        
        Args:
            component: Component name
            impact: Performance impact percentage
            
        Returns:
            Optimization recommendation
        """
        if impact > 50:
            return f"Critical: Security scans severely impact {component}. Consider scheduling scans during low-traffic periods."
        elif impact > 20:
            return f"Warning: Security scans moderately impact {component}. Consider optimizing scan patterns or caching results."
        elif impact > 10:
            return f"Advisory: Security scans have minor impact on {component}. Monitor for trends."
        else:
            return f"Optimal: Security scans have minimal impact on {component}."
    
    async def _publish_correlation_summary(
        self,
        correlations: List[Dict[str, Any]],
    ) -> None:
        """Publish correlation analysis summary.
        
        Args:
            correlations: List of correlation analyses
        """
        summary_event = Event(
            type=EventType.CUSTOM,
            data={
                "event_subtype": "correlation_summary",
                "correlations": correlations,
                "high_impact_components": [
                    c["component"] for c in correlations if c["impact"] > 20
                ],
                "recommendations": [c["recommendation"] for c in correlations],
                "timestamp": time.time(),
            },
            timestamp=time.time(),
            source="security_metrics",
            priority=EventPriority.LOW,
        )
        
        await self.event_bus.publish(summary_event)
    
    def get_security_metrics_summary(self) -> Dict[str, Any]:
        """Get summary of security metrics.
        
        Returns:
            Security metrics summary
        """
        summary = {
            "components": {},
            "vulnerabilities": {},
            "correlations": {},
            "alerts": [],
        }
        
        # Summarize metrics by component
        for component, metrics_list in self._security_metrics.items():
            if metrics_list:
                recent_metrics = list(metrics_list)[-10:]  # Last 10 scans
                
                summary["components"][component] = {
                    "average_scan_time": sum(m.scan_duration_ms for m in recent_metrics) / len(recent_metrics),
                    "total_violations": sum(m.violations_found for m in recent_metrics),
                    "average_false_positive_rate": sum(m.false_positive_rate for m in recent_metrics) / len(recent_metrics),
                    "average_coverage": sum(m.scan_coverage_percent for m in recent_metrics) / len(recent_metrics),
                }
        
        # Summarize vulnerabilities
        for component, vulns in self._vulnerability_inventory.items():
            severity_counts = {}
            for vuln in vulns:
                severity = vuln["severity"]
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            summary["vulnerabilities"][component] = severity_counts
        
        # Include correlation data
        summary["correlations"] = self._performance_impact_cache.copy()
        
        return summary
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard visualization.
        
        Returns:
            Dashboard visualization data
        """
        current_time = time.time()
        
        # Prepare time series data for charts
        time_series = {
            "scan_times": [],
            "violation_counts": [],
            "false_positive_rates": [],
        }
        
        for component, metrics_list in self._security_metrics.items():
            for metric in metrics_list:
                if current_time - metric.timestamp <= 3600:  # Last hour
                    time_series["scan_times"].append({
                        "timestamp": metric.timestamp,
                        "component": component,
                        "value": metric.scan_duration_ms,
                    })
                    time_series["violation_counts"].append({
                        "timestamp": metric.timestamp,
                        "component": component,
                        "value": metric.violations_found,
                    })
                    time_series["false_positive_rates"].append({
                        "timestamp": metric.timestamp,
                        "component": component,
                        "value": metric.false_positive_rate,
                    })
        
        # Get current vulnerability status
        vulnerability_status = {}
        for component, vulns in self._vulnerability_inventory.items():
            active_vulns = [v for v in vulns if not v.get("false_positive", False)]
            vulnerability_status[component] = {
                "total": len(active_vulns),
                "critical": sum(1 for v in active_vulns if v["severity"] == "critical"),
                "high": sum(1 for v in active_vulns if v["severity"] == "high"),
                "medium": sum(1 for v in active_vulns if v["severity"] == "medium"),
                "low": sum(1 for v in active_vulns if v["severity"] == "low"),
            }
        
        return {
            "time_series": time_series,
            "vulnerability_status": vulnerability_status,
            "performance_impact": self._performance_impact_cache,
            "summary": self.get_security_metrics_summary(),
        }


# Singleton instance
_security_metrics: Optional[SecurityMetricsIntegration] = None


def get_security_metrics_integration(
    monitoring_dashboard: Optional[MonitoringDashboardIntegration] = None,
    event_bus: Optional[AsyncEventBus] = None,
) -> SecurityMetricsIntegration:
    """Get or create the security metrics integration instance.
    
    Args:
        monitoring_dashboard: Optional monitoring dashboard instance
        event_bus: Optional event bus instance
        
    Returns:
        Security metrics integration instance
    """
    global _security_metrics
    
    if _security_metrics is None:
        _security_metrics = SecurityMetricsIntegration(monitoring_dashboard, event_bus)
    
    return _security_metrics