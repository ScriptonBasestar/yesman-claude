# Test Naming Standards & pytest Migration Guide

## Overview

This document defines standardized naming conventions and pytest migration guidelines for the Yesman-Claude project. The
goal is to improve test readability, maintainability, and developer experience.

## 📋 Naming Standards

### 1. Test File Naming

```
test_<module>_<feature>.py
```

**Examples:**

- `test_session_manager_creation.py` - SessionManager creation functionality
- `test_claude_manager_monitoring.py` - ClaudeManager monitoring features
- `test_dashboard_rendering.py` - Dashboard rendering capabilities
- `test_api_session_endpoints.py` - API session-related endpoints

### 2. Test Class Naming

```
Test<Module><Feature>
```

**Examples:**

- `TestSessionManagerCreation` - Tests for session creation functionality
- `TestClaudeManagerMonitoring` - Tests for Claude monitoring features
- `TestDashboardRendering` - Tests for dashboard rendering
- `TestApiSessionEndpoints` - Tests for API session endpoints

### 3. Test Function Naming

```
test_<action>_<condition>_<expected_result>
```

**Pattern Components:**

- **action**: What the test is doing (create, start, stop, validate, etc.)
- **condition**: Under what circumstances (with_valid_input, when_missing_file, etc.)
- **expected_result**: What should happen (should_succeed, should_raise_error, etc.)

**Examples:**

```python
# Good examples
def test_create_session_with_valid_config_should_succeed():
def test_start_session_when_already_running_should_skip():
def test_validate_config_with_missing_file_should_raise_error():
def test_parse_template_with_variables_should_substitute_values():
def test_stop_controller_when_not_running_should_return_false():

# Avoid these patterns
def test_session():  # Too vague
def test_create():   # Missing context
def test_error():    # Unclear what causes error
```

### 4. Test Scenario Documentation

Each test should include a clear docstring following this pattern:

```python
def test_create_session_with_valid_config_should_succeed(self):
    """
    Test that session creation succeeds when provided with valid configuration.
    
    Given: A valid session configuration with all required fields
    When: create_session() is called
    Then: Session should be created successfully and return True
    """
```

## 🔄 unittest → pytest Migration

### 1. Class Structure Migration

**Before (unittest):**

```python
import unittest
from unittest.mock import Mock

class TestSessionManager(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()
        
    def tearDown(self):
        self.manager.cleanup()
        
    def test_create_session(self):
        result = self.manager.create_session("test")
        self.assertTrue(result)
        self.assertEqual(self.manager.session_count, 1)
```

**After (pytest):**

```python
import pytest
from unittest.mock import Mock

class TestSessionManager:
    @pytest.fixture
    def manager(self):
        manager = SessionManager()
        yield manager
        manager.cleanup()
        
    def test_create_session_with_valid_name_should_succeed(self, manager):
        """Test that session creation succeeds with valid session name."""
        result = manager.create_session("test")
        assert result is True
        assert manager.session_count == 1
```

### 2. Assertion Migration

| unittest                    | pytest             | Notes             |
| --------------------------- | ------------------ | ----------------- |
| `self.assertTrue(x)`        | `assert x`         | Simple boolean    |
| `self.assertFalse(x)`       | `assert not x`     | Negation          |
| `self.assertEqual(a, b)`    | `assert a == b`    | Equality          |
| `self.assertNotEqual(a, b)` | `assert a != b`    | Inequality        |
| `self.assertIn(a, b)`       | `assert a in b`    | Membership        |
| `self.assertIsNone(x)`      | `assert x is None` | None check        |
| `self.assertRaises(E)`      | `pytest.raises(E)` | Exception testing |

### 3. Mock Integration

**Before (unittest):**

```python
@patch('module.ClassName')
def test_with_mock(self, mock_class):
    mock_instance = Mock()
    mock_class.return_value = mock_instance
    # test code
```

**After (pytest with centralized mocks):**

```python
def test_with_mock(mock_session_manager):
    # Uses centralized fixture from conftest.py
    # No setup needed!
    # test code
```

## 🚀 Migration Strategy

### Phase 1: Standards Documentation ✅

- [x] Define comprehensive naming standards
- [x] Create migration guidelines
- [x] Document best practices

### Phase 2: New Test Standards (Immediate)

- [ ] Apply standards to all new tests
- [ ] Add pre-commit hook for validation
- [ ] Create test template files

### Phase 3: Core File Migration (Gradual)

- [ ] Migrate most critical test files first
- [ ] Focus on files with highest change frequency
- [ ] Validate each migration thoroughly

### Phase 4: Automation Tools

- [ ] Create automated migration scripts
- [ ] Build validation tools
- [ ] Add lint rules for enforcement

## 📂 File Organization Standards

### Directory Structure

```
tests/
├── unit/                    # Unit tests
│   ├── commands/           # Command-specific tests
│   ├── libs/              # Library module tests
│   └── api/               # API-related tests
├── integration/            # Integration tests
├── fixtures/              # Test fixtures and mocks
│   ├── mock_data.py       # Static mock data
│   ├── mock_factories.py  # Mock factory classes
│   └── test_helpers.py    # Test utility functions
└── conftest.py            # Global pytest configuration
```

### Test File Organization

```python
"""
Test module for SessionManager creation functionality.

This module tests all aspects of session creation including:
- Valid configuration handling
- Error conditions and edge cases
- Integration with template system
"""

import pytest
from unittest.mock import Mock
# ... other imports

# Test data constants
VALID_SESSION_CONFIG = {...}
INVALID_SESSION_CONFIG = {...}

class TestSessionManagerCreation:
    """Tests for SessionManager session creation functionality."""
    
    @pytest.fixture
    def session_config(self):
        """Provide valid session configuration for tests."""
        return VALID_SESSION_CONFIG.copy()
    
    def test_create_session_with_valid_config_should_succeed(self, session_config):
        """Test successful session creation with valid configuration."""
        # Test implementation
        
    def test_create_session_with_invalid_config_should_raise_error(self):
        """Test that invalid configuration raises appropriate error."""
        # Test implementation
```

## 🔍 Quality Standards

### Test Quality Checklist

- [ ] Clear, descriptive test names
- [ ] Comprehensive docstrings
- [ ] Proper Given-When-Then structure
- [ ] Single responsibility per test
- [ ] Clear assertion messages
- [ ] Appropriate use of fixtures
- [ ] Minimal test setup/teardown

### Code Quality Standards

```python
# Good test example
def test_validate_session_config_with_missing_name_should_raise_validation_error(self):
    """
    Test that session validation fails when session name is missing.
    
    Given: A session configuration without a session name
    When: validate_session_config() is called  
    Then: ValidationError should be raised with appropriate message
    """
    config = {"template": "django.yaml"}  # Missing session_name
    
    with pytest.raises(ValidationError) as exc_info:
        validate_session_config(config)
    
    assert "session_name is required" in str(exc_info.value)
```

## 🛠️ Tools and Automation

### Pre-commit Hook Configuration

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: test-naming-check
        name: Test Naming Standards Check
        entry: python -m sb_libs_py.test_naming_validator
        language: python
        files: ^tests/.*\.py$
```

### Automated Migration Script

```python
#!/usr/bin/env python3
"""
Automated unittest to pytest migration script.
Converts basic unittest patterns to pytest equivalents.
"""

import re
import sys
from pathlib import Path

class UnittestToPytestMigrator:
    """Migrates unittest test files to pytest format."""
    
    def __init__(self):
        self.patterns = [
            (r'self\.assertTrue\((.+?)\)', r'assert \1'),
            (r'self\.assertFalse\((.+?)\)', r'assert not \1'),
            (r'self\.assertEqual\((.+?), (.+?)\)', r'assert \1 == \2'),
            # ... more patterns
        ]
    
    def migrate_file(self, file_path: Path) -> bool:
        """Migrate a single test file."""
        # Implementation details
        pass
```

### Validation Tools

```python
#!/usr/bin/env python3
"""
Test naming validation script.
Checks that test files follow naming standards.
"""

def validate_test_naming(file_path: Path) -> list:
    """Validate test file naming conventions."""
    violations = []
    
    # Check file naming
    if not file_path.name.startswith('test_'):
        violations.append(f"File {file_path} should start with 'test_'")
    
    # Check function naming
    with open(file_path) as f:
        content = f.read()
        
    for match in re.finditer(r'def (test_\w+)', content):
        func_name = match.group(1)
        if not is_valid_test_name(func_name):
            violations.append(f"Function {func_name} doesn't follow naming convention")
    
    return violations
```

## 📊 Progress Tracking

### Migration Status Dashboard

```
Test File Migration Progress:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 15/50 (30%)

By Category:
├── Commands Tests:     ████████░░ 8/10 (80%)
├── Core Library Tests: ███░░░░░░░ 3/15 (20%) 
├── API Tests:          ██████████ 4/4 (100%)
├── Dashboard Tests:    ░░░░░░░░░░ 0/12 (0%)
└── Integration Tests:  ░░░░░░░░░░ 0/9 (0%)

Priority Files Remaining:
- test_session_manager.py (high priority)
- test_claude_manager.py (high priority)  
- test_dashboard_controller.py (medium priority)
```

## 💡 Best Practices

### 1. Test Organization

- Group related tests in classes
- Use descriptive class and method names
- Keep tests focused and atomic
- Use fixtures for common setup

### 2. Mock Usage

- Prefer centralized mock factories
- Use context managers for patching
- Mock at the boundary of your unit
- Verify mock interactions when relevant

### 3. Assertion Best Practices

- Use specific assertions over generic ones
- Include helpful error messages
- Test both positive and negative cases
- Avoid testing implementation details

### 4. Documentation

- Write clear docstrings for complex tests
- Document test data and fixtures
- Explain non-obvious test logic
- Keep documentation up-to-date

## 🎯 Implementation Timeline

### Week 1: Foundation

- [x] Create standards documentation
- [ ] Set up validation tools
- [ ] Create migration scripts
- [ ] Add pre-commit hooks

### Week 2: Core Migration

- [ ] Migrate critical test files
- [ ] Apply naming standards to new tests
- [ ] Validate migration results
- [ ] Update CI/CD pipeline

### Week 3: Broader Migration

- [ ] Migrate remaining high-priority files
- [ ] Full validation and testing
- [ ] Performance analysis
- [ ] Documentation updates

### Week 4: Finalization

- [ ] Complete remaining migrations
- [ ] Final quality review
- [ ] Tool refinement
- [ ] Team training and rollout

This comprehensive standards document provides a clear roadmap for test naming standardization and pytest migration,
ensuring consistency and maintainability across the test suite.
