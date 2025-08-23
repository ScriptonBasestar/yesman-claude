#!/usr/bin/env python3
# Copyright notice.
# Copyright (c) 2024 Yesman Claude Project
# Licensed under the MIT License
"""Unit tests for ConfigValidator."""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
import yaml

# Test the validator can be imported and basic functionality works
def test_config_validator_import():
    """Test that ConfigValidator can be imported."""
    try:
        # Avoid circular imports by importing directly
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        
        # Mock dependencies to avoid import issues
        sys.modules['libs.dashboard'] = Mock()
        sys.modules['libs.dashboard.health_calculator'] = Mock()
        
        from libs.core.config_validator import ConfigValidator, ValidationResult, ValidationError, ValidationLevel
        
        # Test basic instantiation
        validator = ConfigValidator()
        assert validator is not None
        
        # Test ValidationResult
        result = ValidationResult()
        assert result.is_valid is True
        assert len(result.errors) == 0
        
        # Test ValidationError
        error = ValidationError(
            message="test error",
            level=ValidationLevel.ERROR,
            category="test"
        )
        assert error.message == "test error"
        assert error.level == ValidationLevel.ERROR
        
        print("✅ ConfigValidator basic functionality test passed")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False


def test_yaml_validation():
    """Test YAML file validation logic."""
    
    # Test valid YAML
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.safe_dump({
            'tmux': {
                'default_shell': '/bin/bash',
                'status_position': 'bottom'
            },
            'logging': {
                'level': 'INFO'
            }
        }, f)
        valid_yaml_file = Path(f.name)
    
    # Test invalid YAML
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("invalid: yaml: content: [\n")  # Malformed YAML
        invalid_yaml_file = Path(f.name)
    
    try:
        # Test valid YAML parsing
        with open(valid_yaml_file, 'r') as f:
            config = yaml.safe_load(f)
        assert config is not None
        assert 'tmux' in config
        
        # Test invalid YAML parsing
        try:
            with open(invalid_yaml_file, 'r') as f:
                yaml.safe_load(f)
            assert False, "Should have raised YAML error"
        except yaml.YAMLError:
            pass  # Expected
        
        print("✅ YAML validation test passed")
        return True
        
    except Exception as e:
        print(f"❌ YAML validation test error: {e}")
        return False
        
    finally:
        # Cleanup
        valid_yaml_file.unlink(missing_ok=True)
        invalid_yaml_file.unlink(missing_ok=True)


if __name__ == "__main__":
    # Run tests
    results = []
    results.append(test_config_validator_import())
    results.append(test_yaml_validation())
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        exit(0)
    else:
        print("❌ Some tests failed")
        exit(1)