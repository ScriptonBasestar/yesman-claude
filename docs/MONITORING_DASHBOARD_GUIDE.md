# Monitoring Dashboard Integration Guide

## Overview

The Monitoring Dashboard Integration provides comprehensive real-time performance visualization, automated alerting, and quality gates integration for the Yesman-Agent system. This guide covers setup, configuration, and usage of the monitoring dashboard system.

## Architecture

### Components

1. **Monitoring Integration** (`libs/dashboard/monitoring_integration.py`)
   - Core monitoring dashboard functionality
   - Alert threshold management
   - Performance metrics aggregation
   - Real-time dashboard updates

2. **Configuration Manager** (`libs/dashboard/monitoring_config_manager.py`)
   - Centralized configuration management
   - Hot-reload capabilities
   - Threshold and alert rule management
   - Baseline configuration

3. **Quality Gates Integration** (`scripts/quality_gates_performance.py`)
   - Performance quality gates checks
   - Regression detection
   - Baseline management
   - Quality score calculation

4. **Dashboard Components** (Tauri)
   - `PerformanceMetrics.svelte`: Real-time performance charts
   - `PerformanceAlerts.svelte`: Alert management and display
   - Event-driven updates via Tauri API

5. **Main Orchestrator** (`libs/dashboard/monitoring_main.py`)
   - System initialization
   - Component coordination
   - Alert processing
   - Quality gates monitoring

## Setup

### Prerequisites

```bash
# Install Python dependencies
pip install watchdog psutil

# Install Node.js dependencies for Tauri dashboard
cd tauri-dashboard
pnpm install
```

### Configuration

Create a monitoring configuration file at `config/monitoring_config.json`:

```json
{
  "version": "1.0",
  "thresholds": {
    "response_time_warning": {
      "metric": "response_time",
      "component": "all",
      "warning": 100.0,
      "error": 200.0,
      "critical": 500.0,
      "enabled": true,
      "aggregation_window": 60,
      "min_occurrences": 3
    }
  },
  "alert_rules": {
    "high_response_time": {
      "name": "High Response Time",
      "description": "Alert when response time exceeds threshold",
      "condition": "response_time.p95 > 200",
      "severity": "warning",
      "cooldown": 300,
      "enabled": true,
      "actions": ["log", "dashboard_notification"]
    }
  },
  "dashboard": {
    "update_interval": 1.0,
    "metric_retention": 3600,
    "alert_retention": 86400,
    "chart_max_points": 60,
    "auto_refresh": true,
    "default_view": "overview"
  }
}
```

## Usage

### Starting the Monitoring System

```python
import asyncio
from libs.dashboard.monitoring_main import get_monitoring_system

async def main():
    # Get monitoring system instance
    monitoring_system = get_monitoring_system()
    
    # Start the system
    await monitoring_system.start()
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        await monitoring_system.stop()

asyncio.run(main())
```

### Integrating with Existing Monitoring

The system automatically integrates with the existing `AsyncClaudeMonitor`:

```python
from libs.core.claude_monitor_async import AsyncClaudeMonitor
from libs.dashboard.monitoring_integration import get_monitoring_dashboard

# The monitor automatically publishes metrics to the dashboard
monitor = AsyncClaudeMonitor(
    session_manager=session_manager,
    process_controller=process_controller,
    status_manager=status_manager
)

# Dashboard receives metrics via event bus
dashboard = get_monitoring_dashboard()
await dashboard.start()
```

### Custom Alert Configuration

Add custom alert thresholds programmatically:

```python
from libs.dashboard.monitoring_integration import (
    AlertThreshold,
    MetricType,
    get_monitoring_dashboard
)

dashboard = get_monitoring_dashboard()

# Add custom threshold
threshold = AlertThreshold(
    metric_type=MetricType.RESPONSE_TIME,
    component="critical_component",
    warning_threshold=50.0,
    error_threshold=100.0,
    critical_threshold=200.0
)

dashboard.add_custom_threshold(threshold)
```

### Registering Alert Callbacks

```python
def handle_alert(alert):
    print(f"Alert: {alert.severity} - {alert.message}")
    # Custom alert handling logic

dashboard.register_alert_callback(handle_alert)
```

## Dashboard Features

### Real-time Performance Metrics

The dashboard displays real-time metrics for:
- **Response Time**: Component execution times
- **Memory Usage**: Memory allocation and deltas
- **CPU Usage**: CPU utilization percentages
- **Error Rate**: Component error rates
- **Network I/O**: Network throughput

### Alert Management

- **Severity Levels**: Info, Warning, Error, Critical
- **Alert Aggregation**: Groups similar alerts
- **Cooldown Periods**: Prevents alert spam
- **Alert History**: Maintains alert history

### Performance Regression Detection

Automatically detects performance regressions by:
- Comparing current metrics to baselines
- Configurable regression thresholds
- Automatic baseline updates
- Integration with quality gates

### Quality Gates Integration

Performance metrics are integrated into quality gates:
- **Blocking Gates**: Prevent deployment on failures
- **Warning Gates**: Require review
- **Advisory Gates**: Best practice guidance

## Configuration Reference

### Threshold Configuration

```json
{
  "metric": "response_time",        // Metric type
  "component": "all",               // Component name or "all"
  "warning": 100.0,                 // Warning threshold
  "error": 200.0,                   // Error threshold
  "critical": 500.0,                // Critical threshold
  "enabled": true,                  // Enable/disable threshold
  "aggregation_window": 60,         // Time window in seconds
  "min_occurrences": 3              // Minimum occurrences
}
```

### Alert Rule Configuration

```json
{
  "name": "Rule Name",
  "description": "Rule description",
  "condition": "expression",         // Condition expression
  "severity": "warning",            // Alert severity
  "cooldown": 300,                  // Cooldown in seconds
  "enabled": true,                  // Enable/disable rule
  "actions": ["log", "email"]       // Alert actions
}
```

### Dashboard Configuration

```json
{
  "update_interval": 1.0,            // Update frequency in seconds
  "metric_retention": 3600,          // Metric retention in seconds
  "alert_retention": 86400,          // Alert retention in seconds
  "chart_max_points": 60,            // Maximum chart data points
  "auto_refresh": true,              // Auto-refresh enabled
  "default_view": "overview"         // Default dashboard view
}
```

## API Reference

### MonitoringDashboardIntegration

```python
class MonitoringDashboardIntegration:
    async def start() -> None
    async def stop() -> None
    def register_alert_callback(callback: Callable) -> None
    def add_custom_threshold(threshold: AlertThreshold) -> None
    def get_metrics_for_component(component: str) -> dict
    def get_active_alerts() -> list[PerformanceAlert]
    def update_baseline(component: str, baseline_data: dict) -> None
```

### MonitoringConfigManager

```python
class MonitoringConfigManager:
    def load_config() -> bool
    async def reload_config() -> bool
    def register_change_callback(section: ConfigSection, callback: Callable) -> None
    def get_threshold(threshold_id: str) -> Optional[ThresholdConfig]
    def get_alert_rule(rule_id: str) -> Optional[AlertRuleConfig]
    def update_threshold(threshold_id: str, updates: dict) -> bool
    def save_config() -> bool
```

### QualityGatesPerformanceChecker

```python
class QualityGatesPerformanceChecker:
    async def check_performance_gates() -> dict
    async def update_baselines(metrics: dict) -> None
    def get_performance_report(results: dict) -> str
```

## Tauri Dashboard Components

### PerformanceMetrics Component

Displays real-time performance charts with:
- Multiple metric types
- Component filtering
- Time-series visualization
- Current values summary

### PerformanceAlerts Component

Manages and displays alerts with:
- Alert severity indicators
- System health score
- Alert statistics
- Alert dismissal
- Performance regression details

## Testing

Run the test script to verify the integration:

```bash
python tests/test_monitoring_dashboard.py
```

This simulates:
- Performance metrics generation
- Alert triggering
- Dashboard updates
- Quality gates checks

## Troubleshooting

### Common Issues

1. **No metrics displayed**
   - Check event bus connection
   - Verify monitoring system is running
   - Check configuration file exists

2. **Alerts not triggering**
   - Verify threshold configuration
   - Check alert rules are enabled
   - Review aggregation windows

3. **Configuration not reloading**
   - Ensure file watcher has permissions
   - Check configuration file format
   - Review logs for errors

### Debug Mode

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Performance Considerations

- **Metric Retention**: Adjust `metric_retention` to balance memory usage
- **Update Interval**: Increase `update_interval` for lower CPU usage
- **Alert Aggregation**: Use appropriate `aggregation_window` values
- **Chart Points**: Limit `chart_max_points` for better UI performance

## Best Practices

1. **Set Appropriate Thresholds**
   - Start with conservative thresholds
   - Adjust based on actual performance
   - Use percentiles (p95, p99) for better accuracy

2. **Configure Alert Actions**
   - Use cooldown periods to prevent spam
   - Implement escalation for critical alerts
   - Log all alerts for audit trails

3. **Maintain Baselines**
   - Update baselines after performance improvements
   - Keep separate baselines for different environments
   - Monitor baseline drift over time

4. **Quality Gates Integration**
   - Make performance gates part of CI/CD
   - Block deployments on regression
   - Track performance trends

## Future Enhancements

- [ ] Export metrics to external monitoring systems
- [ ] Machine learning-based anomaly detection
- [ ] Predictive performance analysis
- [ ] Custom dashboard layouts
- [ ] Mobile dashboard support
- [ ] Integration with cloud monitoring services