#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Test script for monitoring dashboard integration.

This script demonstrates the monitoring dashboard system with simulated
performance metrics and alerts.
"""

import asyncio
import random
import time

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from libs.dashboard.monitoring_main import get_monitoring_system


async def simulate_performance_metrics() -> None:
    """Simulate performance metrics from monitoring system."""
    event_bus = get_event_bus()

    components = ["content_capture", "claude_status_check", "prompt_detection", "content_processing", "response_sending", "automation_analysis"]

    while True:
        # Generate random metrics for each component
        component_metrics = {}

        for component in components:
            # Simulate varying performance
            base_response_time = random.uniform(20, 80)
            spike_chance = random.random()

            # Occasional performance spike
            if spike_chance > 0.9:
                response_time = base_response_time * random.uniform(2, 5)
            else:
                response_time = base_response_time

            # Generate component metrics
            component_metrics[component] = {
                "average_ms": response_time,
                "median_ms": response_time * 0.9,
                "p95_ms": response_time * 1.5,
                "p99_ms": response_time * 2.0,
                "peak_ms": response_time * 2.5,
                "sample_count": 100,
                "error_count": random.randint(0, 5),
                "error_rate": random.uniform(0, 0.1),
                "avg_memory_delta_mb": random.uniform(-0.5, 2.0),
                "peak_memory_delta_mb": random.uniform(1.0, 5.0),
                "avg_cpu_percent": random.uniform(10, 40),
                "peak_cpu_percent": random.uniform(40, 80),
                "avg_throughput_mbps": random.uniform(0.1, 2.0),
                "peak_throughput_mbps": random.uniform(1.0, 5.0),
            }

        # Publish performance metrics event
        await event_bus.publish(
            Event(
                type=EventType.PERFORMANCE_METRICS,
                data={
                    "component": "async_claude_monitor",
                    "metrics": {
                        "component_response_times": component_metrics,
                        "current_memory_mb": random.uniform(100, 200),
                        "baseline_memory_mb": 100,
                        "memory_growth_mb": random.uniform(0, 50),
                        "current_cpu_percent": random.uniform(20, 60),
                        "baseline_cpu_percent": 30,
                    },
                },
                timestamp=time.time(),
                source="test_simulator",
                priority=EventPriority.LOW,
            )
        )

        # Simulate dashboard update events
        await event_bus.publish(
            Event(
                type=EventType.DASHBOARD_UPDATE,
                data={
                    "update_type": "metrics_update",
                    "metrics": component_metrics,
                    "alerts": {
                        "active": random.randint(0, 5),
                        "critical": random.randint(0, 1),
                        "error": random.randint(0, 2),
                        "warning": random.randint(0, 3),
                    },
                    "health_score": random.uniform(70, 100),
                },
                timestamp=time.time(),
                source="test_simulator",
                priority=EventPriority.LOW,
            )
        )

        await asyncio.sleep(1)  # Send metrics every second


async def simulate_alerts() -> None:
    """Simulate performance alerts."""
    event_bus = get_event_bus()

    alert_scenarios = [
        {
            "severity": "warning",
            "component": "content_processing",
            "metric_type": "response_time",
            "message": "Response time exceeding threshold",
        },
        {
            "severity": "error",
            "component": "claude_status_check",
            "metric_type": "error_rate",
            "message": "High error rate detected",
        },
        {
            "severity": "critical",
            "component": "memory_monitor",
            "metric_type": "memory_usage",
            "message": "Memory leak detected",
        },
    ]

    while True:
        await asyncio.sleep(random.uniform(10, 30))  # Random alert intervals

        # Pick a random alert scenario
        scenario = random.choice(alert_scenarios)

        # Publish performance alert
        await event_bus.publish(
            Event(
                type=EventType.CUSTOM,
                data={
                    "event_subtype": "performance_alert",
                    "severity": scenario["severity"],
                    "component": scenario["component"],
                    "metric_type": scenario["metric_type"],
                    "current_value": random.uniform(100, 500),
                    "threshold": 100.0,
                    "message": scenario["message"],
                    "context": {
                        "samples": 50,
                        "window": 60,
                    },
                },
                timestamp=time.time(),
                source="test_simulator",
                priority=EventPriority.HIGH,
            )
        )


async def main() -> None:
    """Main test function."""
    print("Starting Monitoring Dashboard Integration Test")
    print("=" * 60)

    # Get monitoring system
    monitoring_system = get_monitoring_system()

    # Start monitoring system
    print("Starting monitoring system...")
    await monitoring_system.start()

    # Get initial status
    status = await monitoring_system.get_system_status()
    print(f"System Status: {status}")
    print()

    # Start simulators
    metrics_task = asyncio.create_task(simulate_performance_metrics())
    alerts_task = asyncio.create_task(simulate_alerts())

    print("Simulating performance metrics and alerts...")
    print("Press Ctrl+C to stop")
    print()

    try:
        # Run for a while
        await asyncio.sleep(60)  # Run for 1 minute

    except KeyboardInterrupt:
        print("\nStopping test...")

    finally:
        # Cancel simulators
        metrics_task.cancel()
        alerts_task.cancel()

        try:
            await metrics_task
            await alerts_task
        except asyncio.CancelledError:
            pass

        # Get final status
        final_status = await monitoring_system.get_system_status()
        print(f"Final System Status: {final_status}")

        # Stop monitoring system
        await monitoring_system.stop()

        print("Test completed")


if __name__ == "__main__":
    # Setup basic logging
    import logging

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")

    # Run test
    asyncio.run(main())
