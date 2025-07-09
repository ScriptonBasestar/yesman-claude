# Task: Add TUI Selection for Enter Command

## Priority: High

## Description
When the `enter` command is used without a session name, provide a TUI-based session selector instead of just text-based selection.

## Requirements
- Implement interactive TUI selection using `rich` or similar library
- Show session list with visual indicators (status, activity)
- Allow arrow key navigation
- Display session details on hover/selection
- Support quick search/filter functionality

## Files to Modify
- `commands/enter.py`: Add TUI selection logic
- Potentially create new module for TUI session selector

## Implementation Notes
- Should reuse existing session listing logic
- Consider using the same TUI components as dashboard
- Fallback to text-based selection if TUI fails
- Integrate with existing session manager functionality