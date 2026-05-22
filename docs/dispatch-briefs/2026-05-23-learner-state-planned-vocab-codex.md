# Dispatch brief — `learner_state.py` planned-vocab fallback

**Agent**: Codex (gpt-5.5, xhigh)
**Mode**: `--worktree --danger` (writes commits, opens PR)
**Date**: 2026-05-23
**Origin**: Item #1 of the 5 outstanding items from `docs/session-state/2026-05-23-v7-design-alignment-m20-reverted.md`, diagnosis run in main session 2026-05-23.

## Context

The m20 (a1/my-morning) revert (`944f4200e4`) exposed that student-aware immersion is **structurally wired but functionally empty** for any module built before its predecessors exist. Diagnosis verified in main session: `cumulative_vocabulary` returns `[]` for m20 → `compute_immersion_band` selects band `a1-m01-03` (first-3-modules band) regardless of actual module number → the `{IMMERSION_RULE}` injected into the writer prompt is the *beginning-of-A1* rule, not a student-aware m20 rule.

`known_grammar` accumulates correctly (95 entries for m20) because `_load_grammar` reads from `plans/`. `_load_vocab` reads from built `curriculum/{track}/{slug}/vocabulary.yaml` files. Only one A1 module is built today (`my-morning`); the other 54 don't have built `vocabulary.yaml` files yet.

User decision (interview, 2026-05-23): fix this **before** the writer-prompt and reviewer-prompt rebuilds (items #2, #3 — which depend on student-aware framing actually working).

## Bug evidence (deterministic, reproducible)

Reproducer (run from repo root):
```bash
cd /Users/krisztiankoos/projects/learn-ukrainian && .venv/bin/python -c "
from scripts.pipeline.learner_state import build_learner_state
from scripts.config import compute_immersion_band
ls = build_learner_state('a1', 20)
print('cumulative_vocabulary len:', len(ls.get('cumulative_vocabulary', [])))
print('known_grammar len:', len(ls.get('known_grammar', [])))
print('band key:', compute_immersion_band('a1', 20, learner_state=ls)['key'])
"
```

Current output:
```
cumulative_vocabulary len: 0
known_grammar len: 95
band key: a1-m01-03
```

Expected output after fix (m20 has 19 prior A1 modules with planned vocab ≈ 7+9 entries each):
```
cumulative_vocabulary len: 100  # ballpark; minimum >50, single-source-of-truth: sum of vocabulary_hints.required+recommended across all prior modules per the manifest order
known_grammar len: 95
band key: <a later A1 band, NOT a1-m01-03>
```

## Plan structure (already verified)

Sample plan: `curriculum/l2-uk-en/plans/a1/colors.yaml`:
```yaml
vocabulary_hints:
  required:
    - "червоний (red)"
    - "жовтий (yellow)"
    - "зелений (green)"
    # ... 7-10 entries
  recommended:
    - "коричневий (brown)"
    - "рожевий (pink)"
    # ... 8-10 entries
```

Hint format: `"<lemma> (<gloss + optional POS>)"`. Parse: split on first ` (` and take prefix, trim.

Edge cases observed in real plans:
- Vocative notes: `"синку (son — vocative, from син)"` → lemma `синку`
- Chunks marked as such: `"вітаю (congratulations — chunk)"` → lemma `вітаю`
- POS markers: `"готовий (ready, adj m)"` → lemma `готовий`

The simple split-on-`" ("` handles all observed cases.

## Files to modify

ONE file: `scripts/pipeline/learner_state.py`

## Fix specification

1. **Add `_parse_vocab_hint_lemma(entry: str) -> str | None`** at module level. Returns the lemma (everything before `" ("`, trimmed). Returns None if the entry is empty/whitespace. Does NOT try to validate the lemma against VESUM here — that's reviewer-side.

2. **Add `_load_planned_vocab(track: str, slug: str) -> list[str]`** at module level. Reads `CURRICULUM_ROOT / "plans" / track / f"{slug}.yaml"`. Returns lemmas from `vocabulary_hints.required + vocabulary_hints.recommended` (in that order, dedup-preserving-order). If the plan file doesn't exist, returns `[]`. If `vocabulary_hints` is absent or malformed, returns `[]`. Tolerant of plan-schema variations (string-list vs dict-list).

3. **Modify `_load_vocab(track: str, slug: str) -> list[str]`** policy:
   - **First**, try built-artifact path (current behavior — `CURRICULUM_ROOT / track / slug / "vocabulary.yaml"`). If the file exists AND returns ≥1 lemma, use that.
   - **Else**, fall back to `_load_planned_vocab(track, slug)`.
   - This matches steady-state ordering: built modules give actual taught vocab; not-yet-built modules use plan intent as the best available proxy.

4. **No change to `build_learner_state` signature or return shape.** Just the underlying lookup gets smarter.

## Acceptance criteria (deterministic)

Codex MUST verify these BEFORE opening the PR. Quote raw output in PR body.

| # | Command | Expected |
|---|---|---|
| 1 | `build_learner_state('a1', 20)['cumulative_vocabulary']` length | `> 50` |
| 2 | `build_learner_state('a1', 20)['known_grammar']` length | `== 95` (unchanged from current behavior) |
| 3 | `compute_immersion_band('a1', 20, learner_state=build_learner_state('a1', 20))['key']` | `!= 'a1-m01-03'` |
| 4 | `build_learner_state('a1', 1)['cumulative_vocabulary']` length | `== 0` (no prior modules to accumulate from) |
| 5 | `build_learner_state('a1', 2)['cumulative_vocabulary']` length | `>= 5` (module 1's planned vocab — required + recommended) |
| 6 | `_parse_vocab_hint_lemma('готовий (ready, adj m)')` | `'готовий'` |
| 7 | `_parse_vocab_hint_lemma('синку (son — vocative, from син)')` | `'синку'` |
| 8 | `_parse_vocab_hint_lemma('')` | `None` (or empty string — pick one and be consistent) |

## Test additions

Add to `tests/test_learner_state.py` (create if not exists):

- `test_load_planned_vocab_a1_colors` — asserts `_load_planned_vocab('a1', 'colors')` returns ≥10 lemmas matching the colors plan
- `test_load_vocab_falls_back_to_planned` — asserts when built `vocabulary.yaml` doesn't exist for some test slug, `_load_vocab` returns the planned lemmas
- `test_load_vocab_prefers_built_when_present` — asserts when built `vocabulary.yaml` exists, `_load_vocab` returns built lemmas (not planned)
- `test_build_learner_state_a1_m20_has_vocab` — asserts `cumulative_vocabulary` non-empty for a1/m20 today (regression guard against the bug we're fixing)
- `test_parse_vocab_hint_lemma_basic` — covers `готовий (ready, adj m)`, `синку (son — vocative, from син)`, `вітаю (congratulations — chunk)`, empty input

If `tests/test_learner_state.py` already exists, ADD these tests; do not rewrite existing tests.

## Numbered steps (from project DISPATCH-BRIEF CHECKLIST)

1. `git worktree add .worktrees/learner-state-planned-vocab origin/main`
2. cd into worktree; create branch `fix/learner-state-planned-vocab`
3. Implement the fix in `scripts/pipeline/learner_state.py` per the spec above
4. Add tests in `tests/test_learner_state.py` per the test-additions list
5. Run `.venv/bin/pytest tests/test_learner_state.py -v` — quote raw output in PR body
6. Run `.venv/bin/ruff check scripts/pipeline/learner_state.py tests/test_learner_state.py` — must be clean
7. Run the manual acceptance reproducer from §Bug evidence — quote raw output in PR body, confirming all 8 acceptance criteria pass
8. Conventional commit: `fix(learner_state): planned-vocab fallback for not-yet-built modules — unblocks student-aware immersion`
9. `git push -u origin fix/learner-state-planned-vocab`
10. `gh pr create` with title above; PR body MUST include: bug evidence (current output), fix summary (3 sentences), acceptance reproducer output (all 8 criteria), pytest output, ruff output
11. **DO NOT auto-merge.** Orchestrator will review.

## NOT in scope (constrain — do not expand)

- Do NOT touch `compute_immersion_band` in `scripts/config.py` — that function is correct; the bug is upstream.
- Do NOT touch `_load_grammar` — it already reads from plans correctly.
- Do NOT add VESUM validation of parsed lemmas — that's reviewer-side concern.
- Do NOT change `vocabulary_hints` schema in plans — the fix must work with the EXISTING schema.
- Do NOT redesign the curriculum directory structure — only `learner_state.py` and the test file.
- Do NOT add a CLI flag for choosing planned-vs-built — the policy "built when available, planned otherwise" is deterministic and not user-configurable.

## #M-4 preamble — deterministic claims

Verifiable claims in this PR body, paired with the tool that grounds them:

| Claim | Tool / evidence required |
|---|---|
| "tests pass" | `pytest` final summary line (`N passed in M.Ms`) — quote raw |
| "ruff clean" | `ruff check` final line (`All checks passed!` or zero-error count) — quote raw |
| "acceptance criteria N pass" | Reproducer Python script output — quote raw for each of the 8 criteria |
| "commit landed" | `git log -1 --oneline` raw output |
| "PR opened" | `gh pr view --json url` raw URL |

No claim in this PR body should appear without the corresponding tool output quoted.
