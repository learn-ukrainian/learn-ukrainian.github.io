# Recovery Plan — Plan Quality Crisis (2026-04-13)

## Context
A1/A2/B1 builds revealed systemic plan quality issues. Plans were not validated for structural consistency before building. This document is the recovery roadmap.

## Current State

### Plans
| Level | Total | Missing Summary | Wrong word_target | No vocab_hints | Status |
|-------|-------|----------------|-------------------|----------------|--------|
| A1 | 55 | 0 | 2 (1000→1200) | 0 | ✅ Mostly clean |
| A2 | 69 | 63 | 12 (1500→2000) | 0 | ❌ Needs fixes |
| B1 | 94 | 5 | 0 | 1 | ⚠️ Minor fixes |
| B2 | 93 | 93 | 0 | 68 | ❌ Major work |
| C1 | 133 | 131 | 0 | 133 | ❌ Major work |
| C2 | 109 | 108 | 23 (4000→5000) | 106 | ❌ Major work |

### Built Modules
- **A1**: 50/52 passing audit. 2 minor fixes needed. 5 modules not yet built.
- **A2**: 0/58 passing. 22 fully built + 28 in-flight from current batch. Prose/activities/vocab are good — fail on missing Summary gate.
- **B1**: 0/75 passing. All from older builds. Need full rebuild.
- **B2-C2**: No builds attempted.

### Wikis
All 100% compiled for A1-C2 (557 articles). Unaffected by plan issues (wikis key off topics, not Summary/vocab fields).

### Orphan plans deleted (2026-04-12)
6 orphan B1 plans removed: `adjectives-suppletive`, `b1-finale`, `double-negation`, `motion-prefixes-around`, `practice-exam-reading`, `practice-exam-writing`. B1 now 94 plans = 94 curriculum modules.

## Recovery Phases

### Phase 0 — FREEZE
**Stop all builds except A1 hotfixes.** No new A2/B1/B2/C1/C2 builds until plan gates pass.

### Phase 1 — Scripted Mechanical Fixes (no LLM, no cost)
Write a deterministic migration script that:
1. Fixes `word_target` to match `config.py` values (A1: 2, A2: 12, C2: 23 plans)
2. Adds `Підсумок — Summary` section to `content_outline` with ~150 word budget for plans that lack it
3. Normalizes `vocabulary` vs `vocabulary_hints` field naming (code bug in validator)
4. Bumps plan version (patch increment)

**Assign to: Codex** (deterministic script, no creativity needed)

### Phase 2 — LLM Content Fixes (Gemini)
For plans that now have the Summary slot but need custom content:
1. Generate Summary bullet points per plan (what the learner reviews)
2. Generate `vocabulary_hints` for B2-C2 plans that lack them
3. Version bump + plan_fixes metadata

**Assign to: Gemini** (content generation, cheap via gemini-3.1-pro-preview)

### Phase 3 — Hard Pre-Build Gate
Add to `v6_build.py` CHECK step (before RESEARCH):
- `content_outline` must contain a Summary/Підсумок section
- `word_target` must match `config.py`
- `content_outline` word sum must be within 15% of `word_target`
- `vocabulary_hints` or `vocabulary` must exist and be non-empty
- B2+ must have level-specific schema fields

**Assign to: Codex** (code change, testable)

### Phase 4 — Salvage A1 + A2
1. **A1**: Fix 2 failing modules + build 5 remaining → 55/55 complete
2. **A2 Summary-only failures**: `--step publish --resume` (cheapest — just re-audit)
3. **A2 word_target failures** (9 checkpoints): `--step review --resume` (content needs expansion)

### Phase 5 — Rebuild B1
Old B1 builds are not worth incremental healing (0/75 passing, richness/engagement failures). Full rebuild after plans pass Phase 1-3 gates.

### Phase 6 — B2-C2
Fix plans (Phase 1+2), validate, then build. No building until all plans pass the pre-build gate.

## Key Decisions
- Summary sections must be **custom per plan**, not a generic template (pedagogical value)
- `vocabulary_hints` missing is **blocking** for builds — density/richness audits fail without them
- Wikis are **safe** — adding Summary sections doesn't affect wiki compilation
- B1 old builds get **full rebuild**, not incremental healing

## Prevention
The pre-build gate (Phase 3) ensures no builds start with broken plans. This is the #1 priority after Phase 1.

## Agent Assignments
| Phase | Agent | Why |
|-------|-------|-----|
| Phase 1 (scripted fixes) | Codex | Deterministic YAML manipulation |
| Phase 2 (LLM content) | Gemini | Content generation, cheap |
| Phase 3 (pre-build gate) | Codex | Code change in v6_build.py |
| Phase 4 (A1/A2 salvage) | Gemini (writer) + Codex (reviewer) | Cross-agent build |
| Phase 5 (B1 rebuild) | Gemini (writer) + Codex (reviewer) | Cross-agent build |

## Gemini/Codex Discussion
Full thread: `ab channel tail architecture --thread f386f3ec029e4b48a80a514a4c80f88a`

## Bug Fix Applied This Session
- `query_cefr_level` in MCP sources server: added missing `limit` parameter (`scripts/wiki/sources_db.py:277`)
- Restart MCP server to pick up fix

## Files Modified This Session
- `scripts/wiki/sources_db.py` — CEFR bug fix
- `docs/RUNBOOK-BUILD.md` — build runbook (needs updating with recovery plan)
- `docs/session-state/2026-04-13-recovery-plan.md` — this file
- Deleted 6 orphan B1 plan files
