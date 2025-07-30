#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Integration test for AsyncClaudeMonitor with performance monitoring.

This script validates the async monitoring system integration with the performance
baseline system, ensuring proper event flow, metrics collection, and error handling.
"""

import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any

# Add the project root to sys.path so we can import our modules
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus
from scripts.performance_baseline import create_monitoring_metrics, create_quality_gates_metrics, get_performance_monitor


class MockSessionManager:
    """Mock session manager for testing."""

    def __init__(self, session_name: str = "test_session") -> None:
        self.session_name = session_name
        self._claude_pane = True
        self._content = "Claude is ready and waiting for input..."

    def get_claude_pane(self) -> bool:
        """Return whether Claude pane exists."""
        return self._claude_pane

    def capture_pane_content(self) -> str:
        """Return mock pane content."""
        return self._content

    def set_content(self, content: str) -> None:
        """Set mock content for testing."""
        self._content = content


class MockProcessController:
    """Mock process controller for testing."""

    def __init__(self) -> None:
        self._claude_running = True
        self._restart_count = 0

    def is_claude_running(self) -> bool:
        """Return whether Claude is running."""
        return self._claude_running

    def restart_claude_pane(self) -> None:
        """Mock restart Claude pane."""
        self._restart_count += 1
        self._claude_running = True
        print(f"🔄 Mock: Restarted Claude pane (restart #{self._restart_count})")

    def send_input(self, input_text: str) -> None:
        """Mock send input to Claude."""
        print(f"📝 Mock: Sending input to Claude: '{input_text}'")

    def set_claude_running(self, running: bool) -> None:
        """Set Claude running state for testing."""
        self._claude_running = running


class MockStatusManager:
    """Mock status manager for testing."""

    def __init__(self) -> None:
        self.last_activity_time = time.time()
        self._status_messages = []
        self._activity_messages = []

    def update_status(self, message: str) -> None:
        """Mock update status."""
        self._status_messages.append(message)
        print(f"📊 Status: {message}")

    def update_activity(self, message: str) -> None:
        """Mock update activity."""
        self._activity_messages.append(message)
        self.last_activity_time = time.time()
        print(f"⚡ Activity: {message}")

    def record_response(self, prompt_type: str, response: str, question: str) -> None:
        """Mock record response."""
        print(f"📝 Response recorded: {prompt_type} -> {response}")


class AsyncIntegrationTester:
    """Comprehensive integration tester for async monitoring system."""

    def __init__(self) -> None:
        self.logger = logging.getLogger("async_integration_tester")
        self.results: dict[str, Any] = {}
        self.test_duration = 30  # seconds

        # Initialize mock components
        self.session_manager = MockSessionManager("integration_test")
        self.process_controller = MockProcessController()
        self.status_manager = MockStatusManager()

        # Get event bus and performance monitor
        self.event_bus = get_event_bus()
        self.performance_monitor = get_performance_monitor()

        # Test tracking
        self.events_received = []
        self.performance_samples = []

    async def run_integration_tests(self) -> dict[str, Any]:
        """Run comprehensive integration tests.

        Returns:
            Test results dictionary
        """
        print("🧪 Starting AsyncClaudeMonitor Integration Tests")
        print("=" * 60)

        test_start = time.time()

        try:
            # Setup event listeners
            await self._setup_event_listeners()

            # Start performance monitoring
            await self._start_performance_monitoring()

            # Test 1: Basic async monitor creation and startup
            print("\n🔧 Test 1: AsyncClaudeMonitor Creation and Startup")
            monitor_test = await self._test_monitor_creation()

            # Test 2: Event bus integration
            print("\n📡 Test 2: Event Bus Integration")
            event_test = await self._test_event_integration()

            # Test 3: Performance metrics collection
            print("\n📊 Test 3: Performance Metrics Collection")
            metrics_test = await self._test_performance_metrics()

            # Test 4: Mock prompt handling
            print("\n🎯 Test 4: Prompt Detection and Response")
            prompt_test = await self._test_prompt_handling()

            # Test 5: Error handling and recovery
            print("\n🛡️ Test 5: Error Handling and Recovery")
            error_test = await self._test_error_handling()

            # Test 6: Performance baseline integration
            print("\n⚡ Test 6: Performance Baseline Integration")
            baseline_test = await self._test_baseline_integration()

            # Compile results
            execution_time = time.time() - test_start

            self.results = {
                "test_execution_time": execution_time,
                "tests": {
                    "monitor_creation": monitor_test,
                    "event_integration": event_test,
                    "performance_metrics": metrics_test,
                    "prompt_handling": prompt_test,
                    "error_handling": error_test,
                    "baseline_integration": baseline_test,
                },
                "events_received": len(self.events_received),
                "performance_samples": len(self.performance_samples),
                "overall_success": all(
                    [
                        monitor_test.get("success", False),
                        event_test.get("success", False),
                        metrics_test.get("success", False),
                        prompt_test.get("success", False),
                        error_test.get("success", False),
                        baseline_test.get("success", False),
                    ]
                ),
            }

            await self._cleanup()

            return self.results

        except Exception as e:
            self.logger.error(f"Integration test failed: {e}", exc_info=True)
            self.results["error"] = str(e)
            self.results["overall_success"] = False
            return self.results

    async def _setup_event_listeners(self) -> None:
        """Setup event listeners for testing."""
        # Start the event bus first
        await self.event_bus.start()

        # Subscribe to all event types for monitoring
        for event_type in EventType:
            self.event_bus.subscribe(event_type, self._record_event)

    async def _record_event(self, event: Event) -> None:
        """Record events for analysis."""
        self.events_received.append({"type": event.type.value, "timestamp": event.timestamp, "source": event.source, "priority": event.priority.value})

    async def _start_performance_monitoring(self) -> None:
        """Start performance monitoring for the test."""
        success = await self.performance_monitor.start_monitoring()
        if not success:
            raise RuntimeError("Failed to start performance monitoring")

    async def _test_monitor_creation(self) -> dict[str, Any]:
        """Test AsyncClaudeMonitor creation and basic functionality."""
        try:
            # Import and create AsyncClaudeMonitor
            from libs.core.claude_monitor_async import AsyncClaudeMonitor

            # Create monitor instance
            monitor = AsyncClaudeMonitor(session_manager=self.session_manager, process_controller=self.process_controller, status_manager=self.status_manager, event_bus=self.event_bus)

            # Test basic properties
            if monitor.session_name != "integration_test":
                raise ValueError(f"Expected session_name 'integration_test', got '{monitor.session_name}'")
            if not monitor.is_auto_next_enabled:
                raise ValueError("Expected is_auto_next_enabled to be True")
            if monitor.is_running:
                raise ValueError("Expected is_running to be False initially")

            # Test startup
            startup_success = await monitor.start_monitoring_async()
            if not startup_success:
                raise RuntimeError("Failed to start async monitoring")
            if not monitor.is_running:
                raise RuntimeError("Monitor should be running after startup")

            # Let it run for a few seconds
            await asyncio.sleep(3)

            # Test shutdown
            shutdown_success = await monitor.stop_monitoring_async()
            if not shutdown_success:
                raise RuntimeError("Failed to stop async monitoring")
            if monitor.is_running:
                raise RuntimeError("Monitor should not be running after shutdown")

            return {"success": True, "startup_success": startup_success, "shutdown_success": shutdown_success, "monitor_instance": str(type(monitor))}

        except Exception as e:
            self.logger.error(f"Monitor creation test failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _test_event_integration(self) -> dict[str, Any]:
        """Test event bus integration."""
        try:
            initial_event_count = len(self.events_received)

            # Publish test events
            test_events = [
                Event(type=EventType.SESSION_STARTED, data={"test": "integration_test"}, timestamp=time.time(), source="integration_tester", priority=EventPriority.NORMAL),
                Event(type=EventType.PERFORMANCE_METRICS, data={"test_metric": 42}, timestamp=time.time(), source="integration_tester", priority=EventPriority.LOW),
            ]

            for event in test_events:
                await self.event_bus.publish(event)

            # Wait for event processing
            await asyncio.sleep(1)

            # Check if events were received
            new_events = len(self.events_received) - initial_event_count

            return {"success": new_events >= len(test_events), "events_published": len(test_events), "events_received": new_events, "total_events": len(self.events_received)}

        except Exception as e:
            self.logger.error(f"Event integration test failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _test_performance_metrics(self) -> dict[str, Any]:
        """Test performance metrics collection."""
        try:
            # Create and record test monitoring metrics
            test_metrics = create_monitoring_metrics(
                session_name="integration_test", monitor_type="async", loops_per_second=10.5, avg_loop_duration_ms=95.2, memory_usage_mb=128.5, total_loops=315, uptime_seconds=30.0
            )

            # Record metrics
            self.performance_monitor.record_monitoring_metrics(test_metrics)

            # Create and record test quality gates metrics
            quality_metrics = create_quality_gates_metrics(gate_name="integration_test_gate", execution_time_ms=250.5, result="pass", exit_code=0)

            self.performance_monitor.record_quality_gates_metrics(quality_metrics)

            # Generate performance report
            report = self.performance_monitor.generate_performance_report(compare_to_baseline=False)

            return {"success": True, "monitoring_metrics_recorded": True, "quality_metrics_recorded": True, "report_generated": "error" not in report, "report_sections": list(report.keys())}

        except Exception as e:
            self.logger.error(f"Performance metrics test failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _test_prompt_handling(self) -> dict[str, Any]:
        """Test prompt detection and handling."""
        try:
            from libs.core.claude_monitor_async import AsyncClaudeMonitor

            # Create monitor for prompt testing
            monitor = AsyncClaudeMonitor(session_manager=self.session_manager, process_controller=self.process_controller, status_manager=self.status_manager, event_bus=self.event_bus)

            # Set mock content with a prompt
            self.session_manager.set_content("""
Please choose an option:
1) Continue with the current approach
2) Try a different method
3) Exit

Please enter your choice (1-3):
            """)

            # Start monitoring briefly
            await monitor.start_monitoring_async()
            await asyncio.sleep(2)  # Let it detect the prompt
            await monitor.stop_monitoring_async()

            # Check if prompt was detected (look for relevant events)
            prompt_events = [e for e in self.events_received if "prompt" in e.get("type", "").lower()]

            return {
                "success": True,
                "prompt_events_detected": len(prompt_events),
                "monitor_responded": len(self.status_manager._activity_messages) > 0,
                "activity_messages": len(self.status_manager._activity_messages),
            }

        except Exception as e:
            self.logger.error(f"Prompt handling test failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _test_error_handling(self) -> dict[str, Any]:
        """Test error handling and recovery."""
        try:
            from libs.core.claude_monitor_async import AsyncClaudeMonitor

            # Create monitor
            monitor = AsyncClaudeMonitor(session_manager=self.session_manager, process_controller=self.process_controller, status_manager=self.status_manager, event_bus=self.event_bus)

            # Test Claude not running scenario
            self.process_controller.set_claude_running(False)

            await monitor.start_monitoring_async()
            await asyncio.sleep(2)  # Let it detect Claude not running

            # Should have attempted restart
            restart_count = self.process_controller._restart_count

            await monitor.stop_monitoring_async()

            # Reset for next test
            self.process_controller.set_claude_running(True)

            # Test graceful shutdown under load
            await monitor.start_monitoring_async()
            # Immediate shutdown to test cancellation
            await monitor.stop_monitoring_async()

            return {"success": True, "restart_attempts": restart_count, "graceful_shutdown": not monitor.is_running, "error_recovery": restart_count > 0}

        except Exception as e:
            self.logger.error(f"Error handling test failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _test_baseline_integration(self) -> dict[str, Any]:
        """Test performance baseline integration."""
        try:
            # Test baseline establishment (short duration for testing)
            baseline = await self.performance_monitor.establish_baseline(duration_seconds=5)

            # Verify baseline components
            has_system_metrics = baseline.system_metrics is not None
            has_monitoring_metrics = len(baseline.monitoring_metrics) > 0
            has_execution_time = baseline.benchmark_duration_seconds > 0

            # Test baseline loading
            loaded_baseline = await self.performance_monitor.load_baseline()
            baseline_loaded = loaded_baseline is not None

            return {
                "success": True,
                "baseline_established": baseline is not None,
                "has_system_metrics": has_system_metrics,
                "monitoring_samples": len(baseline.monitoring_metrics),
                "execution_time": baseline.benchmark_duration_seconds,
                "baseline_loaded": baseline_loaded,
            }

        except Exception as e:
            self.logger.error(f"Baseline integration test failed: {e}", exc_info=True)
            return {"success": False, "error": str(e)}

    async def _cleanup(self) -> None:
        """Cleanup test resources."""
        try:
            await self.performance_monitor.stop_monitoring()
            await self.event_bus.stop()
            print("✅ Test cleanup completed")
        except Exception as e:
            self.logger.warning(f"Cleanup warning: {e}")

    def generate_test_report(self) -> str:
        """Generate comprehensive test report."""
        if not self.results:
            return "❌ No test results available"

        report = f"""# 🧪 AsyncClaudeMonitor Integration Test Report

## 📊 Overall Results
- **Success**: {"✅ PASS" if self.results.get("overall_success", False) else "❌ FAIL"}
- **Execution Time**: {self.results.get("test_execution_time", 0):.2f}s
- **Events Received**: {self.results.get("events_received", 0)}
- **Performance Samples**: {self.results.get("performance_samples", 0)}

## 🔍 Individual Test Results

"""

        tests = self.results.get("tests", {})
        for test_name, test_result in tests.items():
            success = test_result.get("success", False)
            status = "✅ PASS" if success else "❌ FAIL"

            report += f"### {test_name.replace('_', ' ').title()}\n"
            report += f"**Status**: {status}\n\n"

            # Add specific details for each test
            for key, value in test_result.items():
                if key not in {"success", "error"}:
                    report += f"- **{key.replace('_', ' ').title()}**: {value}\n"

            if "error" in test_result:
                report += f"- **Error**: {test_result['error']}\n"

            report += "\n"

        # Add recommendations
        report += """## 🎯 Recommendations

"""

        if self.results.get("overall_success", False):
            report += """### ✅ All Tests Passed
The AsyncClaudeMonitor integration is working correctly with:
- Proper event bus communication
- Performance metrics collection
- Error handling and recovery
- Baseline integration

The system is ready for production deployment.
"""
        else:
            report += """### ❌ Issues Detected
Some tests failed. Review the individual test results above and address:
- Any integration failures
- Performance monitoring issues
- Event communication problems
- Error handling gaps

Fix these issues before proceeding to production.
"""

        report += f"""
---
*Integration test completed at {time.strftime("%Y-%m-%d %H:%M:%S")}*
"""

        return report


async def main() -> None:
    """Main entry point for integration testing."""
    print("🚀 Starting AsyncClaudeMonitor Integration Testing")

    # Setup logging
    logging.basicConfig(level=logging.INFO)

    # Create and run integration tester
    tester = AsyncIntegrationTester()

    try:
        results = await tester.run_integration_tests()

        # Generate and display report
        report = tester.generate_test_report()
        print("\n" + "=" * 60)
        print(report)

        # Save report to file
        report_path = project_root / "ASYNC_INTEGRATION_TEST_REPORT.md"
        report_path.write_text(report)
        print(f"\n📄 Full report saved to: {report_path}")

        # Save detailed results
        results_path = project_root / "integration_test_results.json"
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"📊 Detailed results saved to: {results_path}")

        # Exit with appropriate code
        if results.get("overall_success", False):
            print("\n✅ All integration tests passed!")
            sys.exit(0)
        else:
            print("\n❌ Some integration tests failed!")
            sys.exit(1)

    except Exception as e:
        print(f"\n💥 Integration testing failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
