# Dispatch brief — PR-A + PR-A2: demote 4 LLM dims to warning + --resume default

**Agent:** codex (judgment + cross-file refactor) or claude headless if codex unavailable
**Task ID:** `pr-a-llm-demote-resume-default-2026-05-23`
**Worktree:** `.worktrees/dispatch/codex/pr-a-llm-demote-resume-default-2026-05-23/` (auto-derived via `--worktree` flag)
**Mode:** `danger` (writes commits)
**Effort:** `xhigh`
**Authority:** session-state handoff `docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md` decisions #2, #3, #8.

---

## #M-4 preamble — anti-fabrication requirements

Every verifiable claim in your turn body MUST be tool-backed with the command + cwd + raw output triple. Specifically:

| Claim | Required evidence |
|---|---|
| "Tests pass" | `cd <cwd> && .venv/bin/python -m pytest tests/test_<name>.py -v` + raw final summary line (`N passed in M.MMs`) |
| "Lint clean" | `cd <cwd> && .venv/bin/ruff check scripts/build/v7_build.py scripts/build/linear_pipeline.py scripts/common/thresholds.py tests/test_llm_qg_demote.py tests/test_resume_default.py` + final line |
| "Commit landed" | `cd <cwd> && git log -1 --oneline` raw |
| "PR opened" | `gh pr view --json url --jq .url` raw URL |

Do NOT paraphrase tool output. Do NOT claim something was done without showing the tool result. Quote raw lines, not summaries.

---

## Context — why this PR exists

V7 has terminated builds on subjective LLM-dim verdicts (pedagogical / naturalness / engagement / tone) for 4 weeks. Stochastic non-convergence on subjective dims has produced zero shipped A1 modules across 6 builds in the 2026-05-22→23 window. User + orchestrator agreed (handoff `2026-05-23-architectural-reset-strip-v7-llm-demote.md`): demote 4 subjective dims to warning; **decolonization stays terminal** (political safety, not subjective); manual human review becomes the final gate.

PR-A2 (bundled): make `--resume` the default in `v7_build.py` so failed phases don't replay the writer phase (5-20 min wasted per failed build). Each of the 6 failed builds 2026-05-22→23 burned this replay cost.

---

## Steps — execute in order

### 1. Worktree setup

```bash
# venv symlinked
.venv/bin/python scripts/delegate.py is auto-creating your worktree.
# Your cwd is .worktrees/dispatch/codex/pr-a-llm-demote-resume-default-2026-05-23/
cd .  # (already there)
git status --short  # confirm clean branch from origin/main
git log -1 --oneline  # should show recent main commit (08a49970d or newer)
```

Verify branch:

```bash
git branch --show-current  # should be a dispatch-named branch off origin/main
```

### 2. PR-A — extend aggregate_review for terminal/warning split

**File:** `scripts/common/thresholds.py`

Add at top of file (after existing constants):

```python
LLM_QG_TERMINAL_DIMS: frozenset[str] = frozenset({"decolonization"})
"""LLM QG dims whose REJECT verdict terminates the build.

Per architectural reset 2026-05-23 (docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
decision #2): subjective dims (pedagogical, naturalness, engagement, tone)
were stochastic and produced zero shipped modules across 6 builds 2026-05-22→23.
They're demoted to warning. Decolonization stays terminal because political
safety isn't subjective — Russian framing leaking in is a hard rule, not a
judgment call.

Adding a dim here means: a REJECT in that dim raises LinearPipelineError and
kills the build. Removing a dim means: a REJECT in that dim emits
llm_qg_warning telemetry but the build continues.

When per-dim LLM/human agreement empirics support re-promotion (~20+ shipped
modules with captured human decisions; see PR-G placeholder), dims can be
re-added to this set with the agreement-rate justification logged.
"""

LLM_QG_WARNING_DIMS: frozenset[str] = frozenset(QG_DIMS) - LLM_QG_TERMINAL_DIMS
"""Derived: LLM QG dims whose REJECT verdict is logged but does not terminate."""
```

Then extend `ReviewVerdict` dataclass to add `terminal_verdict`:

```python
@dataclass(frozen=True, slots=True)
class ReviewVerdict:
    """Aggregate LLM QG verdict and the dimensions that drove it."""

    verdict: Literal["PASS", "REVISE", "REJECT"]
    """Full aggregate verdict across ALL dims. Used for telemetry + human review."""

    terminal_verdict: Literal["PASS", "REVISE", "REJECT"]
    """Verdict computed from LLM_QG_TERMINAL_DIMS only. This is what gates the build."""

    failing_dims: tuple[str, ...]
    rejected_dims: tuple[str, ...]
    warning_dims: tuple[str, ...]
    """Subset of failing_dims that are in LLM_QG_WARNING_DIMS (logged, not terminal)."""
    min_score: float
    min_dim: str
```

Extend `aggregate_review` to compute both verdicts:

```python
def aggregate_review(
    scores: Mapping[str, float],
    level_code: str | None,
) -> ReviewVerdict:
    """MIN aggregator for Phase 4 LLM QG, terminal/warning split."""
    floors = get_level_thresholds(level_code).review_floors
    scored_qg = {dim: score for dim, score in scores.items() if dim in floors}
    if not scored_qg:
        raise ValueError(f"No QG dims found in scores: {sorted(scores)}")

    failing = tuple(
        dim for dim, score in scored_qg.items()
        if score < floors[dim].pass_floor
    )
    rejected = tuple(
        dim for dim, score in scored_qg.items()
        if score < floors[dim].reject_floor
    )
    warnings = tuple(d for d in failing if d in LLM_QG_WARNING_DIMS)
    min_dim = min(scored_qg, key=scored_qg.__getitem__)
    min_score = scored_qg[min_dim]

    # Full verdict — for telemetry + human review
    if rejected:
        verdict: Literal["PASS", "REVISE", "REJECT"] = "REJECT"
    elif failing:
        verdict = "REVISE"
    else:
        verdict = "PASS"

    # Terminal verdict — for build gating. Only terminal dims count.
    terminal_rejected = tuple(d for d in rejected if d in LLM_QG_TERMINAL_DIMS)
    terminal_failing = tuple(d for d in failing if d in LLM_QG_TERMINAL_DIMS)
    if terminal_rejected:
        terminal_verdict: Literal["PASS", "REVISE", "REJECT"] = "REJECT"
    elif terminal_failing:
        terminal_verdict = "REVISE"
    else:
        terminal_verdict = "PASS"

    return ReviewVerdict(
        verdict=verdict,
        terminal_verdict=terminal_verdict,
        failing_dims=failing,
        rejected_dims=rejected,
        warning_dims=warnings,
        min_score=min_score,
        min_dim=min_dim,
    )
```

### 3. PR-A — plumb terminal_verdict through linear_pipeline.aggregate_llm_review

**File:** `scripts/build/linear_pipeline.py`

Around line 4200, `aggregate_llm_review` already returns `{"dimensions": ..., "aggregate": asdict(verdict)}`. The `asdict(verdict)` call automatically picks up the new `terminal_verdict` + `warning_dims` fields from the extended dataclass. No code change required here — verify the JSON output shape includes both.

### 4. PR-A — gate v7_build on terminal_verdict, emit warning telemetry

**File:** `scripts/build/v7_build.py`

Locate line 1362 (current):

```python
if aggregate["verdict"] != "PASS":
    raise linear_pipeline.LinearPipelineError(
        f"LLM QG verdict was {aggregate['verdict']}"
    )
```

Replace with:

```python
# Emit warning telemetry when warning-only dims drove the non-PASS aggregate.
# Build continues regardless of warning-dim verdict; reviewer output stays
# in llm_qg.json for human review. Per architectural reset 2026-05-23
# (docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md).
warning_dims = aggregate.get("warning_dims") or ()
if aggregate["verdict"] != "PASS" and warning_dims:
    tracker.emit(
        "llm_qg_warning",
        level=level,
        slug=slug,
        aggregate_verdict=aggregate["verdict"],
        terminal_verdict=aggregate["terminal_verdict"],
        warning_dims=list(warning_dims),
        rejected_dims=list(aggregate.get("rejected_dims") or ()),
        min_dim=aggregate.get("min_dim"),
        min_score=aggregate.get("min_score"),
    )

# Only terminal-dim verdicts kill the build.
if aggregate["terminal_verdict"] != "PASS":
    raise linear_pipeline.LinearPipelineError(
        f"LLM QG terminal verdict was {aggregate['terminal_verdict']} "
        f"(rejected terminal dims: "
        f"{[d for d in aggregate.get('rejected_dims', ()) if d == 'decolonization']})"
    )
```

### 5. PR-A2 — --resume becomes default in v7_build.py CLI

**File:** `scripts/build/v7_build.py`

Find the argparse setup (search for the `--resume` flag). Replace `--resume` action with `--no-resume`:

```python
# Resume is now the default. Pass --no-resume for forced full restart.
# Per architectural reset 2026-05-23 (docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
# decision #8): each of 6 failed builds 2026-05-22→23 burned 5-20min replaying
# the writer phase when only a later phase had failed.
parser.add_argument(
    "--no-resume",
    action="store_true",
    help="Force a full rebuild from scratch. Default behavior resumes from "
    "the last failed phase using artifact existence checks.",
)
# Resume is on whenever --no-resume is absent.
```

Wherever the existing code reads `args.resume`, replace with `not args.no_resume`. Search the file with `git grep -n 'args\.resume\|--resume' scripts/build/v7_build.py` to find every reference.

### 6. Tests

**File:** `tests/test_llm_qg_demote.py` (new)

```python
"""Tests for LLM QG terminal/warning dim split (PR-A, 2026-05-23)."""

import pytest

from scripts.common.thresholds import (
    LLM_QG_TERMINAL_DIMS,
    LLM_QG_WARNING_DIMS,
    QG_DIMS,
    aggregate_review,
)


def test_terminal_and_warning_dims_partition_qg_dims():
    """LLM_QG_TERMINAL_DIMS ∪ LLM_QG_WARNING_DIMS == QG_DIMS, disjoint."""
    assert LLM_QG_TERMINAL_DIMS | LLM_QG_WARNING_DIMS == frozenset(QG_DIMS)
    assert LLM_QG_TERMINAL_DIMS & LLM_QG_WARNING_DIMS == frozenset()


def test_decolonization_is_only_terminal_dim_in_2026_05_23_baseline():
    """Per architectural reset 2026-05-23 decision #3."""
    assert LLM_QG_TERMINAL_DIMS == frozenset({"decolonization"})


def test_warning_dim_reject_does_not_drive_terminal_verdict():
    """A REJECT in a warning dim leaves terminal_verdict == PASS."""
    scores = {
        "pedagogical": 4.0,  # REJECT (below 6.0 reject floor)
        "naturalness": 9.0,
        "decolonization": 9.5,  # PASS
        "engagement": 8.5,
        "tone": 8.5,
    }
    v = aggregate_review(scores, "A1")
    assert v.verdict == "REJECT"  # full aggregate is REJECT
    assert v.terminal_verdict == "PASS"  # terminal-only is PASS
    assert "pedagogical" in v.rejected_dims
    assert "pedagogical" in v.warning_dims


def test_decolonization_reject_drives_terminal_verdict():
    """A REJECT in decolonization terminates the build."""
    scores = {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 4.0,  # REJECT
        "engagement": 8.5,
        "tone": 8.5,
    }
    v = aggregate_review(scores, "A1")
    assert v.verdict == "REJECT"
    assert v.terminal_verdict == "REJECT"
    assert "decolonization" in v.rejected_dims


def test_all_pass_yields_pass_on_both():
    scores = {
        "pedagogical": 9.0,
        "naturalness": 9.0,
        "decolonization": 9.0,
        "engagement": 8.5,
        "tone": 8.5,
    }
    v = aggregate_review(scores, "A1")
    assert v.verdict == "PASS"
    assert v.terminal_verdict == "PASS"
    assert v.warning_dims == ()


def test_warning_revise_does_not_drive_terminal_revise():
    """A score below pass_floor but above reject_floor on a warning dim
    yields verdict=REVISE but terminal_verdict=PASS."""
    scores = {
        "pedagogical": 7.0,  # below A1 pass_floor 9.0, above reject 6.0 → REVISE
        "naturalness": 9.0,
        "decolonization": 9.0,
        "engagement": 8.5,
        "tone": 8.5,
    }
    v = aggregate_review(scores, "A1")
    assert v.verdict == "REVISE"
    assert v.terminal_verdict == "PASS"
```

**File:** `tests/test_resume_default.py` (new — focused on CLI flag behavior, not phase-resume mechanics which are existing)

```python
"""Tests for --no-resume default behavior (PR-A2, 2026-05-23)."""

import subprocess


def test_v7_build_help_lists_no_resume_not_resume():
    """--resume flag was removed; --no-resume is the new opt-out."""
    out = subprocess.run(
        # venv symlinked
        [".venv/bin/python", "scripts/build/v7_build.py", "--help"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert "--no-resume" in out, f"--no-resume missing from --help:\n{out}"
    # --resume should NOT be in --help (it's removed in favor of --no-resume default-on)
    # If your implementation kept --resume for back-compat, this assertion needs review:
    # confirm with maintainer whether back-compat is required.
```

### 7. Run tests

```bash
cd .  # in worktree
# venv symlinked
.venv/bin/python -m pytest tests/test_llm_qg_demote.py tests/test_resume_default.py -v
```

Capture the raw `N passed in M.MMs` line in your turn body.

### 8. Run lint

```bash
.venv/bin/ruff check scripts/build/v7_build.py scripts/build/linear_pipeline.py scripts/common/thresholds.py tests/test_llm_qg_demote.py tests/test_resume_default.py
```

If any errors, fix them. Capture the raw final line.

### 9. Run full test suite for regression check

```bash
# venv symlinked
.venv/bin/python -m pytest tests/ --timeout=120 -q 2>&1 | tail -30
```

If anything else broke from your changes, fix it. Existing tests on `aggregate_review` may need updating to handle the new `terminal_verdict` / `warning_dims` fields — these are non-breaking ADDITIONS to the dataclass, so existing assertions on `verdict` / `failing_dims` / `rejected_dims` should still pass. If a test asserts the exact dataclass shape (e.g. `asdict(v) == {expected}`), update the expected dict to include the new fields.

### 10. Commit

```bash
git add scripts/common/thresholds.py scripts/build/v7_build.py scripts/build/linear_pipeline.py tests/test_llm_qg_demote.py tests/test_resume_default.py
git commit -m "$(cat <<'EOF'
feat(pipeline): demote 4 LLM dims to warning + --resume default (PR-A+A2)

PR-A: pedagogical/naturalness/engagement/tone REJECT no longer terminates
the build. Only decolonization REJECT raises. Per-dim reviewer critiques
still persist to llm_qg.json for human review. Warning-dim non-PASS
verdicts emit llm_qg_warning telemetry events for observability.

PR-A2: --resume becomes default. New --no-resume flag for forced full
restart. Saves 5-20 min writer-phase replay per failed build (six failed
builds 2026-05-22→23 each burned this cost).

Architectural reset rationale: docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
(decisions #2, #3, #8). Subjective LLM-dim gating produced zero shipped
modules across 4 weeks; human review becomes the final gate while corpus
grounding (wiki obligations, implementation_map, VESUM, MCP-tool
verification) stays load-bearing.

Co-Authored-By: Codex CLI <noreply@anthropic.com>
EOF
)"
```

### 11. Push

```bash
git push -u origin HEAD
```

Capture the push output. Verify the branch tracks remote.

### 12. Open PR

```bash
gh pr create --title "feat(pipeline): demote 4 LLM dims to warning + --resume default (PR-A+A2)" --body "$(cat <<'EOF'
## Summary

Implements PR-A + PR-A2 from the 2026-05-23 architectural reset (handoff: `docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md`).

### PR-A — LLM dim terminal/warning split

- `LLM_QG_TERMINAL_DIMS = frozenset({"decolonization"})` in `scripts/common/thresholds.py`
- `LLM_QG_WARNING_DIMS = frozenset(QG_DIMS) - LLM_QG_TERMINAL_DIMS` (4 dims: pedagogical, naturalness, engagement, tone)
- `ReviewVerdict` gains `terminal_verdict` and `warning_dims` fields
- `aggregate_review` computes both verdicts; full aggregate stays for telemetry/human review, terminal verdict gates the build
- `v7_build.py` raises on `terminal_verdict != PASS` only; emits `llm_qg_warning` telemetry when warning dims drove a non-PASS full aggregate
- Decolonization stays terminal — political safety, not subjective

### PR-A2 — --resume default

- `--resume` removed; `--no-resume` added as opt-out
- Resume from last failed phase via existing `_phase_artifact_passes` checks
- Saves 5-20 min writer-phase replay per failed build

## Why

4 weeks of LLM-dim-terminal gating on subjective dims produced 0 shipped A1 modules across 6 builds 2026-05-22→23. Per-build replay of the writer phase compounded the cost. Manual human review replaces LLM gating on subjective dims; corpus-grounding gates (wiki obligations, implementation_map, VESUM, MCP) stay load-bearing.

## Test plan

- [x] `tests/test_llm_qg_demote.py` — 6 unit tests covering terminal/warning partition, decolonization-only-terminal, warning-REJECT-doesn't-terminate, decolonization-REJECT-does-terminate, all-pass, warning-REVISE-doesn't-terminate
- [x] `tests/test_resume_default.py` — CLI surface test for `--no-resume` presence
- [x] Full `pytest tests/` regression — no breakage
- [x] `ruff check` clean

## Out of scope

- PR-B (band widening) — separate PR
- PR-C (writer prompt strip) — separate PR, requires user review of strip plan
- Per-rule firing telemetry — comes with PR-C

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 13. Do NOT auto-merge

Report PR URL. Orchestrator reviews + merges. The `--allow-merge` flag is NOT set on this dispatch (default is `AGENT_NO_MERGE=1`).

---

## Acceptance criteria

- All steps 2-12 completed
- Tests green (capture raw `N passed in M.MMs` line)
- Ruff clean (capture raw final line)
- PR URL surfaced

## Failure recovery

- If `aggregate_review` change breaks existing tests with assertions on the dataclass shape: update the expected dicts to include `terminal_verdict` + `warning_dims`. These are additive fields, not breaking changes.
- If `--no-resume` rename breaks any test that invokes `v7_build.py --resume`: update those tests to either omit the flag (resume is default) or use `--no-resume` (opt-out).
- If you discover the `--resume` flag has callers outside `v7_build.py` (e.g. CI configs, shell scripts): grep `git grep -n 'v7_build.*--resume'` and update those too. If a caller cannot be updated (e.g. external CI), keep `--resume` as a no-op alias for back-compat — note this in the PR body.
