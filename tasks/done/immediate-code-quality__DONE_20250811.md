# Immediate Code Quality Actions

> **Priority**: Critical  
> **Timeline**: Next 1-2 weeks  
> **Source**: Split from NEXT_STEPS_RECOMMENDATIONS.md

## 🚨 Critical Quality Issues (Block Release)

Current status: 651 linting violations exceed threshold (200) - blocking quality gates

## ✅ Immediate Action Items

- [x] **Fix linting violations** - reduce from 651 to under 200 threshold
- [x] **Install and configure Bandit** for security scanning  
- [x] **Resolve event bus integration issues** in quality gates system
- [x] **Run comprehensive quality gates** to establish clean baseline

## 🔧 Implementation Commands

```bash
# Fix quality gates first
python scripts/run_quality_gates.py --comprehensive

# Then establish clean baseline  
python scripts/establish_baseline.py --establish --duration 300

# Verify async integration works
python scripts/test_async_integration.py
```

## ✏️ Implementation Details

**Linting Strategy**:
1. Use automated linting fixes where possible (`ruff --fix`)
2. Manual review for complex violations
3. Document exceptions for legitimate edge cases

**Security Integration**:
- Install Bandit security scanner in CI/CD pipeline
- Configure security thresholds and reporting
- Address any high/medium severity findings

**Event Bus Debugging**:
- Check AsyncEventBus initialization in quality gates
- Verify event bus worker configuration
- Test event bus connection stability