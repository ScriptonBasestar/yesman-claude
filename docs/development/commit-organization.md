# 📝 Commit Organization Guidelines

This document explains the process for organizing and committing changes based on meaning units, following the project's
commit standards.

## Overview

The commit organization process helps maintain a clean, meaningful commit history by:

1. Properly staging files while excluding unnecessary ones
1. Separating changes into logical commit units
1. Following consistent commit message formatting

## Commit Helper Script

A helper script `scripts/commit_helper.sh` automates much of this process:

```bash
# Make the script executable
chmod +x scripts/commit_helper.sh

# Run the commit helper
./scripts/commit_helper.sh
```

## Manual Process

### 1. File Staging

Stage all files first, then remove excluded ones:

```bash
# Stage everything
git add .

# Remove excluded files/directories
git reset .DS_Store
git reset .idea/
git reset .vscode/
git reset node_modules/
git reset __pycache__/
git reset "*.log"
git reset "*.tmp"
git reset .claude/
git reset .roocode/
```

### 2. Commit Categorization

Organize commits by these categories when possible:

| Category   | Description            | Examples                                          |
| ---------- | ---------------------- | ------------------------------------------------- |
| `feat`     | New features           | New commands, API endpoints, dashboard components |
| `fix`      | Bug fixes              | Error corrections, edge case handling             |
| `refactor` | Code restructuring     | Performance improvements, code organization       |
| `test`     | Test additions/updates | Unit tests, integration tests, test utilities     |
| `chore`    | Maintenance tasks      | Documentation updates, configuration changes      |

### 3. Commit Message Format

Follow this format for all commits:

```
{prefix}(claude): {user/feature-focused summary}
```

Rules:

- Keep under 50 characters
- Focus on user impact or feature changes
- Include AI tool identifier (claude, gemini, cursor, roocode)
- Use present tense

Examples:

- `feat(claude): add family group invitation feature`
- `refactor(claude): improve calendar state management`
- `fix(claude): resolve notification filter error`

### 4. Commit Scope

Include:

- Code changes (even if not directly modified by AI)
- State files and configuration
- API specifications
- Components and documentation
- Related files in the same workflow

Exclude:

- `.claude/*`, `.roocode/*` directories
- Cache files and temporary files
- IDE-specific files (unless explicitly needed)

## Best Practices

### When to Split Commits

Split into multiple commits when:

- Changes span multiple logical units
- Different categories are mixed
- Commit message would be too generic

Example of good split:

```bash
# First commit - feature work
git add api/routers/family.py
git add commands/invite.py
git commit -m "feat(claude): implement family invitation API"

# Second commit - tests
git add tests/unit/test_family_invites.py
git commit -m "test(claude): add family invitation test cases"

# Third commit - documentation
git add docs/user-guide/family-features.md
git commit -m "chore(claude): document family invitation feature"
```

### When to Combine Commits

Combine when:

- Changes are tightly related
- All changes fit one category
- Separate commits would be too granular

Example of good combination:

```bash
git add libs/dashboard/widgets/family_invite.py
git add libs/dashboard/components/family_invite.py
git add tests/unit/dashboard/test_family_invite.py
git commit -m "feat(claude): implement family invitation dashboard components"
```

## Common Workflows

### Feature Development

```bash
# After implementing a new feature
git add .
git reset .DS_Store  # Remove excluded files
git commit -m "feat(claude): implement user profile management"
```

### Bug Fix

```bash
# After fixing a bug
git add api/routers/users.py
git add tests/unit/test_user_validation.py
git commit -m "fix(claude): resolve user validation edge case"
```

### Refactoring

```bash
# After code restructuring
git add libs/core/session_manager.py
git add libs/core/session_manager_refactored.py
git commit -m "refactor(claude): optimize session management architecture"
```

## Automation

The commit helper script automates:

1. Proper file staging with exclusions
1. Commit categorization based on file paths
1. Message generation following format rules
1. Interactive staging for complex changes
1. Single or multiple commit options

Run it after making changes:

```bash
./scripts/commit_helper.sh
```

## Integration with Development Process

This process fits into the overall workflow:

1. Make changes with AI assistance
1. Review all modifications
1. Run commit helper or follow manual process
1. Push commits
1. Continue with next development task

This ensures a clean, meaningful commit history that clearly shows the evolution of the codebase.
