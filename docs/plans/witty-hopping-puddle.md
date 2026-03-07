# Plan: Kill the Dual State System

## Context

`pipeline_v5.py` (the ONLY pipeline) calls functions from `pipeline_lib.py` (legacy v3/v4 code). They use **different state files** (`state-v5.json` vs `state.json`), **different phase keys** (`"content"` vs `"2"`), and **different mark functions** (`mark_complete` vs `mark_phase`). This caused the self-audit feature to silently fail for weeks — the flag was written to a dict that `mark_complete` immediately overwrote.

**Goal**: One state file, one naming system, one mark function. No more phantom state.json writes.

## Phase 1: Neutralize Legacy State Writes (do now)

Add `"v5"` to existing guards in `pipeline_lib.py`. Exact same pattern as the `"v4"` guard that already exists.

### Changes

**`scripts/pipeline_lib.py`** — 3 changes:

1. **`mark_phase()` (line 1187)**: Add v5 to the no-op guard
   ```python
   # BEFORE
   if getattr(ctx, "mode", None) == "v4":
       return
   # AFTER
   if getattr(ctx, "mode", None) in ("v4", "v5"):
       return
   ```

2. **`save_state()` (line 1124)**: Add v5 guard
   ```python
   def save_state(ctx: ModuleContext) -> None:
       if getattr(ctx, "mode", None) in ("v4", "v5"):
           return
       # ... existing code
   ```

3. **`is_phase_complete()` (line 1132)**: Add v5 guard (always returns False — v5 has its own `is_complete()`)
   ```python
   def is_phase_complete(ctx: ModuleContext, phase: str) -> bool:
       if getattr(ctx, "mode", None) == "v5":
           return False
       # ... existing code
   ```

**`scripts/pipeline_v5.py`** — 1 change:

4. **`phase_content()` (line ~2946)**: Pass `self_audited` through `mark_complete` kwargs (already done in this session, verify it's correct)
   ```python
   mark_complete(state, "content", ctx, **({"self_audited": True} if self_audited else {}))
   ```

### What This Fixes
- `state.json` stops being written for v5 builds
- `mark_phase` calls inside `phase_B_content` become no-ops — no more fighting state systems
- `is_phase_complete(ctx, "2")` returns False — v5's own `is_complete(state, "content")` is the only authority
- Self-audit flag survives `mark_complete` (passed as kwarg, not pre-written then overwritten)

## Phase 2: Clean Up (later, separate PR)

1. Refactor `phase_B_content` to return a result dataclass (no internal state calls)
2. Move fix-prompt helpers (`_build_fix_prompt`, `_apply_section_fixes`, `_identify_affected_sections` + deps) into `pipeline_v5.py` — only used by v5
3. Stop loading `state.json` in `preflight_v2` for v5 mode
4. Archive `build_module.py` to `scripts/retired/`
5. Bulk-delete stale `state.json` files from orchestration dirs

## Verification (Phase 1)

1. Note current `state.json` timestamp for a1/orchestration/describing-things-adjectives/
2. `.venv/bin/python scripts/build_module_v5.py a1 11 --restart-from content` — rebuild M11
3. Verify: `state-v5.json` updated, `state.json` NOT updated
4. Verify: `state-v5.json` contains `"self_audited": true` in `phases.content`
5. Verify: validate phase logs "Content was self-audited — reducing max fix iterations"

## Files

| File | Phase | Change |
|------|-------|--------|
| `scripts/pipeline_lib.py` | 1 | Add `"v5"` guards to `mark_phase`, `save_state`, `is_phase_complete` |
| `scripts/pipeline_v5.py` | 1 | Pass `self_audited` through `mark_complete` kwargs |
| `scripts/pipeline_lib.py` | 2 | Refactor `phase_B_content` return type, remove dead state calls |
| `scripts/pipeline_v5.py` | 2 | Move fix-prompt helpers in, update `phase_content` |
| `scripts/build_module_v5.py` | 2 | Stop wiring `ctx.state` from `state.json` |
| `scripts/build_module.py` | 2 | Archive to `scripts/retired/` |
