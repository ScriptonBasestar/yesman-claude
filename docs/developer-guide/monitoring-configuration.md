# Monitoring Configuration Guide

## Overview

This guide explains how to configure and optimize the enhanced performance monitoring system in Yesman-Claude for
different deployment scenarios and monitoring requirements.

## Configuration Options

### 1. Event Bus Monitoring Configuration

#### Basic Configuration

```python
from libs.core.async_event_bus import AsyncEventBus

# Standard configuration for development
event_bus = AsyncEventBus(
    max_queue_size=10000,    # Event queue capacity
    worker_count=4           # Concurrent event processors
)
```

#### Production Configuration

```python
# High-throughput production configuration
event_bus = AsyncEventBus(
    max_queue_size=50000,    # Larger queue for high event volume
    worker_count=8           # More workers for better concurrency
)

# Configure metrics reporting interval (default: 60 seconds)
event_bus._metrics_interval = 30.0        # More frequent reporting
event_bus._queue_update_interval = 0.5    # More frequent queue sampling
```

#### Low-Resource Configuration

```python
# Minimal resource usage for resource-constrained environments
event_bus = AsyncEventBus(
    max_queue_size=1000,     # Smaller queue to save memory
    worker_count=2           # Fewer workers to reduce CPU usage
)

event_bus._metrics_interval = 120.0       # Less frequent reporting
```

### 2. Component Monitoring Configuration

#### Sample Retention Settings

```python
from libs.core.claude_monitor_async import AsyncClaudeMonitor
from collections import deque

monitor = AsyncClaudeMonitor(session_manager, process_controller, status_manager)

# Adjust sample retention for different components
monitor._component_timings = {
    'content_capture': deque(maxlen=200),      # High retention for critical component
    'claude_status_check': deque(maxlen=50),   # Lower retention for simple check
    'prompt_detection': deque(maxlen=100),     # Standard retention
    'content_processing': deque(maxlen=150),   # Higher retention for complex processing
    'response_sending': deque(maxlen=100),     # Standard retention
    'automation_analysis': deque(maxlen=75),   # Moderate retention
}

# Adjust memory and CPU sample retention
monitor._component_memory_usage = {
    component: deque(maxlen=30) for component in monitor._component_timings  # Reduced memory samples
}

monitor._component_cpu_usage = {
    component: deque(maxlen=40) for component in monitor._component_timings  # Moderate CPU samples
}
```

#### Performance Reporting Configuration

```python
# Configure performance metrics reporting frequency
monitor._performance_interval = 45.0  # Report every 45 seconds

# Configure baseline measurements
monitor._baseline_memory_mb = monitor._measure_memory_usage()
monitor._baseline_cpu_percent = psutil.cpu_percent(interval=1.0)
```

### 3. Network I/O Monitoring Configuration

#### Network Pattern Tracking

```python
# Configure network I/O sample retention
monitor._component_network_io = {
    component: deque(maxlen=25) for component in monitor._component_timings
}

# Initialize network baseline
monitor._baseline_network_counters = psutil.net_io_counters()
monitor._last_network_counters = monitor._baseline_network_counters
```

## Environment-Specific Configurations

### Development Environment

Optimized for detailed debugging and analysis:

```python
# Development monitoring configuration
DEV_CONFIG = {
    'event_bus': {
        'max_queue_size': 5000,
        'worker_count': 2,
        'metrics_interval': 30.0,
        'queue_update_interval': 1.0
    },
    'component_monitoring': {
        'timing_samples': 150,
        'memory_samples': 50,
        'cpu_samples': 50,
        'network_samples': 30,
        'performance_interval': 30.0
    },
    'logging': {
        'log_bottlenecks': True,
        'bottleneck_thresholds': {
            'response_time_ms': 50,    # Lower threshold for dev
            'memory_delta_mb': 2.0,    # Lower threshold for dev
            'cpu_percent': 25.0,       # Lower threshold for dev
            'network_mbps': 0.5        # Lower threshold for dev
        }
    }
}
```

### Production Environment

Optimized for performance with essential monitoring:

```python
# Production monitoring configuration
PROD_CONFIG = {
    'event_bus': {
        'max_queue_size': 20000,
        'worker_count': 6,
        'metrics_interval': 60.0,
        'queue_update_interval': 2.0
    },
    'component_monitoring': {
        'timing_samples': 100,
        'memory_samples': 30,
        'cpu_samples': 30,
        'network_samples': 20,
        'performance_interval': 60.0
    },
    'logging': {
        'log_bottlenecks': True,
        'bottleneck_thresholds': {
            'response_time_ms': 200,   # Higher threshold for prod
            'memory_delta_mb': 10.0,   # Higher threshold for prod
            'cpu_percent': 75.0,       # Higher threshold for prod
            'network_mbps': 2.0        # Higher threshold for prod
        }
    }
}
```

### Testing Environment

Minimal monitoring for automated testing:

```python
# Testing monitoring configuration
TEST_CONFIG = {
    'event_bus': {
        'max_queue_size': 1000,
        'worker_count': 2,
        'metrics_interval': 10.0,   # Frequent reporting for test validation
        'queue_update_interval': 0.5
    },
    'component_monitoring': {
        'timing_samples': 25,       # Minimal samples for tests
        'memory_samples': 10,
        'cpu_samples': 10,
        'network_samples': 10,
        'performance_interval': 10.0
    },
    'logging': {
        'log_bottlenecks': False,   # Disable bottleneck logging in tests
    }
}
```

## Configuration Application

### Using Configuration Dictionaries

```python
def apply_monitoring_config(monitor: AsyncClaudeMonitor, config: dict) -> None:
    """Apply monitoring configuration to AsyncClaudeMonitor instance."""
    
    # Apply component monitoring settings
    comp_config = config['component_monitoring']
    
    # Update timing sample retention
    for component in monitor._component_timings:
        monitor._component_timings[component] = deque(maxlen=comp_config['timing_samples'])
        monitor._component_memory_usage[component] = deque(maxlen=comp_config['memory_samples'])
        monitor._component_cpu_usage[component] = deque(maxlen=comp_config['cpu_samples'])
        monitor._component_network_io[component] = deque(maxlen=comp_config['network_samples'])
    
    # Update reporting interval
    monitor._performance_interval = comp_config['performance_interval']

def apply_event_bus_config(event_bus: AsyncEventBus, config: dict) -> None:
    """Apply event bus configuration."""
    
    bus_config = config['event_bus']
    
    # Update metrics intervals
    event_bus._metrics_interval = bus_config['metrics_interval']
    event_bus._queue_update_interval = bus_config['queue_update_interval']

# Usage example
monitor = AsyncClaudeMonitor(session_manager, process_controller, status_manager)
event_bus = get_event_bus()

# Apply development configuration
apply_monitoring_config(monitor, DEV_CONFIG)
apply_event_bus_config(event_bus, DEV_CONFIG)
```

### Environment-Based Configuration

```python
import os
from typing import Dict, Any

def get_monitoring_config() -> Dict[str, Any]:
    """Get monitoring configuration based on environment."""
    
    env = os.getenv('YESMAN_ENV', 'development').lower()
    
    if env == 'production':
        return PROD_CONFIG
    elif env == 'testing':
        return TEST_CONFIG
    else:  # development
        return DEV_CONFIG

# Usage
config = get_monitoring_config()
apply_monitoring_config(monitor, config)
```

## Performance Tuning

### Memory Optimization

```python
# Reduce memory usage by limiting sample retention
MEMORY_OPTIMIZED_CONFIG = {
    'timing_samples': 50,      # Reduce from default 100
    'memory_samples': 20,      # Reduce from default 50
    'cpu_samples': 20,         # Reduce from default 50
    'network_samples': 15,     # Reduce from default 50
}

# Apply to monitor
for component in monitor._component_timings:
    monitor._component_timings[component] = deque(maxlen=MEMORY_OPTIMIZED_CONFIG['timing_samples'])
    # ... apply other settings
```

### CPU Optimization

```python
# Reduce CPU usage by less frequent measurements
CPU_OPTIMIZED_CONFIG = {
    'metrics_interval': 120.0,        # Report every 2 minutes instead of 1
    'queue_update_interval': 5.0,     # Update queue metrics every 5 seconds
    'performance_interval': 120.0,    # Report component metrics every 2 minutes
}

# Apply intervals
event_bus._metrics_interval = CPU_OPTIMIZED_CONFIG['metrics_interval']
monitor._performance_interval = CPU_OPTIMIZED_CONFIG['performance_interval']
```

### Network Optimization

```python
# Optimize network monitoring for minimal overhead
NETWORK_OPTIMIZED_CONFIG = {
    'network_samples': 10,             # Minimal network sample retention
    'disable_network_monitoring': False,  # Can be disabled entirely if not needed
}

if NETWORK_OPTIMIZED_CONFIG['disable_network_monitoring']:
    # Disable network monitoring entirely
    monitor._measure_network_io_delta = lambda: (0, 0)
```

## Monitoring Quality Gates Integration

### Configure Quality Gates with Monitoring

```python
# Enhanced quality gates configuration with performance monitoring
QUALITY_GATES_CONFIG = {
    'performance_monitoring': {
        'enabled': True,
        'thresholds': {
            'max_response_time_ms': 500,
            'max_memory_usage_mb': 100,
            'max_cpu_percent': 80,
            'max_queue_utilization_percent': 90
        }
    }
}

# Apply in quality_gates_checker.py
def check_performance_thresholds(metrics: dict) -> bool:
    """Check if performance metrics meet quality gate thresholds."""
    thresholds = QUALITY_GATES_CONFIG['performance_monitoring']['thresholds']
    
    for component, stats in metrics.get('component_response_times', {}).items():
        if stats['average_ms'] > thresholds['max_response_time_ms']:
            return False
    
    return True
```

## Troubleshooting Configuration Issues

### Common Configuration Problems

1. **High Memory Usage**

   ```python
   # Problem: Too many samples retained
   # Solution: Reduce maxlen values
   monitor._component_timings = {
       component: deque(maxlen=25) for component in monitor._component_timings
   }
   ```

1. **CPU Overhead**

   ```python
   # Problem: Too frequent measurements
   # Solution: Increase intervals
   monitor._performance_interval = 300.0  # 5 minutes
   event_bus._metrics_interval = 180.0    # 3 minutes
   ```

1. **Queue Overflow**

   ```python
   # Problem: Queue too small for event volume
   # Solution: Increase queue size or add workers
   event_bus = AsyncEventBus(
       max_queue_size=50000,  # Increase capacity
       worker_count=8         # Add more workers
   )
   ```

### Diagnostic Configuration

```python
# Enable detailed diagnostics for troubleshooting
DIAGNOSTIC_CONFIG = {
    'enable_detailed_logging': True,
    'log_all_metrics': True,
    'trace_bottlenecks': True,
    'performance_alerts': True
}

# Apply diagnostic settings
if DIAGNOSTIC_CONFIG['enable_detailed_logging']:
    logging.getLogger('yesman.async_claude_monitor').setLevel(logging.DEBUG)
    logging.getLogger('yesman.async_event_bus').setLevel(logging.DEBUG)
```

## Best Practices

### 1. Configuration Management

- Store configurations in environment-specific files
- Use environment variables for sensitive settings
- Version control configuration changes
- Document configuration changes with performance impact

### 2. Performance Testing

- Establish baseline performance metrics before configuration changes
- Test configuration changes in staging environment
- Monitor resource usage after configuration updates
- Validate that monitoring itself doesn't impact performance significantly

### 3. Monitoring Monitoring

- Set up alerts for monitoring system health
- Track monitoring overhead (CPU, memory usage)
- Monitor event bus queue health
- Regular performance baseline comparisons

______________________________________________________________________

## Configuration Reference

### Default Values

```python
DEFAULT_CONFIG = {
    'event_bus': {
        'max_queue_size': 10000,
        'worker_count': 4,
        'metrics_interval': 60.0,
        'queue_update_interval': 1.0
    },
    'component_monitoring': {
        'timing_samples': 100,
        'memory_samples': 50,
        'cpu_samples': 50,
        'network_samples': 50,
        'performance_interval': 60.0
    },
    'bottleneck_thresholds': {
        'response_time_ms': 100,
        'memory_delta_mb': 5.0,
        'cpu_percent': 50.0,
        'network_mbps': 1.0
    }
}
```

This configuration guide provides comprehensive options for optimizing the monitoring system based on your specific
deployment requirements and resource constraints.
