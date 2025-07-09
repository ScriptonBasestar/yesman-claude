[x] Task: Add Progress Overview Feature to Dashboard

## Priority: Medium

## Description
Implement a unified progress overview feature that shows all sessions' progress in a single view.

## Requirements
- Aggregate progress from all active sessions
- Show overall completion percentage
- Display task/command execution status
- Visual progress bars or charts
- Real-time updates

## Implementation Ideas
- Progress tracking per session
- Combined view in dashboard
- Visual indicators (progress bars, pie charts)
- Summary statistics
- Timeline view of activities

## Files to Modify
- Dashboard components (both Tauri and TUI versions)
- Session manager to track progress metrics
- Potentially new progress tracking module

## Notes
- Consider what "progress" means in context of Claude sessions
- May need to track command execution, file changes, or other metrics