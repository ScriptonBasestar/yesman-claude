# Test Infrastructure Enhancement & CI/CD Integration

**Priority:** HIGH  
**Status:** TODO  
**Estimated Effort:** 3-4 days  
**Dependencies:** Recovered test infrastructure, monitoring dashboard integration

## Overview

Enhance the recovered test infrastructure with advanced testing strategies and integrate with the monitoring system for test performance tracking. This builds on the comprehensive test infrastructure recovery that was recently completed.

## Problem Statement

While the test infrastructure has been recovered and optimized, several advanced testing capabilities are missing:

- **Limited Test Coverage Types**: Only unit/integration tests, missing property-based and contract testing
- **No Test Performance Monitoring**: Cannot identify slow or degrading tests
- **Missing Chaos Engineering**: No resilience testing for failure scenarios
- **Lack of Test Analytics**: No insights into test effectiveness and performance trends

## Implementation Plan

### Phase 1: Advanced Testing Frameworks (Day 1-2)

**1.1 Property-Based Testing with Hypothesis**
```python
# tests/property/test_session_management.py
from hypothesis import given, strategies as st
from libs.core.session_management import SessionManager

@given(
    session_name=st.text(min_size=1, max_size=64, alphabet=st.characters(whitelist_categories=('Ll', 'Lu', 'Nd'))),
    session_data=st.dictionaries(
        keys=st.text(min_size=1, max_size=50),
        values=st.one_of(st.text(), st.integers(), st.booleans())
    )
)
def test_session_roundtrip_properties(session_name, session_data):
    """Property test: session data should survive save/load cycles."""
    manager = SessionManager()
    
    # Property: saving and loading should preserve data
    manager.save_session(session_name, session_data)
    loaded_data = manager.load_session(session_name)
    
    assert loaded_data == session_data
```

**1.2 Contract Testing for APIs**
```python
# tests/contract/test_api_contracts.py
import pact
from pact import Consumer, Provider, Term

def test_claude_api_contract():
    """Test API contract between our service and Claude API."""
    pact = Consumer('yesman-claude').has_pact_with(Provider('claude-api'))
    
    (pact
     .given('a valid session exists')
     .upon_receiving('a request for session status')
     .with_request(method='GET', path=Term(r'/sessions/\d+', '/sessions/123'))
     .will_respond_with(200, body={
         'session_id': Term(r'\d+', '123'),
         'status': Term(r'(active|inactive|error)', 'active'),
         'last_activity': Term(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', '2024-01-01T12:00:00Z')
     }))
```

**1.3 Test Data Factories**
```python
# tests/factories.py
import factory
from faker import Faker
from libs.core.models import Session, User, ProcessInstance

fake = Faker()

class SessionFactory(factory.Factory):
    class Meta:
        model = Session
    
    name = factory.LazyAttribute(lambda o: fake.slug())
    status = factory.Iterator(['active', 'inactive', 'error'])
    created_at = factory.LazyFunction(lambda: fake.date_time_this_year())
    config = factory.SubFactory('ConfigFactory')

class UserFactory(factory.Factory):
    class Meta:
        model = User
    
    username = factory.LazyAttribute(lambda o: fake.user_name())
    email = factory.LazyAttribute(lambda o: fake.email())
    preferences = factory.Dict({
        'theme': factory.Iterator(['light', 'dark']),
        'notifications': factory.Iterator([True, False])
    })
```

### Phase 2: Test Performance Monitoring (Day 2-3)

**2.1 Test Execution Metrics Collection**
```python
# tests/conftest.py
import time
import pytest
from libs.dashboard.monitoring_integration import get_monitoring_dashboard

@pytest.fixture(autouse=True)
def test_performance_tracking(request):
    """Automatically track test performance."""
    start_time = time.perf_counter()
    monitoring = get_monitoring_dashboard()
    
    yield
    
    duration = time.perf_counter() - start_time
    test_name = f"{request.module.__name__}::{request.function.__name__}"
    
    # Publish test metrics
    asyncio.create_task(monitoring.publish_test_metrics({
        'test_name': test_name,
        'duration_ms': duration * 1000,
        'status': 'passed' if request.session.testsfailed == 0 else 'failed',
        'timestamp': time.time()
    }))
```

**2.2 Test Performance Dashboard Integration**
```python
# libs/dashboard/test_metrics_integration.py
from enum import Enum
from dataclasses import dataclass

class TestMetricType(Enum):
    EXECUTION_TIME = "test_execution_time"
    FAILURE_RATE = "test_failure_rate"
    COVERAGE = "test_coverage"
    FLAKINESS = "test_flakiness"

@dataclass
class TestPerformanceMetrics:
    test_suite: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    total_duration_ms: float
    average_test_duration_ms: float
    slowest_tests: list[tuple[str, float]]
    coverage_percent: float
    flaky_tests: list[str]
```

### Phase 3: Chaos Engineering Tests (Day 3-4)

**3.1 Network Failure Simulation**
```python
# tests/chaos/test_network_failures.py
import pytest
import asyncio
from unittest.mock import patch
from libs.core.claude_monitor_async import AsyncClaudeMonitor

@pytest.mark.chaos
async def test_claude_monitor_network_timeout():
    """Test system behavior during network timeouts."""
    monitor = AsyncClaudeMonitor()
    
    with patch('aiohttp.ClientSession.get') as mock_get:
        # Simulate network timeout
        mock_get.side_effect = asyncio.TimeoutError()
        
        # System should degrade gracefully
        result = await monitor.check_claude_status()
        
        assert result.status == 'degraded'
        assert 'network_timeout' in result.error_details

@pytest.mark.chaos
async def test_memory_pressure_handling():
    """Test system behavior under memory pressure."""
    import psutil
    import gc
    
    # Create memory pressure
    memory_hog = []
    available_mb = psutil.virtual_memory().available / 1024 / 1024
    
    try:
        # Consume 80% of available memory
        for _ in range(int(available_mb * 0.8)):
            memory_hog.append([0] * 1024)  # 1MB chunks
        
        # System should handle gracefully
        monitor = AsyncClaudeMonitor()
        await monitor.start_monitoring_async()
        
        # Should not crash and should report memory pressure
        metrics = monitor.get_current_metrics()
        assert metrics.memory_pressure_detected is True
        
    finally:
        del memory_hog
        gc.collect()
```

**3.2 Resource Exhaustion Tests**
```python
# tests/chaos/test_resource_exhaustion.py
@pytest.mark.chaos
async def test_file_descriptor_exhaustion():
    """Test behavior when file descriptors are exhausted."""
    import resource
    
    # Get current limits
    soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)
    
    # Temporarily reduce limit
    resource.setrlimit(resource.RLIMIT_NOFILE, (50, hard))
    
    try:
        # Try to create many sessions
        session_manager = SessionManager()
        sessions = []
        
        for i in range(60):  # More than the limit
            try:
                session = await session_manager.create_session(f"test_session_{i}")
                sessions.append(session)
            except OSError:
                # Should handle gracefully
                break
        
        # System should not crash and should report resource exhaustion
        assert session_manager.get_health_status().resource_warnings
        
    finally:
        resource.setrlimit(resource.RLIMIT_NOFILE, (soft, hard))
```

### Phase 4: Test Analytics and Reporting (Day 4)

**4.1 Test Performance Baselines**
```python
# scripts/test_baseline_manager.py
class TestBaselineManager:
    def __init__(self):
        self.baselines_file = Path("data/test_baselines.json")
        self.baselines = self._load_baselines()
    
    def update_baseline(self, test_name: str, duration_ms: float) -> None:
        """Update performance baseline for a test."""
        if test_name not in self.baselines:
            self.baselines[test_name] = {
                'samples': [],
                'baseline_ms': duration_ms,
                'variance_threshold': 0.2  # 20% variance allowed
            }
        
        samples = self.baselines[test_name]['samples']
        samples.append(duration_ms)
        
        # Keep only recent samples
        if len(samples) > 100:
            samples = samples[-100:]
        
        # Recalculate baseline
        if len(samples) >= 10:
            self.baselines[test_name]['baseline_ms'] = statistics.median(samples)
    
    def check_regression(self, test_name: str, duration_ms: float) -> bool:
        """Check if test duration represents a performance regression."""
        if test_name not in self.baselines:
            return False
        
        baseline = self.baselines[test_name]['baseline_ms']
        threshold = self.baselines[test_name]['variance_threshold']
        
        return duration_ms > baseline * (1 + threshold)
```

**4.2 Automated Test Reporting**
```python
# scripts/test_report_generator.py
class TestReportGenerator:
    def generate_performance_report(self) -> dict:
        """Generate comprehensive test performance report."""
        return {
            'summary': {
                'total_tests': len(self.test_results),
                'avg_duration_ms': statistics.mean(r.duration_ms for r in self.test_results),
                'slowest_tests': sorted(self.test_results, key=lambda x: x.duration_ms, reverse=True)[:10],
                'fastest_tests': sorted(self.test_results, key=lambda x: x.duration_ms)[:10],
                'flaky_tests': self._identify_flaky_tests(),
                'regression_alerts': self._check_regressions()
            },
            'coverage': self._get_coverage_metrics(),
            'trends': self._analyze_trends(),
            'recommendations': self._generate_recommendations()
        }
    
    def _identify_flaky_tests(self) -> list[str]:
        """Identify tests with inconsistent results."""
        flaky = []
        for test_name, results in self.test_history.items():
            if len(results) > 10:
                failure_rate = sum(1 for r in results if not r.passed) / len(results)
                duration_variance = statistics.stdev([r.duration_ms for r in results])
                
                if 0.1 < failure_rate < 0.9 or duration_variance > results[0].duration_ms * 0.5:
                    flaky.append(test_name)
        
        return flaky
```

## Technical Implementation

### File Structure

```
tests/
├── property/              # Property-based tests
│   ├── test_session_management.py
│   ├── test_process_control.py
│   └── test_event_bus.py
├── contract/             # Contract tests
│   ├── test_api_contracts.py
│   └── test_internal_contracts.py
├── chaos/                # Chaos engineering tests
│   ├── test_network_failures.py
│   ├── test_resource_exhaustion.py
│   └── test_dependency_failures.py
├── performance/          # Performance benchmark tests
│   ├── test_monitoring_benchmarks.py
│   └── test_event_bus_benchmarks.py
├── factories.py          # Test data factories
└── conftest.py          # Enhanced pytest configuration

scripts/
├── test_baseline_manager.py
├── test_report_generator.py
└── chaos_test_runner.py

libs/dashboard/
└── test_metrics_integration.py
```

### Makefile Integration

```makefile
# Enhanced test targets in Makefile.test.mk
test-property:
	@echo "Running property-based tests..."
	uv run pytest tests/property/ -v --maxfail=1

test-contract:
	@echo "Running contract tests..."
	uv run pytest tests/contract/ -v

test-chaos:
	@echo "Running chaos engineering tests..."
	uv run pytest tests/chaos/ -v -m chaos --tb=short

test-performance:
	@echo "Running performance benchmark tests..."
	uv run pytest tests/performance/ -v --benchmark-only

test-all-enhanced: test-property test-contract test-performance
	@echo "All enhanced tests completed"
```

## Success Criteria

### Functional Requirements
- [x] Property-based tests validate core invariants
- [x] Contract tests ensure API compatibility
- [x] Chaos tests validate system resilience
- [x] Test performance metrics integrated into monitoring dashboard
- [x] Automated test regression detection

### Performance Requirements
- [x] Test performance monitoring adds <1ms overhead per test
- [x] Chaos tests complete within reasonable timeframes
- [x] Performance benchmarks provide stable baselines

### Quality Requirements
- [x] Test coverage increased by at least 20%
- [x] Flaky test detection and reporting
- [x] Test performance regression alerts

## Deliverables

1. **Enhanced Test Suite**
   - Property-based tests for core components
   - Contract tests for API reliability
   - Chaos engineering test scenarios
   - Performance benchmark tests

2. **Test Performance Monitoring**
   - Test execution metrics collection
   - Integration with monitoring dashboard
   - Performance regression detection
   - Automated reporting

3. **Test Analytics System**
   - Test performance baselines
   - Flaky test identification
   - Test effectiveness metrics
   - Optimization recommendations

4. **Documentation**
   - Enhanced testing guide
   - Chaos engineering playbook
   - Test performance analysis guide

## Follow-up Opportunities

1. **AI-Powered Test Generation**: Use LLMs to generate additional test cases
2. **Visual Test Reporting**: Create interactive test performance dashboards
3. **Predictive Test Analytics**: Predict test failures based on code changes
4. **Distributed Testing**: Scale chaos testing across multiple environments

---

**Files to Create:**
- `tests/property/` directory with property-based tests
- `tests/contract/` directory with API contract tests  
- `tests/chaos/` directory with chaos engineering tests
- `scripts/test_baseline_manager.py`
- `scripts/test_report_generator.py`
- `libs/dashboard/test_metrics_integration.py`

**Files to Modify:**
- `tests/conftest.py` - Add performance tracking
- `Makefile.test.mk` - Add new test targets
- `libs/dashboard/monitoring_integration.py` - Add test metrics support
- `tauri-dashboard/src/lib/components/` - Add test performance widgets