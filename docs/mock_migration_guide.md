# Mock Migration Guide

## Quick Reference

### Before (Old Pattern) → After (New Pattern)

#### ❌ Old: Manual Mock Setup (15+ lines)

```python
@patch('libs.core.session_manager.SessionManager')
def test_create_session(self, mock_session_manager):
    # Repetitive setup in every test
    mock_instance = MagicMock()
    mock_instance.create_session.return_value = True
    mock_instance.get_sessions.return_value = [{
        "session_name": "test-session", 
        "status": "active"
    }]
    mock_instance.session_exists.return_value = True
    mock_session_manager.return_value = mock_instance
    
    # Actual test (2 lines)
    result = my_function()
    assert result is True
```

#### ✅ New: Factory-Based (2 lines)

```python
def test_create_session(mock_session_manager):
    # Zero setup - fixture handles everything!
    result = my_function()
    assert result is True
```

## Migration Patterns

### 1. Using pytest Fixtures (Recommended)

**Auto-injection via conftest.py:**

```python
# Old way
@patch('libs.core.session_manager.SessionManager')
def test_something(self, mock_session_manager):
    mock_instance = create_long_setup()
    mock_session_manager.return_value = mock_instance
    
# New way - uses fixture from conftest.py
def test_something(mock_session_manager):
    # Ready to use immediately!
```

**Available fixtures:**

- `mock_session_manager` - StandardSessionManager
- `mock_claude_manager` - ClaudeManager with default controller
- `mock_tmux_manager` - TmuxManager with standard sessions
- `mock_subprocess_result` - subprocess.run result
- `mock_api_response` - HTTP response mock

### 2. Custom Mock Behavior

#### Method A: Context Factory (Best for isolation)

```python
from tests.fixtures.mock_factories import PatchContextFactory

def test_session_creation_failure():
    with PatchContextFactory.patch_session_manager(
        create_session_result=False,
        sessions=[]
    ) as mock_manager:
        result = create_session("test")
        assert result is False
        mock_manager.create_session.assert_called_once()
```

#### Method B: Direct Factory Usage

```python
from tests.fixtures.mock_factories import ManagerMockFactory

def test_multiple_sessions():
    custom_sessions = [
        {"session_name": "session1", "status": "active"},
        {"session_name": "session2", "status": "stopped"}
    ]
    
    mock_manager = ManagerMockFactory.create_session_manager_mock(
        sessions=custom_sessions
    )
    
    with patch('my.module.SessionManager', return_value=mock_manager):
        # Test code here
```

#### Method C: Bridge Function (Transitional)

```python
from tests.fixtures.mock_data import get_factory_mock

def test_with_bridge():
    mock_manager = get_factory_mock('session_manager', 
                                   sessions=[{"session_name": "test"}])
    # Use the mock
```

### 3. Migration Steps for Each File

1. **Identify mock patterns** in the file
1. **Replace setup code** with fixture usage
1. **Run tests** to verify behavior
1. **Clean up** unused imports and patch decorators

#### Example Migration

**File: `tests/commands/test_setup.py`**

```python
# BEFORE (Pattern found 8 times in file)
class TestSetupCommand:
    @patch('commands.setup.SessionManager')
    def test_setup_creates_sessions(self, mock_session_manager):
        # 15 lines of mock setup
        mock_instance = MagicMock()
        mock_instance.create_session.return_value = True
        mock_instance.get_sessions.return_value = [MOCK_SESSION_DATA]
        mock_instance.session_exists.return_value = False
        mock_session_manager.return_value = mock_instance
        
        runner = CliRunner()
        result = runner.invoke(setup, ['--all'])
        
        assert result.exit_code == 0
        mock_instance.create_session.assert_called()

# AFTER (Reduced to 2 lines per test)
class TestSetupCommand:
    def test_setup_creates_sessions(self, mock_session_manager):
        runner = CliRunner()
        result = runner.invoke(setup, ['--all'])
        
        assert result.exit_code == 0
        mock_session_manager.create_session.assert_called()
        
    def test_setup_with_existing_session(self):
        # For custom behavior, use context factory
        with PatchContextFactory.patch_session_manager(
            session_exists_result=True
        ):
            runner = CliRunner()
            result = runner.invoke(setup, ['existing-session'])
            assert "already exists" in result.output
```

## Advanced Patterns

### Error Simulation

```python
def test_validation_error():
    def raise_validation_error(name):
        if name == "invalid":
            raise ValueError("Invalid session name")
    
    with PatchContextFactory.patch_session_manager(
        validate_session_name_side_effect=raise_validation_error
    ) as mock:
        with pytest.raises(ValueError):
            validate_session("invalid")
```

### Integration Test Mocks

```python
from tests.fixtures.mock_data import create_mock_session_with_controller

def test_full_workflow():
    mocks = create_mock_session_with_controller(
        sessions=[{"session_name": "integration-test"}],
        controller_count=2
    )
    
    with patch.multiple(
        'my.module',
        SessionManager=lambda: mocks['session_manager'],
        ClaudeManager=lambda: mocks['claude_manager']
    ):
        # Full workflow test
```

### API Test Patterns

```python
from tests.fixtures.mock_data import create_api_test_mocks

def test_api_success():
    mocks = create_api_test_mocks(success=True)
    
    with patch('api.routes.SessionManager', return_value=mocks['session_manager']):
        response = client.get("/api/sessions")
        assert response.status_code == 200

def test_api_failure():
    mocks = create_api_test_mocks(success=False)
    
    with patch('api.routes.SessionManager', return_value=mocks['session_manager']):
        response = client.post("/api/sessions", json={"name": "test"})
        assert response.status_code == 500
```

## Migration Checklist

### Before Migration

- [ ] Run existing tests to get baseline success rate
- [ ] Identify all mock patterns in the file
- [ ] Note any custom mock behaviors or edge cases

### During Migration

- [ ] Replace mock setup with fixture usage
- [ ] Remove unused imports and decorators
- [ ] Handle custom behaviors with context factories
- [ ] Verify test names and assertions remain unchanged

### After Migration

- [ ] Run tests to ensure same behavior
- [ ] Check code coverage hasn't decreased
- [ ] Verify performance hasn't degraded significantly
- [ ] Update any test documentation

### Validation Commands

```bash
# Run specific test file
python -m pytest tests/commands/test_setup.py -v

# Run with coverage
python -m pytest tests/commands/test_setup.py --cov=commands.setup

# Run performance comparison
python -m pytest tests/commands/test_setup.py --durations=10
```

## Troubleshooting

### Common Issues

**Issue: Test fails after migration**

```
AssertionError: Expected call not found
```

**Solution:** Check that fixture provides expected mock methods

```python
# Check what methods are available
print(dir(mock_session_manager))
# Verify the factory creates expected behavior
assert hasattr(mock_session_manager, 'create_session')
```

**Issue: Mock behavior differs from original**

```
AttributeError: Mock object has no attribute 'custom_method'
```

**Solution:** Use custom factory parameters

```python
mock_manager = ManagerMockFactory.create_session_manager_mock(
    custom_method=MagicMock(return_value="expected")
)
```

**Issue: Import errors after migration**

```
ImportError: cannot import name 'PatchContextFactory'
```

**Solution:** Update imports

```python
# Add to imports
from tests.fixtures.mock_factories import PatchContextFactory
# Or use bridge function
from tests.fixtures.mock_data import get_factory_mock
```

## Best Practices

1. **Use fixtures for standard cases** - 95% of tests should use fixtures
1. **Use context factories for custom behavior** - When you need specific mock behavior
1. **Use bridge functions during transition** - For gradual migration
1. **Keep one pattern per file** - Don't mix old and new patterns in same file
1. **Test immediately after migration** - Don't batch migrations without testing

## Performance Benefits

- **75% less code** in test setup
- **Consistent behavior** across all tests
- **Faster test writing** - no boilerplate
- **Easier maintenance** - change once, apply everywhere
- **Better test reliability** - standardized mock behavior
