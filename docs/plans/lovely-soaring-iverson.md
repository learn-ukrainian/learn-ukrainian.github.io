# Pipeline Consolidation & Optimization

## Context

The build pipeline has accumulated 3 generations of code (v3/v4/v5). `pipeline_lib.py` is 3,845 lines but 72.9% (~2,800 lines) is dead code from retired pipelines. The live code is spread across pipeline_lib.py (shared utilities), build/pipeline_v5.py (phase implementations), and build/build_module_v5.py (CLI). Dispatch routing is fragile — split across 3 files with multiple factory functions. This makes every bug fix harder and introduces regressions (e.g., the preflight routing bug from today).

With 1700+ modules to build, reliability matters more than features. This refactor makes the pipeline smaller, clearer, and harder to break.

## Phase 1: Delete Dead Code (LOW RISK)

**Goal:** Remove ~2,400 lines of provably dead code from `pipeline_lib.py`.

**What to delete:**
- Legacy phase implementations: `phase_8_mdx`, `phase_9_final_review`
- Legacy Claude dispatch: `_claude_cli`, `_run_claude_headless`, `_apply_file_fixes`, `dispatch_claude_final_review`
- Legacy state management: `load_state` (old), `save_state` (old), `is_phase_complete`, `mark_phase`, `_init_state_lock`, `clean_phase_artifacts`, `_phase_state_ids`, `_external_artifacts_for_phase`, `PHASE_SEQUENCE`, `PHASE_ARTIFACT_PATTERNS`
- Legacy extraction: `extract_phase_output`, `_extract_delimited_content`, `_parse_section`
- Legacy preflight: `preflight()` — merge its essential logic into `preflight_v2()`

**Key risk:** `preflight_v2()` calls `preflight()` internally. Must inline the needed parts before deleting.

**Result:** pipeline_lib.py drops from 3,845 to ~1,450 lines.

**Verify:**
1. `grep -rn <function_name> scripts/ tests/` for every deleted function — zero external callers
2. Full test suite passes
3. `--dry-run` on a1 1 works
4. `--verify` on already-built modules passes

**Files:** `scripts/pipeline_lib.py`

---

## Phase 2: Flatten Content Delegation Chain (MEDIUM RISK)

**Goal:** Eliminate 3-layer indirection: v5 `phase_content` → `phase_B_content` → `phase_2_content`.

**What to do:**
- Move `phase_2_content` logic into pipeline_v5.py's `phase_content`
- Inline useful parts of `phase_B_content` (adopt-existing, research-alignment check)
- Remove archive restoration path (dead for current builds)
- Delete `phase_B_content` and `phase_2_content` from pipeline_lib.py (~400 lines)

**Result:** Content phase is self-contained in pipeline_v5.py. No cross-file delegation.

**Verify:**
1. Build a1 1 with `--writer claude` (Claude content path)
2. Build a1 2 with default (Gemini content path)
3. Both produce same quality output

**Files:** `scripts/build/pipeline_v5.py`, `scripts/pipeline_lib.py`

---

## Phase 3: Consolidate Dispatch (MEDIUM RISK)

**Goal:** One file for all dispatch logic. No more hunting across 3 files for routing bugs.

**What to do:**
- Create `scripts/pipeline/dispatch.py` (~300 lines)
- Move from pipeline_lib.py: `dispatch_gemini_raw`, `dispatch_gemini`, `save_gemini_session`, `_run_with_heartbeat`
- Move from pipeline_v5.py: `_dispatch_claude_phase`
- Move from build_module_v5.py: `_make_preflight_claude_dispatch`
- Add unified `dispatch_phase(ctx, phase, prompt, ...)` that checks `ctx.use_claude` internally
- Update all callers

**Result:** All dispatch in one place. Adding a new LLM backend = one file to change.

**Verify:**
1. `--writer claude` builds correctly
2. `--writer gemini` builds correctly (default)
3. Preflight routes to opposite agent
4. Rate-limit fallback still works

**Files:** New `scripts/pipeline/dispatch.py`, update `scripts/pipeline_lib.py`, `scripts/build/pipeline_v5.py`, `scripts/build/build_module_v5.py`

---

## Phase 4: Extract Config & Templates (LOW RISK)

**Goal:** Move config tables and template helpers out of pipeline_lib.py into focused modules.

**What to do:**
- Create `scripts/pipeline/config_tables.py` (~400 lines): TRACK_SKILLS, IMMERSION_RULES, all accessor functions
- Create `scripts/pipeline/templates.py` (~250 lines): template selectors, tier helpers, scoring helpers, fill_template, check_prompt_health
- Update importers, add backward-compat re-exports in pipeline_lib.py

**Result:** pipeline_lib.py drops to ~600 lines (ModuleContext, log, run_verify, preflight_v2, build_placeholders).

**Verify:**
1. Full test suite
2. `build_placeholders` produces identical output before/after

**Files:** New `scripts/pipeline/config_tables.py`, new `scripts/pipeline/templates.py`, update `scripts/pipeline_lib.py`

---

## Phase 5: Final Restructure (LOW-MEDIUM RISK)

**Goal:** Clean file names, break circular dependencies, final polish.

**What to do:**
- Rename pipeline_lib.py → pipeline/core.py (add backward-compat stub)
- Move `preflight_v2` → `pipeline/preflight.py`
- Move content helpers → `pipeline/content_helpers.py`
- Break `pipeline/state.py` circular dependency on pipeline_lib (it uses `_get_pipeline_lib()`)
- Gradually update imports from `pipeline_lib` to `pipeline.*`

**Final structure:**
```
scripts/pipeline/
  core.py              (~200 lines) ModuleContext, log, verify
  dispatch.py          (~300 lines) Gemini + Claude dispatch
  config_tables.py     (~400 lines) Track config, immersion rules
  templates.py         (~250 lines) Template selection, scoring
  content_helpers.py   (~400 lines) RAG prefetch, section budgets
  preflight.py         (~300 lines) preflight_v2, build_placeholders
  state.py             (~200 lines) State management
  screen.py            (~540 lines) Deterministic validation
  prompt_preflight.py  (~460 lines) Prompt review
  fixes.py             (~275 lines) Fix generation
  consultation.py      (~340 lines) Consultation loop
  parsing*.py          (~1,000 lines) Parsing helpers
  learner_state.py     (~190 lines) Learner state
  semantic_russianisms.py (~180 lines) Russicism detection
```

**Total: ~5,035 lines** (down from ~11,000). Each file has one job.

---

## Execution Summary

| Phase | Lines Removed | Risk | Depends On |
|-------|--------------|------|------------|
| 1. Delete dead code | ~2,400 | LOW | None |
| 2. Flatten content chain | ~400 | MEDIUM | Phase 1 |
| 3. Consolidate dispatch | ~300 | MEDIUM | Phase 1 |
| 4. Extract config/templates | ~800 | LOW | Phase 1 |
| 5. Restructure | ~600 | LOW-MEDIUM | Phases 2-4 |

**Net reduction: ~4,500 lines (~41% of codebase)**

Phase 1 is the clear first move — zero behavioral change, massive complexity reduction.
Phases 2+3 address the dispatch routing bugs directly.
Phases 4+5 are quality-of-life for long-term maintainability.
