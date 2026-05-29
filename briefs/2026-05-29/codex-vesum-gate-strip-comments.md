# Codex brief — VESUM gate must strip HTML comments (proven false-positive)

## Why (root-caused + empirically reproduced)
The `vesum_verified` python_qg gate false-fails on Cyrillic words that appear ONLY inside HTML
comments. The m20 rebuild failed with `missing: ["одіватися"]` even though `одіватися` appears
ONLY in protected positions in module.md:
1. a bad-form marker: `the form <!-- bad -->одіватися<!-- /bad --> is not used` (correctly excluded), and
2. a VERIFY annotation comment: `<!-- VERIFY: source="..."; check_russian_shadow(word='одіватися') -->`.

`_strip_metalinguistic` (scripts/build/linear_pipeline.py ~line 7853, used by `_build_vesum_text`)
strips `_AVOID_MARKER_RE` (`<!-- bad -->X<!-- /bad -->`) but does NOT strip regular `<!-- ... -->`
comments — so the VERIFY-comment occurrence survives into the VESUM lookup and fails. Reproduced:

```python
from scripts.build.linear_pipeline import _build_vesum_text
s = ('the form <!-- bad -->одіватися<!-- /bad --> is not used '
     '<!-- VERIFY: check_russian_shadow(word=\'одіватися\') -->')
assert "одіватися" not in _build_vesum_text(s, [], [], [])   # CURRENTLY FAILS — одіватися survives
```

This is LATENT and broad: writers routinely document `verify_words` / `check_russian_shadow` tool
calls in `<!-- VERIFY: ... -->` comments with Cyrillic args; any non-VESUM arg (Russianism, typo,
dialectism) false-fails the build. The writer here did everything RIGHT (taught одягатися 20×,
marked одіватися as the bad form, documented the russian-shadow check) — the GATE is wrong.

## The fix (ordering is critical)
In `_strip_metalinguistic`, strip remaining HTML comments AFTER `_AVOID_MARKER_RE` runs. Use the
existing `_strip_comments` helper (scripts/build/linear_pipeline.py ~line 10111):

```python
    text = _AVOID_MARKER_RE.sub(" ", text)     # existing — removes <!-- bad -->X<!-- /bad --> incl. X
    text = _strip_comments(text)               # ADD — removes remaining <!-- ... --> comments (VERIFY, etc.)
    text = _WARNING_QUOTE_RE.sub(" ", text)     # existing
    ...
```

**MUST be AFTER `_AVOID_MARKER_RE`** — if comments are stripped first, the `<!-- bad -->` / `<!-- /bad -->`
delimiters vanish and the inner bad-form text (одіватися) is left BARE → re-introduces the false
positive. Verify the ordering with a test.

## Tests (`tests/` — extend the vesum gate test module or add a focused one)
- The reproduction above: `_build_vesum_text(s, [], [], [])` does NOT contain `одіватися` (neither the
  bad-marker nor the VERIFY-comment occurrence survives).
- A bad-marker form alone is still excluded (regression guard for ordering): bad-marker одіватися gone.
- A normal prose Cyrillic word OUTSIDE any comment/marker still survives (no over-stripping).
- `_vesum_gate` end-to-end on a module_text with a VERIFY-comment Russianism → `passed: True`.

## Verification (#M-4 — quote raw)
- `.venv/bin/python -m pytest tests/test_vesum_gate.py <new/edited test> -q` → final `N passed`.
- `.venv/bin/ruff check scripts/build/linear_pipeline.py <test>` → `All checks passed!`.
- Paste the reproduction assertion passing.

## Steps (dispatch enforces worktree)
1. Confirm worktree root.
2. Apply the 1-line fix + tests.
3. pytest (vesum gate suite + new test) + ruff — paste raw final lines.
4. `git commit` conventional (`fix(vesum-gate): strip HTML comments before VESUM lookup so VERIFY-annotation Cyrillic args don't false-fail (#2380)`); Co-Authored-By line.
5. `git push -u origin <branch>` ; `gh pr create --base main`. **No auto-merge.**
Report PR URL (raw) + pytest/ruff lines + the reproduction assertion result.
