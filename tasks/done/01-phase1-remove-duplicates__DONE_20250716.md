---
priority: high
severity: high
---

# Phase 1: Remove Duplicates

## Command Consolidation

\[x\] Delete commands/ls.py and rename ls_improved.py to ls.py [x] Delete commands/setup.py and rename setup_improved.py
to setup.py\
\[x\] Update all imports and references to these commands [ ] Run tests to ensure functionality is preserved

## API Router Consolidation

\[x\] Delete api/routers/sessions.py and rename sessions_improved.py to sessions.py [x] Update router imports in
api/main.py [x] Verify all endpoints are still functional

## Test Directory Merger

\[x\] Merge test-integration content into tests/integration [x] Consolidate duplicate test utilities [x] Update test
scripts and CI/CD references [x] Remove empty test-integration directory

## Verification

\[x\] All tests pass after consolidation [x] No broken imports or references [x] Documentation updated if needed
