# Dispatch brief — Issue #2210 V7 learner-state vocabulary source drift

**Agent**: codex
**Mode**: danger
**Effort**: high
**Branch base**: `origin/main`
**Task ID**: `issue-2210-learner-state-vocab-drift-2026-05-25`

## Why this is on codex (not agy/cursor)
This touches V7 pipeline correctness and is a load-bearing blocker for the upcoming A1 builds (m01-m19 + m21-m55 under claude-tools writer). Codex has the deepest familiarity with `scripts/pipeline/learner_state.py` + `scripts/config.py` + `scripts/build/linear_pipeline.py` integration paths.

## Read first
- `gh issue view 2210` — full problem statement
- `scripts/pipeline/learner_state.py` — current vocabulary derivation (reads `curriculum/l2-uk-en/{track}/{slug}/vocabulary.yaml`)
- `docs/decisions/2026-05-13-ulp-derived-student-aware-immersion.md` — the ACCEPTED decision spec
- `docs/best-practices/v7-design-and-corpus.md` §1.3 — the SSOT entry point
- `docs/best-practices/ulp-presentation-pattern.md` — NEW 2026-05-25, has the Ohoiko presentation moves + S1→S6 progression. **Critical context for why learner-state correctness matters.**
- `scripts/config.py:718` (`compute_immersion_band` function)
- `scripts/build/linear_pipeline.py:52,2629-2656` (LEARNER_STATE wiring)

## The drift problem
Per the issue body, `learner_state.py` currently derives cumulative learner vocabulary from the BUILT artifact `curriculum/l2-uk-en/{track}/{slug}/vocabulary.yaml`, but V7 intends cumulative vocab to come from:
- plan `targets.new_vocabulary` declared in `curriculum/l2-uk-en/plans/{track}/{slug}.yaml`
- canonical V7 generated artifacts (when present)
- manifest-aware build outputs

When a module hasn't been built yet (which is most of A1 in our current state), the built `vocabulary.yaml` is missing or stale, and the learner-state falls back silently. The student-aware immersion model then operates on wrong cumulative vocab → wrong immersion band → wrong writer prompt for the next module.

## Verifiable claims preamble (#M-4)
- "drift is closed" → quote a unit test that constructs a synthetic plan with `targets.new_vocabulary: [<list>]` AND verifies `_load_vocab()` returns that list when the built `vocabulary.yaml` doesn't exist
- "compute_immersion_band uses the new source" → quote a test passing a learner-state with planned-but-not-built modules and asserting the derived band reflects planned vocab
- "no regression on built modules" → quote tests passing for the existing "module is built" path
- ruff + pytest green

## Steps

1. `git worktree add -B fix/issue-2210-learner-state-vocab-source .worktrees/dispatch/codex/issue-2210 origin/main && cd .worktrees/dispatch/codex/issue-2210`
2. Update `scripts/pipeline/learner_state.py::_load_vocab()` precedence:
   1. Try `curriculum/l2-uk-en/{track}/{slug}/vocabulary.yaml` (the built artifact — present after build, treat as authoritative when present)
   2. **NEW**: fall back to `curriculum/l2-uk-en/plans/{track}/{slug}.yaml` reading `targets.new_vocabulary` + `vocabulary_hints.required` + `vocabulary_hints.recommended` (the planned vocab, for not-yet-built modules)
   3. Empty list as final fallback
   Note: this is similar to PR #2211 (which fixed the path layout) but EXTENDS it with the plan-based fallback.
3. Verify `compute_immersion_band` at `scripts/config.py:718` uses the new source correctly by inspecting + running tests against synthetic learner-states.
4. Add tests in `tests/test_learner_state_v7_layout.py` (or a new `tests/test_learner_state_vocab_source_drift.py`):
   - Test A: module IS built → reads from `vocabulary.yaml`, returns those lemmas
   - Test B: module NOT built but plan has `targets.new_vocabulary: [...]` → returns plan's list
   - Test C: module NOT built, plan has `vocabulary_hints.required: [...]` but no `targets.new_vocabulary` → returns hints' required
   - Test D: module NOT built, plan has neither → returns empty list (graceful)
5. `.venv/bin/python -m pytest tests/test_learner_state* -q`
6. **Smoke test**: build `compute_immersion_band` for a1 module=20 (my-morning) with a synthetic plan-only state covering m01-m19, verify the returned band has non-trivial vocab + reasonable advisory_pct_min/max.
7. `.venv/bin/ruff check scripts tests`
8. Commit: `fix(learner_state): plan-based fallback for not-yet-built module vocab (closes #2210)`
9. Push, open PR. Body MUST cite the related PR #2211 history + show the test outputs.

## Stop conditions
- The plan schema doesn't have `targets.new_vocabulary` for any A1 plan yet (per Decision Card §"Open Q5" — A1 backfill is targeted lazy). If so, the fallback to `vocabulary_hints.required` becomes the primary signal — verify the data is there in current A1 plans before relying on it.
- `compute_immersion_band` calibration constants need re-tuning to handle the planned-vocab signal (e.g. planned vocab count differs from real-built vocab count in shape) → that's calibration follow-up, file as a separate issue and ship the wiring fix in this PR.
- Any existing test breaks → understand why before forcing through.

## Done criteria
PR URL + `gh pr checks <N>` + raw pytest summary + the smoke-test output showing learner_state for synthetic m01-m19 returns expected cumulative vocab count.

## Cross-link
This dispatch unblocks the upcoming a1 m01 build under claude-tools writer (next planned action after PR #2266 split + a1/m20 codex anchor land).
