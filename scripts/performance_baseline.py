#!/usr/bin/env python3

# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License

"""
Performance monitoring baseline system for Yesman-Claude project.

This module provides comprehensive performance benchmarking to establish baselines
and measure the impact of architectural improvements, particularly async conversions.

Key Features:
- System resource monitoring (CPU, memory, I/O)
- Claude monitoring loop performance metrics
- Event bus throughput and latency
- Quality gates execution timing
- Async vs sync performance comparison
- Historical performance tracking
"""

import asyncio
import json
import logging
import platform
import time
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import psutil

from libs.core.async_event_bus import Event, EventPriority, EventType, get_event_bus


@dataclass
class SystemMetrics:
    """System resource metrics snapshot."""

    timestamp: float
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_bytes_sent: int
    network_bytes_recv: int
    process_count: int
    python_version: str
    system_platform: str


@dataclass
class MonitoringMetrics:
    """Claude monitoring performance metrics."""

    timestamp: float
    session_name: str
    monitor_type: str  # "legacy" or "async"
    loops_per_second: float
    average_loop_duration_ms: float
    memory_usage_mb: float
    cpu_percent: float
    active_threads: int
    total_loops: int
    uptime_seconds: float
    error_count: int
    prompt_detection_latency_ms: float
    content_capture_latency_ms: float


@dataclass
class EventBusMetrics:
    """AsyncEventBus performance metrics."""

    timestamp: float
    events_published: int
    events_processed: int
    events_failed: int
    average_event_latency_ms: float
    events_per_second: float
    active_subscribers: int
    queue_size: int
    memory_usage_mb: float
    total_uptime_seconds: float


@dataclass
class QualityGatesMetrics:
    """Quality gates execution performance."""

    timestamp: float
    gate_name: str
    execution_time_ms: float
    result: str  # "pass", "fail", "warning"
    exit_code: int
    memory_peak_mb: float
    cpu_peak_percent: float


@dataclass
class PerformanceBaseline:
    """Complete performance baseline snapshot."""

    timestamp: float
    system_metrics: SystemMetrics
    monitoring_metrics: List[MonitoringMetrics]
    event_bus_metrics: Optional[EventBusMetrics]
    quality_gates_metrics: List[QualityGatesMetrics]
    benchmark_duration_seconds: float
    total_cpu_time_seconds: float
    baseline_version: str


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system.

    Provides baseline establishment, continuous monitoring, and performance
    comparison capabilities for the Yesman-Claude project.
    """

    def __init__(self, data_dir: Optional[Path] = None):
        """
        Initialize the performance monitor.

        Args:
            data_dir: Directory for storing performance data (defaults to project root)
        """
        self.data_dir = data_dir or Path.cwd() / "performance_data"
        self.data_dir.mkdir(exist_ok=True)

        self.logger = logging.getLogger("yesman.performance_monitor")
        self.event_bus = get_event_bus()

        # Monitoring state
        self.is_monitoring = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._start_time = 0.0

        # Performance tracking
        self._system_samples: List[SystemMetrics] = []
        self._monitoring_samples: List[MonitoringMetrics] = []
        self._event_bus_samples: List[EventBusMetrics] = []
        self._quality_gates_samples: List[QualityGatesMetrics] = []

        # Baseline data
        self._current_baseline: Optional[PerformanceBaseline] = None
        self._historical_baselines: List[PerformanceBaseline] = []

        # Process monitoring
        self._process = psutil.Process()
        self._initial_io_counters = None
        self._initial_net_counters = None

    async def establish_baseline(self, duration_seconds: int = 60) -> PerformanceBaseline:
        """
        Establish a new performance baseline over specified duration.

        Args:
            duration_seconds: How long to monitor for baseline establishment

        Returns:
            Complete performance baseline data
        """
        self.logger.info(f"Establishing performance baseline over {duration_seconds} seconds...")

        # Clear existing samples
        self._system_samples.clear()
        self._monitoring_samples.clear()
        self._event_bus_samples.clear()
        self._quality_gates_samples.clear()

        baseline_start = time.time()

        # Start monitoring
        await self.start_monitoring()

        # Run baseline monitoring for specified duration
        try:
            await asyncio.sleep(duration_seconds)
        finally:
            await self.stop_monitoring()

        baseline_end = time.time()
        actual_duration = baseline_end - baseline_start

        # Collect final system metrics
        system_metrics = self._collect_system_metrics()

        # Create baseline snapshot
        baseline = PerformanceBaseline(
            timestamp=baseline_end,
            system_metrics=system_metrics,
            monitoring_metrics=self._monitoring_samples.copy(),
            event_bus_metrics=self._event_bus_samples[-1] if self._event_bus_samples else None,
            quality_gates_metrics=self._quality_gates_samples.copy(),
            benchmark_duration_seconds=actual_duration,
            total_cpu_time_seconds=sum(m.cpu_percent for m in self._monitoring_samples),
            baseline_version="1.0.0",
        )

        # Save baseline
        await self._save_baseline(baseline)
        self._current_baseline = baseline
        self._historical_baselines.append(baseline)

        # Publish baseline established event
        await self.event_bus.publish(
            Event(
                type=EventType.PERFORMANCE_METRICS,
                data={
                    "event_subtype": "baseline_established",
                    "duration_seconds": actual_duration,
                    "system_samples": len(self._system_samples),
                    "monitoring_samples": len(self._monitoring_samples),
                    "baseline_file": str(self.data_dir / f"baseline_{int(baseline_end)}.json"),
                },
                timestamp=time.time(),
                source="performance_monitor",
                priority=EventPriority.NORMAL,
            )
        )

        self.logger.info(f"Performance baseline established: {len(self._system_samples)} system samples, {len(self._monitoring_samples)} monitoring samples")

        return baseline

    async def start_monitoring(self) -> bool:
        """Start continuous performance monitoring."""
        if self.is_monitoring:
            self.logger.warning("Performance monitoring already active")
            return False

        try:
            self.is_monitoring = True
            self._start_time = time.time()

            # Initialize baseline counters
            self._initial_io_counters = self._process.io_counters()
            self._initial_net_counters = psutil.net_io_counters()

            # Start monitoring task
            self._monitor_task = asyncio.create_task(self._monitoring_loop())

            self.logger.info("Performance monitoring started")
            return True

        except Exception as e:
            self.is_monitoring = False
            self.logger.error(f"Failed to start performance monitoring: {e}")
            return False

    async def stop_monitoring(self) -> bool:
        """Stop continuous performance monitoring."""
        if not self.is_monitoring:
            return True

        self.is_monitoring = False

        # Cancel monitoring task
        if self._monitor_task and not self._monitor_task.done():
            self._monitor_task.cancel()
            try:
                await asyncio.wait_for(self._monitor_task, timeout=5.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                self.logger.warning("Monitor task cancellation timed out")

        self.logger.info("Performance monitoring stopped")
        return True

    async def _monitoring_loop(self) -> None:
        """Main monitoring loop for continuous performance data collection."""
        sample_interval = 2.0  # Sample every 2 seconds

        try:
            while self.is_monitoring:
                loop_start = time.perf_counter()

                try:
                    # Collect system metrics
                    system_metrics = self._collect_system_metrics()
                    self._system_samples.append(system_metrics)

                    # Collect event bus metrics if available
                    event_bus_metrics = await self._collect_event_bus_metrics()
                    if event_bus_metrics:
                        self._event_bus_samples.append(event_bus_metrics)

                    # Limit sample history to prevent memory bloat
                    self._limit_sample_history()

                except Exception as e:
                    self.logger.error(f"Error collecting performance samples: {e}")

                # Calculate sleep time to maintain consistent interval
                loop_duration = time.perf_counter() - loop_start
                sleep_time = max(0.1, sample_interval - loop_duration)
                await asyncio.sleep(sleep_time)

        except asyncio.CancelledError:
            self.logger.info("Performance monitoring loop cancelled")
        except Exception as e:
            self.logger.error(f"Critical error in monitoring loop: {e}")

    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system resource metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Disk I/O (calculate delta from start)
            current_io = self._process.io_counters()
            disk_read_mb = 0.0
            disk_write_mb = 0.0

            if self._initial_io_counters:
                disk_read_mb = (current_io.read_bytes - self._initial_io_counters.read_bytes) / (1024 * 1024)
                disk_write_mb = (current_io.write_bytes - self._initial_io_counters.write_bytes) / (1024 * 1024)

            # Network I/O (calculate delta from start)
            current_net = psutil.net_io_counters()
            net_sent = 0
            net_recv = 0

            if self._initial_net_counters:
                net_sent = current_net.bytes_sent - self._initial_net_counters.bytes_sent
                net_recv = current_net.bytes_recv - self._initial_net_counters.bytes_recv

            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_bytes_sent=net_sent,
                network_bytes_recv=net_recv,
                process_count=len(psutil.pids()),
                python_version=platform.python_version(),
                system_platform=platform.platform(),
            )

        except Exception as e:
            self.logger.error(f"Error collecting system metrics: {e}")
            # Return minimal metrics on error
            return SystemMetrics(
                timestamp=time.time(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_used_mb=0.0,
                memory_available_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_bytes_sent=0,
                network_bytes_recv=0,
                process_count=0,
                python_version=platform.python_version(),
                system_platform=platform.platform(),
            )

    async def _collect_event_bus_metrics(self) -> Optional[EventBusMetrics]:
        """Collect AsyncEventBus performance metrics."""
        try:
            # Get metrics from event bus if available
            if hasattr(self.event_bus, "get_performance_metrics"):
                metrics_data = await self.event_bus.get_performance_metrics()

                return EventBusMetrics(
                    timestamp=time.time(),
                    events_published=metrics_data.get("events_published", 0),
                    events_processed=metrics_data.get("events_processed", 0),
                    events_failed=metrics_data.get("events_failed", 0),
                    average_event_latency_ms=metrics_data.get("avg_latency_ms", 0.0),
                    events_per_second=metrics_data.get("events_per_second", 0.0),
                    active_subscribers=metrics_data.get("active_subscribers", 0),
                    queue_size=metrics_data.get("queue_size", 0),
                    memory_usage_mb=metrics_data.get("memory_usage_mb", 0.0),
                    total_uptime_seconds=metrics_data.get("uptime_seconds", 0.0),
                )

            return None

        except Exception as e:
            self.logger.error(f"Error collecting event bus metrics: {e}")
            return None

    def record_monitoring_metrics(self, metrics: MonitoringMetrics) -> None:
        """Record monitoring performance metrics from claude_monitor or async_claude_monitor."""
        self._monitoring_samples.append(metrics)

        # Publish metrics event
        asyncio.create_task(
            self.event_bus.publish(
                Event(
                    type=EventType.PERFORMANCE_METRICS,
                    data={"component": "claude_monitor", "metrics": asdict(metrics)},
                    timestamp=time.time(),
                    source="performance_monitor",
                    priority=EventPriority.LOW,
                )
            )
        )

    def record_quality_gates_metrics(self, metrics: QualityGatesMetrics) -> None:
        """Record quality gates execution metrics."""
        self._quality_gates_samples.append(metrics)

        # Publish metrics event
        asyncio.create_task(
            self.event_bus.publish(
                Event(
                    type=EventType.PERFORMANCE_METRICS, data={"component": "quality_gates", "metrics": asdict(metrics)}, timestamp=time.time(), source="performance_monitor", priority=EventPriority.LOW
                )
            )
        )

    def _limit_sample_history(self, max_samples: int = 1000) -> None:
        """Limit sample history to prevent memory growth."""
        if len(self._system_samples) > max_samples:
            self._system_samples = self._system_samples[-max_samples:]
        if len(self._monitoring_samples) > max_samples:
            self._monitoring_samples = self._monitoring_samples[-max_samples:]
        if len(self._event_bus_samples) > max_samples:
            self._event_bus_samples = self._event_bus_samples[-max_samples:]
        if len(self._quality_gates_samples) > max_samples:
            self._quality_gates_samples = self._quality_gates_samples[-max_samples:]

    async def _save_baseline(self, baseline: PerformanceBaseline) -> None:
        """Save baseline data to file."""
        try:
            filename = f"baseline_{int(baseline.timestamp)}.json"
            filepath = self.data_dir / filename

            # Convert baseline to dict with proper serialization
            baseline_dict = asdict(baseline)

            # Save to file
            with open(filepath, "w") as f:
                json.dump(baseline_dict, f, indent=2, default=str)

            # Also save as latest baseline
            latest_path = self.data_dir / "latest_baseline.json"
            with open(latest_path, "w") as f:
                json.dump(baseline_dict, f, indent=2, default=str)

            self.logger.info(f"Baseline saved to: {filepath}")

        except Exception as e:
            self.logger.error(f"Failed to save baseline: {e}")

    async def load_baseline(self, filename: Optional[str] = None) -> Optional[PerformanceBaseline]:
        """Load baseline data from file."""
        try:
            if filename:
                filepath = self.data_dir / filename
            else:
                filepath = self.data_dir / "latest_baseline.json"

            if not filepath.exists():
                self.logger.warning(f"Baseline file not found: {filepath}")
                return None

            with open(filepath, "r") as f:
                baseline_dict = json.load(f)

            # Convert back to dataclass (simplified for now)
            # In production, you'd want proper deserialization
            baseline = PerformanceBaseline(**baseline_dict)

            self._current_baseline = baseline
            self.logger.info(f"Baseline loaded from: {filepath}")

            return baseline

        except Exception as e:
            self.logger.error(f"Failed to load baseline: {e}")
            return None

    def generate_performance_report(self, compare_to_baseline: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive performance report.

        Args:
            compare_to_baseline: Whether to include baseline comparison

        Returns:
            Detailed performance report
        """
        try:
            report = {
                "report_timestamp": time.time(),
                "report_date": datetime.now().isoformat(),
                "monitoring_duration_seconds": time.time() - self._start_time if self.is_monitoring else 0,
                "system_summary": self._generate_system_summary(),
                "monitoring_summary": self._generate_monitoring_summary(),
                "event_bus_summary": self._generate_event_bus_summary(),
                "quality_gates_summary": self._generate_quality_gates_summary(),
                "baseline_comparison": None,
            }

            # Add baseline comparison if requested and available
            if compare_to_baseline and self._current_baseline:
                report["baseline_comparison"] = self._generate_baseline_comparison()

            return report

        except Exception as e:
            self.logger.error(f"Error generating performance report: {e}")
            return {"error": str(e), "timestamp": time.time()}

    def _generate_system_summary(self) -> Dict[str, Any]:
        """Generate system performance summary."""
        if not self._system_samples:
            return {"error": "No system samples available"}

        cpu_values = [s.cpu_percent for s in self._system_samples]
        memory_values = [s.memory_percent for s in self._system_samples]

        return {
            "samples_count": len(self._system_samples),
            "cpu_percent": {
                "current": cpu_values[-1] if cpu_values else 0,
                "average": sum(cpu_values) / len(cpu_values) if cpu_values else 0,
                "peak": max(cpu_values) if cpu_values else 0,
                "min": min(cpu_values) if cpu_values else 0,
            },
            "memory_percent": {
                "current": memory_values[-1] if memory_values else 0,
                "average": sum(memory_values) / len(memory_values) if memory_values else 0,
                "peak": max(memory_values) if memory_values else 0,
                "min": min(memory_values) if memory_values else 0,
            },
            "disk_io_mb": {
                "total_read": self._system_samples[-1].disk_io_read_mb if self._system_samples else 0,
                "total_write": self._system_samples[-1].disk_io_write_mb if self._system_samples else 0,
            },
            "network_bytes": {
                "total_sent": self._system_samples[-1].network_bytes_sent if self._system_samples else 0,
                "total_recv": self._system_samples[-1].network_bytes_recv if self._system_samples else 0,
            },
        }

    def _generate_monitoring_summary(self) -> Dict[str, Any]:
        """Generate Claude monitoring performance summary."""
        if not self._monitoring_samples:
            return {"error": "No monitoring samples available"}

        loops_per_sec = [m.loops_per_second for m in self._monitoring_samples]
        loop_duration = [m.average_loop_duration_ms for m in self._monitoring_samples]

        return {
            "samples_count": len(self._monitoring_samples),
            "loops_per_second": {
                "current": loops_per_sec[-1] if loops_per_sec else 0,
                "average": sum(loops_per_sec) / len(loops_per_sec) if loops_per_sec else 0,
                "peak": max(loops_per_sec) if loops_per_sec else 0,
            },
            "loop_duration_ms": {
                "current": loop_duration[-1] if loop_duration else 0,
                "average": sum(loop_duration) / len(loop_duration) if loop_duration else 0,
                "peak": max(loop_duration) if loop_duration else 0,
                "min": min(loop_duration) if loop_duration else 0,
            },
            "monitor_types": list(set(m.monitor_type for m in self._monitoring_samples)),
            "total_loops": sum(m.total_loops for m in self._monitoring_samples),
            "total_errors": sum(m.error_count for m in self._monitoring_samples),
        }

    def _generate_event_bus_summary(self) -> Dict[str, Any]:
        """Generate event bus performance summary."""
        if not self._event_bus_samples:
            return {"info": "No event bus samples available"}

        latest = self._event_bus_samples[-1]

        return {
            "samples_count": len(self._event_bus_samples),
            "current_metrics": asdict(latest),
            "throughput": {
                "events_per_second": latest.events_per_second,
                "total_published": latest.events_published,
                "total_processed": latest.events_processed,
                "success_rate": (latest.events_processed / latest.events_published * 100) if latest.events_published > 0 else 100,
            },
        }

    def _generate_quality_gates_summary(self) -> Dict[str, Any]:
        """Generate quality gates performance summary."""
        if not self._quality_gates_samples:
            return {"info": "No quality gates samples available"}

        execution_times = [q.execution_time_ms for q in self._quality_gates_samples]
        results = [q.result for q in self._quality_gates_samples]

        return {
            "samples_count": len(self._quality_gates_samples),
            "execution_time_ms": {
                "average": sum(execution_times) / len(execution_times) if execution_times else 0,
                "fastest": min(execution_times) if execution_times else 0,
                "slowest": max(execution_times) if execution_times else 0,
            },
            "results_distribution": {"pass": results.count("pass"), "fail": results.count("fail"), "warning": results.count("warning")},
            "gates_tested": list(set(q.gate_name for q in self._quality_gates_samples)),
        }

    def _generate_baseline_comparison(self) -> Dict[str, Any]:
        """Generate comparison with baseline metrics."""
        if not self._current_baseline:
            return {"error": "No baseline available for comparison"}

        try:
            # This would implement detailed baseline comparison
            # For now, return placeholder structure
            return {
                "baseline_timestamp": self._current_baseline.timestamp,
                "baseline_version": self._current_baseline.baseline_version,
                "improvements": {"cpu_usage": "TBD", "memory_usage": "TBD", "monitoring_performance": "TBD", "event_bus_throughput": "TBD"},
                "regressions": [],
                "overall_assessment": "baseline_comparison_pending",
            }

        except Exception as e:
            return {"error": f"Baseline comparison failed: {e}"}


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


# Factory functions for creating monitoring metrics
def create_monitoring_metrics(session_name: str, monitor_type: str, loops_per_second: float, **kwargs) -> MonitoringMetrics:
    """Factory function for creating MonitoringMetrics."""
    return MonitoringMetrics(
        timestamp=time.time(),
        session_name=session_name,
        monitor_type=monitor_type,
        loops_per_second=loops_per_second,
        average_loop_duration_ms=kwargs.get("avg_loop_duration_ms", 0.0),
        memory_usage_mb=kwargs.get("memory_usage_mb", 0.0),
        cpu_percent=kwargs.get("cpu_percent", 0.0),
        active_threads=kwargs.get("active_threads", 1),
        total_loops=kwargs.get("total_loops", 0),
        uptime_seconds=kwargs.get("uptime_seconds", 0.0),
        error_count=kwargs.get("error_count", 0),
        prompt_detection_latency_ms=kwargs.get("prompt_detection_latency_ms", 0.0),
        content_capture_latency_ms=kwargs.get("content_capture_latency_ms", 0.0),
    )


def create_quality_gates_metrics(gate_name: str, execution_time_ms: float, result: str, exit_code: int = 0) -> QualityGatesMetrics:
    """Factory function for creating QualityGatesMetrics."""
    return QualityGatesMetrics(
        timestamp=time.time(),
        gate_name=gate_name,
        execution_time_ms=execution_time_ms,
        result=result,
        exit_code=exit_code,
        memory_peak_mb=0.0,  # Would be measured during execution
        cpu_peak_percent=0.0,  # Would be measured during execution
    )
