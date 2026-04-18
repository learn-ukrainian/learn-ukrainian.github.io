# Plan Coherence Overhaul (#702)

## Date: 2026-03-01

## What was done

### Tier 1: Structural Fixes (5,749 changes across 1,496 plans)
- Script: `scripts/fix_plan_structure.py` (idempotent)
- Fixed sequence duplicates/gaps across A2, B1, BIO, LIT, RUTH
- Added `word_target` to 509 plans from config.py
- Added per-section `words` to 934 plans (proportional allocation)
- Migrated OES/RUTH from Schema C → Schema A (description→points, title_uk→title, activity_types→activity_hints)
- Migrated ISTORIO subsections → points
- Fixed B2-PRO word_target 2000 → 4000
- Fixed vocabulary_hints "[]" strings
- Closed #700 as superseded

### Tier 2: Navigation Graph (1,231 links, 667 files)
- Script: `scripts/wire_navigation.py` (idempotent)
- Wired connects_to/prerequisites for all unwired plans
- Cross-level chain verified: A1→A2→B1→B2→C1→C2

### Tier 3.3: Objectives (313 plans)
- Script: `scripts/generate_objectives.py`
- C2: 85 TBD → focus-specific objectives
- OES: 100, RUTH: 112, BIO: 9, LIT: 6, C1: 1

## Schema convergence
All 1,496 plans now use Schema A:
- `module`, `level`, `sequence`, `slug`, `version`, `title`
- `word_target`, `objectives`, `content_outline[{section, words, points}]`
- `vocabulary_hints`, `activity_hints`, `connects_to`, `prerequisites`

## Three plan schemas found (pre-fix)
- Schema A (core): standard fields
- Schema B (HIST/BIO/LIT/ISTORIO): like A but no per-section words, ISTORIO used subsections
- Schema C (OES/RUTH): completely different (title_en/title_uk, module_number, phase_id, activity_types)
All converged to Schema A.

## Module ID format
- All levels now use 3-digit zero-padding: `{level}-{seq:03d}` (e.g., `a2-001`, `c2-091`)

## Word targets by level
**DO NOT TRUST THESE — always re-read `scripts/audit/config.py` for current values.**
See non-negotiable-rules.md for the authoritative table.

## Remaining work
- T3.4: C1/C2 topic differentiation review (manual)
- T3.5: Vocabulary progression audit A1→C2 (manual)
- Tier 4: Seminar content depth review (deferred)
- OES/RUTH vocabulary_hints still empty (need actual content)
