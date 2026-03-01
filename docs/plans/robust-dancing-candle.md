# Plan: Pipeline v4 — Named Phases, Simplified Architecture

## Context

Pipeline v3 has accumulated complexity:
- Phases named with letters (A, B, C, D, E, F) plus one named ("audit") — inconsistent
- D.0/D.0.5 (deterministic checks) trapped inside Claude-dependent Phase D
- Three separate fix loops (audit, D.0.5, D.2) with audit running in 5+ places
- Separate Phase F that duplicates Phase D's review
- User can't get full deterministic report without Claude

**v4 goals:**
- Named phases (no more A/B/C/D/E/F)
- Merge audit + screen into single `validate` phase
- Merge D + F into single `review` phase (report + one fix attempt)
- Clear separation: Claude only needed for `review`
- Three modes: research-only, rc (default), full (with review)

## Quality Assurance Philosophy

This project provides Ukrainian language education. Content quality is non-negotiable — errors in language teaching actively harm learners, and in the current political context, getting Ukrainian right matters.

**Principle: review is mandatory for publication, but decoupled from build.**

- RC mode builds and validates — the module is a "draft" (deterministic QA only)
- Review mode adds Claude adversarial review — the module becomes "reviewed"
- MDX runs in both modes (for preview), but **module status reflects review state**
- A module without review is `status: draft` — usable for preview, not publication
- A module with review is `status: reviewed` — publication-ready

This means the cross-agent adversarial principle ("Gemini builds, Claude reviews") isn't optional — it's deferred. Every module should eventually pass review before reaching learners.

## v4 Pipeline

```
research → content → activities → validate → [review] → mdx
```

| Phase | What it does | Agent | Claude? |
|-------|-------------|-------|---------|
| `research` | Research + meta YAML | Gemini | No |
| `content` | Prose writing | Gemini | No |
| `activities` | Activities + vocabulary | Gemini | No |
| `validate` | Full audit + Russicism + filler + RAG verify + Gemini fix loop | Gemini + deterministic | No |
| `review` | Structured review + one fix attempt | Claude | **Yes** |
| `mdx` | MDX generation + lint | Deterministic | No |

### Pipeline Modes

- `--research-only`: just `research`
- Default (RC): `research → content → activities → validate → mdx` (module status: `draft`)
- `--review`: `research → content → activities → validate → review → mdx` (module status: `reviewed`)

### Resume After RC

`--restart-from review` runs: `review → mdx`

(mdx re-runs after review because review may change content)

### Module Status Tracking

| Pipeline mode | Status after validate | Status after review |
|--------------|---------------------|-------------------|
| RC (default) | `draft` | — |
| Full (`--review`) | `draft` | `reviewed` |
| Review fails | — | `needs-manual-review` (not `needs-rebuild` — preserves Gemini work) |

## Phase Details

### `validate` (merges v3: audit + screen + D.0 + D.0.5)

One phase, one fix loop, one validation function:

1. Run `_deterministic_screen()` — full audit (content_only=False) + Russicism + filler + RAG verify
2. If clean → mark complete, save results
3. If issues → Gemini fix loop (up to `max_iters` iterations):
   - Dispatch Gemini fix prompt
   - Apply fixes
   - Re-run `_deterministic_screen()`
   - If clean → break
4. After loop: save final `DScreenResult` to `screen-result.json`
5. Print summary report (audit pass/fail, issue counts, RAG coverage)

Key change: uses `content_only=False` from the start (not prose-only). Activities exist by this point.

### `review` (merges v3: D.1 + D.2 + F)

Simplified — review + up to 2 fix attempts:

1. Load cached `screen-result.json` from validate (stale check hashes md+activities+vocab)
2. Claude structured review (current D.1 logic: inject metrics, deterministic issues, RAG verify into prompt)
3. If PASS → mark `reviewed`, done
4. If FAIL → up to 2 Claude fix attempts:
   - Attempt 1: fix the issue Claude found
   - Attempt 2: fix formatting breakage from attempt 1 (if any)
   - Re-validate after each attempt
5. If still fails after 2 attempts → mark `needs-manual-review` (preserves Gemini work)

No Phase F. No re-review. Claude gets one review + up to 2 fixes.

## Files to Modify

| File | Change |
|------|--------|
| `scripts/build_module_v3.py` | New constants, new phase functions, new `run_pipeline_v4()`. Reuse existing internal functions (`_deterministic_screen`, `_format_*`, `_parse_d1_review`, etc.) |

## Step-by-Step

### 1. New constants (~line 99)

```python
# v4 pipeline
PHASE_SEQUENCE_V4 = ["research", "content", "activities", "validate", "review", "mdx"]

_V4_PHASE_STATE_IDS = {
    "research":   ["v4-research"],
    "content":    ["v4-content"],
    "activities": ["v4-activities"],
    "validate":   ["v4-validate"],
    "review":     ["v4-review"],
    "mdx":        ["v4-mdx"],
}

PHASE_LABELS_V4 = {
    "research":   "Research + Meta",
    "content":    "Content (prose)",
    "activities": "Activities + Vocab",
    "validate":   "Validate (audit + screen + Gemini fix)",
    "review":     "Review (Claude, optional)",
    "mdx":        "MDX Generation",
}
```

### 2. Phase functions — thin wrappers over existing code

```python
def phase_research_v4(ctx, state):
    """v4 research = v3 Phase A."""
    return phase_A_v3(ctx, state)  # Reuse entirely

def phase_content_v4(ctx, state):
    """v4 content = v3 Phase B."""
    return phase_B_v3(ctx, state)  # Reuse entirely

def phase_activities_v4(ctx, state):
    """v4 activities = v3 Phase C."""
    return phase_C_v3(ctx, state)  # Reuse entirely

def phase_mdx_v4(ctx):
    """v4 mdx = v3 Phase E."""
    return phase_E_v3(ctx)  # Reuse entirely
```

### 3. `phase_validate_v4()` — merged audit + screen

New function that combines:
- v3 `phase_audit_v3` fix loop logic (but with `content_only=False`)
- v3 `_deterministic_screen()` (all 7 checks)
- v3 D.0.5 Gemini proofread

```python
def phase_validate_v4(ctx, state):
    """Validate: full deterministic checks + Gemini fix loop.

    Merges v3 audit + screen + D.0 + D.0.5 into one phase.
    Runs content_only=False (full audit including activities).
    """
    phase = "validate"
    # ... skip if complete, dry_run guard ...

    # Check sidecar files exist
    # ... (moved from phase_D_v3) ...

    # Initial screen
    screen = _deterministic_screen(ctx)
    log(f"  Validate: Initial — audit {'PASS' if screen.audit_passed else 'FAIL'}, "
        f"{len(screen.deterministic_issues)} issue(s)")

    if screen.audit_passed and not screen.deterministic_issues:
        _save_screen_result(ctx, screen)
        _mark_phase_v4(ctx, state, phase, "complete", attempts=0)
        return True

    # Gemini proofread fix (D.0.5 logic)
    _run_gemini_proofread(ctx)

    # Gemini fix loop (audit fix loop logic)
    max_iters = _max_audit_iters(ctx.track)
    for attempt in range(1, max_iters + 1):
        screen = _deterministic_screen(ctx)

        if screen.audit_passed and not screen.deterministic_issues:
            _save_screen_result(ctx, screen)
            _mark_phase_v4(ctx, state, phase, "complete", attempts=attempt)
            return True

        if attempt >= max_iters:
            # Exhausted — save results anyway for reporting
            _save_screen_result(ctx, screen)
            _mark_phase_v4(ctx, state, phase, "failed", attempts=attempt)
            # Escalation to Claude optional
            return False

        # Dispatch Gemini fix
        fix_prompt = _build_fix_prompt(ctx, screen.audit_output, content_only=False)
        # ... dispatch + apply fixes (reuse existing logic) ...

    _save_screen_result(ctx, screen)
    return False
```

### 4. `phase_review_v4()` — consolidated D.1 + one fix

```python
def phase_review_v4(ctx, state):
    """Review: Claude structured review + one fix attempt.

    Loads cached screen results from validate phase.
    Claude reviews holistically (pedagogy, naturalness, accuracy).
    If FAIL: one Claude fix attempt, then re-validate. No loop.
    """
    phase = "review"
    # ... skip if complete, dry_run guard ...

    # Load cached screen results (with stale hash fallback)
    screen = _load_screen_result(ctx)
    if screen is None:
        screen = _deterministic_screen(ctx)

    # D.1: Claude structured review (reuse existing injection + dispatch logic)
    # ... inject metrics, deterministic issues, RAG verify into prompt ...
    # ... dispatch Claude, parse D1Result ...

    if review_result.verdict == "PASS" and screen.audit_passed:
        _mark_phase_v4(ctx, state, phase, "complete")
        return True

    # ONE fix attempt (simplified D.2 — no loop)
    # ... dispatch Claude fix prompt ...
    # ... apply FIND/REPLACE fixes ...

    # Re-validate after fix
    screen = _deterministic_screen(ctx)
    if screen.audit_passed:
        _mark_phase_v4(ctx, state, phase, "complete", note="fixed")
        return True

    _mark_phase_v4(ctx, state, phase, "failed", note="needs-manual-review")
    return False
```

### 5. `run_pipeline_v4()` — new runner

```python
PHASE_FUNCTIONS_V4 = {
    "research":   phase_research_v4,
    "content":    phase_content_v4,
    "activities": phase_activities_v4,
    "validate":   phase_validate_v4,
    "review":     phase_review_v4,
    "mdx":        phase_mdx_v4,
}

def run_pipeline_v4(ctx, research_only=False):
    state = _load_state_v4(ctx)

    if research_only:
        return _call_phase(phase_research_v4, "research", ctx, state)

    # Determine sequence based on --review flag
    if ctx.review:
        sequence = PHASE_SEQUENCE_V4  # all phases including review
    else:
        sequence = [p for p in PHASE_SEQUENCE_V4 if p != "review"]  # RC mode

    for phase_id in sequence:
        if not _call_phase(PHASE_FUNCTIONS_V4[phase_id], phase_id, ctx, state):
            return False
    return True
```

### 6. State helpers — v4 versions

Reuse existing pattern but with v4 keys:
- `_load_state_v4()` / `_save_state_v4()` — same as v3 but reads/writes `state-v4.json`
- `_mark_phase_v4()` — same as `_mark_phase_v3()` but uses v4 state IDs
- `_is_phase_v4_complete()` — same pattern

### 7. Screen result serialization

```python
def _save_screen_result(ctx, screen: DScreenResult):
    """Save DScreenResult + content hash for review phase reuse."""
    content_path = ctx.paths["md"]
    data = dataclasses.asdict(screen)
    data["content_hash"] = hashlib.md5(content_path.read_bytes()).hexdigest()[:12]
    (ctx.orch_dir / "screen-result.json").write_text(
        json.dumps(data, ensure_ascii=False, indent=2), "utf-8")

def _load_screen_result(ctx) -> DScreenResult | None:
    """Load cached screen result, return None if stale or missing."""
    f = ctx.orch_dir / "screen-result.json"
    if not f.exists():
        return None
    data = json.loads(f.read_text("utf-8"))
    content_path = ctx.paths["md"]
    current_hash = hashlib.md5(content_path.read_bytes()).hexdigest()[:12]
    if data.get("content_hash") != current_hash:
        log("  Review: Cached screen stale — re-screening")
        return None
    return DScreenResult(**{k: v for k, v in data.items() if k != "content_hash"})
```

### 8. CLI changes

```python
parser.add_argument("--review", action="store_true",
    help="Include Claude review phase (default: RC mode without review)")
parser.add_argument("--stop-before", type=str,
    help="Stop before this phase (e.g. --stop-before validate)")
parser.add_argument("--restart-from", type=str,
    help="Clear and restart from this phase (e.g. --restart-from review)")
parser.add_argument("--force-phase", type=str,
    help="Force re-run a single phase (e.g. --force-phase validate)")
```

### 9. What stays, what goes

**Reused as-is** (internal functions):
- `_deterministic_screen()`, `_format_*()`, `_parse_d1_review()`
- `_dispatch_claude_phase()`, `dispatch_gemini()`
- `_build_fix_prompt()`, `_apply_find_replace_fixes()`
- `_prefetch_rag_context()`, `_get_track_calibration()`
- `run_verify()`, `_run_deterministic_fixes()`
- `phase_A_v3()`, `phase_B_v3()`, `phase_C_v3()`, `phase_E_v3()` (delegated to)

**Removed / superseded:**
- `phase_audit_v3()` → merged into `phase_validate_v4()`
- `phase_D_v3()` → split into `phase_validate_v4()` (D.0/D.0.5) + `phase_review_v4()` (D.1 + one D.2)
- `phase_F_v3()` → merged into `phase_review_v4()`
- `phase_D_rescreen()` → replaced by `--force-phase validate`
- `run_pipeline_v3()` → replaced by `run_pipeline_v4()`
- All v3 constants (`PHASE_SEQUENCE_V3`, `_V3_PHASE_STATE_IDS`, etc.)
- v2→v3 migration code (no longer needed)

**State files:**
- New: `state-v4.json` (fresh start, no migration from v3)
- Old `state.json` / `state-v3.json` ignored by v4

## What Changes for the User

| Before (v3) | After (v4) |
|-------------|------------|
| `--stop-before D` | Default mode (RC) — no flag needed |
| Letters: A, B, C, D, E, F, "audit" | Names: research, content, activities, validate, review, mdx |
| 3 fix loops + audit in 5 places | 1 fix loop (validate) + 1 fix attempt (review) |
| Phase D required for any quality report | `validate` gives full report without Claude |
| Phase F = separate review | Consolidated into `review` |
| `--restart-from D` | `--restart-from review` |
| Always runs D if in pipeline | Review only runs with `--review` flag |

## Gemini Adversarial Review — Issues Found & Fixes

### 1. State corruption via reused v3 functions (VALID)

v3 phase functions internally call `_mark_phase_v3()`. Thin wrappers can't just delegate.

**Fix:** Extract the core logic of each v3 phase function into an `_inner_*` function that accepts a phase-marking callback. v4 wrappers pass `_mark_phase_v4`. Alternatively, since we're rewriting: refactor phase functions to return a result tuple, and let the pipeline runner handle state marking.

### 2. Incomplete cache invalidation (VALID)

Screen result only hashes MD file, but validate checks activities+vocab too.

**Fix:** Hash all three files: `md + activities.yaml + vocabulary.yaml`. Cache stale if any changed.

### 3. No MDX on validate failure (VALID)

User needs MDX preview even when validate fails. Current design halts pipeline on failure.

**Fix:** MDX always runs, regardless of validate/review outcome. Change `run_pipeline_v4()` to not halt on validate failure — continue to mdx. Only `review` depends on validate passing.

### 4. Proofread triggered unnecessarily (VALID)

If only activities fail, Gemini prose proofread is wasteful.

**Fix:** Only run `_run_gemini_proofread()` when `screen.deterministic_issues` contains prose-related issues (RUSSIANISM, LLM_FILLER) or audit output shows prose gate failures. Skip if only activity/schema issues.

### 5. needs-rebuild vs needs-manual-review (VALID — typo)

Plan says `needs-manual-review`, code example says `needs-rebuild`.

**Fix:** Code must use `needs-manual-review`. Preserves Gemini work.

### 6. One fix attempt is brittle (VALID — changed to 2)

Claude's fix may break formatting, and one attempt doesn't allow self-correction.

**Fix:** Allow 2 fix iterations (same as v3 D.2). One to fix the issue, one to fix formatting if needed. Still much simpler than v3's unbounded loops.

### 7. Status propagation missing (VALID)

No mechanism to write `draft`/`reviewed` into `status/{slug}.json`.

**Fix:** After validate completes, write `"pipeline_status": "draft"` to status JSON. After review passes, update to `"pipeline_status": "reviewed"`. MDX generator doesn't need to know — status is tracked separately.

### 8. Redundant audit_passed check in review (ACKNOWLEDGED)

Defensive code, harmless. Keep it — belt and suspenders.

## Verification

1. Run default pipeline on a module → confirm: research → content → activities → validate → mdx (no review)
2. Run `--review` → confirm review phase runs between validate and mdx
3. Run `--restart-from review` → confirm: review → mdx
4. Run `--force-phase validate` → confirm validate re-runs
5. Run `--research-only` → confirm only research runs
6. Validate phase: confirm Russicism + filler + RAG verify + full audit all run
7. Review phase: confirm cached screen loads, Claude reviews, 2 fix attempts if FAIL
8. Validate failure → confirm mdx still runs (preview available)
9. Module status JSON shows `draft` after RC mode, `reviewed` after full mode
10. Cache invalidation: edit activities.yaml → confirm review detects stale cache
