# Agent Coordination Hub

**Last Updated:** 2026-01-01
**Coordinator:** Claude (this session)

## Active Agents

| Code | Agent | Subscription | Current Task | Issue | Status |
|------|-------|--------------|--------------|-------|--------|
| **A** | Gemini 1 | User's | A2 enrichment (M16-M57) | #340 | 🔄 Running (low context) |
| **M** | Gemini 2 | User's | B1 migration + enrichment | #350 | 🆕 Starting |
| **K** | Gemini 3 | User's | (waiting) | - | ⏳ Context limit reset |
| **C2** | Claude 2 | Different sub | B2 migration + enrichment | #349 | 🆕 Starting |

## This Session (Coordinator)

- **Role:** Review hub, agent coordination, issue management
- **NOT doing:** Direct migration/enrichment work
- **Tracking:** All agent progress, reviewing completed work

## Context Files

| Agent | Context Document |
|-------|------------------|
| Agent M (Gemini 2) | `docs/dev/GEMINI2_B1_MIGRATION_CONTEXT.md` |
| Claude 2 | `docs/dev/CLAUDE_B2_MIGRATION_CONTEXT.md` |
| Agent K (Gemini 3) | TBD - assign when context resets |

## Migration Progress

| Level | Modules | Extraction | Enrichment | Assigned To |
|-------|---------|------------|------------|-------------|
| A1 | 34 | ✅ Done | ✅ Done | Complete |
| A2 | 57 | ✅ Done | ⏳ 13/57 | Agent A |
| B1 | 86 | 🆕 Starting | ❌ | Agent M |
| B2 | 106 | 🆕 Starting | ❌ | Claude 2 |

## Issue Tracking

- **#340** - Epic: Vocabulary YAML Architecture (Agent A - A2)
- **#349** - B2 YAML Migration (Claude 2)
- **#350** - B1 YAML Migration (Agent M)

## When Agent K (Gemini 3) Comes Online

Potential assignments:
1. Help with remaining A2 enrichment if Agent A runs out of context
2. Start C1 planning/scaffolding
3. Review/validate completed migrations

## Communication Protocol

1. Agents comment on their assigned issues with progress
2. Coordinator (this session) reviews and updates this file
3. Cross-agent dependencies flagged in issue comments
