# Code Quality Guide

## Overview

Yesman-Claude uses Ruff as the primary tool for code formatting, linting, and import organization. This guide documents
the code quality tools, their configuration, and best practices for maintaining consistent code quality across the
project.

## Quick Start

### Essential Commands

```bash
# Format code
make format      # or make fmt

# Check code quality without fixing
make lint        # Basic lint check
make lint-fast   # Ultra-fast lint (1-3s)

# Fix linting issues automatically
make lint-fix

# Comprehensive quality check
make full        # Runs all quality checks
```

## Tool Stack

### Ruff - All-in-One Python Tool

We use [Ruff](https://github.com/astral-sh/ruff) for:

- Code formatting (replacing Black)
- Import sorting (replacing isort)
- Linting (replacing Flake8, pylint, and others)
- Security checks (partially replacing Bandit)

### Additional Tools

- **mypy**: Static type checking
- **bandit**: Security vulnerability scanning
- **mdformat**: Markdown file formatting
- **pre-commit**: Git hooks for automatic quality checks

## Configuration

### Ruff Configuration (ruff.toml)

Key settings:

- Line length: 200 characters
- Target Python version: 3.11+
- Import sorting with known first-party packages: `libs`, `commands`, `api`
- Format style: Similar to Black (double quotes, spaces for indentation)

### Pre-commit Hooks

The project uses a two-stage pre-commit strategy:

1. **pre-commit** (fast, 1-3s): Essential formatting and fixes
1. **pre-push** (comprehensive, 5-10s): Full validation including tests

Install hooks:

```bash
make hooks-install
```

## Formatting vs Linting

### make format

- Reformats code to match style guidelines
- Organizes imports
- Applies safe automatic fixes
- **Always safe to run**

### make lint

- Checks code without making changes
- Reports style violations
- Identifies potential bugs
- **Read-only operation**

### make lint-fix

- Combines linting with automatic fixes
- Applies safe corrections
- May require manual review for complex issues

## Common Issues and Solutions

### Import Sorting Conflicts

**Problem**: Previously, `make format` used Black+isort while `make lint` used Ruff, causing conflicts.

**Solution**: All formatting now uses Ruff exclusively, ensuring consistency.

### Format After Lint Still Shows Errors

This should no longer happen. If it does:

1. Run `make format` first
1. Then run `make lint`
1. If issues persist, they likely require manual fixes

### Pre-commit Hook Failures

If pre-commit hooks fail:

1. Let the hooks apply automatic fixes
1. Review the changes
1. Add the fixed files and commit again

## Workflow Integration

### Development Workflow

1. **Before coding**: Run `make hooks-install` (one-time setup)
1. **During development**: Use `make format` frequently
1. **Before committing**: Automatic pre-commit hooks run
1. **Before pushing**: Comprehensive pre-push hooks run
1. **For CI/CD**: Use `make lint-ci` for GitHub Actions format

### Incremental Linting

For large codebases, use targeted linting:

```bash
# Lint only changed files
make lint-new

# Lint specific files
CLAUDE_FILES="file1.py file2.py" make lint-file
```

## Quality Levels

The project uses a hierarchical lint system:

### Level 1: Basic (Default)

- `make lint` - Standard checks
- `make lint-fast` - Ultra-fast checks
- Used in pre-commit hooks

### Level 2: Auto-fix

- `make lint-fix` - Apply safe fixes
- `make format` - Format code
- Used during development

### Level 3: Strict

- `make lint-strict` - Comprehensive analysis
- `make quality-strict` - All quality checks
- Used before releases

## Best Practices

1. **Regular Formatting**: Run `make format` before committing
1. **Use Git Hooks**: Install with `make hooks-install` for automatic checks
1. **Fix Issues Early**: Address linting issues as they appear
1. **Type Hints**: Add type annotations to new code
1. **Security First**: Pay attention to Bandit security warnings

## Troubleshooting

### Ruff vs Black/isort Compatibility

Ruff's formatter is not 100% compatible with Black+isort. Key differences:

- Import grouping may vary slightly
- Some formatting edge cases differ
- Use Ruff exclusively to avoid conflicts

### Performance Issues

If linting is slow:

1. Use `make lint-fast` for quick checks
1. Enable caching (default in Ruff)
1. Lint specific directories instead of the entire codebase

### IDE Integration

Configure your IDE to use Ruff:

- VS Code: Install the Ruff extension
- PyCharm: Configure external tool for Ruff
- Format on save recommended

## Migration Notes

### From Black+isort to Ruff

The project has migrated from Black+isort to Ruff for all formatting needs:

- `make format` now uses `ruff format` instead of `black`
- Import sorting uses `ruff check --select I` instead of `isort`
- Configuration consolidated in `ruff.toml`

### Removed Tools

The following tools are no longer used:

- Black (replaced by Ruff format)
- isort (replaced by Ruff import sorting)
- Some Flake8 plugins (replaced by Ruff rules)

## Additional Resources

- [Ruff Documentation](https://beta.ruff.rs/docs/)
- [Pre-commit Documentation](https://pre-commit.com/)
- Project-specific configuration: `/ruff.toml`
- Makefile quality module: `/Makefile.quality.mk`
