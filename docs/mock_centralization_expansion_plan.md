# Mock Centralization Expansion Plan

## Current State Analysis

### ✅ Existing Infrastructure

- `tests/fixtures/mock_data.py`: Basic mock classes and static data
- `tests/fixtures/mock_factories.py`: New comprehensive factory system (COMPLETED)
- `tests/conftest.py`: Enhanced with factory-based fixtures (COMPLETED)

### 📊 Mock Usage Analysis Results

**High-Priority Targets (Completed Analysis):**

1. **SessionManager**: 20 duplications across 10 files
1. **ClaudeManager**: 9 duplications across 7 files
1. **subprocess.run**: 15 duplications across 8 files
1. **TmuxManager**: 6 duplications across 4 files
1. **libtmux.Server**: 4 duplications across 4 files

## Expansion Strategy

### Phase 1: Infrastructure Complete ✅

- [x] Created comprehensive `ManagerMockFactory` with 3 manager types
- [x] Created `ComponentMockFactory` for common components
- [x] Created `PatchContextFactory` for easy context management
- [x] Enhanced `conftest.py` with factory-based fixtures

### Phase 2: Integration & Migration (CURRENT)

#### 2.1 Fixture Integration Review

**Current `mock_data.py` Analysis:**

- Contains basic `MockTmuxSession`, `MockTmuxWindow`, `MockTmuxPane` classes
- Provides static data: `MOCK_SESSION_DATA`, `MOCK_PROMPTS`, `MOCK_API_RESPONSES`
- **Decision**: Keep existing basic classes, integrate with new factories

#### 2.2 Enhanced Integration Plan

```python
# Enhance mock_data.py to work with new factories
class EnhancedMockTmuxSession(MockTmuxSession):
    """Enhanced version that works with new factory system"""
    @classmethod
    def from_factory(cls, **kwargs):
        return ComponentMockFactory.create_tmux_session_mock(**kwargs)

# Add factory convenience methods
MOCK_FACTORIES = {
    'session_manager': ManagerMockFactory.create_session_manager_mock,
    'claude_manager': ManagerMockFactory.create_claude_manager_mock,
    'tmux_manager': ManagerMockFactory.create_tmux_manager_mock,
}
```

#### 2.3 Backward Compatibility Strategy

- **Keep existing mock classes** for tests that rely on them
- **Add factory alternatives** as preferred new patterns
- **Gradual migration** rather than breaking changes

### Phase 3: Progressive Migration Plan

#### 3.1 Target Files for Migration (Priority Order)

1. **commands/test_setup.py** - SessionManager (8 occurrences)
1. **api/test_sessions.py** - SessionManager + API responses (6 occurrences)
1. **commands/test_dashboard.py** - ClaudeManager (4 occurrences)
1. **tests/unit/core/test_session_manager.py** - SessionManager (high complexity)
1. **tests/integration/test_full_automation.py** - Multiple managers

#### 3.2 Migration Standards

```python
# OLD PATTERN (to be replaced)
@patch('libs.core.session_manager.SessionManager')
def test_create_session(self, mock_session_manager):
    mock_instance = MagicMock()
    mock_instance.create_session.return_value = True
    mock_instance.get_sessions.return_value = [MOCK_SESSION_DATA]
    mock_session_manager.return_value = mock_instance
    # ... test code

# NEW PATTERN (target)
def test_create_session(mock_session_manager):
    # Uses fixture from conftest.py
    # Zero setup code needed!
    # ... test code

# OR for custom behavior
def test_create_session_with_failure():
    with PatchContextFactory.patch_session_manager(create_session_result=False) as mock:
        # ... test code
```

#### 3.3 Migration Validation Process

1. **Pre-migration**: Run specific test file to get baseline
1. **Migrate**: Replace mock setup with factory/fixture
1. **Validate**: Ensure identical test behavior
1. **Performance check**: Verify no significant slowdown

## Implementation Timeline

### Week 1: Foundation Enhancement

- [x] **Day 1-2**: Create factory system (COMPLETED)
- [x] **Day 3**: Update conftest.py (COMPLETED)
- [x] **Day 4**: Create demo and documentation (COMPLETED)
- [ ] **Day 5**: Enhance mock_data.py integration

### Week 2: High-Impact Migration

- [ ] **Day 1**: Migrate commands/test_setup.py (SessionManager priority)
- [ ] **Day 2**: Migrate api/test_sessions.py (API + SessionManager)
- [ ] **Day 3**: Migrate commands/test_dashboard.py (ClaudeManager)
- [ ] **Day 4-5**: Testing and validation

### Week 3: Broader Migration

- [ ] **Day 1-2**: Migrate unit test files
- [ ] **Day 3-4**: Migrate integration tests (careful approach)
- [ ] **Day 5**: Documentation and guidelines

## Risk Mitigation

### Low-Risk Files (Start Here)

- Commands tests (isolated, straightforward)
- API route tests (standardized patterns)
- Unit tests with simple mock usage

### High-Risk Files (Later)

- Integration tests with complex mock interactions
- Tests with custom mock behaviors
- Tests with timing/async dependencies

### Rollback Strategy

- Keep original test code in comments during migration
- Use feature flags for gradual rollout
- Immediate rollback if test failure rate increases

## Success Metrics

### Quantitative Goals

- [ ] **Code Reduction**: 75% reduction in mock setup code
- [ ] **Consistency**: 100% standardized mock behavior
- [ ] **Performance**: No more than 10% test execution time increase
- [ ] **Coverage**: Maintain existing test coverage levels

### Qualitative Goals

- [ ] **Maintainability**: Easier to modify mock behaviors globally
- [ ] **Developer Experience**: Faster test writing with less boilerplate
- [ ] **Code Quality**: Consistent mock patterns across codebase

## Next Immediate Actions

1. **Enhance mock_data.py** with factory integration
1. **Create migration guide** for developers
1. **Start with lowest-risk migration** (commands/test_setup.py)
1. **Set up validation pipeline** for each migration step

## Integration Points

### Existing Systems

- Leverage current `conftest.py` structure
- Maintain compatibility with pytest fixtures
- Keep existing test data constants

### New Factory System

- Use `ManagerMockFactory` as primary pattern
- Apply `PatchContextFactory` for complex scenarios
- Utilize `ComponentMockFactory` for standard components

This expansion plan provides a systematic approach to modernizing our test infrastructure while minimizing risk and
maximizing developer productivity.
