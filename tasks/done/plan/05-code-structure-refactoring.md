---
status: converted
converted_at: 2025-07-16
todo_files:
  - /tasks/todo/phase-2/001-create-mixins.md
  - /tasks/todo/phase-2/002-create-base-batch-processor.md
  - /tasks/todo/phase-2/003-create-validation-utils.md
  - /tasks/todo/phase-2/004-create-session-helpers.md
  - /tasks/todo/phase-2/005-refactor-existing-modules.md
  - /tasks/todo/phase-3/001-migrate-commands-to-basecommand.md
  - /tasks/todo/phase-3/002-create-dependency-injection.md
  - /tasks/todo/phase-3/003-centralize-configuration.md
  - /tasks/todo/phase-3/004-standardize-error-handling.md
  - /tasks/todo/phase-3/005-documentation-and-testing.md
---

# Code Structure Refactoring Plan

## Overview

This document outlines a comprehensive plan to improve the Yesman-Claude project structure by eliminating duplicate
code, standardizing patterns, and enhancing maintainability.

## Current State Analysis

### 1. Duplicate Implementations

The codebase contains several instances of duplicate or near-duplicate implementations:

#### Command Duplicates

- **ls.py vs ls_improved.py**: Both implement template/project listing functionality

  - `ls.py`: Original implementation with basic functionality
  - `ls_improved.py`: Refactored with BaseCommand pattern, better error handling

- **setup.py vs setup_improved.py**: Similar duplication pattern

  - `setup.py`: Original setup command
  - `setup_improved.py`: Enhanced with dependency injection and improved validation

#### API Router Duplicates

- **sessions.py vs sessions_improved.py**: Session management endpoints
  - `sessions.py`: Direct implementation with basic functionality
  - `sessions_improved.py`: Includes dependency injection, singleton management, better error handling

#### Batch Processor Duplicates

- **libs/logging/batch_processor.py**: Handles log batching for file I/O
- **api/utils/batch_processor.py**: Handles WebSocket message batching
- Both share similar structure (MessageBatch/LogBatch, flush mechanisms, statistics)

### 2. Repeated Patterns

Common patterns found across multiple files:

#### Statistics Pattern

- `get_statistics()` method appears in:
  - `libs/logging/async_logger.py`
  - `libs/logging/batch_processor.py`
  - `api/utils/batch_processor.py`
  - `libs/ai/response_analyzer.py`

#### Status Management Pattern

- `update_status()` / `update_activity()` methods in:
  - `commands/status.py`
  - `commands/browse.py`
  - `libs/dashboard/tui_dashboard.py`
  - Multiple dashboard widgets

#### Layout Management Pattern

- `create_layout()` / `update_layout()` in:
  - `commands/status.py`
  - `commands/browse.py`

#### Validation Pattern

- Session name validation scattered across modules
- Precondition checks duplicated in multiple places

### 3. Structural Issues

#### Test Directory Duplication

- `/test-integration/` and `/tests/integration/` contain similar integration test setups
- Duplicate test helpers and fixtures

#### Inconsistent Patterns

- Some commands use BaseCommand, others don't
- Singleton implementation varies across modules
- Dependency injection only in some API routers

## Refactoring Plan

### Phase 1: Remove Duplicates (Week 1)

#### 1.1 Command Consolidation

```
Actions:
- Delete commands/ls.py, rename ls_improved.py → ls.py
- Delete commands/setup.py, rename setup_improved.py → setup.py
- Update all imports and references
- Run tests to ensure functionality preserved
```

#### 1.2 API Router Consolidation

```
Actions:
- Delete api/routers/sessions.py, rename sessions_improved.py → sessions.py
- Update router imports in api/main.py
- Verify all endpoints still functional
```

#### 1.3 Test Directory Merger

```
Actions:
- Merge test-integration content into tests/integration
- Consolidate duplicate test utilities
- Update test scripts and CI/CD references
```

### Phase 2: Extract Common Patterns (Week 2)

#### 2.1 Create Base Classes

**libs/core/mixins.py**

```python
class StatisticsProviderMixin:
    """Mixin for classes that provide statistics"""
    def get_statistics(self) -> dict[str, Any]:
        raise NotImplementedError

class StatusManagerMixin:
    """Mixin for status and activity management"""
    def update_status(self, status: str) -> None:
        raise NotImplementedError
    
    def update_activity(self, activity: str) -> None:
        raise NotImplementedError

class LayoutManagerMixin:
    """Mixin for layout management"""
    def create_layout(self) -> Any:
        raise NotImplementedError
    
    def update_layout(self, layout: Any) -> None:
        raise NotImplementedError
```

**libs/core/base_batch_processor.py**

```python
class BaseBatchProcessor[T]:
    """Generic batch processor for any type of items"""
    def __init__(self, batch_size: int, flush_interval: float):
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self._batch: list[T] = []
        self._lock = threading.Lock()
    
    def add(self, item: T) -> None:
        """Add item to batch"""
        pass
    
    def flush(self) -> None:
        """Flush current batch"""
        pass
    
    def get_statistics(self) -> dict[str, Any]:
        """Get processor statistics"""
        pass
```

#### 2.2 Create Utility Modules

**libs/utils/validation.py**

```python
def validate_session_name(name: str) -> bool:
    """Validate tmux session name"""
    pass

def validate_project_name(name: str) -> bool:
    """Validate project name"""
    pass

def validate_template_exists(template: str) -> bool:
    """Check if template exists"""
    pass
```

**libs/utils/session_helpers.py**

```python
def get_session_info(session_name: str) -> SessionInfo:
    """Get session information"""
    pass

def create_session_windows(session_name: str, template: dict) -> None:
    """Create windows for session from template"""
    pass
```

### Phase 3: Standardize Architecture (Week 3)

#### 3.1 Command Pattern Migration

```
Actions:
- Migrate all commands to use BaseCommand
- Standardize command initialization
- Implement consistent error handling
- Add command-specific configuration loading
```

#### 3.2 Dependency Injection Standardization

```
Actions:
- Create dependency injection container
- Standardize singleton management
- Apply to all API routers
- Document injection patterns
```

#### 3.3 Configuration Management

```
Actions:
- Centralize configuration loading
- Implement configuration validation
- Create configuration schema
- Add environment-specific overrides
```

## Implementation Strategy

### Migration Order

1. **Low Risk**: Remove obvious duplicates (ls.py, setup.py)
1. **Medium Risk**: Extract mixins and base classes
1. **High Risk**: Architectural changes (DI, command patterns)

### Testing Strategy

- Create comprehensive test suite before changes
- Test each phase independently
- Maintain backward compatibility
- Performance benchmarks before/after

### Rollback Plan

- Git tags at each phase completion
- Feature flags for major changes
- Parallel implementation where needed
- Gradual migration for critical paths

## Success Metrics

### Code Quality

- [ ] Duplicate code reduced by 30%
- [ ] All commands use BaseCommand pattern
- [ ] Consistent error handling across modules
- [ ] Test coverage maintained or improved

### Maintainability

- [ ] Single source of truth for common patterns
- [ ] Clear separation of concerns
- [ ] Documented architectural decisions
- [ ] Simplified onboarding for new developers

### Performance

- [ ] No regression in response times
- [ ] Memory usage stable or improved
- [ ] Batch processing efficiency maintained

## Risks and Mitigation

### Risk 1: Breaking Changes

**Mitigation**: Comprehensive test suite, phased rollout, feature flags

### Risk 2: Performance Regression

**Mitigation**: Benchmark critical paths, profile before/after changes

### Risk 3: Integration Issues

**Mitigation**: Integration tests, staged deployment, monitoring

## Timeline

- **Week 1**: Phase 1 - Remove duplicates
- **Week 2**: Phase 2 - Extract common patterns
- **Week 3**: Phase 3 - Standardize architecture
- **Week 4**: Testing, documentation, and cleanup

## Next Steps

1. Review and approve this plan
1. Create feature branch for refactoring
1. Set up additional tests for affected areas
1. Begin Phase 1 implementation
1. Regular progress reviews

______________________________________________________________________

*This plan aims to improve code quality while maintaining all existing functionality. Each phase will be thoroughly
tested before proceeding to the next.*
