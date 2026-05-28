# 2026-05-27 — Missing verify_quote tests on PR #2367 (Gemini follow-up)

> Dispatch target: `gemini --mode danger --worktree`, model `gemini-3.1-pro-preview`.
> Base: existing branch `gemini/v7-verify-quote-gate-2026-05-27` (currently open as PR #2367; push a follow-up commit to the same branch).
> Tracking: orchestrator review of PR #2367 surfaced fabricated test claim in PR body.

## Why this exists

PR #2367's Summary claims:
> Tests: 4 cases on verify_quote (match / mismatch / partial / no-attribution)

The actual branch added only `tests/test_prev_next.py` (4 prev_next tests). **Zero tests on the new 148-LOC `_textbook_quote_fidelity_gate` function.** No regression test for the m20 `Кнак` case the gate was built to catch.

Adding the 4 missing tests now. Same branch, same PR — push a follow-up commit; the PR will re-trigger CI and become mergeable.

## What to build

Create `tests/test_textbook_quote_fidelity_gate.py` with 4 tests covering the gate function `_textbook_quote_fidelity_gate` (defined at the end of `scripts/build/linear_pipeline.py`).

### Test 1 — match (happy path)

Synthetic chunk where the blockquote's Cyrillic-normalized text appears verbatim. Use `monkeypatch.setattr` on `scripts.wiki.sources_db.search_textbooks` to return a list with one dict containing `{"text": "<chunk text containing the blockquote verbatim>"}`. Assert `gate["passed"] is True` and `gate["violations"] == []`.

### Test 2 — mismatch (m20 `Кнак` regression)

Use the actual m20 blockquote text (5 lines from `curriculum/l2-uk-en/a1/my-morning/module.md:55-62`):

```
> Мій день
> — Сьогодні в мене багато справ, — мови-
> ло жабеня Кнак. — Запишу.
> «Поснідати. Одягнутися. Піти до Квака.
> Прогулятися з Кваком. Пообідати. Подрімати.
> Погратися з Кваком. Повечеряти. Лягти спати».
> — Ну от і все. Тут за-пи-са-ний  у-весь
> мій  день (за Арнольдом  Лобелом).

*— Захарійчук, Grade 1, p.24*
```

Mock `search_textbooks` to return a chunk where the corresponding text says `Квак` instead of `Кнак` (Levenshtein distance ≥ 3 once normalized, since other small differences will compound). Assert:
- `gate["passed"] is False`
- At least one violation with `reason` containing `"differs"` or `">=3"`
- The violation's `nearest_source` contains `Квак`

### Test 3 — partial-mismatch below threshold

Blockquote differs from source by exactly 2 characters (e.g., one typo'd consonant + one whitespace artifact). Mock `search_textbooks` accordingly. Assert `gate["passed"] is True` (below the 3-char threshold).

### Test 4 — no-attribution + NO_VERIFY opt-out

Two assertions in one test (or two test functions, your call):
- **(a)** Bare `> ...` blockquote followed by EOF (no `*— Source, p.N*` line within the lookahead window). Assert `gate["passed"] is False` and the violation's `reason` contains `"Missing attribution"` (matching the gate's `"Missing attribution without NO_VERIFY"` string).
- **(b)** Same blockquote preceded by `<!-- NO_VERIFY: orchestrator review pending -->` immediately before the `>`. Assert `gate["passed"] is True`.

### Minor cleanup (one extra commit OR same commit, your call)

`tests/test_prev_next.py:23-25` defines:

```python
# both exist (for m20, prev is m19 which exists. next is m21 which DOES NOT exist. Wait, let's make m21 exist for this test)
def exists_all(self): return True
monkeypatch.setattr(Path, "exists", exists_all)
```

This OVERRIDES the carefully-set-up `exists_mock` from lines 20-22 before `exists_mock` is ever used. Either:
- Delete the `exists_all` lines and the comment, and trust `exists_mock` to provide the "both exist" state (m19 + m20 exist, m21 doesn't — but the assertion expects `next_val == "m21"` which contradicts). Fix the assertion to match `exists_mock`, OR
- Reframe the "both exist" block to explicitly set up a state where both prev and next exist (`exists_mock` returns True for m19.mdx + m21.mdx) and remove the dead `exists_all` lines.

Either is fine; the test currently works because subsequent monkeypatch calls override `exists_all`, but the code reads as a partial edit.

## Anti-fabrication contract (#M-4)

| Claim | Required evidence in PR comment |
|---|---|
| "4 verify_quote tests pass" | `.venv/bin/pytest tests/test_textbook_quote_fidelity_gate.py -v --no-header` raw output showing 4 PASSED |
| "PRev_next test cleanup applied" | `git diff HEAD~1 -- tests/test_prev_next.py` showing the `exists_all` lines removed |
| "Full pre-existing test suite still green" | `.venv/bin/pytest tests/test_linear_pipeline.py tests/test_prev_next.py tests/test_v7_build*.py -q --no-header` final summary line raw |
| "Lint clean on new file" | `.venv/bin/ruff check tests/test_textbook_quote_fidelity_gate.py` final line raw |

## Numbered execution steps

1. **Switch to the existing PR branch.** `delegate.py dispatch` created a fresh worktree on a NEW branch named after your task-id. You need to operate on the EXISTING open PR #2367 branch instead. Run:
   ```
   git fetch origin gemini/v7-verify-quote-gate-2026-05-27:gemini/v7-verify-quote-gate-2026-05-27
   git checkout gemini/v7-verify-quote-gate-2026-05-27
   ```
   Verify with `git branch --show-current` (should print `gemini/v7-verify-quote-gate-2026-05-27`). If the local branch already exists from a prior worktree (it might), use `git checkout gemini/v7-verify-quote-gate-2026-05-27` directly and `git pull --rebase origin gemini/v7-verify-quote-gate-2026-05-27` to sync.

2. **Rebase against origin/main** to pick up the now-merged PR #2366 (codex prompt hardening): `git fetch origin main && git rebase origin/main`. If conflicts, resolve trivially (your changes touch different files than the codex prompt PR).

3. **Read the existing gate function** in `scripts/build/linear_pipeline.py` (the `_textbook_quote_fidelity_gate` function at the bottom). Confirm its public signature and what shape the input `module_text` takes. Confirm the import path for `search_textbooks` (`scripts.wiki.sources_db`).

4. **Write `tests/test_textbook_quote_fidelity_gate.py`** with the 4 tests above. Use `pytest`'s `monkeypatch` fixture to stub `search_textbooks`. Match the existing project test style — see `tests/test_prev_next.py` for the monkeypatch pattern.

5. **Test 2 (regression)** is the load-bearing one. Use the m20 `Кнак` blockquote text verbatim (copy from `curriculum/l2-uk-en/a1/my-morning/module.md:55-62`). Mock `search_textbooks` to return a chunk that says `Квак` where the blockquote says `Кнак` — this proves the gate would have caught the bug that motivated it.

6. **Apply the test_prev_next.py cleanup** (delete `exists_all` lines + comment, fix the first assertion to match `exists_mock` reality, OR rework `exists_mock` to actually represent "both exist").

7. **Run the test suite.** `.venv/bin/pytest tests/test_textbook_quote_fidelity_gate.py tests/test_prev_next.py -v --no-header`. Capture full output. If any test fails, fix the gate logic OR fix the test (your judgment on which is buggy — read the gate function to decide).

8. **Run ruff.** `.venv/bin/ruff check tests/test_textbook_quote_fidelity_gate.py tests/test_prev_next.py`. Capture final line.

9. **Commit** with conventional message:
   ```
   test(v7-gates): add 4 verify_quote tests covering match/mismatch/partial/no-attr

   PR #2367 review caught: the 148-LOC _textbook_quote_fidelity_gate
   landed without test coverage despite the PR Summary claiming 4 tests.
   Adds tests/test_textbook_quote_fidelity_gate.py with:
   - match: blockquote text appears verbatim in mocked source chunk
   - mismatch: m20 'Кнак' regression — gate catches the typo class
     that VESUM cannot detect
   - partial: 2-char difference (below 3-char threshold) passes
   - no-attribution: bare > blockquote fails; NO_VERIFY opt-out passes

   Also cleans up tests/test_prev_next.py exists_all override that
   defeated the prior exists_mock setup.

   X-Agent: gemini/verify-quote-tests-followup-2026-05-27
   ```

10. **Push to the EXISTING PR branch.** `git push origin gemini/v7-verify-quote-gate-2026-05-27` (force-push only if rebase requires it: `git push --force-with-lease origin gemini/v7-verify-quote-gate-2026-05-27`). The PR #2367 will pick up the new commit and re-run CI. Do NOT push your dispatch-derived branch — that creates a duplicate PR.

11. **Post a PR comment on #2367** with the raw pytest + ruff outputs (the anti-fabrication evidence).

12. **DO NOT touch the gate function itself unless a test reveals a real bug.** If a test reveals a real gate bug (e.g., normalization edge case), fix the gate AND note it in the PR comment. If a test fails because the gate works differently than the brief assumed, adjust the test assertion (the gate is the source of truth on shape).

13. **DO NOT auto-merge.** Orchestrator review required.

## Scope guardrails

- DO NOT change the gate logic except to fix bugs revealed by the tests.
- DO NOT add new gates or new pipeline phases.
- DO NOT modify `scripts/build/prev_next.py` (that part of PR #2367 is fine as-is).
- DO NOT modify the writer prompt or reviewer rubric (those are PR #2366's territory, already merged).
- If the gate function's `search_textbooks` interface differs from what the brief assumed, follow the actual signature; report the discrepancy in PR comment.
