# TODO.md (MVP 필수 기능)


## Dashboard Terminal Compatibility

[x] Fix Dashboard Terminal Output Corruption
- 관련 ISSUE: Dashboard Terminal Output Corruption (Issue #5)
- 위치: libs/dashboard/app.py:27-40

[x] Add terminal compatibility checks
- 관련 ISSUE: Dashboard Terminal Output Corruption (Issue #5)
- 위치: libs/dashboard/app.py

[x] Implement fallback safe mode for incompatible terminals
- 관련 ISSUE: Dashboard Terminal Output Corruption (Issue #5)
- 위치: libs/dashboard/app.py

## Claude Manager

[ ] Fix Claude Manager Auto-Start Failure
- 관련 ISSUE: Claude Manager Auto-Start Failure (Issue #6)
- 위치: libs/dashboard/claude_manager.py:47-60

[ ] Enhance Claude detection patterns
- 관련 ISSUE: Claude Manager Auto-Start Failure (Issue #6)
- 위치: libs/dashboard/claude_manager.py

## Performance Optimization

[ ] Implement smart dependency check for pnpm install
- 관련 ISSUE: Inefficient Package Installation (Issue #7)
- 위치: projects.yaml

## System Setup

[ ] Ensure proper log directory setup with correct permissions
- 관련 ISSUE: Log Directory Permissions (Issue #9)
- 위치: ~/tmp/logs/yesman/
