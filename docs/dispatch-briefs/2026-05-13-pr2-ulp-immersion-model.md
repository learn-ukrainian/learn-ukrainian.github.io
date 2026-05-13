# Dispatch Brief — PR2: ULP-derived cumulative-vocab-aware immersion model

> **Status:** PENDING DISPATCH (after PR1 v2 lands). Authority: `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` § "PR2 — ULP-derived cumulative-vocab-aware immersion model".
> Scope is PR2 of the 2-PR split. PR1 must be merged to main before this dispatches.

## Mission

Replace the static `IMMERSION_POLICIES` band dict in `scripts/config.py` with a **derivation function** that computes the immersion band for module N from `learner_state` (PR1's contribution). Add lemma-frequency tracking, a recycle-cadence audit gate, and the unified `plan.targets` schema that subsumes the Gate 4 work from `#1916`. Behind feature flag `USE_ULP_IMMERSION_DERIVATION=false` default; calibration is Phase 4 (separate dispatch).

## Determined verifiable claims this PR will produce

| Claim | Deterministic tool | Output format (raw evidence required) |
|---|---|---|
| `compute_immersion_band` function exists with the documented signature | `grep -n "def compute_immersion_band" scripts/config.py` | raw line + signature |
| Feature flag exists and defaults to OFF | `grep -n "USE_ULP_IMMERSION_DERIVATION" scripts/config.py` | raw line showing `= False` default |
| Lemma-frequency module exists | `ls -la scripts/build/learner_immersion.py` | raw `-rw-r--r-- ...` line |
| `plan.targets` schema documented | `grep -n "plan.targets\|new_vocabulary\|targets:" docs/lesson-contract.md` | raw lines |
| Migration script for 55 A1 plans | `ls scripts/migrations/2026-05-13-add-plan-targets.py` | raw listing |
| Recycle-cadence audit check registered | `grep -rn "recycle_cadence" scripts/audit/` | raw lines |
| Tests pass | `.venv/bin/pytest tests/test_learner_immersion.py tests/test_compute_immersion_band.py tests/test_recycle_cadence_gate.py tests/test_plan_targets_schema.py -v 2>&1 \| tail -3` | raw `passed in M.MMs` line |
| Full test suite no regressions | `.venv/bin/pytest tests/ -x --ignore=tests/e2e 2>&1 \| tail -5` | raw final summary |
| Lint clean | `.venv/bin/ruff check scripts/config.py scripts/build/learner_immersion.py scripts/audit/checks/recycle_cadence.py scripts/migrations/2026-05-13-add-plan-targets.py tests/test_learner_immersion.py tests/test_compute_immersion_band.py tests/test_recycle_cadence_gate.py tests/test_plan_targets_schema.py` | raw `All checks passed!` |

Per `#M-4`: paraphrased claims = hallucination. Every assertion in PR body backed by `<command + cwd + raw-output>` triple.

## Numbered steps

### Step 1 — Worktree

```bash
git fetch origin
git worktree add -b codex/pr2-ulp-immersion-2026-05-13 \
  .worktrees/dispatch/codex/pr2-ulp-immersion-2026-05-13 \
  origin/main
cd .worktrees/dispatch/codex/pr2-ulp-immersion-2026-05-13
```

PR1 MUST be merged to main first. If `origin/main` does not contain the `{LEARNER_STATE}` placeholder (`grep -c '{LEARNER_STATE}' scripts/build/phases/linear-write.md`) ≥ 1, ABORT with `GOAL_ABORT reason="pr1-not-landed"` rather than improvising.

### Step 2 — File-level work

#### 2a. New file: `scripts/build/learner_immersion.py`

Module providing:

```python
def build_lemma_frequency_map(track: str, up_to_module: int) -> dict[str, list[tuple[int, int]]]:
    """For each lemma, return list of (module_num, surface_form_count) tuples
    from all modules before up_to_module. Cached on disk in
    .cache/lemma-frequency-{track}-{module}.json.
    """
```

Walk `curriculum/l2-uk-en/{track}/{slug}/vocabulary.yaml` for every module before `up_to_module` (use `curriculum.yaml` for ordering, same as `learner_state.build_learner_state`). For surface-form counts, scan `module.md` body prose with the same UK-lemma extractor used by `learner_state` PR1's audit gate (`scripts/audit/checks/learner_state.py`). Reuse the extractor; do NOT duplicate the regex.

Cache invalidation: if any source `vocabulary.yaml` mtime > cache file mtime, rebuild. Keep the cache writes atomic (tempfile + rename).

#### 2b. Replace `IMMERSION_POLICIES` static dict in `scripts/config.py`

Add at top of `scripts/config.py`:

```python
USE_ULP_IMMERSION_DERIVATION: bool = False  # Phase 3 default; flipped after Phase 4 calibration.
```

Add new function in `scripts/config.py`:

```python
def compute_immersion_band(track: str, module_num: int, learner_state: dict | None = None) -> dict[str, Any]:
    """Compute the immersion band for module N derived from cumulative-vocab
    state. When USE_ULP_IMMERSION_DERIVATION is False, this function is a
    thin shim around the static IMMERSION_POLICIES fallback (so behavior
    is unchanged until calibration completes). When True, derives band
    advisory_pct_min/max + structural fields from learner_state's
    cumulative_vocabulary count + known_grammar count, using calibration
    constants _ULP_VOCAB_KNEE_PER_BAND.
    """
```

Implementation outline:

- When flag OFF: delegate to existing `_find_immersion_band(track, module_num)` (current behavior preserved).
- When flag ON: lookup which band the cumulative-vocab COUNT falls into (use `_ULP_VOCAB_KNEE_PER_BAND` thresholds), return that band's normalized record.
- `_ULP_VOCAB_KNEE_PER_BAND`: dict of `{track: [(vocab_threshold, band_key), ...]}` constants — initial values are placeholders for Phase 4 calibration. Mark with `# PHASE_4_PLACEHOLDER` inline comment.

Modify all 4 existing accessors (`get_immersion_policy`, `get_immersion_range`, `get_immersion_structural`, `get_immersion_rule`) to optionally accept `learner_state` and forward to `compute_immersion_band` when flag ON, falling back to current behavior otherwise. Backward-compatible signature (positional + keyword), no breaking changes for current callers.

#### 2c. Recycle-cadence audit gate: new file `scripts/audit/checks/recycle_cadence.py`

For a given module:

- Read lemma-frequency map (from 2a) covering preceding modules.
- Identify "stale" lemmas: introduced ≥ `recycle_window` modules ago, last seen ≥ `recycle_window/2` modules ago.
- Count occurrences of stale lemmas in the current module's body.
- Threshold (`recycle_floor`): minimum number of stale-lemma occurrences this module must include.

Severity:
- A1: WARN
- A2+: defer/skip (will be HARD post-calibration; for now WARN at all levels)

`recycle_window` + `recycle_floor` are calibration constants — initial values land as placeholders in `scripts/config.py` with `# PHASE_4_PLACEHOLDER` annotation. The gate runs but only WARNs until Phase 4 flips it.

Register the check in the audit registry (same module PR1 touched).

#### 2d. `plan.targets` schema + migration

Extend the plan YAML schema with a new optional block:

```yaml
targets:
  new_vocabulary:        # words this module introduces
    - lemma1
    - lemma2
  new_grammar:           # grammar topics this module introduces
    - topic1
    - topic2
  recycle_vocabulary:    # earlier-introduced lemmas this module deliberately recycles (optional)
    - earlier-lemma
```

This subsumes the `vocabulary_hints.required` informal field. Migration must:

1. Add a Pydantic / dataclass model in the plan schema module (locate via `grep -rln 'class.*Plan' scripts/`).
2. Make `plan.targets` optional for backward compat — old plans without it fall back to the informal `vocabulary_hints.required` parse for now.
3. Migration script `scripts/migrations/2026-05-13-add-plan-targets.py`:
   - Reads each `curriculum/l2-uk-en/plans/a1/*.yaml` (55 files).
   - If `vocabulary_hints.required` exists AND `targets` does NOT, write a stub `targets.new_vocabulary` list populated from `vocabulary_hints.required` (extracting just the lemma — strip parenthetical English glosses).
   - Keep `vocabulary_hints` intact for backward compat.
   - Dry-run mode flag (`--dry-run`) prints proposed diff, no write.
   - Default mode writes in-place with atomic tempfile + rename.
   - Run with `--dry-run` first; commit a small sample (≤ 3 plans) actually migrated as proof-of-shape. Do NOT migrate all 55 in this PR — that's an operational decision the orchestrator makes after reviewing the proof-of-shape.

Document `plan.targets` schema in `docs/lesson-contract.md` (the authoritative spec). Add a new section "### Plan Targets (PR2)".

#### 2e. Wire `compute_immersion_band` into `linear_pipeline.py:writer_context`

In `scripts/build/linear_pipeline.py:writer_context()` (the same dict PR1 added `{LEARNER_STATE}` to), pass `learner_state` to whichever helper currently calls `get_immersion_policy`. Goal: when flag ON, immersion rules / structural thresholds are learner-state-aware. When flag OFF, behavior is byte-identical to PR1's main-after-merge.

**Scope discipline:** you may touch ONLY the `writer_context` substitution dict's existing immersion-related entries + the call sites of `get_immersion_*`. Do NOT touch `_advisory_immersion_pct`, `_l2_exposure_floor_gate`, `_long_uk_ceiling_gate`, `_component_density_gate` — those will be re-wired in a Phase 4 follow-up PR.

### Step 3 — Tests

#### 3a. `tests/test_learner_immersion.py`

- Build a fake mini-curriculum (3 modules with overlapping vocab).
- Assert `build_lemma_frequency_map(track, 3)` returns the right shape with right counts.
- Assert cache invalidates on source file mtime change.

#### 3b. `tests/test_compute_immersion_band.py`

- With flag OFF: assert `compute_immersion_band('a1', 5)` returns the same dict as today's `get_immersion_policy('a1', 5)`.
- With flag ON: assert it returns a band whose `advisory_pct_min/max` depends on the passed `learner_state.cumulative_vocabulary` count (not on module_num alone).
- Assert backward-compat: `get_immersion_policy`, `get_immersion_range`, etc. behavior is preserved when flag OFF.

#### 3c. `tests/test_recycle_cadence_gate.py`

- Fake module with no recycle of any earlier lemma → WARN.
- Fake module with sufficient recycle → PASS.
- Assert severity is WARN at A1 (placeholder phase).

#### 3d. `tests/test_plan_targets_schema.py`

- Valid plan with `targets` block parses.
- Plan without `targets` falls back to `vocabulary_hints.required`.
- Migration script `--dry-run` on a fixture plan: assert it produces the expected diff (parse `vocabulary_hints.required` → emit `targets.new_vocabulary`).
- Migration writes file atomically + preserves YAML key order.

### Step 4 — Test suite + ruff

```bash
.venv/bin/pytest tests/test_learner_immersion.py tests/test_compute_immersion_band.py tests/test_recycle_cadence_gate.py tests/test_plan_targets_schema.py -v
.venv/bin/pytest tests/ -x --ignore=tests/e2e 2>&1 | tail -10
.venv/bin/ruff check scripts/config.py scripts/build/learner_immersion.py scripts/audit/checks/recycle_cadence.py scripts/migrations/ tests/test_learner_immersion.py tests/test_compute_immersion_band.py tests/test_recycle_cadence_gate.py tests/test_plan_targets_schema.py
```

### Step 5 — Proof-of-shape migration sample

Pick the first 3 A1 plans (`sounds-letters-and-hello`, `reading-ukrainian`, `special-signs`) and run the migration script (NOT dry-run) on those 3 only. Commit the resulting plan YAML changes. Do NOT migrate the rest — that's a separate operational call.

### Step 6 — Conventional commit

```bash
git add scripts/config.py scripts/build/learner_immersion.py scripts/audit/checks/recycle_cadence.py scripts/migrations/2026-05-13-add-plan-targets.py docs/lesson-contract.md tests/test_learner_immersion.py tests/test_compute_immersion_band.py tests/test_recycle_cadence_gate.py tests/test_plan_targets_schema.py
# plus the audit-registry file you updated
# plus the 3 sample-migrated plan YAMLs
git status --short
git commit -m "$(cat <<'CMSG'
feat(immersion+plan-targets): ULP-derived band derivation + recycle-cadence gate + plan.targets schema

PR2 of the 2-PR split per docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md.

- scripts/config.py: compute_immersion_band(track, module_num, learner_state)
  + USE_ULP_IMMERSION_DERIVATION feature flag (default False; Phase 4 calibrates
  + flips). Backward-compatible accessors.
- scripts/build/learner_immersion.py: lemma-frequency map with disk cache.
- scripts/audit/checks/recycle_cadence.py: new audit gate (WARN at A1; calibration
  in Phase 4 follow-up).
- scripts/migrations/2026-05-13-add-plan-targets.py: plan.targets schema
  migration (dry-run + atomic write). Proof-of-shape: 3 A1 plans migrated.
- docs/lesson-contract.md: plan.targets section added.

Scope strictly per Decision Card § "PR2 — ULP-derived cumulative-vocab-aware
immersion model". Does NOT touch decolonization rules, writer choice, or
the tab-aware structural Gates 1-3.

Co-Authored-By: Codex <noreply@openai.com>
CMSG
)"
```

### Step 7 — Push + PR

```bash
git push -u origin codex/pr2-ulp-immersion-2026-05-13
gh pr create --title "feat(immersion+plan-targets): ULP-derived band derivation + recycle-cadence gate + plan.targets schema" \
  --body-file - <<'EOF'
## Summary

PR2 of the 2-PR split ratified in `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md`.

- `compute_immersion_band(track, module_num, learner_state)` — flag-gated, backward-compatible.
- `scripts/build/learner_immersion.py` — lemma-frequency map.
- `scripts/audit/checks/recycle_cadence.py` — new audit gate (WARN at A1; Phase 4 calibrates + flips to HARD).
- `plan.targets` schema + migration (subsumes #1916 Gate 4 schema work; proof-of-shape on 3 A1 plans).

## Feature flag

`USE_ULP_IMMERSION_DERIVATION=False` by default. Flipping to True activates derivation. Phase 4 calibration replay sets the `_ULP_VOCAB_KNEE_PER_BAND` constants empirically against the ULP S1-S6 corpus before flipping.

## Out of scope

- `_advisory_immersion_pct`, `_l2_exposure_floor_gate`, etc. — Phase 4 follow-up will wire those to receive `learner_state` too.
- Bulk migration of the remaining 52 A1 plans — operational call, not a code-PR.
- Phase 4 calibration — separate dispatch.

## Test plan

(verbatim raw output blocks per #M-4 deterministic-evidence — replace this stub with actual command + raw output triples for each item in the "Verifiable claims" table at the top of the dispatch brief)

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
```

### Step 8 — NO AUTO-MERGE

Per `AGENT_NO_MERGE=1`.

## Pre-submit checklist (per AGENTS.md:11-26)

- [ ] `.python-version` unchanged
- [ ] `.yamllint` / `.markdownlint.json` unchanged
- [ ] No `status/*.json` or audit-review files in diff
- [ ] No `sys.executable`
- [ ] No `@pytest.mark.skip` with empty `pass`
- [ ] No assertions weakened
- [ ] All changed files directly related
- [ ] Total files < 20 (~14 expected: 4 new code files + 1 migration + docs + 4 test files + audit registry + 3 sample-migrated plans = 13)
- [ ] Code runs without `NameError` / `KeyError` / `ImportError`

## Scope boundaries (HARD)

May touch ONLY:

- `scripts/config.py` (replace bands + add function + flag — backward compat preserved)
- `scripts/build/learner_immersion.py` (new)
- `scripts/build/linear_pipeline.py` — STRICTLY: `writer_context` learner-state passthrough into immersion accessors. NOTHING else.
- `scripts/audit/checks/recycle_cadence.py` (new)
- The audit-registry module (whichever registers checks — locate via PR1)
- `scripts/migrations/2026-05-13-add-plan-targets.py` (new)
- `docs/lesson-contract.md` (add "Plan Targets" section)
- `tests/test_learner_immersion.py` (new)
- `tests/test_compute_immersion_band.py` (new)
- `tests/test_recycle_cadence_gate.py` (new)
- `tests/test_plan_targets_schema.py` (new)
- 3 sample-migrated plan YAMLs: `curriculum/l2-uk-en/plans/a1/{sounds-letters-and-hello,reading-ukrainian,special-signs}.yaml`

May NOT touch:

- Plan-schema Pydantic/dataclass module — if the plan parser needs an update to accept `targets`, add a narrow optional field; do NOT redesign the parser.
- `scripts/pipeline/learner_state.py` (PR1 owns this)
- `scripts/build/phases/linear-write.md` (PR1 owns the placeholder)
- Other plan YAMLs (52 not in the proof-of-shape set)
- `_advisory_immersion_pct` and structural Gates 1-3 in `linear_pipeline.py`
- Writer choice, reviewer phase, decolonization rules, decision cards, session-state

If a task in the brief seems to require touching something outside this list, emit `GOAL_ABORT reason="scope-boundary"` rather than improvising.

---

*Authority: `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` § "PR2".*
*Per `#M-4` (deterministic-over-hallucination), `#DISPATCH-BRIEF-CHECKLIST`, and the user-overridden Plan A overnight orchestration.*
