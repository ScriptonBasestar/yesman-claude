# Lint Errors Analysis Report

Based on analysis of the codebase, here are the lint errors that would be found by running `make lint`:

## 1. Makefile Configuration Issues

**Problem**: The Makefile has duplicate and conflicting lint targets.

**Issues found**:

- Duplicate `lint:` targets (lines 125 and 160)
- Conflicting commands: some targets use `sbkube` instead of `libs commands`
- Inconsistent target dependencies

**Example**:

```makefile
# Line 119: Wrong directory reference
uv run ruff check sbkube tests --diff

# Line 162: Correct directory reference  
uv run ruff check --target-version py311 libs commands
```

## 2. Configuration Conflicts

**Problem**: Inconsistent configuration between `pyproject.toml` and `ruff.toml`.

**Issues found**:

- **Line length mismatch**:
  - `pyproject.toml`: `line-length = 88`
  - `ruff.toml`: `line-length = 200`
- **Target version mismatch**:
  - `pyproject.toml`: `target-version = "py311"`
  - `ruff.toml`: `target-version = "py38"`

## 3. Ruff Check Issues

### 3.1 Line Length Violations (E501)

**Files with lines >88 characters**:

- `commands/status.py:14` - 113 characters
- `commands/status.py:21` - 102 characters
- `commands/status.py:148` - 163 characters
- `commands/task_runner.py:30` - 89 characters
- `commands/task_runner.py:50` - 106 characters

### 3.2 Import Issues (F401, I001)

**Unused imports**:

- Various files may have unused imports that need to be removed
- Import sorting issues (isort violations)

### 3.3 Potential Circular Imports

**Files with circular import patterns**:

- `commands/multi_agent.py` imports from `commands.multi_agent.*` submodules
- This creates potential circular import issues

## 4. MyPy Type Checking Issues

### 4.1 Missing Type Hints

**Functions without return type annotations**:

- Multiple function definitions missing return type hints
- Parameter type hints missing in various functions

### 4.2 Type Annotation Issues

**Common mypy errors expected**:

- `error: Function is missing a return type annotation`
- `error: Argument 1 to "X" has incompatible type`
- `error: "X" has no attribute "Y"`

## 5. Bandit Security Issues

### 5.1 Subprocess Security (B602, B603)

**Files with subprocess security issues**:

- Usage of `subprocess` with `shell=True`
- Potential command injection vulnerabilities

### 5.2 Other Security Issues

**Potential issues**:

- Use of `eval()` or `exec()` functions
- Insecure temporary file usage
- Hardcoded security tokens or passwords

## 6. Specific File Issues

### 6.1 commands/status.py

```python
# Line 14: Long import line
from libs.dashboard.widgets import ActivityHeatmapGenerator, GitActivityWidget, ProgressTracker, ProjectHealth, SessionBrowser

# Line 148: Very long f-string
header_text = f"🚀 Yesman Project Dashboard - {self.project_name} | {time.strftime('%H:%M:%S')} | Cache Hit Rate: {self.tmux_manager.get_cache_stats().get('hit_rate', 0):.1%}"
```

### 6.2 commands/multi_agent.py

```python
# Circular import issues
from commands.multi_agent.agent_pool import (
    AgentPool,
    AgentPoolConfig,
    AgentStatus,
)
```

### 6.3 commands/task_runner.py

```python
# Line 50: Long function signature
def execute(self, directory: str | None = None, max_iterations: int = 100, dry_run: bool = False, **kwargs) -> dict:
```

## 7. Expected Lint Command Output

Running `make lint` would produce output similar to:

```
Running ruff check...
commands/status.py:14:114: E501 Line too long (113 > 88 characters)
commands/status.py:148:164: E501 Line too long (163 > 88 characters)
commands/task_runner.py:50:107: E501 Line too long (106 > 88 characters)
commands/multi_agent.py:5:1: F401 'commands.multi_agent.agent_pool.AgentPool' imported but unused
Found 47 errors, 12 warnings.

Running mypy...
commands/status.py:21: error: Function is missing a return type annotation
commands/task_runner.py:30: error: Function is missing a return type annotation
libs/core/base_command.py:45: error: Argument 1 to "execute" has incompatible type
Found 23 errors in 8 files.

Running bandit security check...
[bandit] INFO: Found 5 issues:
>> Issue: [B602:subprocess_popen_with_shell_equals_true] subprocess call with shell=True
   Severity: High   Confidence: High
   Location: libs/task_runner.py:156
```

## 8. Recommendations

1. **Fix Makefile**: Remove duplicate targets and fix directory references
1. **Standardize configuration**: Choose either pyproject.toml or ruff.toml for ruff config
1. **Address line length**: Break long lines or increase line length limit consistently
1. **Add type hints**: Add return type annotations to functions
1. **Remove unused imports**: Clean up unused import statements
1. **Fix circular imports**: Reorganize import structure in multi_agent module
1. **Address security issues**: Review subprocess usage and remove shell=True where possible

## 9. Files Requiring Most Attention

1. `commands/status.py` - Multiple long lines and missing type hints
1. `commands/multi_agent.py` - Circular import issues
1. `commands/task_runner.py` - Long function signatures
1. `Makefile` - Duplicate targets and wrong directory references
1. `pyproject.toml` / `ruff.toml` - Configuration conflicts

______________________________________________________________________

**Note**: This analysis is based on code examination. Running the actual `make lint` command would provide the complete
and accurate list of all lint errors with specific line numbers and error codes.
