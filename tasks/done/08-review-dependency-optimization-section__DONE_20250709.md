[x] Task: Review and Relocate Dependency Optimization Section

## Priority: Low

## Description
The dependency optimization section seems out of place in the Smart Template feature section. Review and potentially relocate it.

## Actions Required
1. Analyze if dependency optimization is actually a template feature
2. If not, move to appropriate section (e.g., Performance Optimization)
3. If yes, clarify how it relates to templates
4. Update documentation structure accordingly

## Considerations
- The feature mentions "pnpm/npm install only runs when changes detected"
- This might be a session management feature rather than template feature
- Could be part of optimization or automation features
- May need its own section if it's a significant feature

## Files to Update
- `FEATURES_tobe.md`: Reorganize sections
- Any related documentation explaining this feature

## Completion Notes
- FEATURES_tobe.md does not exist; found content in FEATURES.md instead
- Dependency optimization is correctly placed as part of Smart Template feature
- It's implemented through conditional shell commands in templates
- Updated documentation to clarify the feature with concrete example
- Also updated Isolated mode naming (was Local mode)