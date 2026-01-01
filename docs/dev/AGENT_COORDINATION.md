# Agent Coordination Hub

**Last Updated:** 2026-01-01 (21:00 UTC)
**Coordinator:** Claude 1 (this session)

## Active Agents

| Code | Agent | Subscription | Current Task | Issue | Status |
|------|-------|--------------|--------------|-------|--------|
| **A** | Gemini 1 | User's | B2 M111 creation | #349 | 🔄 Testing new workflow |
| **M** | Gemini 2 | User's | B2 M112 creation | #349 | 🔄 Testing new workflow |
| **K** | Gemini 3 | User's | (waiting) | - | ⏳ Context limit reset |
| **C1-b** | Claude 1 (other session) | User's | B2 enrichment | #349 | 🔄 M01-M10 done |
| **C2** | Claude 2 | Different sub | (standing by) | - | ⏳ Available |

## This Session (C1-a: Coordinator)

- **Role:** Review hub, agent coordination, issue management
- **Same Claude, different session:** C1-b is doing B2 migration
- **Tracking:** All agent progress, reviewing completed work

## Context Files

| Agent | Context Document |
|-------|------------------|
| Agent M (Gemini 2) | `docs/dev/GEMINI2_B1_MIGRATION_CONTEXT.md` |
| C1-b (Claude other session) | `docs/dev/CLAUDE_B2_MIGRATION_CONTEXT.md` |
| Agent K (Gemini 3) | TBD - assign when context resets |
| C2 (Claude 2) | TBD - standing by for assignment |

## Migration Progress

| Level | Modules | Extraction | Enrichment | Assigned To |
|-------|---------|------------|------------|-------------|
| A1 | 34 | ✅ Done | ✅ Done | Complete |
| A2 | 57 | ✅ Done | ✅ Done | Complete |
| B1 | 86 | ✅ Done | ✅ Done | ✅ Complete (quality verified) |
| B2 | 110 | ✅ Done | 🔄 10/110 | C1-b |

## C1-b B2 Enrichment Progress

```
☒ Run B2 vocabulary extraction script
☒ Verify extraction (110 YAML files)
☒ Enrich M01-M03 (passive voice)
☒ Enrich M04-M10 (passive voice remainder)
☐ Enrich vocabulary M11-M30 (syntax, registers)
☐ Enrich vocabulary M31-M70 (idioms, synonyms)
☐ Run global vocab audit validation
☐ Test pipeline on B2
```

**Note:** M71-M110 (history modules) not yet in enrichment queue.

## B2 Module Status

| Range | Count | Content | Vocabulary YAML | Enrichment |
|-------|-------|---------|-----------------|------------|
| M01-M10 | 10 | ✅ | ✅ | ✅ Done |
| M11-M70 | 60 | ✅ | ✅ | ❌ Pending |
| M71-M110 | 40 | ✅ | ✅ | ❌ Pending |
| M111-M145 | 35 | ❌ Need to build | ❌ | ❌ |

**User updated M107-M110** with more content - may need vocab review.

## Issue Tracking

- **#340** - Epic: Vocabulary YAML Architecture (Agent A - A2)
- **#349** - B2 YAML Migration (C1-b)
- **#350** - B1 YAML Migration (Agent M)

## When Agent K (Gemini 3) Comes Online

Potential assignments:
1. B2 enrichment M71-M110 (history modules)
2. Review M107-M110 vocabulary after content updates
3. Start C1 planning/scaffolding

## Communication Protocol

1. Agents comment on their assigned issues with progress
2. Coordinator (this session) reviews and updates this file
3. Cross-agent dependencies flagged in issue comments
