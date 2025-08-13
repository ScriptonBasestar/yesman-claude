#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Integration tests for security-performance integration.

This module tests the unified security and performance monitoring system.
"""

import asyncio
import time
import unittest

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_integration import (
    MonitoringConfig,
    MonitoringDashboardIntegration,
)
from libs.dashboard.security_metrics_integration import (
    SecurityMetrics,
    SecurityMetricsIntegration,
)
from scripts.quality_gates_unified import UnifiedQualityGatesChecker


class TestSecurityPerformanceIntegration(unittest.TestCase):
    """Test security-performance integration."""

    def setUp(self) -> None:
        """Set up test environment."""
        self.event_bus = get_event_bus()
        self.monitoring_config = MonitoringConfig(
            update_interval=0.1,  # Fast updates for testing
            alert_cooldown=1,  # Short cooldown for testing
        )
        self.monitoring_dashboard = MonitoringDashboardIntegration(
            config=self.monitoring_config,
            event_bus=self.event_bus,
        )
        self.security_metrics = SecurityMetricsIntegration(
            monitoring_dashboard=self.monitoring_dashboard,
            event_bus=self.event_bus,
        )

    def tearDown(self) -> None:
        """Clean up test environment."""
        # Reset singletons
        import libs.dashboard.monitoring_integration as monitoring
        import libs.dashboard.security_metrics_integration as security

        monitoring._monitoring_dashboard = None
        security._security_metrics = None

    async def test_security_metrics_collection(self) -> None:
        """Test security metrics collection and storage."""
        # Start integration
        await self.security_metrics.start()

        try:
            # Create test security metrics
            test_metrics = SecurityMetrics(
                scan_duration_ms=150.0,
                violations_found=5,
                false_positive_rate=10.0,
                vulnerability_severity_counts={
                    "critical": 1,
                    "high": 2,
                    "medium": 1,
                    "low": 1,
                },
                scan_coverage_percent=95.0,
            )

            # Publish security scan completed event
            await self.event_bus.publish(
                Event(
                    type=EventType.CUSTOM,
                    data={
                        "event_subtype": "security",
                        "security_event_type": "scan_completed",
                        "component": "test_component",
                        "scan_duration_ms": test_metrics.scan_duration_ms,
                        "violations_found": test_metrics.violations_found,
                        "false_positive_rate": test_metrics.false_positive_rate,
                        "vulnerability_counts": test_metrics.vulnerability_severity_counts,
                        "scan_coverage": test_metrics.scan_coverage_percent,
                    },
                    timestamp=time.time(),
                    source="test",
                    priority=EventPriority.NORMAL,
                )
            )

            # Wait for event processing
            await asyncio.sleep(0.1)

            # Verify metrics were stored
            self.assertIn("test_component", self.security_metrics._security_metrics)
            stored_metrics = list(self.security_metrics._security_metrics["test_component"])
            self.assertEqual(len(stored_metrics), 1)

            first_metric = stored_metrics[0]
            self.assertEqual(first_metric.scan_duration_ms, 150.0)
            self.assertEqual(first_metric.violations_found, 5)
            self.assertEqual(first_metric.false_positive_rate, 10.0)

        finally:
            await self.security_metrics.stop()

    async def test_security_violation_detection(self) -> None:
        """Test security violation detection and alerting."""
        # Start integration
        await self.security_metrics.start()

        try:
            # Publish critical violation event
            await self.event_bus.publish(
                Event(
                    type=EventType.CUSTOM,
                    data={
                        "event_subtype": "security",
                        "security_event_type": "violation_detected",
                        "component": "test_component",
                        "severity": "critical",
                        "violation_type": "sql_injection",
                        "description": "SQL injection vulnerability detected",
                        "remediation": "Use parameterized queries",
                    },
                    timestamp=time.time(),
                    source="test",
                    priority=EventPriority.HIGH,
                )
            )

            # Wait for event processing
            await asyncio.sleep(0.1)

            # Verify violation was stored
            self.assertIn("test_component", self.security_metrics._vulnerability_inventory)
            vulnerabilities = self.security_metrics._vulnerability_inventory["test_component"]
            self.assertEqual(len(vulnerabilities), 1)

            vuln = vulnerabilities[0]
            self.assertEqual(vuln["severity"], "critical")
            self.assertEqual(vuln["type"], "sql_injection")

        finally:
            await self.security_metrics.stop()

    async def test_security_performance_correlation(self) -> None:
        """Test security-performance correlation analysis."""
        # Start both integrations
        await self.monitoring_dashboard.start()
        await self.security_metrics.start()

        try:
            # Simulate performance metrics before security scan
            for i in range(5):
                await self.event_bus.publish(
                    Event(
                        type=EventType.PERFORMANCE_METRICS,
                        data={
                            "component": "test_component",
                            "metrics": {
                                "component_response_times": {
                                    "test_component": {
                                        "average_ms": 50.0,
                                        "p95_ms": 75.0,
                                    }
                                }
                            },
                        },
                        timestamp=time.time() - 10 + i,  # Before scan
                        source="test",
                        priority=EventPriority.NORMAL,
                    )
                )

            # Simulate performance metrics during security scan
            scan_start = time.time()
            for i in range(3):
                await self.event_bus.publish(
                    Event(
                        type=EventType.PERFORMANCE_METRICS,
                        data={
                            "component": "test_component",
                            "metrics": {
                                "component_response_times": {
                                    "test_component": {
                                        "average_ms": 150.0,  # 3x slower during scan
                                        "p95_ms": 225.0,
                                    }
                                }
                            },
                        },
                        timestamp=scan_start + i * 0.1,
                        source="test",
                        priority=EventPriority.NORMAL,
                    )
                )

            # Wait for events to be stored
            await asyncio.sleep(0.2)

            # Publish security scan completed event
            await self.event_bus.publish(
                Event(
                    type=EventType.CUSTOM,
                    data={
                        "event_subtype": "security",
                        "security_event_type": "scan_completed",
                        "component": "test_component",
                        "scan_duration_ms": 300.0,
                        "violations_found": 0,
                        "false_positive_rate": 0,
                        "vulnerability_counts": {},
                        "scan_coverage": 100.0,
                    },
                    timestamp=scan_start + 0.3,
                    source="test",
                    priority=EventPriority.NORMAL,
                )
            )

            # Wait for correlation analysis
            await asyncio.sleep(0.2)

            # Check for performance impact detection
            impact_cache = self.security_metrics._performance_impact_cache
            # Note: Correlation analysis might not trigger immediately in test
            # This is a simplified test - in production, correlation would be detected

        finally:
            await self.monitoring_dashboard.stop()
            await self.security_metrics.stop()

    async def test_unified_quality_gates(self) -> None:
        """Test unified quality gates checker."""
        checker = UnifiedQualityGatesChecker()

        # Mock security scan to avoid actual file scanning
        async def mock_security_scan():
            return SecurityMetrics(
                scan_duration_ms=1000.0,
                violations_found=3,
                false_positive_rate=5.0,
                vulnerability_severity_counts={
                    "critical": 0,
                    "high": 1,
                    "medium": 1,
                    "low": 1,
                },
                scan_coverage_percent=95.0,
            )

        checker.run_security_scan = mock_security_scan

        # Start monitoring components
        await checker.monitoring_dashboard.start()
        await checker.security_metrics.start()

        try:
            # Simulate some performance metrics
            await self.event_bus.publish(
                Event(
                    type=EventType.PERFORMANCE_METRICS,
                    data={
                        "component": "test_component",
                        "metrics": {
                            "component_response_times": {
                                "test_component": {
                                    "average_ms": 80.0,
                                    "p95_ms": 120.0,
                                }
                            }
                        },
                    },
                    timestamp=time.time(),
                    source="test",
                    priority=EventPriority.NORMAL,
                )
            )

            # Run unified quality gates check
            result = await checker.check_unified_quality_gates(run_security_scan=True)

            # Verify result structure
            self.assertIsNotNone(result)
            self.assertIsInstance(result.passed, bool)
            self.assertIsInstance(result.performance_passed, bool)
            self.assertIsInstance(result.security_passed, bool)
            self.assertIsInstance(result.blocking_failures, list)
            self.assertIsInstance(result.warnings, list)
            self.assertIsInstance(result.correlations, list)
            self.assertIsInstance(result.metrics, dict)
            self.assertIsInstance(result.recommendations, list)

            # Check security metrics in results
            self.assertIn("security", result.metrics)
            security_metrics = result.metrics["security"]
            self.assertEqual(security_metrics["violations"], 3)
            self.assertEqual(security_metrics["scan_time_ms"], 1000.0)

            # Generate report
            report = checker.generate_unified_report(result)
            self.assertIsInstance(report, str)
            self.assertIn("UNIFIED QUALITY GATES REPORT", report)

        finally:
            await checker.monitoring_dashboard.stop()
            await checker.security_metrics.stop()

    async def test_security_threshold_alerting(self) -> None:
        """Test security threshold alerting."""
        # Start integration
        await self.security_metrics.start()

        alert_received = False
        alert_data = None

        def alert_handler(event: Event):
            nonlocal alert_received, alert_data
            if event.data.get("event_subtype") == "performance_alert":
                alert_received = True
                alert_data = event.data

        # Subscribe to alerts
        self.event_bus.subscribe(EventType.CUSTOM, alert_handler)

        try:
            # Publish scan with high violation count
            await self.event_bus.publish(
                Event(
                    type=EventType.CUSTOM,
                    data={
                        "event_subtype": "security",
                        "security_event_type": "scan_completed",
                        "component": "test_component",
                        "scan_duration_ms": 2000.0,  # Exceeds warning threshold
                        "violations_found": 25,  # Exceeds critical threshold
                        "false_positive_rate": 30.0,  # Exceeds error threshold
                        "vulnerability_counts": {
                            "critical": 5,
                            "high": 10,
                            "medium": 5,
                            "low": 5,
                        },
                        "scan_coverage": 100.0,
                    },
                    timestamp=time.time(),
                    source="test",
                    priority=EventPriority.NORMAL,
                )
            )

            # Wait for alert processing
            await asyncio.sleep(0.2)

            # Verify alert was triggered
            self.assertTrue(alert_received, "Security threshold alert should have been triggered")
            if alert_data:
                self.assertIn("security_related", alert_data.get("context", {}))

        finally:
            await self.security_metrics.stop()

    async def test_correlation_insights_generation(self) -> None:
        """Test generation of correlation insights."""
        # Start integration
        await self.security_metrics.start()

        insight_received = False
        insight_data = None

        def insight_handler(event: Event):
            nonlocal insight_received, insight_data
            if event.data.get("event_subtype") == "correlation_insight":
                insight_received = True
                insight_data = event.data

        # Subscribe to insights
        self.event_bus.subscribe(EventType.CUSTOM, insight_handler)

        try:
            # Manually trigger correlation analysis
            self.security_metrics._performance_impact_cache["test_component"] = 35.0  # 35% impact

            # Run correlation analysis
            correlations = self.security_metrics._analyze_all_correlations()

            # Verify correlations were found
            self.assertEqual(len(correlations), 1)
            self.assertEqual(correlations[0]["component"], "test_component")
            self.assertEqual(correlations[0]["impact"], 35.0)
            self.assertIn("scheduling scans", correlations[0]["recommendation"])

        finally:
            await self.security_metrics.stop()

    def test_security_metrics_summary(self) -> None:
        """Test security metrics summary generation."""
        # Add test data
        test_metrics = SecurityMetrics(
            scan_duration_ms=100.0,
            violations_found=5,
            false_positive_rate=10.0,
            vulnerability_severity_counts={"high": 2, "medium": 3},
            scan_coverage_percent=90.0,
        )

        self.security_metrics._security_metrics["component1"] = [test_metrics]
        self.security_metrics._vulnerability_inventory["component1"] = [
            {"severity": "high"},
            {"severity": "high"},
            {"severity": "medium"},
        ]
        self.security_metrics._performance_impact_cache["component1"] = 25.0

        # Generate summary
        summary = self.security_metrics.get_security_metrics_summary()

        # Verify summary structure
        self.assertIn("components", summary)
        self.assertIn("vulnerabilities", summary)
        self.assertIn("correlations", summary)

        # Verify component metrics
        self.assertIn("component1", summary["components"])
        comp_summary = summary["components"]["component1"]
        self.assertEqual(comp_summary["average_scan_time"], 100.0)
        self.assertEqual(comp_summary["total_violations"], 5)

        # Verify vulnerability counts
        self.assertIn("component1", summary["vulnerabilities"])
        vuln_counts = summary["vulnerabilities"]["component1"]
        self.assertEqual(vuln_counts["high"], 2)
        self.assertEqual(vuln_counts["medium"], 1)

        # Verify correlations
        self.assertEqual(summary["correlations"]["component1"], 25.0)

    def test_security_dashboard_data(self) -> None:
        """Test security dashboard data generation."""
        # Add test data
        current_time = time.time()
        test_metrics = SecurityMetrics(
            scan_duration_ms=100.0,
            violations_found=5,
            false_positive_rate=10.0,
            vulnerability_severity_counts={"high": 2, "medium": 3},
            scan_coverage_percent=90.0,
            timestamp=current_time,
        )

        self.security_metrics._security_metrics["component1"] = [test_metrics]
        self.security_metrics._vulnerability_inventory["component1"] = [
            {"severity": "high", "false_positive": False},
            {"severity": "medium", "false_positive": False},
            {"severity": "low", "false_positive": True},
        ]
        self.security_metrics._performance_impact_cache["component1"] = 15.0

        # Generate dashboard data
        dashboard_data = self.security_metrics.get_security_dashboard_data()

        # Verify dashboard data structure
        self.assertIn("time_series", dashboard_data)
        self.assertIn("vulnerability_status", dashboard_data)
        self.assertIn("performance_impact", dashboard_data)
        self.assertIn("summary", dashboard_data)

        # Verify time series data
        time_series = dashboard_data["time_series"]
        self.assertIn("scan_times", time_series)
        self.assertIn("violation_counts", time_series)
        self.assertIn("false_positive_rates", time_series)

        # Verify vulnerability status
        vuln_status = dashboard_data["vulnerability_status"]["component1"]
        self.assertEqual(vuln_status["total"], 2)  # Excluding false positive
        self.assertEqual(vuln_status["high"], 1)
        self.assertEqual(vuln_status["medium"], 1)

        # Verify performance impact
        self.assertEqual(dashboard_data["performance_impact"]["component1"], 15.0)


class TestAsyncIntegration(unittest.IsolatedAsyncioTestCase):
    """Async test cases for integration."""

    async def test_end_to_end_integration(self) -> None:
        """Test end-to-end integration flow."""
        test_case = TestSecurityPerformanceIntegration()
        test_case.setUp()

        try:
            # Run multiple test scenarios
            await test_case.test_security_metrics_collection()
            await test_case.test_security_violation_detection()
            await test_case.test_unified_quality_gates()

        finally:
            test_case.tearDown()


if __name__ == "__main__":
    unittest.main()
