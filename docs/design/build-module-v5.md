# Design: build_module_v5.py — Clean Pipeline Rewrite

**Issue:** #750
**Status:** Draft v2 (post-Gemini adversarial review)
**Author:** Claude (architect)
**Reviewer:** Gemini Pro (adversarial review, 2026-03-06)

---

## Problem

`build_module.py` is 6143 lines with three accumulated layers:
- **v2** state migration code (dead)
- **v3** pipeline with full phase implementations (Phase A/B/C/D/E/F)
- **v4** thin wrappers that delegate to v3 functions

The v4 phases are literally:
```python
def phase_content_v4(ctx, state):
    if _is_phase_v4_complete(ctx, "content", state):
        return True
    result = phase_B_v3(ctx, _V3_EMPTY_STATE)  # delegates to v3
    if result:
        _mark_phase_v4(ctx, state, "content", "complete")
    return result
```

This creates confusion:
- Two state systems (`state-v3.json` + `state-v4.json`)
- Two preflight functions (`preflight_v3` + `preflight_v4`)
- Two pipeline runners (`run_pipeline_v3` + `run_pipeline_v4`)
- v3 compat flags polluting the CLI (`--v3`, `--final-review`, `--stop-after`, `--rescreen`)
- Helper functions shared between v3 and v4 with different calling conventions

---

## Goals

1. **Single pipeline** — no v2/v3/v4 branching
2. **Single state file** — `state-v5.json` (v4 format, clean phase keys)
3. **Inlined phase logic** — no delegation to v3 functions
4. **Clean CLI** — remove v3 compat flags
5. **Same behavior** — identical output, same Gemini/Claude dispatches, same audit gates
6. **Coexist with old code** — new files, don't touch `build_module.py` or `pipeline_lib.py`

---

## Architecture

### New Files

| File | Lines (est.) | Purpose |
|------|-------------|---------|
| `scripts/build_module_v5.py` | ~600 | CLI + batch runner + single module runner |
| `scripts/pipeline_v5.py` | ~3200 | Phase implementations + state + all phase helpers |

### Reused Without Changes

| File | What We Use |
|------|------------|
| `scripts/pipeline_lib.py` | `ModuleContext`, `dispatch_gemini`, `dispatch_gemini_raw`, `fill_template`, `run_verify`, `write_placeholders`, `write_completion_report_v2`, `log`, `_init_log`, `_build_fix_prompt`, config getters, preflight helpers |
| `scripts/batch_gemini_config.py` | `get_module_index`, `slug_for_num`, `get_module_paths` |
| `scripts/video_discovery.py` | `run_discovery`, `write_discovery_yaml`, etc. |
| `scripts/plan_autofix.py` | `auto_fix_plan` |
| `scripts/audit/` | All audit modules unchanged (see Consumer Updates below) |

### What Gets Deleted (Not Carried to v5)

| Code | Lines | Why |
|------|-------|-----|
| v2 state migration | ~65 | Dead code |
| v3 state system | ~70 | Replaced by single state |
| v3 pipeline phases (A/B/C/D/E/F) | ~800 | Inlined into v5 phases |
| v3 pipeline runner | ~170 | Replaced by v5 runner |
| v3 preflight | ~70 | Merged into single preflight |
| v3 compat CLI flags | ~50 | Removed |
| v4 delegation wrappers | ~30 | Inlined |
| Dual state checks | ~60 | Single state |
| **Total removed** | **~1315** | |

---

## Phase Design

### State Format

Uses `state-v5.json` (NOT `state.json` — avoids collision with 519 legacy v2 `state.json` files):

```json
{
  "slug": "the-cyrillic-code-i",
  "track": "a1",
  "mode": "v5",
  "phases": {
    "research": { "status": "complete", "ts": "2026-03-06T10:00:00Z" },
    "discover": { "status": "complete", "ts": "2026-03-06T10:01:00Z" },
    "content":  { "status": "complete", "ts": "2026-03-06T10:05:00Z" },
    "activities": { "status": "complete", "ts": "2026-03-06T10:08:00Z" },
    "validate": { "status": "failed", "ts": "2026-03-06T10:15:00Z", "attempts": 6 }
  }
}
```

No more `v4-` prefixes on phase keys. No more `_V4_PHASE_STATE_IDS` mapping table.

### State Compatibility (Gemini Review Finding #1)

**On-disk reality:**
- 519 legacy `state.json` (v2 format — no `phases` key, different structure)
- 1598 `state-v3.json` files
- 21 `state-v4.json` files

**v5 state loading priority:**
```python
def load_state(ctx) -> dict:
    # 1. v5 state — authoritative
    if (ctx.orch_dir / "state-v5.json").exists():
        return read_json("state-v5.json")
    # 2. v4 state — migrate (strip "v4-" prefixes from phase keys)
    if (ctx.orch_dir / "state-v4.json").exists():
        return _migrate_v4_to_v5(read_json("state-v4.json"))
    # 3. Anything else (v3, v2, nothing) — fresh state
    #    v3/v2 modules need rebuilding anyway, no point migrating old state
    return fresh_state(ctx)
```

**v5 always writes `state-v5.json`.** Legacy files are left untouched. v3/v2 modules start fresh when run through v5 (they need rebuilding regardless).

### Phase Functions

All phases follow the same signature:

```python
def phase_research(ctx: ModuleContext, state: dict) -> bool:
    """Research + meta outline generation."""
    if is_complete(state, "research"):
        log("  research: SKIP (already complete)")
        return True
    # ... inlined logic (was phase_A_v3) ...
    mark_complete(state, "research")
    return True
```

### Pipeline Runner

```python
PHASES = ["research", "discover", "content", "activities", "validate", "review", "mdx"]

def run_pipeline(ctx: ModuleContext, state: dict) -> bool:
    for phase_id in PHASES:
        if should_skip(ctx, phase_id):
            continue
        func = PHASE_FUNCTIONS[phase_id]
        ok = func(ctx, state)
        if not ok and phase_id not in NON_BLOCKING:
            return False
    return True
```

### CLI (Simplified)

**Removed flags:** `--v3`, `--final-review`, `--final-review-agent`, `--stop-after`, `--rescreen`, `--claude-model-F`

**Kept flags:** `--review`, `--review-claude`, `--rebuild`, `--no-auto-rebuild`, `--force-phase`, `--restart-from`, `--stop-before`, `--dry-run`, `--refresh`, `--verify`, `--research-only`, `--skip-discover`, `--all`, `--range`, `--max-fix`, `--use-claude`, `--gemini-model`, `--claude-model-A/C/D`

---

## Module Breakdown (Gemini Review Finding #3 — Fixed)

Phase helpers belong in `pipeline_v5.py` alongside the phases they support, NOT in the CLI file.

### `pipeline_v5.py` (~3200 lines)

```
State management          (~100 lines)
  load_state, save_state, is_complete, mark_complete, mark_failed
  _migrate_v4_to_v5

Phase: research           (~120 lines) — inlined from phase_A_v3
Phase: discover           (~120 lines) — inlined from phase_discover_v4
Phase: content            (~200 lines) — inlined from phase_B_v3
Phase: activities         (~200 lines) — inlined from phase_C_v3
Phase: validate           (~350 lines) — inlined from phase_validate_v4
Phase: review (Gemini)    (~400 lines) — inlined from phase_review_gemini_v4
Phase: review (Claude)    (~200 lines) — inlined from phase_review_v4
Phase: mdx                (~30 lines)  — inlined from phase_E_v3

Phase helpers             (~1400 lines) — moved from build_module.py
  _deterministic_screen, _run_deterministic_fixes, screen result caching
  _extract_audit_failures, _build_d3_context, _extract_gate_blockers
  _apply_module_fixes, _snapshot_module_files, _apply_fixes_with_rollback
  _escalate_fix, DScreenResult, D1Result, _scan_llm_filler
  _parse_d1_review, _extract_fix_plan, _get_track_calibration
  _load_rag_for_review, _build_pass1_prompt, _build_pass2_prompt
  _parse_factual_review, _merge_gemini_review_passes, _gemini_fix_iteration
```

### `build_module_v5.py` (~600 lines)

```
Imports + constants       (~30 lines)
CLI parser                (~80 lines)  — simplified, no v3 flags
preflight                 (~100 lines) — single function, merged v3+v4
run_pipeline              (~60 lines)  — single loop, delegates to pipeline_v5
_run_single_module        (~80 lines)  — simplified, no v3 branches
Batch runner              (~200 lines) — same logic, no v3 branches
Verify mode               (~30 lines)
```

---

## Consumer Updates (Gemini Review Finding #2)

These files read state files and must be updated to recognize `state-v5.json`:

| File | Current Code | Required Change |
|------|-------------|-----------------|
| `scripts/api/state_router.py:214` | Priority: `state-v4.json > state-v3.json > state.json` | Add `state-v5.json` at top of priority chain |
| `scripts/api/comms_router.py:645` | Scans `state-v3.json` for live activity | Also scan `state-v5.json` |
| `scripts/audit/checks/review_gaming.py:642` | Reads `state-v3.json` for `builder_model` | Also check `state-v5.json`, then `state-v4.json` |
| `scripts/generate_mdx.py:186` | Reads `state-v4.json > state-v3.json > state.json` | Add `state-v5.json` at top |

These are small, safe changes (add one more file to the lookup chain). They can be done before or during v5 development.

---

## Migration Path

1. Update consumers (state_router, comms_router, review_gaming, generate_mdx) to recognize `state-v5.json`
2. Build `pipeline_v5.py` + `build_module_v5.py`
3. Test on M1 (fully built — verify skip behavior via state migration)
4. Test on M2 (partially built — verify resumption via v4 state migration)
5. Test with a v3-only module (verify v5 starts fresh, ignores v3 state)
6. Run `test_pipeline.py` with v5 variants
7. Live build on a new module
8. Batch test (`--range 1-5`)
9. When proven on 50+ modules: make v5 the default
10. Later cleanup: remove v3/v4 code from `build_module.py` and `pipeline_lib.py`

### State Files Are Never Deleted

v5 writes `state-v5.json` alongside existing files. Legacy `state.json`, `state-v3.json`, and `state-v4.json` are left on disk (read-only). This means:
- Old `build_module.py` continues to work on the same modules
- API/audit consumers still find their expected files
- Rollback is trivial: just use `build_module.py` again

---

## Risk Assessment

| Risk | Mitigation |
|------|-----------|
| Behavioral regression | test_pipeline.py tests both old and new |
| v2 state.json collision | Use `state-v5.json`, never `state.json` |
| 1598 v3 modules start fresh | Expected — v3 modules need rebuilding anyway |
| Consumer breakage (API, audit, MDX) | Update 4 files to add `state-v5.json` to lookup chain |
| Active batch conflicts | v5 writes `state-v5.json`, old code writes `state-v4.json` — no collision |
| Missing edge case | Don't delete old code until v5 runs 50+ modules |

---

## Verification Plan

### Unit Tests (test_pipeline.py)
1. All existing tests must pass with v5
2. New: `test_v5_state_migration_v4` — load v4 state, verify v5 reads it correctly
3. New: `test_v5_ignores_v3_state` — v3 state present, v5 starts fresh
4. New: `test_v5_no_state_collision` — verify v5 writes `state-v5.json`, not `state.json`

### Integration Tests
6. `build_module_v5.py a1 1 --dry-run` — identical skip behavior to v4
7. `build_module_v5.py a1 1 --verify` — identical audit output
8. Consumer test: `generate_mdx.py` runs on a v5-built module without error
9. Consumer test: `state_router.py` classifies a v5 module correctly
10. Consumer test: `review_gaming.py` finds `builder_model` from v5 state

### End-to-End
11. Live build: `build_module_v5.py a1 {new_module} --review` — full pipeline, PASS verdict
12. Batch: `build_module_v5.py a1 --range 1-5` — must skip completed modules
13. Resumption: run v5 on a module with v3 state, verify it resumes (not restarts)

---

## Non-Goals

- No new features (content quality checks, plan auto-fix improvements)
- No changes to audit logic (except state file lookup in review_gaming.py)
- No changes to Gemini/Claude dispatch
- No changes to template files
- No changes to pipeline_lib.py shared utilities

---

## Gemini Adversarial Review — Issues Addressed

| # | Finding | Severity | Resolution |
|---|---------|----------|------------|
| 1 | `state.json` collision with 519 v2 files | CRITICAL | Use `state-v5.json` instead |
| 2 | 1598 `state-v3.json` files not migrated | CRITICAL | Not needed — v3 modules need rebuilding anyway. v5 starts fresh. |
| 3 | Helpers in CLI file, not pipeline file | ARCHITECTURAL | Moved all phase helpers to `pipeline_v5.py` |
| 4 | Consumer breakage (API, audit, MDX) | HIGH | Documented 4 consumer files to update |
| 5 | Missing integration tests | HIGH | Added 8 new tests (state migration, consumer, resumption) |
