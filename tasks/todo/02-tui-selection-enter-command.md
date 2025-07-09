# Task: Add TUI Selection for Enter Command

## Priority: High

## Description
When the `enter` command is used without a session name, provide a TUI-based session selector instead of just text-based selection.

## TODO Items
- [x] Check current enter command implementation
- [x] Create TUI session selector component
- [x] Implement arrow key navigation
- [x] Add session status indicators
- [x] Add search/filter functionality
- [x] Integrate with enter command
- [x] Add fallback to text-based selection
- [x] Test TUI functionality

## Files to Modify
- `commands/enter.py`: Add TUI selection logic
- Potentially create new module for TUI session selector

## Implementation Notes
- Should reuse existing session listing logic
- Consider using the same TUI components as dashboard
- Fallback to text-based selection if TUI fails
- Integrate with existing session manager functionality