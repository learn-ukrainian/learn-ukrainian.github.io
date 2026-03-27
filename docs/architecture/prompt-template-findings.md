# Prompt Template Review — 2026-03-27

## Templates reviewed

| Template | Version | Placeholders | H2 sections |
|----------|---------|-------------|-------------|
| v6-write.md | 1.0.0 | 15 | 9 |
| v6-write-seminar.md | 1.0.0 | 11 | 9 |
| v6-review.md | 1.0.0 | 8 | 10 |
| v6-skeleton.md | 1.0.0 | 9 | 8 |
| v6-activities.md | 1.0.0 | 11 | 13 |
| v6-vocab.md | 1.0.0 | 2 | 5 |

## Unreplaced placeholders

**None found.** All placeholders in all templates have corresponding replacement code in v6_build.py. BUG-09 (seminar template {SKELETON_SECTION}/{CORRECTION_SECTION}) was fixed this session.

## Cross-template contradictions

### 1. Exercise format: core vs seminar (MINOR — intentional)
- **v6-write.md**: "Place `<!-- INJECT_ACTIVITY -->` markers only. Do NOT write exercises."
- **v6-write-seminar.md**: "Write exercises directly in DSL format (:::quiz, :::fill-in)."
- **Status**: Intentional — seminar exercises (reading comprehension, essay prompts) are simpler and go inline as DSL. Core exercises use the YAML activities pipeline.
- **Risk**: None if understood. Should be documented in the architecture.

### 2. Stress marks — CONSISTENT
All templates agree: writer does NOT add stress marks. Review template says "do NOT check for stress marks."

### 3. Vocabulary tables — CONSISTENT
Write template says "NO vocabulary tables." Review template says "do NOT penalize словник — ENRICH adds it."

### 4. Tool prefix — CONSISTENT
No hardcoded prefixes in templates. Dynamically injected via `get_family(writer).tool_prefix`.

### 5. Word target calculations — CONSISTENT
- Write: `{WORD_TARGET}–{WORD_CEILING}` (ceiling = 1.5x target)
- Skeleton: `{WORD_TARGET}` with overshoot `{WORD_OVERSHOOT}` (1.1x target)
- Both are correct for their purpose (skeleton plans tight, writer has room).

## Stale instructions

### 1. v6-review.md line 68 (MAJOR)
- **Says**: "List every exercise block (`:::quiz`, `:::fill-in`, `:::match-up`, `:::group-sort`, `:::true-false`). These are filled exercises — a deterministic tool converted placeholders to real content."
- **Reality**: V6 uses YAML activities (`activities/{slug}.yaml`), not inline DSL blocks. The PUBLISH step injects activities from YAML. Only seminar modules still use DSL.
- **Fix**: Update Step 2 to describe YAML activities and INJECT_ACTIVITY markers.

## Dispatch alignment

All templates are correctly aligned with their dispatch paths:

| Template | Model tier | MCP tools | Timeout |
|----------|-----------|-----------|---------|
| skeleton | fast | No | 300s |
| write | thinking (default) | If -tools | 600-900s |
| write-seminar | thinking (default) | If -tools | 600-900s |
| activities | fast (Claude) / Pro (Gemini) | Yes | 300s |
| vocab | fast | No | 180s |
| review | thinking | Yes | 600s |

## Summary

**2 issues found: 1 major, 1 minor**

- **MAJOR**: Review template Step 2 describes DSL exercises but V6 uses YAML activities
- **MINOR**: Seminar write template says "write DSL directly" while core says "markers only" (intentional difference, should be documented)

No critical issues. No unreplaced placeholders. Dispatch alignment is correct.
