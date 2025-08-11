# Enhanced Performance Monitoring System

## Overview

The Yesman-Claude project includes a comprehensive performance monitoring system that provides detailed insights into system resource usage, component performance, and bottleneck identification. This document describes the enhanced monitoring capabilities implemented in the AsyncEventBus and AsyncClaudeMonitor components.

## Key Features

### 1. Event Bus Queue Depth Monitoring

The `AsyncEventBus` now provides detailed queue depth analysis:

- **Real-time Queue Metrics**: Current queue size, utilization percentage, and backlog duration
- **Historical Tracking**: Queue depth history with configurable sample retention
- **Overflow Detection**: Automatic detection of queue overflow events
- **Peak Analysis**: Track peak queue depth and identify capacity bottlenecks

```python
from libs.core.async_event_bus import get_event_bus

event_bus = get_event_bus()
metrics = event_bus.get_metrics()

print(f"Queue utilization: {metrics.queue_utilization_percent:.1f}%")
print(f"Peak queue depth: {metrics.peak_queue_depth}")
print(f"Overflow events: {metrics.queue_overflow_events}")
```

### 2. Individual Component Response Time Tracking

The `AsyncClaudeMonitor` tracks detailed timing metrics for each component:

- **Content Capture**: Time spent capturing pane content
- **Claude Status Check**: Process status verification timing  
- **Prompt Detection**: Time to analyze content for prompts
- **Content Processing**: Overall content processing duration
- **Response Sending**: Time to send responses to Claude
- **Automation Analysis**: Context analysis and automation detection

Each component tracks:
- Average, median, P95, and P99 response times
- Peak response times
- Error rates and success/failure tracking
- Sample counts for statistical significance

### 3. Memory Usage Per Component Tracking

Enhanced memory monitoring provides:

- **Memory Delta Tracking**: Memory allocation/deallocation per component operation
- **Peak Memory Usage**: Highest memory usage recorded per component
- **Allocation Patterns**: Number and size of memory allocations
- **Memory Efficiency**: Track memory leaks and optimization opportunities

### 4. CPU Utilization Per Async Task Monitoring

CPU monitoring includes:

- **Component CPU Usage**: Estimated CPU usage per component operation
- **CPU Efficiency**: CPU utilization relative to available cores
- **Peak CPU Tracking**: Highest CPU usage recorded
- **P95 CPU Utilization**: 95th percentile CPU usage for performance analysis

### 5. Network I/O Pattern Tracking

Network monitoring provides:

- **Bytes Sent/Received**: Network traffic per component operation
- **Throughput Analysis**: Network throughput in MB/s
- **Network Operation Counting**: Number of network-active operations
- **Peak Throughput Tracking**: Maximum network throughput observed

## Architecture

### EventMetrics Enhancement

The `EventMetrics` class now includes enhanced queue depth monitoring fields:

```python
@dataclass
class EventMetrics:
    # ... existing fields ...
    
    # Enhanced queue depth monitoring
    max_queue_depth: int = 0
    queue_depth_history: list[int] = None
    queue_utilization_percent: float = 0.0
    queue_backlog_duration_ms: float = 0.0
    peak_queue_depth: int = 0
    queue_overflow_events: int = 0
```

### AsyncClaudeMonitor Enhancement

The monitor now includes comprehensive resource tracking:

```python
# Component timing tracking
self._component_timings: dict[str, deque] = {
    'content_capture': deque(maxlen=100),
    'claude_status_check': deque(maxlen=100),
    'prompt_detection': deque(maxlen=100),
    'content_processing': deque(maxlen=100),
    'response_sending': deque(maxlen=100),
    'automation_analysis': deque(maxlen=100),
}

# Memory usage tracking
self._component_memory_usage: dict[str, deque] = {
    component: deque(maxlen=50) for component in self._component_timings
}

# CPU utilization tracking
self._component_cpu_usage: dict[str, deque] = {
    component: deque(maxlen=50) for component in self._component_timings
}

# Network I/O tracking
self._component_network_io: dict[str, deque] = {
    component: deque(maxlen=50) for component in self._component_timings
}
```

## Performance Metrics Collection

### Automatic Monitoring

The monitoring system automatically tracks performance during normal operation:

1. **Timing Measurement**: Each component operation is timed using `time.perf_counter()`
2. **Memory Measurement**: Memory usage measured before/after operations using `psutil`
3. **CPU Estimation**: CPU usage estimated based on execution time and system load
4. **Network Tracking**: Network I/O deltas measured using `psutil.net_io_counters()`

### Metrics Reporting

Performance metrics are reported via the event bus every 60 seconds (configurable):

```python
async def _report_performance_metrics(self) -> None:
    component_metrics = self._get_component_metrics()
    
    metrics = {
        "session_name": self.session_name,
        "loops_per_second": loops_per_second,
        "component_response_times": component_metrics,
        "current_memory_mb": current_memory_mb,
        "memory_growth_mb": total_memory_growth,
        "current_cpu_percent": self._measure_cpu_usage(),
    }
    
    await self.event_bus.publish(
        Event(type=EventType.PERFORMANCE_METRICS, data=metrics, ...)
    )
```

## Bottleneck Detection

The system automatically detects performance bottlenecks and logs warnings for:

- **Response Time Bottlenecks**: Components averaging > 100ms
- **Memory Usage**: Components using > 5MB memory delta
- **CPU Usage**: Components using > 50% CPU
- **Network Usage**: Components with > 1MB/s network throughput

Example log output:
```
WARNING - Bottleneck in content_capture: avg=150.5ms, p95=200.1ms, errors=0, mem=2.5MB, cpu=25.3%, net=1.2MB/s
```

## Usage Examples

### Monitoring Queue Depth

```python
from libs.core.async_event_bus import get_event_bus

event_bus = get_event_bus()
await event_bus.start()

# Publish events and monitor queue depth
for i in range(10):
    await event_bus.publish(Event(...))

metrics = event_bus.get_metrics()
if metrics.queue_utilization_percent > 80:
    print(f"Warning: High queue utilization ({metrics.queue_utilization_percent:.1f}%)")
```

### Component Performance Analysis

```python
from libs.core.claude_monitor_async import AsyncClaudeMonitor

monitor = AsyncClaudeMonitor(session_manager, process_controller, status_manager)
await monitor.start_monitoring_async()

# Let monitor run for some time...
await asyncio.sleep(60)

# Get component metrics
metrics = monitor._get_component_metrics()
for component, stats in metrics.items():
    if stats['average_ms'] > 100:
        print(f"{component} is slow: {stats['average_ms']:.1f}ms average")
    if stats['avg_memory_delta_mb'] > 5:
        print(f"{component} uses high memory: {stats['avg_memory_delta_mb']:.1f}MB")
```

### Performance Baseline Establishment

```python
from scripts.performance_baseline import get_performance_monitor

perf_monitor = get_performance_monitor()
await perf_monitor.start_monitoring()

# Establish 60-second baseline
baseline = await perf_monitor.establish_baseline(duration_seconds=60)

print(f"Baseline established with {len(baseline.monitoring_metrics)} samples")
print(f"System CPU: {baseline.system_metrics.cpu_percent:.1f}%")
print(f"Memory: {baseline.system_metrics.memory_used_mb:.1f}MB")
```

## Configuration

### Queue Monitoring Configuration

```python
# Configure event bus with custom queue size
event_bus = AsyncEventBus(
    max_queue_size=10000,  # Maximum events in queue
    worker_count=4         # Number of processing workers
)

# Configure metrics reporting interval
event_bus._metrics_interval = 30.0  # Report every 30 seconds
```

### Component Monitoring Configuration

```python
# Configure sample retention
monitor._component_timings['content_capture'] = deque(maxlen=200)  # More samples
monitor._performance_interval = 30.0  # Report every 30 seconds
```

## Integration with Quality Gates

The performance monitoring system integrates with the quality gates checker:

```python
# Enhanced security scanning includes performance metrics
python scripts/quality_gates_checker.py --enhanced-security --performance-monitoring
```

Performance metrics are included in the quality gates report for continuous monitoring.

## Troubleshooting

### High Memory Usage

If components show high memory usage:

1. Check for memory leaks in component logic
2. Review deque maxlen settings to prevent excessive sample retention
3. Monitor memory growth over time using baseline comparison

### High CPU Usage

For high CPU usage components:

1. Profile the component code for CPU-intensive operations
2. Consider moving blocking operations to thread pools
3. Review async/await usage for proper non-blocking patterns

### Network Performance Issues

For network-related bottlenecks:

1. Monitor network I/O patterns for inefficient operations
2. Check for excessive network calls in automation components
3. Review prompt detection logic for network dependencies

## Future Enhancements

Planned improvements include:

- **Database Storage**: Persist performance metrics for long-term analysis
- **Dashboard Integration**: Real-time performance visualization in web dashboard
- **Alerting System**: Automated alerts for performance degradation
- **Comparative Analysis**: Performance comparison across different sessions
- **Resource Optimization**: Automatic resource usage optimization suggestions

---

## API Reference

### AsyncEventBus Methods

- `get_metrics()` → `EventMetrics`: Get current event bus performance metrics
- `_update_queue_depth_metrics()`: Update queue depth monitoring metrics

### AsyncClaudeMonitor Methods

- `_record_component_timing(component, duration_ms, success)`: Record timing metrics
- `_record_component_memory(component, memory_delta_mb)`: Record memory usage
- `_record_component_cpu(component, cpu_percent)`: Record CPU usage
- `_record_component_network_io(component, sent, recv, duration)`: Record network I/O
- `_get_component_metrics()`: Get comprehensive component performance metrics
- `_measure_memory_usage()`: Get current process memory usage
- `_measure_cpu_usage()`: Get current process CPU usage
- `_measure_network_io_delta()`: Get network I/O delta since last measurement

### EventMetrics Fields

| Field | Type | Description |
|-------|------|-------------|
| `max_queue_depth` | int | Maximum queue depth in current interval |
| `queue_depth_history` | list[int] | Historical queue depth samples |
| `queue_utilization_percent` | float | Current queue utilization percentage |
| `queue_backlog_duration_ms` | float | Estimated time to process current backlog |
| `peak_queue_depth` | int | Peak queue depth since monitoring started |
| `queue_overflow_events` | int | Number of queue overflow events |

---

This enhanced monitoring system provides comprehensive visibility into system performance, enabling proactive optimization and bottleneck identification in the Yesman-Claude project.