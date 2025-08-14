#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Main Monitoring Dashboard Integration Module.

This module provides the main entry point for the monitoring dashboard system,
integrating all components including visualization, alerting, and quality gates.
"""

import asyncio
import logging

from libs.core.async_event_bus import get_event_bus
from libs.dashboard.monitoring_config_manager import (
    ConfigSection,
    get_monitoring_config_manager,
)
from libs.dashboard.monitoring_integration import (
    AlertSeverity,
    AlertThreshold,
    MetricType,
    PerformanceAlert,
    get_monitoring_dashboard,
)
from scripts.quality_gates_performance import QualityGatesPerformanceChecker


class MonitoringDashboardSystem:
    """Main monitoring dashboard system orchestrator."""

    def __init__(self) -> None:
        """Initialize monitoring dashboard system."""
        self.logger = logging.getLogger("yesman.monitoring_dashboard")

        # Initialize components
        self.event_bus = get_event_bus()
        self.config_manager = get_monitoring_config_manager()
        self.monitoring_dashboard = get_monitoring_dashboard()
        self.quality_gates_checker = QualityGatesPerformanceChecker()

        # Setup configuration change handlers
        self._setup_config_handlers()

        # System state
        self._is_running = False
        self._quality_gates_task: asyncio.Task | None = None

    def _setup_config_handlers(self) -> None:
        """Setup configuration change handlers."""
        # Handle threshold changes
        self.config_manager.register_change_callback(ConfigSection.THRESHOLDS, self._handle_threshold_change)

        # Handle alert rule changes
        self.config_manager.register_change_callback(ConfigSection.ALERTS, self._handle_alert_change)

        # Handle dashboard changes
        self.config_manager.register_change_callback(ConfigSection.DASHBOARD, self._handle_dashboard_change)

        # Handle baseline changes
        self.config_manager.register_change_callback(ConfigSection.BASELINES, self._handle_baseline_change)

    def _handle_threshold_change(self, thresholds: dict) -> None:
        """Handle threshold configuration changes.

        Args:
            thresholds: New threshold configurations
        """
        self.logger.info("Threshold configuration updated")

        # Clear existing thresholds
        self.monitoring_dashboard._alert_thresholds.clear()

        # Add new thresholds
        for threshold_id, threshold_config in thresholds.items():
            if not threshold_config.enabled:
                continue

            # Map configuration to MetricType
            metric_type_map = {
                "response_time": MetricType.RESPONSE_TIME,
                "memory_usage": MetricType.MEMORY_USAGE,
                "cpu_usage": MetricType.CPU_USAGE,
                "error_rate": MetricType.ERROR_RATE,
                "network_io": MetricType.NETWORK_IO,
            }

            metric_type = metric_type_map.get(threshold_config.metric)
            if not metric_type:
                continue

            alert_threshold = AlertThreshold(
                metric_type=metric_type,
                component=threshold_config.component,
                warning_threshold=threshold_config.warning,
                error_threshold=threshold_config.error,
                critical_threshold=threshold_config.critical,
                aggregation_window=threshold_config.aggregation_window,
                min_occurrences=threshold_config.min_occurrences,
            )

            self.monitoring_dashboard.add_custom_threshold(alert_threshold)

    def _handle_alert_change(self, alert_rules: dict) -> None:
        """Handle alert rule configuration changes.

        Args:
            alert_rules: New alert rule configurations
        """
        self.logger.info("Alert rules configuration updated")
        # Alert rules are evaluated in the alert monitoring loop

    def _handle_dashboard_change(self, dashboard_config: dict) -> None:
        """Handle dashboard configuration changes.

        Args:
            dashboard_config: New dashboard configuration
        """
        self.logger.info("Dashboard configuration updated")

        # Update monitoring dashboard configuration
        if hasattr(dashboard_config, "update_interval"):
            self.monitoring_dashboard.config.update_interval = dashboard_config.update_interval
        if hasattr(dashboard_config, "metric_retention"):
            self.monitoring_dashboard.config.metric_retention = dashboard_config.metric_retention
        if hasattr(dashboard_config, "alert_retention"):
            self.monitoring_dashboard.config.alert_retention = dashboard_config.alert_retention

    def _handle_baseline_change(self, baselines: dict) -> None:
        """Handle baseline configuration changes.

        Args:
            baselines: New baseline configurations
        """
        self.logger.info("Baseline configuration updated")

        # Update baselines in monitoring dashboard
        for component, baseline_data in baselines.items():
            self.monitoring_dashboard.update_baseline(component, baseline_data)

        # Update baselines in quality gates checker
        self.quality_gates_checker.baselines = baselines

    async def start(self) -> None:
        """Start the monitoring dashboard system."""
        if self._is_running:
            self.logger.warning("Monitoring dashboard system already running")
            return

        self._is_running = True
        self.logger.info("Starting monitoring dashboard system")

        # Apply initial configuration
        config = self.config_manager.config
        self._handle_threshold_change(config.thresholds)
        self._handle_dashboard_change(config.dashboard)
        self._handle_baseline_change(config.baselines)

        # Start monitoring dashboard
        await self.monitoring_dashboard.start()

        # Register alert callback
        self.monitoring_dashboard.register_alert_callback(self._handle_performance_alert)

        # Start quality gates monitoring
        self._quality_gates_task = asyncio.create_task(self._quality_gates_monitoring_loop())

        self.logger.info("Monitoring dashboard system started successfully")

    async def stop(self) -> None:
        """Stop the monitoring dashboard system."""
        if not self._is_running:
            return

        self._is_running = False
        self.logger.info("Stopping monitoring dashboard system")

        # Stop quality gates monitoring
        if self._quality_gates_task and not self._quality_gates_task.done():
            self._quality_gates_task.cancel()
            try:
                await self._quality_gates_task
            except asyncio.CancelledError:
                pass

        # Stop monitoring dashboard
        await self.monitoring_dashboard.stop()

        # Stop configuration manager
        self.config_manager.stop()

        self.logger.info("Monitoring dashboard system stopped")

    async def _quality_gates_monitoring_loop(self) -> None:
        """Quality gates monitoring loop."""
        check_interval = 60.0  # Check every minute

        while self._is_running:
            try:
                # Check quality gates
                results = await self.quality_gates_checker.check_performance_gates()

                # Process results
                if results.get("blocking_failures"):
                    self.logger.error("Quality gates failed: %d blocking failures", len(results["blocking_failures"]))

                    # Create alerts for blocking failures
                    for failure in results["blocking_failures"]:
                        alert = PerformanceAlert(
                            timestamp=asyncio.get_event_loop().time(),
                            severity=AlertSeverity.ERROR,
                            metric_type=MetricType.RESPONSE_TIME,  # Default to response time
                            component="quality_gates",
                            current_value=failure.get("value", 0),
                            threshold=failure.get("threshold", 0),
                            message=f"Quality gate failed: {failure.get('name', 'unknown')}",
                            context={"failure": failure},
                        )
                        await self.monitoring_dashboard._process_alert(alert)

                # Update baselines if metrics are good
                if not results.get("blocking_failures") and not results.get("regression_detected"):
                    if results.get("metrics"):
                        await self.quality_gates_checker.update_baselines(results["metrics"])

                await asyncio.sleep(check_interval)

            except asyncio.CancelledError:
                break
            except Exception:
                self.logger.exception("Error in quality gates monitoring loop")
                await asyncio.sleep(check_interval)

    def _handle_performance_alert(self, alert: PerformanceAlert) -> None:
        """Handle performance alert from monitoring dashboard.

        Args:
            alert: Performance alert
        """
        # Log alert
        self.logger.warning(
            "Performance alert: [%s] %s - %s (value=%.2f, threshold=%.2f)",
            alert.severity.value,
            alert.component,
            alert.message,
            alert.current_value,
            alert.threshold,
        )

        # Check alert rules from configuration
        alert_rules = self.config_manager.get_enabled_alert_rules()

        for rule_id, rule in alert_rules.items():
            # Simple condition evaluation (in production, use a proper expression evaluator)
            if self._evaluate_alert_condition(alert, rule.condition):
                # Execute alert actions
                for action in rule.actions:
                    self._execute_alert_action(action, alert, rule)

    def _evaluate_alert_condition(self, alert: PerformanceAlert, condition: str) -> bool:
        """Evaluate alert condition.

        Args:
            alert: Performance alert
            condition: Condition expression

        Returns:
            True if condition matches
        """
        # Simple condition evaluation (can be enhanced with expression parser)
        try:
            if "response_time" in condition and alert.metric_type == MetricType.RESPONSE_TIME:
                return True
            if "memory" in condition and alert.metric_type == MetricType.MEMORY_USAGE:
                return True
            if "cpu" in condition and alert.metric_type == MetricType.CPU_USAGE:
                return True
            if "error" in condition and alert.metric_type == MetricType.ERROR_RATE:
                return True
            if "regression" in condition and "regression" in alert.context:
                return True
        except Exception as e:
            self.logger.debug("Error evaluating alert condition: %s", e)

        return False

    def _execute_alert_action(self, action: str, alert: PerformanceAlert, rule: dict) -> None:
        """Execute alert action.

        Args:
            action: Action to execute
            alert: Performance alert
            rule: Alert rule configuration
        """
        if action == "log":
            self.logger.error("Alert Rule '%s' triggered: %s", rule.name, alert.message)
        elif action == "dashboard_notification":
            # Dashboard notifications are handled by the event bus
            pass
        elif action == "email":
            # Email notification would be implemented here
            self.logger.info("Email notification would be sent for: %s", rule.name)

    async def get_system_status(self) -> dict:
        """Get current system status.

        Returns:
            System status dictionary
        """
        status = {
            "is_running": self._is_running,
            "monitoring_dashboard": {
                "is_running": self.monitoring_dashboard._is_running,
                "active_alerts": len(self.monitoring_dashboard.get_active_alerts()),
                "health_score": self.monitoring_dashboard._calculate_health_score(),
            },
            "configuration": {
                "thresholds": len(self.config_manager.get_enabled_thresholds()),
                "alert_rules": len(self.config_manager.get_enabled_alert_rules()),
                "baselines": len(self.config_manager.config.baselines),
            },
            "quality_gates": {
                "enabled": self.config_manager.config.quality_gates.get("enabled", True),
                "regression_threshold": self.config_manager.config.quality_gates.get("performance_regression_threshold", 20.0),
            },
        }

        return status


# Singleton instance
_monitoring_system: MonitoringDashboardSystem | None = None


def get_monitoring_system() -> MonitoringDashboardSystem:
    """Get or create monitoring dashboard system.

    Returns:
        Monitoring dashboard system instance
    """
    global _monitoring_system  # noqa: PLW0603

    if _monitoring_system is None:
        _monitoring_system = MonitoringDashboardSystem()

    return _monitoring_system


async def main() -> None:
    """Main entry point for monitoring dashboard system."""
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Get monitoring system
    monitoring_system = get_monitoring_system()

    try:
        # Start the system
        await monitoring_system.start()

        # Keep running
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        print("\nShutting down monitoring dashboard system...")
    finally:
        # Stop the system
        await monitoring_system.stop()


if __name__ == "__main__":
    asyncio.run(main())
