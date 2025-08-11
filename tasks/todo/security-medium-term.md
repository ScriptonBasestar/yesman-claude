# Security Review - Medium Term Improvements

> **Priority**: Medium  
> **Timeline**: Next 2 weeks  
> **Source**: Split from security-priorities.md

## 📋 Priority 2: Test Infrastructure Security (Medium Priority)

Address 44 medium-severity security issues in test code (B108: Hardcoded temp directory). These are low-risk as they only affect test environments.

## ✅ Action Items  

- [ ] **Replace hardcoded `/tmp` with `tempfile.mkdtemp()`** - use proper temp handling in tests
- [ ] **Update test configuration** - implement platform-appropriate temp directories
- [ ] **Estimate 2-3 hours total effort** - plan incremental implementation

## ✏️ Implementation Strategy

**Files Affected**:
- `tests/integration/` directory tests
- `tests/test_agent_pool.py` 
- Various test files with B108 violations

**Approach**:
- Replace hardcoded `/tmp` paths when touching test files
- Use `tempfile.mkdtemp()` or `pytest.TempPathFactory`
- Implement during regular test maintenance
- No urgent timeline due to test-only impact

**Risk Assessment**: 
- Impact: Portability issues across operating systems
- Security Risk: LOW (test code only)
- Business Impact: MINIMAL