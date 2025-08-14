#!/usr/bin/env python3

# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""Async-first Claude monitoring system integrated with AsyncEventBus.

This module provides a high-performance, event-driven Claude monitoring system
that replaces the thread-based approach with native async operations. It integrates
seamlessly with the AsyncEventBus for decoupled, reactive system communication.

Key Improvements:
- Native async operation without separate threads
- Event-driven architecture integration
- Non-blocking I/O operations
- Performance monitoring and metrics
- Graceful error handling and recovery
"""

import asyncio
import logging
import time
from collections import deque
from typing import Any, cast

import psutil

from libs.ai.adaptive_response import AdaptiveConfig, AdaptiveResponse
from libs.automation.automation_manager import AutomationManager
from libs.dashboard.health_calculator import HealthCalculator
from libs.logging.async_logger import AsyncLogger, LogLevel

from .async_event_bus import AsyncEventBus, Event, EventPriority, EventType, get_event_bus
from .content_collector import ClaudeContentCollector
from .prompt_detector import ClaudePromptDetector, PromptInfo, PromptType


class AsyncClaudeMonitor:
    """High-performance async Claude monitoring system.

    This class provides event-driven Claude monitoring with non-blocking operations,
    integrated performance metrics, and seamless AsyncEventBus communication.
    """

    def __init__(
        self,
        session_manager: object,
        process_controller: object,
        status_manager: object,
        event_bus: AsyncEventBus | None = None,
    ) -> None:
        """Initialize the AsyncClaudeMonitor.

        Args:
            session_manager: Session management interface
            process_controller: Process control interface
            status_manager: Status management interface
            event_bus: Optional event bus instance (uses global if None)
        """
        self.session_manager = session_manager
        self.process_controller = process_controller
        self.status_manager = status_manager
        self.session_name = getattr(session_manager, "session_name", "unknown")

        # Event-driven architecture
        self.event_bus = event_bus or get_event_bus()

        # Monitoring state
        self.is_running = False
        self._monitor_task: asyncio.Task | None = None
        self._cleanup_task: asyncio.Task | None = None

        # Performance monitoring
        self._loop_count = 0
        self._start_time = 0.0
        self._last_performance_report = 0.0
        self._performance_interval = 60.0  # Report performance every 60 seconds

        # Enhanced component response time tracking
        self._component_timings: dict[str, deque] = {
            "content_capture": deque(maxlen=100),
            "claude_status_check": deque(maxlen=100),
            "prompt_detection": deque(maxlen=100),
            "content_processing": deque(maxlen=100),
            "response_sending": deque(maxlen=100),
            "automation_analysis": deque(maxlen=100),
        }
        self._component_peak_times: dict[str, float] = {}
        self._component_error_counts: dict[str, int] = {component: 0 for component in self._component_timings}

        # Enhanced memory usage tracking per component
        self._component_memory_usage: dict[str, deque] = {component: deque(maxlen=50) for component in self._component_timings}
        self._component_peak_memory: dict[str, float] = {}
        self._baseline_memory_mb: float = 0.0

        # Enhanced CPU utilization tracking per component
        self._component_cpu_usage: dict[str, deque] = {component: deque(maxlen=50) for component in self._component_timings}
        self._component_peak_cpu: dict[str, float] = {}
        self._baseline_cpu_percent: float = 0.0
        self._last_cpu_times: dict = {}

        # Process monitoring for memory and CPU tracking
        self._process = psutil.Process()
        self._system_cpu_count = psutil.cpu_count()

        # Thread pool monitoring for async task CPU usage
        self._thread_pool_executor = None
        self._async_task_cpu_usage: dict[str, list[float]] = {}

        # Network I/O pattern tracking
        self._component_network_io: dict[str, deque] = {component: deque(maxlen=50) for component in self._component_timings}
        self._component_network_patterns: dict[str, dict] = {}
        self._baseline_network_counters = None
        self._last_network_counters = None

        # Auto-response settings (backward compatibility)
        self.is_auto_next_enabled = True
        self.yn_mode = "Auto"
        self.yn_response = "y"
        self.mode12 = "Auto"
        self.mode12_response = "1"
        self.mode123 = "Auto"
        self.mode123_response = "1"

        # Prompt detection and content analysis
        self.prompt_detector = ClaudePromptDetector()
        self.content_collector = ClaudeContentCollector(self.session_name)
        self.current_prompt: PromptInfo | None = None
        self.waiting_for_input = False
        self._last_content = ""

        # AI-powered adaptive response system
        self.adaptive_response = AdaptiveResponse(
            config=AdaptiveConfig(
                min_confidence_threshold=0.7,
                learning_enabled=True,
                auto_response_enabled=True,
                response_delay_ms=1500,
            ),
        )

        # Context-aware automation system
        self.automation_manager = AutomationManager(project_path=None)

        # Project health monitoring system
        self.health_calculator = HealthCalculator(project_path=None)

        # High-performance async logging system
        self.async_logger: AsyncLogger | None = None

        # Logger setup
        self.logger = logging.getLogger(f"yesman.async_claude_monitor.{self.session_name}")

        # Event subscriptions
        self._setup_event_subscriptions()

    def _setup_event_subscriptions(self) -> None:
        """Set up event bus subscriptions for system events."""
        self.event_bus.subscribe(EventType.SYSTEM_SHUTDOWN, self._handle_system_shutdown)

    def _record_component_timing(self, component: str, duration_ms: float, success: bool = True) -> None:
        """Record timing metrics for a specific component.

        Args:
            component: Component name
            duration_ms: Duration in milliseconds
            success: Whether the operation was successful
        """
        if component in self._component_timings:
            self._component_timings[component].append(duration_ms)

            # Update peak time
            if duration_ms > self._component_peak_times.get(component, 0):
                self._component_peak_times[component] = duration_ms

            # Track errors
            if not success:
                self._component_error_counts[component] += 1

    def _record_component_memory(self, component: str, memory_delta_mb: float) -> None:
        """Record memory usage for a specific component.

        Args:
            component: Component name
            memory_delta_mb: Memory change in MB (positive for increase, negative for decrease)
        """
        if component in self._component_memory_usage:
            self._component_memory_usage[component].append(memory_delta_mb)

            # Update peak memory usage
            if abs(memory_delta_mb) > abs(self._component_peak_memory.get(component, 0)):
                self._component_peak_memory[component] = memory_delta_mb

    def _record_component_cpu(self, component: str, cpu_percent: float) -> None:
        """Record CPU usage for a specific component.

        Args:
            component: Component name
            cpu_percent: CPU usage percentage for this component
        """
        if component in self._component_cpu_usage:
            self._component_cpu_usage[component].append(cpu_percent)

            # Update peak CPU usage
            if cpu_percent > self._component_peak_cpu.get(component, 0):
                self._component_peak_cpu[component] = cpu_percent

    def _record_component_network_io(self, component: str, bytes_sent: int, bytes_recv: int, duration_ms: float) -> None:
        """Record network I/O metrics for a specific component.

        Args:
            component: Component name
            bytes_sent: Bytes sent during component execution
            bytes_recv: Bytes received during component execution
            duration_ms: Duration of the operation in milliseconds
        """
        if component in self._component_network_io:
            io_data = {
                "bytes_sent": bytes_sent,
                "bytes_recv": bytes_recv,
                "total_bytes": bytes_sent + bytes_recv,
                "duration_ms": duration_ms,
                "throughput_mbps": ((bytes_sent + bytes_recv) / (1024 * 1024)) / (duration_ms / 1000) if duration_ms > 0 else 0,
                "timestamp": time.time(),
            }
            self._component_network_io[component].append(io_data)

            # Update network patterns for this component
            if component not in self._component_network_patterns:
                self._component_network_patterns[component] = {"peak_throughput_mbps": 0, "total_bytes_sent": 0, "total_bytes_recv": 0, "network_active_operations": 0}

            patterns = self._component_network_patterns[component]
            patterns["total_bytes_sent"] += bytes_sent
            patterns["total_bytes_recv"] += bytes_recv

            patterns["peak_throughput_mbps"] = max(patterns["peak_throughput_mbps"], io_data["throughput_mbps"])

            if bytes_sent > 0 or bytes_recv > 0:
                patterns["network_active_operations"] += 1

    def _measure_memory_usage(self) -> float:
        """Measure current memory usage in MB.

        Returns:
            Current memory usage in MB
        """
        try:
            memory_info = self._process.memory_info()
            return memory_info.rss / (1024 * 1024)  # Convert bytes to MB
        except Exception:
            self.logger.exception("Error measuring memory usage")
            return 0.0

    def _measure_cpu_usage(self) -> float:
        """Measure current CPU usage percentage.

        Returns:
            Current CPU usage percentage (0-100, can exceed 100 for multi-core)
        """
        try:
            # Get process CPU percentage (interval=None uses cached values for efficiency)
            cpu_percent = self._process.cpu_percent(interval=None)
            return cpu_percent
        except Exception:
            self.logger.exception("Error measuring CPU usage")
            return 0.0

    def _calculate_component_cpu_delta(self, component: str, start_time: float, end_time: float) -> float:
        """Calculate CPU usage delta for a component based on execution time.

        Args:
            component: Component name
            start_time: Start time (perf_counter)
            end_time: End time (perf_counter)

        Returns:
            Estimated CPU usage percentage for this component
        """
        try:
            # Simple estimation: CPU usage = (execution_time / total_time) * system_cpu_usage
            execution_duration = end_time - start_time

            # Get system-wide CPU usage as baseline
            system_cpu = psutil.cpu_percent(interval=None)

            # Estimate component CPU usage
            # This is a rough approximation - actual CPU usage depends on thread scheduling
            if execution_duration > 0.001:  # Only calculate for operations taking > 1ms
                estimated_cpu = min(system_cpu, (execution_duration / 1.0) * system_cpu)
                return estimated_cpu

            return 0.0
        except Exception:
            self.logger.exception("Error calculating component CPU delta")
            return 0.0

    def _measure_network_io_delta(self) -> tuple[int, int]:
        """Measure network I/O delta since last measurement.

        Returns:
            Tuple of (bytes_sent_delta, bytes_recv_delta)
        """
        try:
            current_counters = psutil.net_io_counters()

            if self._last_network_counters is None:
                self._last_network_counters = current_counters
                return (0, 0)

            bytes_sent_delta = current_counters.bytes_sent - self._last_network_counters.bytes_sent
            bytes_recv_delta = current_counters.bytes_recv - self._last_network_counters.bytes_recv

            self._last_network_counters = current_counters

            return (max(0, bytes_sent_delta), max(0, bytes_recv_delta))

        except Exception:
            self.logger.exception("Error measuring network I/O delta")
            return (0, 0)

    def _get_component_metrics(self) -> dict[str, dict[str, float]]:
        """Get comprehensive component timing and memory metrics."""
        metrics = {}

        for component, timings in self._component_timings.items():
            # Timing metrics
            if timings:
                timings_list = list(timings)
                timing_metrics = {
                    "average_ms": sum(timings_list) / len(timings_list),
                    "median_ms": sorted(timings_list)[len(timings_list) // 2],
                    "p95_ms": sorted(timings_list)[int(len(timings_list) * 0.95)],
                    "p99_ms": sorted(timings_list)[int(len(timings_list) * 0.99)] if len(timings_list) > 10 else timings_list[-1],
                    "peak_ms": self._component_peak_times.get(component, 0),
                    "sample_count": len(timings_list),
                    "error_count": self._component_error_counts[component],
                    "error_rate": self._component_error_counts[component] / len(timings_list) if timings_list else 0,
                }
            else:
                timing_metrics = {
                    "average_ms": 0,
                    "median_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                    "peak_ms": 0,
                    "sample_count": 0,
                    "error_count": 0,
                    "error_rate": 0,
                }

            # Memory metrics
            memory_deltas = self._component_memory_usage.get(component, [])
            if memory_deltas:
                memory_list = list(memory_deltas)
                positive_deltas = [m for m in memory_list if m > 0]
                memory_metrics = {
                    "avg_memory_delta_mb": sum(memory_list) / len(memory_list),
                    "peak_memory_delta_mb": self._component_peak_memory.get(component, 0),
                    "memory_allocations": len(positive_deltas),
                    "avg_allocation_size_mb": sum(positive_deltas) / len(positive_deltas) if positive_deltas else 0,
                    "memory_sample_count": len(memory_list),
                }
            else:
                memory_metrics = {
                    "avg_memory_delta_mb": 0,
                    "peak_memory_delta_mb": 0,
                    "memory_allocations": 0,
                    "avg_allocation_size_mb": 0,
                    "memory_sample_count": 0,
                }

            # CPU metrics
            cpu_usage = self._component_cpu_usage.get(component, [])
            if cpu_usage:
                cpu_list = list(cpu_usage)
                cpu_metrics = {
                    "avg_cpu_percent": sum(cpu_list) / len(cpu_list),
                    "peak_cpu_percent": self._component_peak_cpu.get(component, 0),
                    "cpu_utilization_p95": sorted(cpu_list)[int(len(cpu_list) * 0.95)] if len(cpu_list) > 5 else max(cpu_list) if cpu_list else 0,
                    "cpu_sample_count": len(cpu_list),
                    "cpu_efficiency": (sum(cpu_list) / len(cpu_list)) / self._system_cpu_count if cpu_list and self._system_cpu_count else 0,
                }
            else:
                cpu_metrics = {
                    "avg_cpu_percent": 0,
                    "peak_cpu_percent": 0,
                    "cpu_utilization_p95": 0,
                    "cpu_sample_count": 0,
                    "cpu_efficiency": 0,
                }

            # Network I/O metrics
            network_io_data = self._component_network_io.get(component, [])
            network_patterns = self._component_network_patterns.get(component, {})
            if network_io_data:
                io_list = list(network_io_data)
                total_sent = sum(io["bytes_sent"] for io in io_list)
                total_recv = sum(io["bytes_recv"] for io in io_list)
                throughputs = [io["throughput_mbps"] for io in io_list if io["throughput_mbps"] > 0]

                network_metrics = {
                    "total_bytes_sent": total_sent,
                    "total_bytes_recv": total_recv,
                    "total_network_bytes": total_sent + total_recv,
                    "avg_throughput_mbps": sum(throughputs) / len(throughputs) if throughputs else 0,
                    "peak_throughput_mbps": network_patterns.get("peak_throughput_mbps", 0),
                    "network_operations": len(io_list),
                    "network_active_ops": network_patterns.get("network_active_operations", 0),
                    "network_utilization": (len(throughputs) / len(io_list)) * 100 if io_list else 0,
                }
            else:
                network_metrics = {
                    "total_bytes_sent": 0,
                    "total_bytes_recv": 0,
                    "total_network_bytes": 0,
                    "avg_throughput_mbps": 0,
                    "peak_throughput_mbps": 0,
                    "network_operations": 0,
                    "network_active_ops": 0,
                    "network_utilization": 0,
                }

            # Combine timing, memory, CPU, and network metrics
            metrics[component] = {**timing_metrics, **memory_metrics, **cpu_metrics, **network_metrics}

        return metrics

    async def _handle_system_shutdown(self, event: Event) -> None:
        """Handle system shutdown events gracefully."""
        self.logger.info("Received system shutdown event, stopping monitor")
        await self.stop_monitoring_async()

    # Core monitoring methods
    async def start_monitoring_async(self) -> bool:
        """Start the async monitoring loop.

        Returns:
            True if monitoring started successfully, False otherwise
        """
        if not cast("Any", self.session_manager).get_claude_pane():
            await self._publish_status_event("error", "Cannot start: No Claude pane in session")
            return False

        if self.is_running:
            await self._publish_status_event("warning", "Monitor already running")
            return False

        try:
            self.is_running = True
            self._start_time = time.time()
            self._loop_count = 0

            # Establish baseline memory, CPU, and network usage
            self._baseline_memory_mb = self._measure_memory_usage()
            self._baseline_cpu_percent = psutil.cpu_percent(interval=1.0)  # Get initial CPU reading
            self._baseline_network_counters = psutil.net_io_counters()
            self._last_network_counters = self._baseline_network_counters

            await self._start_async_logging()

            # Start the main monitoring task
            self._monitor_task = asyncio.create_task(self._monitor_loop_async())

            # Start cleanup task for maintenance
            self._cleanup_task = asyncio.create_task(self._maintenance_loop())

            await self._publish_status_event("success", f"Started async Claude monitor for {self.session_name}")

            # Publish monitoring started event
            await self.event_bus.publish(
                Event(
                    type=EventType.SESSION_STARTED,
                    data={"session_name": self.session_name, "monitor_type": "async_claude_monitor", "auto_next_enabled": self.is_auto_next_enabled},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.HIGH,
                )
            )

            return True

        except Exception as e:
            self.is_running = False
            await self._publish_status_event("error", f"Failed to start Claude monitor: {e}")
            self.logger.error("Failed to start Claude monitor: %s", e, exc_info=True)
            return False

    async def stop_monitoring_async(self) -> bool:
        """Stop the async monitoring loop gracefully.

        Returns:
            True if monitoring stopped successfully, False otherwise
        """
        if not self.is_running:
            await self._publish_status_event("warning", "Claude monitor not running")
            return False

        self.logger.info("Stopping async Claude monitor...")
        self.is_running = False

        # Cancel monitoring tasks
        tasks_to_cancel = []
        if self._monitor_task and not self._monitor_task.done():
            tasks_to_cancel.append(self._monitor_task)
        if self._cleanup_task and not self._cleanup_task.done():
            tasks_to_cancel.append(self._cleanup_task)

        if tasks_to_cancel:
            # Cancel tasks gracefully
            for task in tasks_to_cancel:
                task.cancel()

            # Wait for cancellation with timeout
            try:
                await asyncio.wait_for(asyncio.gather(*tasks_to_cancel, return_exceptions=True), timeout=5.0)
            except TimeoutError:
                self.logger.warning("Monitor tasks cancellation timed out")

        # Stop async logging
        await self._stop_async_logging()

        # Publish monitoring stopped event
        await self.event_bus.publish(
            Event(
                type=EventType.SESSION_STOPPED,
                data={"session_name": self.session_name, "monitor_type": "async_claude_monitor", "uptime_seconds": time.time() - self._start_time, "total_loops": self._loop_count},
                timestamp=time.time(),
                source="async_claude_monitor",
                correlation_id=self.session_name,
                priority=EventPriority.HIGH,
            )
        )

        await self._publish_status_event("info", f"Stopped async Claude monitor for {self.session_name}")
        return True

    async def _monitor_loop_async(self) -> None:
        """Main async monitoring loop - non-blocking and event-driven.

        This is the core performance-critical method that replaces the
        thread-based monitoring with pure async operations.
        """
        if not cast("Any", self.session_manager).get_claude_pane():
            self.logger.error("Cannot start monitoring: no Claude pane for %s", self.session_name)
            self.is_running = False
            return

        self.logger.info("Starting async monitoring loop for %s", self.session_name)

        try:
            while self.is_running:
                loop_start = time.perf_counter()

                try:
                    # Async content capture (non-blocking) with comprehensive monitoring
                    content_start = time.perf_counter()
                    memory_before = self._measure_memory_usage()
                    net_sent_before, net_recv_before = self._measure_network_io_delta()
                    content = await self._capture_pane_content_async()
                    content_end = time.perf_counter()
                    memory_after = self._measure_memory_usage()
                    net_sent_after, net_recv_after = self._measure_network_io_delta()

                    content_duration = (content_end - content_start) * 1000
                    memory_delta = memory_after - memory_before
                    cpu_usage = self._calculate_component_cpu_delta("content_capture", content_start, content_end)

                    self._record_component_timing("content_capture", content_duration, True)
                    self._record_component_memory("content_capture", memory_delta)
                    self._record_component_cpu("content_capture", cpu_usage)
                    self._record_component_network_io("content_capture", net_sent_after, net_recv_after, content_duration)

                    # Check Claude process status asynchronously with comprehensive monitoring
                    status_start = time.perf_counter()
                    memory_before = self._measure_memory_usage()
                    net_sent_before, net_recv_before = self._measure_network_io_delta()
                    claude_running = await self._check_claude_status_async()
                    status_end = time.perf_counter()
                    memory_after = self._measure_memory_usage()
                    net_sent_after, net_recv_after = self._measure_network_io_delta()

                    status_duration = (status_end - status_start) * 1000
                    memory_delta = memory_after - memory_before
                    cpu_usage = self._calculate_component_cpu_delta("claude_status_check", status_start, status_end)

                    self._record_component_timing("claude_status_check", status_duration, claude_running)
                    self._record_component_memory("claude_status_check", memory_delta)
                    self._record_component_cpu("claude_status_check", cpu_usage)
                    self._record_component_network_io("claude_status_check", net_sent_after, net_recv_after, status_duration)

                    if not claude_running:
                        await self._handle_claude_not_running()
                        continue

                    # Process content for prompts and automation with comprehensive monitoring
                    process_start = time.perf_counter()
                    memory_before = self._measure_memory_usage()
                    net_sent_before, net_recv_before = self._measure_network_io_delta()
                    await self._process_content_async(content)
                    process_end = time.perf_counter()
                    memory_after = self._measure_memory_usage()
                    net_sent_after, net_recv_after = self._measure_network_io_delta()

                    process_duration = (process_end - process_start) * 1000
                    memory_delta = memory_after - memory_before
                    cpu_usage = self._calculate_component_cpu_delta("content_processing", process_start, process_end)

                    self._record_component_timing("content_processing", process_duration, True)
                    self._record_component_memory("content_processing", memory_delta)
                    self._record_component_cpu("content_processing", cpu_usage)
                    self._record_component_network_io("content_processing", net_sent_after, net_recv_after, process_duration)

                    # Update performance metrics
                    self._loop_count += 1

                    # Report performance metrics periodically
                    if time.time() - self._last_performance_report > self._performance_interval:
                        await self._report_performance_metrics()
                        self._last_performance_report = time.time()

                except asyncio.CancelledError:
                    self.logger.info("Monitor loop cancelled")
                    break
                except Exception as e:
                    self.logger.error("Error in monitoring loop: %s", e, exc_info=True)

                    # Publish error event
                    await self.event_bus.publish(
                        Event(
                            type=EventType.CLAUDE_ERROR,
                            data={"session_name": self.session_name, "error": str(e), "error_type": type(e).__name__},
                            timestamp=time.time(),
                            source="async_claude_monitor",
                            correlation_id=self.session_name,
                            priority=EventPriority.HIGH,
                        )
                    )

                    # Wait longer on errors to prevent tight error loops
                    await asyncio.sleep(5.0)
                    continue

                # Optimal sleep duration - non-blocking
                loop_duration = time.perf_counter() - loop_start
                optimal_sleep = max(0.1, 1.0 - loop_duration)  # Aim for ~1 second intervals
                await asyncio.sleep(optimal_sleep)

        except asyncio.CancelledError:
            self.logger.info("Async monitoring loop cancelled")
        except Exception as e:
            self.logger.error("Critical error in monitoring loop: %s", e, exc_info=True)
        finally:
            self.is_running = False
            self.logger.info("Async monitoring loop stopped")

    async def _capture_pane_content_async(self) -> str:
        """Capture pane content asynchronously.

        Returns:
            Current pane content as string
        """
        try:
            # Run the potentially blocking pane capture in a thread pool
            loop = asyncio.get_event_loop()
            content = await loop.run_in_executor(None, cast("Any", self.session_manager).capture_pane_content)
            return cast(str, content)
        except Exception:
            self.logger.exception("Error capturing pane content")
            return ""

    async def _check_claude_status_async(self) -> bool:
        """Check Claude process status asynchronously.

        Returns:
            True if Claude is running, False otherwise
        """
        try:
            # Run potentially blocking process check in thread pool
            loop = asyncio.get_event_loop()
            is_running = await loop.run_in_executor(None, cast("Any", self.process_controller).is_claude_running)
            return cast(bool, is_running)
        except Exception:
            self.logger.exception("Error checking Claude status")
            return False

    async def _handle_claude_not_running(self) -> None:
        """Handle the case when Claude is not running."""
        if self.is_auto_next_enabled:
            self.logger.info("Claude not running, attempting auto-restart")

            await self._publish_activity_event("🔄 Auto-restarting Claude...")

            try:
                # Run restart in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                await loop.run_in_executor(None, cast("Any", self.process_controller).restart_claude_pane)

                # Publish restart event
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_STATUS_CHANGED,
                        data={"session_name": self.session_name, "status": "restarted", "auto_restart": True},
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.HIGH,
                    )
                )

            except Exception as e:
                self.logger.exception("Failed to restart Claude")
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_ERROR,
                        data={"session_name": self.session_name, "error": f"Restart failed: {e}", "auto_restart_failed": True},
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.CRITICAL,
                    )
                )
        else:
            await self._publish_status_event("warning", "Claude not running. Auto-restart disabled.")

    async def _process_content_async(self, content: str) -> None:
        """Process pane content for prompts and automation opportunities.

        Args:
            content: Current pane content
        """
        # Check for prompts with comprehensive monitoring
        prompt_start = time.perf_counter()
        memory_before = self._measure_memory_usage()
        net_sent_before, net_recv_before = self._measure_network_io_delta()
        prompt_info = await self._check_for_prompt_async(content)
        prompt_end = time.perf_counter()
        memory_after = self._measure_memory_usage()
        net_sent_after, net_recv_after = self._measure_network_io_delta()

        prompt_duration = (prompt_end - prompt_start) * 1000
        memory_delta = memory_after - memory_before
        cpu_usage = self._calculate_component_cpu_delta("prompt_detection", prompt_start, prompt_end)

        self._record_component_timing("prompt_detection", prompt_duration, prompt_info is not None)
        self._record_component_memory("prompt_detection", memory_delta)
        self._record_component_cpu("prompt_detection", cpu_usage)
        self._record_component_network_io("prompt_detection", net_sent_after, net_recv_after, prompt_duration)

        if prompt_info:
            # Handle prompt response with comprehensive monitoring
            response_start = time.perf_counter()
            memory_before = self._measure_memory_usage()
            net_sent_before, net_recv_before = self._measure_network_io_delta()
            await self._handle_prompt_async(prompt_info, content)
            response_end = time.perf_counter()
            memory_after = self._measure_memory_usage()
            net_sent_after, net_recv_after = self._measure_network_io_delta()

            response_duration = (response_end - response_start) * 1000
            memory_delta = memory_after - memory_before
            cpu_usage = self._calculate_component_cpu_delta("response_sending", response_start, response_end)

            self._record_component_timing("response_sending", response_duration, True)
            self._record_component_memory("response_sending", memory_delta)
            self._record_component_cpu("response_sending", cpu_usage)
            self._record_component_network_io("response_sending", net_sent_after, net_recv_after, response_duration)
        elif self.waiting_for_input:
            await self._publish_activity_event("⏳ Waiting for user input...")
        else:
            # Clear prompt state if no longer waiting
            self._clear_prompt_state()

        # Update AI patterns periodically
        await self.adaptive_response.update_patterns()

        # Analyze content for automation contexts (only if content changed)
        if content != self._last_content and len(content.strip()) > 0:
            automation_start = time.perf_counter()
            memory_before = self._measure_memory_usage()
            net_sent_before, net_recv_before = self._measure_network_io_delta()
            await self._analyze_automation_context(content)
            await self._collect_content_interaction(content, prompt_info)
            automation_end = time.perf_counter()
            memory_after = self._measure_memory_usage()
            net_sent_after, net_recv_after = self._measure_network_io_delta()

            automation_duration = (automation_end - automation_start) * 1000
            memory_delta = memory_after - memory_before
            cpu_usage = self._calculate_component_cpu_delta("automation_analysis", automation_start, automation_end)

            self._record_component_timing("automation_analysis", automation_duration, True)
            self._record_component_memory("automation_analysis", memory_delta)
            self._record_component_cpu("automation_analysis", cpu_usage)
            self._record_component_network_io("automation_analysis", net_sent_after, net_recv_after, automation_duration)
            await self._publish_activity_event("📝 Content updated")
            self._last_content = content

    async def _check_for_prompt_async(self, content: str) -> PromptInfo | None:
        """Check for prompts in content asynchronously.

        Args:
            content: Content to analyze

        Returns:
            PromptInfo if prompt detected, None otherwise
        """
        try:
            # Run prompt detection in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            prompt_info = await loop.run_in_executor(None, self.prompt_detector.detect_prompt, content)

            if prompt_info:
                self.current_prompt = prompt_info
                self.waiting_for_input = True
                self.logger.info("Prompt detected: %s - %s", prompt_info.type.value, prompt_info.question)

                # Publish prompt detection event
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_PROMPT_SENT,
                        data={
                            "session_name": self.session_name,
                            "prompt_type": prompt_info.type.value,
                            "question": prompt_info.question,
                            "options": prompt_info.options,
                            "confidence": prompt_info.confidence,
                        },
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.NORMAL,
                    )
                )
            else:
                # Check if still waiting based on content patterns
                self.waiting_for_input = await loop.run_in_executor(None, self.prompt_detector.is_waiting_for_input, content)

            return prompt_info

        except Exception:
            self.logger.exception("Error checking for prompts")
            return None

    async def _handle_prompt_async(self, prompt_info: PromptInfo, content: str) -> None:
        """Handle detected prompts with AI-powered and fallback responses.

        Args:
            prompt_info: Detected prompt information
            content: Current content context
        """
        if not self.is_auto_next_enabled:
            await self._publish_activity_event(f"⏳ Waiting for input: {prompt_info.type.value}")
            return

        try:
            # Try AI-powered adaptive response first
            context = f"session:{self.session_name}, type:{prompt_info.type.value}"

            should_respond, ai_response, confidence = await self.adaptive_response.should_auto_respond(
                prompt_info.question,
                context,
                self.session_name,
            )

            if should_respond:
                success = await self._send_ai_response(prompt_info, ai_response, confidence, context)
                if success:
                    return

            # Fallback to pattern-based response
            if await self._auto_respond_to_selection_async(prompt_info):
                response = self._get_legacy_response(prompt_info)
                await self._send_legacy_response(prompt_info, response, context)
                return

            # No auto-response available
            await self._publish_activity_event(f"⏳ Waiting for input: {prompt_info.type.value}")

        except Exception as e:
            self.logger.exception("Error handling prompt")
            await self._publish_activity_event(f"❌ Error handling prompt: {e}")

    async def _send_ai_response(self, prompt_info: PromptInfo, response: str, confidence: float, context: str) -> bool:
        """Send AI-generated response and handle the result."""
        try:
            success = await self.adaptive_response.send_adaptive_response(
                prompt_info.question,
                response,
                confidence,
                context,
                self.session_name,
            )

            if success:
                # Send response to Claude
                await self._send_input_async(response)

                await self._publish_activity_event(f"🤖 AI auto-responded: '{response}' (confidence: {confidence:.2f})")
                await self._record_response_async(prompt_info.type.value, response, prompt_info.question)

                # Confirm success to adaptive system
                self.adaptive_response.confirm_response_success(
                    prompt_info.question,
                    response,
                    context,
                    self.session_name,
                    True,
                )

                # Publish successful response event
                await self.event_bus.publish(
                    Event(
                        type=EventType.CLAUDE_RESPONSE,
                        data={"session_name": self.session_name, "response": response, "response_type": "ai_adaptive", "confidence": confidence, "prompt_type": prompt_info.type.value},
                        timestamp=time.time(),
                        source="async_claude_monitor",
                        correlation_id=self.session_name,
                        priority=EventPriority.NORMAL,
                    )
                )

                self._clear_prompt_state()
                return True

        except Exception:
            self.logger.exception("Error sending AI response")

        return False

    async def _send_legacy_response(self, prompt_info: PromptInfo, response: str, context: str) -> None:
        """Send pattern-based legacy response."""
        try:
            await self._send_input_async(response)

            await self._publish_activity_event(f"✅ Legacy auto-responded: '{response}' to {prompt_info.type.value}")
            await self._record_response_async(prompt_info.type.value, response, prompt_info.question)

            # Learn from legacy response for future AI improvements
            self.adaptive_response.learn_from_manual_response(
                prompt_info.question,
                response,
                context,
                self.session_name,
            )

            # Publish legacy response event
            await self.event_bus.publish(
                Event(
                    type=EventType.CLAUDE_RESPONSE,
                    data={"session_name": self.session_name, "response": response, "response_type": "legacy_pattern", "prompt_type": prompt_info.type.value},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.NORMAL,
                )
            )

            self._clear_prompt_state()

        except Exception:
            self.logger.exception("Error sending legacy response")

    async def _send_input_async(self, input_text: str) -> None:
        """Send input to Claude process asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.process_controller).send_input, input_text)
        except Exception:
            self.logger.exception("Error sending input")
            raise

    async def _record_response_async(self, prompt_type: str, response: str, question: str) -> None:
        """Record response asynchronously."""
        try:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.status_manager).record_response, prompt_type, response, question)
        except Exception:
            self.logger.exception("Error recording response")

    async def _auto_respond_to_selection_async(self, prompt_info: PromptInfo) -> bool:
        """Check if we should auto-respond to selection prompts."""
        if not self.is_auto_next_enabled:
            return False

        try:
            # Run response logic in thread pool
            loop = asyncio.get_event_loop()
            should_respond = await loop.run_in_executor(None, self._should_auto_respond, prompt_info)
            return should_respond
        except Exception:
            self.logger.exception("Error checking auto-response")
            return False

    def _should_auto_respond(self, prompt_info: PromptInfo) -> bool:
        """Determine if we should auto-respond (runs in thread pool)."""
        try:
            return prompt_info.type in {
                PromptType.NUMBERED_SELECTION,
                PromptType.BINARY_CHOICE,
                PromptType.CONFIRMATION,
                PromptType.LOGIN_REDIRECT,
            }
        except Exception:
            return False

    async def _analyze_automation_context(self, content: str) -> None:
        """Analyze content for automation contexts."""
        try:
            loop = asyncio.get_event_loop()
            automation_contexts = await loop.run_in_executor(None, self.automation_manager.analyze_content_for_context, content, self.session_name)

            for auto_context in automation_contexts:
                if hasattr(auto_context, "context_type") and hasattr(auto_context, "confidence"):
                    self.logger.info(
                        "Automation context detected: %s (confidence: %.2f)",
                        auto_context.context_type.value,
                        auto_context.confidence,
                    )

                    # Publish automation context event
                    await self.event_bus.publish(
                        Event(
                            type=EventType.CUSTOM,
                            data={
                                "event_subtype": "automation_context_detected",
                                "session_name": self.session_name,
                                "context_type": auto_context.context_type.value,
                                "confidence": auto_context.confidence,
                            },
                            timestamp=time.time(),
                            source="async_claude_monitor",
                            correlation_id=self.session_name,
                            priority=EventPriority.LOW,
                        )
                    )

        except Exception:
            self.logger.exception("Error analyzing automation context")

    async def _collect_content_interaction(self, content: str, prompt_info: PromptInfo | None) -> None:
        """Collect content interaction for pattern analysis."""
        try:
            # Convert PromptInfo to dict for compatibility
            prompt_dict = None
            if prompt_info:
                prompt_dict = {
                    "type": prompt_info.type.value,
                    "question": prompt_info.question,
                    "options": prompt_info.options,
                    "confidence": prompt_info.confidence,
                }

            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, self.content_collector.collect_interaction, content, prompt_dict, None)
        except Exception:
            self.logger.exception("Error collecting content interaction")

    async def _maintenance_loop(self) -> None:
        """Background maintenance loop for cleanup and optimization."""
        maintenance_interval = 300.0  # 5 minutes

        try:
            while self.is_running:
                await asyncio.sleep(maintenance_interval)

                if not self.is_running:
                    break

                try:
                    # Cleanup old collections
                    loop = asyncio.get_event_loop()
                    cleaned_count = await loop.run_in_executor(
                        None,
                        self.content_collector.cleanup_old_files,
                        7,  # Keep 7 days
                    )

                    if cleaned_count > 0:
                        self.logger.info("Cleaned up %d old collection files", cleaned_count)

                    # Check Claude idle automation
                    if hasattr(self.status_manager, "last_activity_time"):
                        idle_context = await loop.run_in_executor(
                            None,
                            self.automation_manager.analyze_claude_idle,
                            cast("Any", self.status_manager).last_activity_time,
                            60,  # 60 second idle threshold
                        )

                        if idle_context and hasattr(idle_context, "confidence"):
                            self.logger.debug("Claude idle context: %.2f", idle_context.confidence)

                except Exception:
                    self.logger.exception("Error in maintenance loop")

        except asyncio.CancelledError:
            self.logger.info("Maintenance loop cancelled")

    async def _report_performance_metrics(self) -> None:
        """Report performance metrics to the event bus."""
        try:
            uptime = time.time() - self._start_time
            loops_per_second = self._loop_count / uptime if uptime > 0 else 0

            # Get component timing metrics
            component_metrics = self._get_component_metrics()

            # Get current memory usage and calculate growth
            current_memory_mb = self._measure_memory_usage()
            total_memory_growth = current_memory_mb - self._baseline_memory_mb

            metrics = {
                "session_name": self.session_name,
                "uptime_seconds": uptime,
                "total_loops": self._loop_count,
                "loops_per_second": loops_per_second,
                "is_running": self.is_running,
                "auto_next_enabled": self.is_auto_next_enabled,
                "waiting_for_input": self.waiting_for_input,
                "current_prompt_type": self.current_prompt.type.value if self.current_prompt else None,
                "component_response_times": component_metrics,
                "current_memory_mb": current_memory_mb,
                "baseline_memory_mb": self._baseline_memory_mb,
                "memory_growth_mb": total_memory_growth,
                "current_cpu_percent": self._measure_cpu_usage(),
                "baseline_cpu_percent": self._baseline_cpu_percent,
            }

            await self.event_bus.publish(
                Event(
                    type=EventType.PERFORMANCE_METRICS,
                    data={"component": "async_claude_monitor", "metrics": metrics},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.LOW,
                )
            )

            # Log detailed component performance
            current_memory_mb = self._measure_memory_usage()
            total_memory_growth = current_memory_mb - self._baseline_memory_mb
            self.logger.debug("Performance: %.2f loops/sec, %d loops, memory: %.1fMB (+%.1fMB from baseline)", loops_per_second, self._loop_count, current_memory_mb, total_memory_growth)

            # Log component bottlenecks (performance, memory, CPU, or network intensive)
            for component, stats in component_metrics.items():
                if stats["average_ms"] > 100 or abs(stats["avg_memory_delta_mb"]) > 5.0 or stats["avg_cpu_percent"] > 50.0 or stats["avg_throughput_mbps"] > 1.0:
                    self.logger.warning(
                        "Bottleneck in %s: avg=%.1fms, p95=%.1fms, errors=%d, mem=%.2fMB, cpu=%.1f%%, net=%.2fMB/s",
                        component,
                        stats["average_ms"],
                        stats["p95_ms"],
                        stats["error_count"],
                        stats["avg_memory_delta_mb"],
                        stats["avg_cpu_percent"],
                        stats["avg_throughput_mbps"],
                    )

        except Exception:
            self.logger.exception("Error reporting performance metrics")

    # Event publishing helpers
    async def _publish_status_event(self, status_type: str, message: str) -> None:
        """Publish status update event."""
        try:
            await self.event_bus.publish(
                Event(
                    type=EventType.DASHBOARD_UPDATE,
                    data={"update_type": "status", "status_type": status_type, "message": message, "session_name": self.session_name},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.NORMAL,
                )
            )

            # Also update status manager for backward compatibility
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.status_manager).update_status, f"[{status_type}]{message}[/]")
        except Exception:
            self.logger.exception("Error publishing status event")

    async def _publish_activity_event(self, message: str) -> None:
        """Publish activity update event."""
        try:
            await self.event_bus.publish(
                Event(
                    type=EventType.DASHBOARD_UPDATE,
                    data={"update_type": "activity", "message": message, "session_name": self.session_name},
                    timestamp=time.time(),
                    source="async_claude_monitor",
                    correlation_id=self.session_name,
                    priority=EventPriority.LOW,
                )
            )

            # Also update status manager for backward compatibility
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, cast("Any", self.status_manager).update_activity, message)
        except Exception:
            self.logger.exception("Error publishing activity event")

    # Utility methods (maintaining backward compatibility)
    def _clear_prompt_state(self) -> None:
        """Clear the current prompt state."""
        self.current_prompt = None
        self.waiting_for_input = False

    def _get_legacy_response(self, prompt_info: PromptInfo) -> str:
        """Get response that would be used by legacy auto-response system."""
        try:
            if prompt_info.type == PromptType.NUMBERED_SELECTION:
                opts_count = cast("dict[str, Any]", prompt_info.metadata).get("option_count", len(prompt_info.options))
                if opts_count == 2 and self.mode12 == "Manual":
                    return self.mode12_response
                if opts_count >= 3 and self.mode123 == "Manual":
                    return self.mode123_response
                return getattr(prompt_info, "recommended_response", None) or "1"

            if prompt_info.type == PromptType.BINARY_CHOICE:
                if self.yn_mode == "Manual":
                    return self.yn_response.lower() if isinstance(self.yn_response, str) else str(self.yn_response)
                return getattr(prompt_info, "recommended_response", None) or "y"

            if prompt_info.type == PromptType.CONFIRMATION:
                if self.mode12 == "Manual":
                    return self.mode12_response
                return getattr(prompt_info, "recommended_response", None) or "1"

            if prompt_info.type == PromptType.LOGIN_REDIRECT:
                question = prompt_info.question.lower()
                if "continue" in question or "press enter" in question:
                    return ""  # Just press Enter

        except Exception:
            self.logger.exception("Error getting legacy response")

        return "1"  # Safe fallback

    # Async logging methods
    async def _start_async_logging(self) -> None:
        """Start the async logging system."""
        if self.async_logger:
            return

        try:
            self.async_logger = AsyncLogger(
                name=f"yesman.async_claude_monitor.{self.session_name}",
                min_level=LogLevel.INFO,
                enable_batch_processing=True,
                batch_size=25,
                enable_console=False,
                enable_file=True,
            )
            await self.async_logger.start()
            self.logger.info("Async logging system started")
        except Exception:
            self.logger.exception("Failed to start async logging")

    async def _stop_async_logging(self) -> None:
        """Stop the async logging system."""
        if self.async_logger:
            try:
                await self.async_logger.stop()
                self.async_logger = None
                self.logger.info("Async logging system stopped")
            except Exception:
                self.logger.exception("Error stopping async logging")

    # Public interface methods (backward compatibility)
    def set_auto_next(self, enabled: bool) -> None:
        """Enable or disable auto-next responses."""
        self.is_auto_next_enabled = enabled
        status = "enabled" if enabled else "disabled"
        cast("Any", self.status_manager).update_status(f"[cyan]Auto next {status}[/]")

    def set_mode_yn(self, mode: str, response: str) -> None:
        """Set manual override for Y/N prompts."""
        self.yn_mode = mode
        self.yn_response = response

    def set_mode_12(self, mode: str, response: str) -> None:
        """Set manual override for 1/2 prompts."""
        self.mode12 = mode
        self.mode12_response = response

    def set_mode_123(self, mode: str, response: str) -> None:
        """Set manual override for 1/2/3 prompts."""
        self.mode123 = mode
        self.mode123_response = response

    def is_waiting_for_input(self) -> bool:
        """Check if Claude is currently waiting for user input."""
        return self.waiting_for_input

    def get_current_prompt(self) -> PromptInfo | None:
        """Get the current prompt information."""
        return self.current_prompt

    def get_collection_stats(self) -> dict[str, Any]:
        """Get content collection statistics."""
        return cast("dict[str, Any]", self.content_collector.get_collection_stats())

    # Legacy compatibility methods (delegate to original ClaudeMonitor for non-async operations)
    def start_monitoring(self) -> bool:
        """Legacy sync method - creates async task."""
        if self.is_running:
            return True

        # Create async task to run the monitoring
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                asyncio.create_task(self.start_monitoring_async())
                return True
            else:
                # If not in async context, run until complete
                return loop.run_until_complete(self.start_monitoring_async())
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.start_monitoring_async())

    def stop_monitoring(self) -> bool:
        """Legacy sync method - stops async monitoring."""
        if not self.is_running:
            return True

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, create a task
                asyncio.create_task(self.stop_monitoring_async())
                return True
            else:
                # If not in async context, run until complete
                return loop.run_until_complete(self.stop_monitoring_async())
        except RuntimeError:
            # No event loop, create new one
            return asyncio.run(self.stop_monitoring_async())


# Factory function for creating monitors based on async capability
def create_claude_monitor(
    session_manager: object,
    process_controller: object,
    status_manager: object,
    prefer_async: bool = True,
    event_bus: AsyncEventBus | None = None,
) -> Any:
    """Factory function to create appropriate Claude monitor.

    Args:
        session_manager: Session management interface
        process_controller: Process control interface
        status_manager: Status management interface
        prefer_async: Whether to prefer async implementation
        event_bus: Optional event bus instance

    Returns:
        AsyncClaudeMonitor if prefer_async=True, else legacy ClaudeMonitor
    """
    if prefer_async:
        return AsyncClaudeMonitor(session_manager=session_manager, process_controller=process_controller, status_manager=status_manager, event_bus=event_bus)
    else:
        # Import and return legacy monitor for backward compatibility
        from .claude_monitor import ClaudeMonitor

        return ClaudeMonitor(session_manager=session_manager, process_controller=process_controller, status_manager=status_manager)
