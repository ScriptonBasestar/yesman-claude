<!-- 🚫 AI_MODIFY_PROHIBITED -->

# Architecture Decision Records (ADRs)

This directory contains Architecture Decision Records (ADRs) that document significant architectural decisions made in the Yesman-Claude project.

## What is an ADR?

An ADR is a document that captures an important architectural decision made along with its context and consequences.

## ADR Format

Each ADR follows this structure:

1. **Title**: ADR-XXX: [Decision Title]
1. **Date**: When the decision was made
1. **Status**: Proposed/Accepted/Deprecated/Superseded
1. **Context**: What prompted this decision
1. **Decision**: What was decided
1. **Consequences**: What are the positive and negative outcomes
1. **Alternatives Considered**: What other options were evaluated

## Current ADRs

- [001-command-pattern.md](001-command-pattern.md) - Base Command Pattern for CLI
- [002-dependency-injection.md](002-dependency-injection.md) - Dependency Injection Pattern
- [003-configuration-management.md](003-configuration-management.md) - Configuration Management Strategy

## Creating a New ADR

1. Copy the template from `_template.md`
1. Name it with the next sequential number: `XXX-decision-name.md`
1. Fill in all sections
1. Submit for review through normal PR process

## Modifying ADRs

ADRs are immutable once accepted. If a decision needs to be changed:

1. Create a new ADR that supersedes the old one
1. Update the old ADR's status to "Superseded by ADR-XXX"
1. Link to the new ADR
