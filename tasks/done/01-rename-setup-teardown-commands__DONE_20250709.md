# Task: Rename setup/teardown commands to up/down

## Priority: Medium

## Description
Rename the CLI commands for better usability:
- `setup` → `up`
- `teardown` → `down`

## TODO Items
- [x] Update command names in `yesman.py`
- [x] Rename `commands/setup.py` → `commands/up.py`
- [x] Rename `commands/teardown.py` → `commands/down.py`
- [x] Update command implementations to use new names
- [x] Update CLAUDE.md with new command names
- [x] Update README.md usage examples
- [x] Search and update any test files referencing these commands
- [x] Add backward compatibility aliases (optional)

## Files to Modify
- `yesman.py`: Update command registration
- `commands/setup.py` → `commands/up.py`
- `commands/teardown.py` → `commands/down.py`
- `CLAUDE.md`: Update command documentation
- `README.md`: Update usage examples
- Any test files referencing these commands

## Notes
- Consider maintaining backward compatibility with aliases
- Update any scripts or documentation that reference the old commands