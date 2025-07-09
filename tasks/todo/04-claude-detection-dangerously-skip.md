# Task: Update Claude Detection to Use --dangerously-skip-permissions

## Priority: High

## Description
Update the Claude detection mechanism to use the `--dangerously-skip-permissions` flag instead of keyword-based detection.

## Changes Required
1. Remove keyword detection patterns
2. Update Claude launch commands to include `--dangerously-skip-permissions`
3. Remove pattern-based prompt detection
4. Simplify ClaudeManager logic

## Files to Modify
- `libs/core/claude_manager.py`: Remove keyword detection
- `libs/core/prompt_detector.py`: May be removed entirely
- `patterns/` directory: Can be removed
- Template files: Update Claude launch commands
- `libs/core/content_collector.py`: Simplify content collection

## Implementation Notes
- This flag bypasses all permission prompts
- Significantly simplifies the automation logic
- Remove all auto-response related code
- Update documentation to reflect this change