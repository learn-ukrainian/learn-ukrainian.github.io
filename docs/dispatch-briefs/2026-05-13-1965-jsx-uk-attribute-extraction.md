# Dispatch — #1965 JSX uk= attribute extraction (V7 DialogueBox shape)

**Issue:** [#1965](https://github.com/krisztiankoos/learn-ukrainian/issues/1965) — `_jsx_text_values` only extracts `text=` attribute; misses `uk=`/`en=` V7 DialogueBox shape.

**Agent:** codex / gpt-5.5 / high
**Base:** `main` @ `157b346434` (post-#1964 contract bundle + handoff)
**Expected scope:** ~20-40 LOC source + ~60-120 LOC tests. Single bundled PR.

---

## #M-4 Deterministic preamble — verifiable claims this work will produce

| Claim | Tool / command | Output format that captures evidence |
|---|---|---|
| "Build #4 module had 10 DialogueBox elements with `uk=`/`en=` props" | `grep -c '<DialogueBox' .worktrees/builds/a1-my-morning-20260513-193448/curriculum/l2-uk-en/a1/my-morning/module.md` | Quote raw count (`10`) + 3 sample lines |
| "Gate counter blind: `uk_dialogue_lines: 5` observed vs 14 required" | `python3 -c 'import json; print(json.load(open("...python_qg.json"))["gates"]["l2_exposure_floor"]["observed"])'` | Quote raw dict |
| "Component density measured at 36-55% per box (~50% = bilingual prop pair)" | same python_qg.json `gates.component_density.observed` | Quote raw list |
| "Tests pass after fix" | `.venv/bin/python -m pytest tests/test_immersion_gates.py tests/build/test_linear_pipeline.py -v` | Quote final `N passed in M.MMs` line raw |
| "Ruff clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_immersion_gates.py tests/build/test_linear_pipeline.py` | Quote final `All checks passed!` or zero-error line |
| "PR opened" | `gh pr view --json url` | Quote raw URL line |
| "Commit landed" | `git log -1 --oneline` | Quote raw line |

No "I checked X" prose. Every claim above MUST come back as a raw command output line.

---

## Root cause (already diagnosed — implement, don't re-diagnose)

`scripts/build/linear_pipeline.py:5631-5647` defines two helpers used by `l2_exposure_floor` and `component_density` gates:

```python
def _jsx_text_values(jsx_block: str) -> list[str]:
    return re.findall(r"\btext\s*(?:=|:)\s*\"([^\"\n]*)\"", jsx_block)


def _component_language_text(tag: str, jsx_block: str) -> str:
    if tag == "DialogueBox":
        text_values = _jsx_text_values(jsx_block)
        if text_values:
            return "\n".join(text_values)
    paired = re.match(...)
    if paired:
        return paired.group(2)
    return "\n".join(_JSX_STRING_VALUE_RE.findall(jsx_block))
```

V7 canonical DialogueBox shape (writer naturally emits this per the #1964 contract):

```jsx
<DialogueBox uk="— Насте, коли ти прокидаєшся?" en="— Nastia, when do you wake up?" />
```

- `_jsx_text_values` returns `[]` — no `text=` attr present → `_count_uk_dialogue_lines` (line 5366) misses every DialogueBox.
- `_component_language_text` falls through past the DialogueBox branch (because `text_values` is empty), hits the self-closing-no-paired-tag fallback at line 5647, returns BOTH the `uk=` and `en=` string contents joined → `component_density` measures `uk_pct ≈ 50%` (one UK + one EN string per box) instead of 100%.

## Fix

Update `_jsx_text_values` to extract the `uk=` attribute in ADDITION to `text=`:

```python
def _jsx_text_values(jsx_block: str) -> list[str]:
    """Extract canonical UK-content attributes from V7 components.

    `text=` is the legacy convention; `uk=` is the V7 DialogueBox convention
    introduced by the a1-m15-24 shape contract (#1964 / PR #1962).
    """
    text_attrs = re.findall(r"\btext\s*(?:=|:)\s*\"([^\"\n]*)\"", jsx_block)
    uk_attrs = re.findall(r"\buk\s*(?:=|:)\s*\"([^\"\n]*)\"", jsx_block)
    return text_attrs + uk_attrs
```

This single change cascades:

1. `_count_uk_dialogue_lines` (line 5366) → counts each `<DialogueBox uk="..."/>` once. **Fixes `l2_exposure_floor.uk_dialogue_lines`.**
2. `_component_language_text` (line 5635) → for `DialogueBox`, now returns the UK content from `uk=` only, skipping the `en=` (because the function returns early at line 5639 when `text_values` is non-empty). **Fixes `component_density` per-box pct calculation.**

No additional changes needed to `_component_language_text` itself — the existing DialogueBox-special-case branch (lines 5636-5639) was correct in intent but couldn't fire because `_jsx_text_values` couldn't see the new prop name. Fix the upstream helper; the gate logic falls into place.

## Tests required

Add the following to `tests/test_immersion_gates.py` (NEW tests; do not modify existing passing tests):

1. `test_l2_exposure_floor_credits_dialoguebox_uk_prop` — module text containing 14 `<DialogueBox uk="..." en="..." />` elements PLUS 0 blockquote dialogue should PASS the `l2_exposure_floor.uk_dialogue_lines` requirement (≥14 for A1).
2. `test_component_density_dialoguebox_uk_prop_pass` — single `<DialogueBox uk="Привіт, як справи?" en="Hi, how are you?" />` should observe `uk_pct=100.0` (UK-only), passing the 95-100 expected range.
3. `test_component_density_dialoguebox_legacy_text_prop_still_passes` — single `<DialogueBox text="Привіт!" />` (legacy form, matches existing line-189 test pattern) still observes 100% UK.

Add the following to `tests/build/test_linear_pipeline.py`:

4. `test_jsx_text_values_extracts_uk_attribute` — direct unit test on `_jsx_text_values('<DialogueBox uk="привіт" en="hi" />')` → `["привіт"]`.
5. `test_jsx_text_values_extracts_legacy_text_attribute` — direct unit test on `_jsx_text_values('<DialogueBox text="привіт" />')` → `["привіт"]`.
6. `test_jsx_text_values_extracts_both_when_present` — mixed shape (one box with `text=`, another in same block with `uk=`) returns both.
7. `test_component_language_text_dialoguebox_uk_prop` — `_component_language_text("DialogueBox", '<DialogueBox uk="привіт" en="hi" />')` → `"привіт"` (NOT `"привіт\nhi"`).

All tests must use realistic Ukrainian content (no Lorem ipsum); the existing tests at `tests/test_immersion_gates.py:55-94` show the canonical fixture shape — match it.

## Build #4 evidence to verify against (read-only, do not modify)

After implementing, run the gates against build #4's actual module.md to confirm the fix flips the observed counts:

```bash
cd .worktrees/builds/a1-my-morning-20260513-193448
.venv/bin/python -c "
import sys
sys.path.insert(0, '/Users/krisztiankoos/projects/learn-ukrainian')
# Re-import from your worktree's modified linear_pipeline:
from scripts.build.linear_pipeline import _count_uk_dialogue_lines, _component_density_gate
body = open('curriculum/l2-uk-en/a1/my-morning/module.md').read()
print('uk_dialogue_lines:', _count_uk_dialogue_lines(body))
# Expected: ≥10 (the 10 DialogueBox elements) + 5 (blockquote source lines) = 15, up from 5
"
```

This is a sanity check, NOT a test commit — do not commit the worktree path or the inline script. Just confirm the integer flipped from 5 → ≥15 and report it raw in the PR body.

## Pre-submit checklist (numbered, NOT footnoted — per `dispatch-brief-checklist`)

1. `git worktree add -b fix/1965-jsx-uk-attribute ../jsx-uk-attribute origin/main` — set up isolated worktree from clean `main`.
2. **File-level work:** edit `scripts/build/linear_pipeline.py:5631-5634` per fix block above. Add 4 + 4 tests per the test-required section.
3. **Test suite:** `.venv/bin/python -m pytest tests/test_immersion_gates.py tests/build/test_linear_pipeline.py -v` — must show all new tests PASS and existing tests still PASS. **Forbid `-x` per #1942** — capture full failure count if any.
4. **Ruff:** `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_immersion_gates.py tests/build/test_linear_pipeline.py` — must show "All checks passed!"
5. **Commit:** conventional message `fix(immersion_gates): extract uk= attribute for V7 DialogueBox shape (#1965)` — body cites the issue and quotes the before/after `uk_dialogue_lines` count from the build #4 sanity check.
6. **Push:** `git push -u origin fix/1965-jsx-uk-attribute`.
7. **PR:** `gh pr create --base main --title "fix(immersion_gates): extract uk= attribute for V7 DialogueBox (#1965)" --body "<see template below>"` — DO NOT auto-merge.
8. **No auto-merge.** Report PR URL + final `gh pr checks` raw output in your dispatch finalize message; orchestrator will merge after blocking checks go green.

## PR body template

```
## Summary

- `_jsx_text_values` now extracts `uk=` attribute (V7 DialogueBox convention) in addition to `text=` (legacy)
- Cascades through `_count_uk_dialogue_lines` and `_component_language_text` to fix `l2_exposure_floor` and `component_density` gate counters
- Closes #1965

## Why

Per the #1964 a1-m15-24 shape contract, the writer correctly emits `<DialogueBox uk="..." en="..." />` for bilingual dialogue. Gate counters were calibrated against an older `text=` shape that the writer no longer uses. Build #4 (`.worktrees/builds/a1-my-morning-20260513-193448/`) showed 10 DialogueBox elements scored 0 toward `uk_dialogue_lines` and ~50% per-box on `component_density` — both miscounts trace to one missing regex alternative in `_jsx_text_values`.

## Build #4 sanity check (before/after)

Before: `uk_dialogue_lines = 5` (only counts blockquote sources)
After: `uk_dialogue_lines = <RAW INTEGER FROM SCRIPT>` (counts 10 DialogueBox elements + 5 blockquote)

## Test plan

- [x] New tests in `tests/test_immersion_gates.py` cover DialogueBox `uk=` prop for both `l2_exposure_floor` and `component_density`
- [x] New unit tests in `tests/build/test_linear_pipeline.py` cover `_jsx_text_values` + `_component_language_text` directly
- [x] Existing `text=` legacy-form tests still pass (back-compat preserved)
- [x] Ruff clean
```

## Forbidden

- ❌ Modifying `_component_language_text` body (intent was correct; fix upstream).
- ❌ Lowering `l2_exposure_floor.min_uk_dialogue_lines` or `component_density.required_components` policy values.
- ❌ `pytest -x` in the final pre-push verification (per #1942 — masks downstream failures).
- ❌ Auto-merge (`gh pr merge ... --auto`). Orchestrator merges after CI.
- ❌ Touching any file outside `scripts/build/linear_pipeline.py`, `tests/test_immersion_gates.py`, `tests/build/test_linear_pipeline.py`.

## Halt conditions

- If tests for the legacy `text=` form fail after your change → STOP, post the failing test output, do not commit. The regex append is additive; the legacy capture must continue to work.
- If `_component_density_gate` against the build #4 module.md does NOT flip from ~50% to 100% per-DialogueBox → STOP and report; the cascade assumption is wrong and the fix needs `_component_language_text` work too.

---

*Companion docs: `claude_extensions/rules/dispatch-brief-checklist` (numbered steps required); `docs/best-practices/deterministic-over-hallucination.md` (#M-4 evidence shape); issue #1965 body (root cause).*
