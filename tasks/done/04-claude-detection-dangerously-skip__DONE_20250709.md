[x] Task: Update Claude Detection to Use --dangerously-skip-permissions

## Priority: High

## Description
Update the Claude detection mechanism to use the `--dangerously-skip-permissions` flag instead of keyword-based detection.

## Changes Required
1. [x] Update Claude launch commands to include `--dangerously-skip-permissions`
2. [>] Remove keyword detection patterns for permission prompts - Deferred to task 05
3. [>] Keep pattern-based prompt detection for non-permission prompts - Deferred to task 05
4. [>] Simplify ClaudeManager logic for permission handling - Deferred to task 05

## Files to Modify
- `libs/core/claude_manager.py`: Remove permission-related detection
- `libs/core/prompt_detector.py`: Keep but simplify for non-permission prompts
- `patterns/` directory: Keep for non-permission prompts
- [x] Template files: Update Claude launch commands
- `libs/core/content_collector.py`: Keep for learning system

## Implementation Notes
- This flag bypasses all permission prompts
- Keep auto-response for other prompt types (file selection, yes/no)
- Maintain AI learning system for non-permission interactions
- Update documentation to reflect this change

## Completion Notes
- Successfully added --dangerously-skip-permissions flag to all template files
- This change significantly reduces the need for permission prompt handling
- Further simplification of the auto-response system should be done in task 05
- The flag is confirmed to exist in Claude Code (verified with --help)