#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Performance Quality Gates Integration.

This module integrates performance monitoring metrics into the quality gates system,
enabling automated performance regression detection and enforcement of performance thresholds.
"""

import asyncio
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from libs.core.async_event_bus import get_event_bus
from libs.dashboard.monitoring_integration import (
    AlertSeverity,
    MetricType,
    MonitoringConfig,
    get_monitoring_dashboard,
)


@dataclass
class PerformanceQualityGate:
    """Performance-related quality gate configuration."""
    
    name: str
    description: str
    metric_type: MetricType
    component: str
    threshold: float
    level: str  # 'blocking', 'warning', 'advisory'
    aggregation: str = 'average'  # 'average', 'p95', 'p99', 'max'


class QualityGatesPerformanceChecker:
    """Performance checker for quality gates system."""
    
    def __init__(self, baseline_path: Optional[Path] = None):
        """Initialize performance quality gates checker.
        
        Args:
            baseline_path: Path to performance baseline file
        """
        self.baseline_path = baseline_path or Path("data/performance_baselines.json")
        self.monitoring_dashboard = get_monitoring_dashboard()
        self.event_bus = get_event_bus()
        
        # Load performance gates configuration
        self.performance_gates = self._load_performance_gates()
        
        # Load performance baselines
        self.baselines = self._load_baselines()
    
    def _load_performance_gates(self) -> list[PerformanceQualityGate]:
        """Load performance quality gates configuration.
        
        Returns:
            List of performance quality gates
        """
        gates = []
        
        # Response time gates
        gates.append(
            PerformanceQualityGate(
                name="response_time_average",
                description="Average response time should be under 100ms",
                metric_type=MetricType.RESPONSE_TIME,
                component="all",
                threshold=100.0,
                level="warning",
                aggregation="average",
            )
        )
        
        gates.append(
            PerformanceQualityGate(
                name="response_time_p95",
                description="95th percentile response time should be under 200ms",
                metric_type=MetricType.RESPONSE_TIME,
                component="all",
                threshold=200.0,
                level="warning",
                aggregation="p95",
            )
        )
        
        gates.append(
            PerformanceQualityGate(
                name="response_time_max",
                description="Maximum response time should be under 500ms",
                metric_type=MetricType.RESPONSE_TIME,
                component="all",
                threshold=500.0,
                level="blocking",
                aggregation="max",
            )
        )
        
        # Memory usage gates
        gates.append(
            PerformanceQualityGate(
                name="memory_usage_delta",
                description="Memory usage delta should be under 5MB per operation",
                metric_type=MetricType.MEMORY_USAGE,
                component="all",
                threshold=5.0,
                level="warning",
                aggregation="average",
            )
        )
        
        gates.append(
            PerformanceQualityGate(
                name="memory_leak_detection",
                description="No memory leaks detected (growing memory usage)",
                metric_type=MetricType.MEMORY_USAGE,
                component="all",
                threshold=50.0,  # Total growth over session
                level="blocking",
                aggregation="max",
            )
        )
        
        # CPU usage gates
        gates.append(
            PerformanceQualityGate(
                name="cpu_usage_average",
                description="Average CPU usage should be under 50%",
                metric_type=MetricType.CPU_USAGE,
                component="all",
                threshold=50.0,
                level="advisory",
                aggregation="average",
            )
        )
        
        gates.append(
            PerformanceQualityGate(
                name="cpu_usage_peak",
                description="Peak CPU usage should be under 90%",
                metric_type=MetricType.CPU_USAGE,
                component="all",
                threshold=90.0,
                level="warning",
                aggregation="max",
            )
        )
        
        # Error rate gates
        gates.append(
            PerformanceQualityGate(
                name="error_rate",
                description="Error rate should be under 5%",
                metric_type=MetricType.ERROR_RATE,
                component="all",
                threshold=5.0,
                level="blocking",
                aggregation="average",
            )
        )
        
        # Network I/O gates
        gates.append(
            PerformanceQualityGate(
                name="network_throughput",
                description="Network throughput should be reasonable",
                metric_type=MetricType.NETWORK_IO,
                component="all",
                threshold=10.0,  # MB/s
                level="advisory",
                aggregation="average",
            )
        )
        
        return gates
    
    def _load_baselines(self) -> dict[str, dict[str, float]]:
        """Load performance baselines.
        
        Returns:
            Performance baselines dictionary
        """
        if self.baseline_path.exists():
            try:
                with open(self.baseline_path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    async def check_performance_gates(self) -> dict[str, Any]:
        """Check all performance quality gates.
        
        Returns:
            Dictionary with gate results
        """
        results = {
            "passed": [],
            "warnings": [],
            "failures": [],
            "blocking_failures": [],
            "metrics": {},
            "regression_detected": False,
        }
        
        # Get current metrics from monitoring dashboard
        all_components = [
            'content_capture', 'claude_status_check', 'prompt_detection',
            'content_processing', 'response_sending', 'automation_analysis'
        ]
        
        component_metrics = {}
        for component in all_components:
            metrics = self.monitoring_dashboard.get_metrics_for_component(component)
            if metrics:
                component_metrics[component] = self._aggregate_metrics(metrics)
        
        # Check each performance gate
        for gate in self.performance_gates:
            gate_result = await self._check_single_gate(gate, component_metrics)
            
            if gate_result["passed"]:
                results["passed"].append(gate_result)
            elif gate.level == "blocking" and not gate_result["passed"]:
                results["blocking_failures"].append(gate_result)
                results["failures"].append(gate_result)
            elif gate.level == "warning" and not gate_result["passed"]:
                results["warnings"].append(gate_result)
            else:
                results["failures"].append(gate_result)
        
        # Check for performance regression
        regression_results = await self._check_regression(component_metrics)
        if regression_results["regression_detected"]:
            results["regression_detected"] = True
            results["warnings"].append({
                "name": "performance_regression",
                "description": "Performance regression detected",
                "details": regression_results["regressions"],
            })
        
        # Store aggregated metrics
        results["metrics"] = component_metrics
        
        return results
    
    def _aggregate_metrics(self, metrics: dict[str, list[tuple[float, float]]]) -> dict[str, dict[str, float]]:
        """Aggregate raw metrics into summary statistics.
        
        Args:
            metrics: Raw metrics data
            
        Returns:
            Aggregated metrics
        """
        aggregated = {}
        
        for metric_type_str, values in metrics.items():
            if not values:
                continue
            
            # Extract just the values (ignore timestamps)
            metric_values = [v for _, v in values]
            
            if metric_values:
                aggregated[metric_type_str] = {
                    "average": sum(metric_values) / len(metric_values),
                    "min": min(metric_values),
                    "max": max(metric_values),
                    "p95": self._calculate_percentile(metric_values, 95),
                    "p99": self._calculate_percentile(metric_values, 99),
                    "count": len(metric_values),
                }
        
        return aggregated
    
    def _calculate_percentile(self, values: list[float], percentile: int) -> float:
        """Calculate percentile value.
        
        Args:
            values: List of values
            percentile: Percentile to calculate (0-100)
            
        Returns:
            Percentile value
        """
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        index = int(len(sorted_values) * (percentile / 100))
        index = min(index, len(sorted_values) - 1)
        
        return sorted_values[index]
    
    async def _check_single_gate(
        self,
        gate: PerformanceQualityGate,
        component_metrics: dict[str, dict[str, dict[str, float]]],
    ) -> dict[str, Any]:
        """Check a single performance gate.
        
        Args:
            gate: Performance gate to check
            component_metrics: Component metrics data
            
        Returns:
            Gate check result
        """
        result = {
            "name": gate.name,
            "description": gate.description,
            "level": gate.level,
            "passed": True,
            "value": 0.0,
            "threshold": gate.threshold,
            "components_failed": [],
        }
        
        # Check metrics for each component or all
        components_to_check = (
            list(component_metrics.keys()) if gate.component == "all"
            else [gate.component] if gate.component in component_metrics
            else []
        )
        
        for component in components_to_check:
            metrics = component_metrics.get(component, {})
            metric_data = metrics.get(gate.metric_type.value, {})
            
            if not metric_data:
                continue
            
            # Get the aggregated value based on gate configuration
            value = metric_data.get(gate.aggregation, 0.0)
            
            # Special handling for memory leak detection
            if gate.name == "memory_leak_detection":
                # Check for consistent memory growth
                if gate.metric_type.value in metrics:
                    values = [v for _, v in self.monitoring_dashboard.get_metrics_for_component(component).get(gate.metric_type.value, [])]
                    if len(values) > 10:
                        # Simple linear regression to detect growth trend
                        growth = self._detect_memory_growth(values)
                        value = growth
            
            # Check against threshold
            if value > gate.threshold:
                result["passed"] = False
                result["components_failed"].append({
                    "component": component,
                    "value": value,
                    "threshold": gate.threshold,
                })
                result["value"] = max(result["value"], value)
        
        return result
    
    def _detect_memory_growth(self, values: list[float]) -> float:
        """Detect memory growth trend.
        
        Args:
            values: Memory usage values over time
            
        Returns:
            Growth rate (MB per measurement)
        """
        if len(values) < 2:
            return 0.0
        
        # Simple linear regression
        n = len(values)
        x = list(range(n))
        
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        
        # Return total growth over the measurement period
        return abs(slope * n)
    
    async def _check_regression(self, current_metrics: dict[str, dict[str, dict[str, float]]]) -> dict[str, Any]:
        """Check for performance regression against baselines.
        
        Args:
            current_metrics: Current performance metrics
            
        Returns:
            Regression check results
        """
        results = {
            "regression_detected": False,
            "regressions": [],
        }
        
        regression_threshold = 20.0  # 20% regression threshold
        
        for component, metrics in current_metrics.items():
            if component not in self.baselines:
                continue
            
            baseline = self.baselines[component]
            
            # Check response time regression
            if "response_time" in metrics:
                current_avg = metrics["response_time"].get("average", 0)
                baseline_avg = baseline.get("response_time_average", 0)
                
                if baseline_avg > 0 and current_avg > 0:
                    regression_percent = ((current_avg - baseline_avg) / baseline_avg) * 100
                    
                    if regression_percent > regression_threshold:
                        results["regression_detected"] = True
                        results["regressions"].append({
                            "component": component,
                            "metric": "response_time",
                            "baseline": baseline_avg,
                            "current": current_avg,
                            "regression_percent": regression_percent,
                        })
            
            # Check memory regression
            if "memory_usage" in metrics:
                current_avg = metrics["memory_usage"].get("average", 0)
                baseline_avg = baseline.get("memory_usage_average", 0)
                
                if baseline_avg > 0 and current_avg > baseline_avg * 1.5:  # 50% increase
                    results["regression_detected"] = True
                    results["regressions"].append({
                        "component": component,
                        "metric": "memory_usage",
                        "baseline": baseline_avg,
                        "current": current_avg,
                        "regression_percent": ((current_avg - baseline_avg) / baseline_avg) * 100,
                    })
        
        return results
    
    async def update_baselines(self, metrics: dict[str, dict[str, dict[str, float]]]) -> None:
        """Update performance baselines with current metrics.
        
        Args:
            metrics: Current performance metrics
        """
        for component, component_metrics in metrics.items():
            if component not in self.baselines:
                self.baselines[component] = {}
            
            # Update baseline values
            if "response_time" in component_metrics:
                self.baselines[component]["response_time_average"] = component_metrics["response_time"]["average"]
                self.baselines[component]["response_time_p95"] = component_metrics["response_time"]["p95"]
            
            if "memory_usage" in component_metrics:
                self.baselines[component]["memory_usage_average"] = component_metrics["memory_usage"]["average"]
                self.baselines[component]["memory_usage_max"] = component_metrics["memory_usage"]["max"]
            
            if "cpu_usage" in component_metrics:
                self.baselines[component]["cpu_usage_average"] = component_metrics["cpu_usage"]["average"]
                self.baselines[component]["cpu_usage_max"] = component_metrics["cpu_usage"]["max"]
        
        # Save baselines to file
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_path, "w") as f:
            json.dump(self.baselines, f, indent=2)
        
        # Update monitoring dashboard baselines
        for component, baseline in self.baselines.items():
            self.monitoring_dashboard.update_baseline(component, baseline)
    
    def get_performance_report(self, results: dict[str, Any]) -> str:
        """Generate performance quality gates report.
        
        Args:
            results: Quality gates check results
            
        Returns:
            Formatted report string
        """
        report = []
        report.append("=" * 60)
        report.append("PERFORMANCE QUALITY GATES REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Summary
        total_gates = len(self.performance_gates)
        passed = len(results.get("passed", []))
        warnings = len(results.get("warnings", []))
        failures = len(results.get("failures", []))
        blocking = len(results.get("blocking_failures", []))
        
        report.append("SUMMARY:")
        report.append(f"  Total Gates: {total_gates}")
        report.append(f"  Passed: {passed}")
        report.append(f"  Warnings: {warnings}")
        report.append(f"  Failures: {failures}")
        report.append(f"  Blocking: {blocking}")
        report.append("")
        
        # Blocking failures
        if results.get("blocking_failures"):
            report.append("BLOCKING FAILURES:")
            for failure in results["blocking_failures"]:
                report.append(f"  ❌ {failure['name']}: {failure['description']}")
                report.append(f"     Value: {failure['value']:.2f}, Threshold: {failure['threshold']:.2f}")
                if failure.get("components_failed"):
                    for comp in failure["components_failed"]:
                        report.append(f"     - {comp['component']}: {comp['value']:.2f}")
            report.append("")
        
        # Warnings
        if results.get("warnings"):
            report.append("WARNINGS:")
            for warning in results["warnings"]:
                report.append(f"  ⚠️  {warning.get('name', 'unknown')}: {warning.get('description', '')}")
                if warning.get("details"):
                    for detail in warning.get("details", []):
                        if isinstance(detail, dict):
                            report.append(f"     - {detail.get('component', '')}: +{detail.get('regression_percent', 0):.1f}%")
            report.append("")
        
        # Performance regression
        if results.get("regression_detected"):
            report.append("PERFORMANCE REGRESSION DETECTED:")
            report.append("  Performance has regressed compared to baseline.")
            report.append("  Consider investigating the following components:")
            for regression in results.get("regressions", []):
                report.append(f"  - {regression['component']}: {regression['metric']} +{regression['regression_percent']:.1f}%")
            report.append("")
        
        # Metrics summary
        if results.get("metrics"):
            report.append("METRICS SUMMARY:")
            for component, metrics in results["metrics"].items():
                if "response_time" in metrics:
                    rt = metrics["response_time"]
                    report.append(f"  {component}:")
                    report.append(f"    Response Time: avg={rt['average']:.1f}ms, p95={rt['p95']:.1f}ms")
            report.append("")
        
        report.append("=" * 60)
        
        return "\n".join(report)


async def check_performance_quality_gates() -> tuple[bool, str]:
    """Check performance quality gates.
    
    Returns:
        Tuple of (success, report)
    """
    checker = QualityGatesPerformanceChecker()
    results = await checker.check_performance_gates()
    
    # Generate report
    report = checker.get_performance_report(results)
    
    # Determine success
    success = len(results.get("blocking_failures", [])) == 0
    
    return success, report


if __name__ == "__main__":
    # Run performance quality gates check
    success, report = asyncio.run(check_performance_quality_gates())
    print(report)
    
    if not success:
        exit(1)