# Dispatch brief — PR-B: word_count tolerance + engagement_floor callout_min

**Agent:** gemini
**Task ID:** `pr-b-band-widening-2026-05-23`
**Worktree:** auto-derived via `--worktree`
**Mode:** `danger`
**Base SHA:** `2a0c0e7e17` (post-PR-A merge)
**Authority:** session-state handoff `docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md` decision row "B".

## #M-4 preamble

Every verifiable claim MUST be tool-backed with command + cwd + raw output. Required evidence:

| Claim | Evidence |
|---|---|
| Tests pass | `.venv/bin/python -m pytest tests/test_pr_b_band_widening.py tests/test_pipeline_helpers.py -v` + raw final line |
| Lint clean | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_pr_b_band_widening.py` + raw final line |
| Commit landed | `git log -1 --oneline` raw |
| PR opened | `gh pr view --json url --jq .url` raw URL |

No paraphrasing tool output. No "I checked X" without command+cwd+output.

---

## Context

V7 builds 2026-05-22→23 produced module word counts clustering around the target:
- gemini-tools 1031 (14% short of 1200 — rejected correctly)
- deepseek-pro 1197 (0.25% short of 1200 — rejected on a rounding-error basis)
- deepseek-pro 1212 (above target — passes)

Current `_word_count_gate` is a one-sided floor: `count >= target`. The handoff cites this as too rigid — a 1197 vs 1200 fail is silly. Adding an 8% lower-bound tolerance catches 1031 (still rejects) while passing 1197.

Same handoff: `engagement_floor` requires `callout_min = 2`, but writers consistently emit 1 callout. The "minimum 2" was aspirational not empirical. Drop to 1.

User direction (2026-05-23 reaffirmation of 2026-05-17): "word targets are MINIMUMS." The tolerance preserves the spirit (still rejects gemini's 1031 = 14% short) while allowing 8% slack for near-target builds.

---

## Steps — execute in order

### 1. Worktree setup

`scripts/delegate.py dispatch` auto-creates your worktree at `.worktrees/dispatch/gemini/pr-b-band-widening-2026-05-23/`. Your cwd is already there.

Verify clean branch from origin/main:

```bash
git status --short  # expect empty
git log -1 --oneline  # expect 2a0c0e7e17 (PR-A merged) or newer
```

### 2. Change `_word_count_gate` to add 8% lower-bound tolerance

**File:** `scripts/build/linear_pipeline.py` around line 6458.

Current implementation:

```python
def _word_count_gate(text: str, target: int) -> dict[str, Any]:
    count = _word_count(_strip_comments(text))
    return {
        "passed": count >= target,
        "count": count,
        "target": target,
    }
```

Replace with:

```python
# Word-target tolerance: 8% lower band. User direction 2026-05-23
# (handoff docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
# decision row B): word targets stay as MINIMUMS for the writer prompt
# guidance, but the gate tolerates ±8% below target to avoid 0.25%-short
# rejections like deepseek-pro 1197/1200. Empirically the 8% band still
# rejects gemini-tools 1031/1200 (14% short).
_WORD_COUNT_TOLERANCE_BELOW = 0.08


def _word_count_gate(text: str, target: int) -> dict[str, Any]:
    count = _word_count(_strip_comments(text))
    min_with_tolerance = int(target * (1 - _WORD_COUNT_TOLERANCE_BELOW))
    return {
        "passed": count >= min_with_tolerance,
        "count": count,
        "target": target,
        "min_with_tolerance": min_with_tolerance,
        "tolerance_below_pct": _WORD_COUNT_TOLERANCE_BELOW * 100,
    }
```

### 3. Change `callout_min` from 2 to 1 in `_engagement_floor_gate`

**File:** `scripts/build/linear_pipeline.py` around line 8813.

Current:

```python
callout_min = 2
```

Replace with:

```python
# callout_min: 2 → 1 per user direction 2026-05-23 (handoff decision row B).
# Writers consistently emit 1 callout; "minimum 2" was aspirational not
# empirical. The full engagement_floor still catches modules with 0 callouts.
callout_min = 1
```

Also update the warning message a few lines below (if it hardcodes the "minimum 2" phrasing):

```bash
grep -n 'minimum 2\|callout_min' scripts/build/linear_pipeline.py
```

If the warning message says `minimum {callout_min}` (uses the variable), no further change needed. If it hardcodes "2", update to use `{callout_min}`.

### 4. Tests

**File:** `tests/test_pr_b_band_widening.py` (new)

```python
"""Tests for PR-B band widening: word_count tolerance + callout_min (2026-05-23)."""

from scripts.build.linear_pipeline import (
    _engagement_floor_gate,
    _word_count_gate,
)


# ----- word_count tolerance --------------------------------------------------


def test_word_count_at_target_passes() -> None:
    """Baseline: count exactly at target passes."""
    text = "word " * 1200
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True
    assert report["count"] == 1200


def test_word_count_above_target_passes() -> None:
    text = "word " * 1300
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True


def test_word_count_within_8pct_tolerance_passes() -> None:
    """Regression: deepseek-pro 1197 vs A1 target 1200 (0.25% short) now passes."""
    text = "word " * 1197
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True
    assert report["count"] == 1197
    assert report["min_with_tolerance"] == 1104  # int(1200 * 0.92)


def test_word_count_at_band_edge_passes() -> None:
    """count == min_with_tolerance (target * 0.92) passes."""
    text = "word " * 1104  # int(1200 * 0.92)
    report = _word_count_gate(text, 1200)
    assert report["passed"] is True
    assert report["min_with_tolerance"] == 1104


def test_word_count_just_below_band_fails() -> None:
    """count == min_with_tolerance - 1 fails."""
    text = "word " * 1103
    report = _word_count_gate(text, 1200)
    assert report["passed"] is False
    assert report["count"] == 1103


def test_word_count_14pct_below_target_fails() -> None:
    """Regression: gemini-tools 1031 vs A1 target 1200 (14% short) still fails."""
    text = "word " * 1031
    report = _word_count_gate(text, 1200)
    assert report["passed"] is False
    assert report["count"] == 1031


def test_word_count_reports_tolerance_metadata() -> None:
    """The gate report includes min_with_tolerance + tolerance_below_pct."""
    report = _word_count_gate("word " * 1200, 1200)
    assert report["min_with_tolerance"] == 1104
    assert report["tolerance_below_pct"] == 8.0
    assert report["target"] == 1200


# ----- callout_min ------------------------------------------------------------


def test_engagement_floor_passes_with_one_callout() -> None:
    """Regression: single callout now satisfies the floor (was minimum 2)."""
    text = """
# Module

Some intro prose.

:::tip
A pedagogical mnemonic the learner can carry.
:::

More prose with a bullet list:

- Перший приклад (first example)
- Другий приклад (second example)
- Третій приклад (third example)
- Четвертий приклад (fourth example)
- П'ятий приклад (fifth example)
- Шостий приклад (sixth example)
"""
    plan = {"word_target": 100, "level": "a1"}
    report = _engagement_floor_gate(text, plan)
    # callout_min is the load-bearing check for this PR. The engagement_floor
    # also requires other signals; we assert specifically on callout_min.
    assert report["callout_min"] == 1
    # If the only failing dimension was callout count, passing now succeeds.
    assert report["callouts"] >= 1


def test_engagement_floor_callout_min_is_1() -> None:
    """The callout floor is exactly 1, not 2 (regression on PR-B)."""
    text = ":::tip\nA mnemonic.\n:::\n"
    plan = {"word_target": 100, "level": "a1"}
    report = _engagement_floor_gate(text, plan)
    assert report["callout_min"] == 1
```

### 5. Run focused tests

```bash
# venv symlinked
.venv/bin/python -m pytest tests/test_pr_b_band_widening.py -v
```

Expect 9 passes. If the engagement_floor test fails on missing dependencies (it's a partial fixture), revisit the test — the load-bearing assertions are `callout_min == 1`.

### 6. Run regression tests

```bash
# venv symlinked
.venv/bin/python -m pytest tests/test_pipeline_helpers.py tests/test_pipeline_v5.py tests/test_pipeline_parsing.py -v --timeout=120 2>&1 | tail -30
```

Existing tests that assert the word_count gate's report shape may need updates if they did `assert report == {"passed": True, "count": 1200, "target": 1200}` exactly. Update to include the new keys, or use `>=` style assertions.

### 7. Lint

```bash
.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_pr_b_band_widening.py
```

### 8. Commit

```bash
git add scripts/build/linear_pipeline.py tests/test_pr_b_band_widening.py
git commit -m "$(cat <<'EOF'
feat(audit): widen word_count to 8% lower-band tolerance + drop callout_min to 1 (PR-B)

word_count gate: was `count >= target` (one-sided floor with no tolerance);
now `count >= int(target * 0.92)`. Empirically deepseek-pro 1197/1200 was
rejected on a 0.25% basis; new band passes it while still rejecting
gemini-tools 1031/1200 (14% short).

engagement_floor.callout_min: 2 → 1. Writers consistently emit 1 callout;
the minimum-2 expectation was aspirational not empirical. Modules with 0
callouts still fail; the floor catches the load-bearing case (engagement
totally absent) without rejecting modules that picked one strong callout
over two weak ones.

Word targets stay as MINIMUMS in the writer prompt and per-section budget
guidance (user direction 2026-05-23 reaffirming 2026-05-17). The 8%
tolerance applies only at the deterministic gate level, where a 0.25%
shortfall is a rounding error, not a quality regression.

Per architectural reset 2026-05-23 (docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md
decision row B).

Co-Authored-By: Gemini CLI <noreply@anthropic.com>
EOF
)"
```

### 9. Push + open PR

```bash
git push -u origin HEAD
gh pr create --title "feat(audit): widen word_count to 8% lower-band tolerance + drop callout_min to 1 (PR-B)" --body "$(cat <<'EOF'
## Summary

Implements PR-B from the 2026-05-23 architectural reset (handoff: `docs/session-state/2026-05-23-architectural-reset-strip-v7-llm-demote.md`, decision row B).

### word_count tolerance

`_word_count_gate` was `count >= target` (one-sided floor, no tolerance). Now `count >= int(target * 0.92)`. The gate report adds `min_with_tolerance` and `tolerance_below_pct` for telemetry.

Empirical justification:
- deepseek-pro 1197/1200 (0.25% short) → was rejected; now passes
- gemini-tools 1031/1200 (14% short) → was rejected; still rejected
- Tolerance 8% catches the rounding-error case while preserving the quality floor

### engagement_floor callout_min

`callout_min` 2 → 1. Writers consistently emit 1 callout; minimum-2 was aspirational. Modules with 0 callouts still fail.

## Why

Word targets remain MINIMUMS in the writer prompt + per-section budgets (user direction 2026-05-23 reaffirming 2026-05-17). The tolerance applies only at the deterministic gate level. A 0.25% shortfall is a rounding error, not a quality regression. The previous gate rejected deepseek-pro 1197 on this basis, wasting a build.

## Test plan

- [x] `tests/test_pr_b_band_widening.py` (9 tests) — at-target, above-target, within-tolerance, band-edge, just-below-band, 14%-below, metadata reporting; callout_min == 1
- [x] Pipeline-helpers regression tests pass
- [x] `ruff check` clean

## Breaking change

None. Gate report adds new fields (`min_with_tolerance`, `tolerance_below_pct`); existing fields unchanged.

## Out of scope

- PR-C (writer prompt strip) — requires user review of strip plan at `audit/2026-05-23-writer-prompt-strip-plan/REPORT.html`

🤖 Generated with [Claude Code](https://claude.com/claude-code)
EOF
)"
```

### 10. Do NOT auto-merge

Report PR URL. Orchestrator reviews + merges.

## Acceptance criteria

- Steps 2-9 completed
- 9/9 PR-B tests pass + regression tests pass
- Ruff clean
- PR URL surfaced

## Failure recovery

- If `_word_count_gate` test failures cascade because some existing test asserts the full gate-report dict shape: update those assertions to use subset matching (`report["passed"] is True`) instead of exact-equality. The new keys are additive.
- If `_engagement_floor_gate` warning message hardcodes "minimum 2": update to interpolate `callout_min`.
- Stay strictly in scope. Do not modify other files outside `scripts/build/linear_pipeline.py` + `tests/test_pr_b_band_widening.py`. If something else needs fixing, mention it in the PR body as a follow-up, do NOT touch it.
