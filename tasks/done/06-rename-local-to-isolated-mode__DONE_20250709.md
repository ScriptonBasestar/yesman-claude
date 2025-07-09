[x] Task: Rename Local Mode to Isolated Mode

## Priority: Low

## Description
Rename "Local" configuration mode to "Isolated" mode throughout the project for better clarity.

## Changes Required
1. Update mode names in configuration handling
2. Update documentation
3. Update CLI help text
4. Update variable names and constants

## Files to Search and Modify
- `libs/yesman_config.py`: Configuration mode handling
- All documentation files mentioning "Local mode"
- CLI command help strings
- Any configuration examples
- Test files

## Implementation Notes
- Use grep/search to find all occurrences of "local mode"
- Ensure backward compatibility if config files use "local"
- Update any error messages or logs
- Consider adding deprecation warning for "local" mode