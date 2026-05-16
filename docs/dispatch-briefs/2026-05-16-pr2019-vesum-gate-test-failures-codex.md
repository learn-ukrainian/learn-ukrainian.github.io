# Dispatch brief — Fix PR #2019's 3 vesum-gate test failures (unblocks m20)

> **Owner:** Codex
> **Filed:** 2026-05-16
> **Scope:** 3 pytest failures in `tests/test_vesum_verified_postfix.py` and
> `tests/test_vesum_gate_distractor_and_phonetic.py` blocking PR #2019
> from merging. Fix in `scripts/build/linear_pipeline.py` (the V7 VESUM
> gate). PR #2019 ships m20 gate + writer-prompt + 5 regression tests;
> these 3 tests in the same suite went red after the patches landed.
>
> Until #2019 merges, m20 (a1/my-morning) cannot advance. The night
> queue gates on this fix.

---

## The 3 failing tests (raw assertions from CI)

```
FAILED tests/test_vesum_gate_distractor_and_phonetic.py::test_pronunciation_transcription_stripped_in_prose
  AssertionError: assert 'вмиваєсся' not in {'вмиваєшся', 'вмиваєтьcя', 'вмиваєцця', 'вмиваєсся'}
  # The 'sounds like **X**' cue should strip X from the verify_words call.
  # Currently вмиваєсся sneaks through.

FAILED tests/test_vesum_verified_postfix.py::test_vesum_gate_normalizes_stress_and_markdown_before_lookup
  AssertionError: assert [['вмиваю', 'вмиваюся', 'чудов']] == [['вмиваю', 'вмиваюся', 'ся', 'чудов']]
  # Standalone **ся** in module text should normalize to 'ся' and reach VESUM lookup.
  # Currently dropped (likely by VESUM_MIN_WORD_LENGTH=3 filter on normalized path).

FAILED tests/test_vesum_verified_postfix.py::test_vesum_gate_missing_report_preserves_decorated_surface
  AssertionError: assert ['вмива́юся'] == ['вмива́ю**ся**']
  # Report should preserve the original DECORATED surface (with stress + markdown).
  # Currently shows decorated stripped of markdown but with stress preserved.
```

CI run (raw): https://github.com/learn-ukrainian/learn-ukrainian.github.io/actions/runs/25941251143/job/76259167136

## The 3 failing test bodies (verbatim)

`tests/test_vesum_verified_postfix.py:55-90` — read both tests in full
before diagnosing. They define the contract: **normalize for lookup,
preserve decorated surface in report** (two independent paths).

```python
def test_vesum_gate_normalizes_stress_and_markdown_before_lookup() -> None:
    seen: list[list[str]] = []

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        seen.append(words)
        valid = {"вмиваюся", "вмиваю", "ся", "чудов"}
        return {word: ([{"lemma": word}] if word in valid else []) for word in words}

    gate = _vesum_gate(
        module_text="вмива́ю**ся** вмива́ю **ся** чу́до**в**",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert gate["passed"] is True
    assert seen == [["вмиваю", "вмиваюся", "ся", "чудов"]]
    assert gate["missing"] == []


def test_vesum_gate_missing_report_preserves_decorated_surface() -> None:
    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        assert words == ["вмиваюся"]
        return {word: [] for word in words}

    gate = _vesum_gate(
        module_text="вмива́ю**ся**",
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert gate["passed"] is False
    assert gate["missing"] == ["вмива́ю**ся**"]
```

`tests/test_vesum_gate_distractor_and_phonetic.py:122-145` — phonetic-cue
strip path. Note: `вмиваєсся` (3 letters + `сся` suffix) IS already long
enough; the bug is the cue regex not catching the prose `sounds like` context.

```python
def test_pronunciation_transcription_stripped_in_prose() -> None:
    """A bold phonetic form following 'sounds like' must not hit VESUM."""
    module_text = (
        "The spelling **вмиваєшся** sounds like **вмиваєсся**, and "
        "**вмивається** sounds like **вмиваєцця**."
    )
    sent_for_verification: set[str] = set()

    def verify_words(words: list[str]) -> dict[str, list[dict[str, str]]]:
        sent_for_verification.update(words)
        return {word: [{"lemma": word}] for word in words}

    _vesum_gate(
        module_text=module_text,
        activities=[],
        vocabulary=[],
        resources=[],
        verify_words_fn=verify_words,
    )

    assert "вмиваєсся" not in sent_for_verification
    assert "вмиваєцця" not in sent_for_verification
    assert "вмиваєшся" in sent_for_verification
```

## Where to dig in `scripts/build/linear_pipeline.py`

| Line | What | Why relevant |
|---|---|---|
| 421-426 | `_VESUM_DECORATED_WORD_RE` | Pattern for surface-form extraction with markdown/stress |
| 429 | `_VESUM_SHORT_DECORATED_WORDS = frozenset({"ся", "сь"})` | Short-word allowlist for the DECORATED path; not applied to the normalized path |
| 461-463 | `_MORPHEME_FRAGMENT_RE` | Strips `-ться` / `-шся` morpheme labels |
| 464-467 | `_PRONUNCIATION_CUE_PATTERN` | "sounds like / звучить як / вимова: \*\*X\*\*" cue strip |
| 4428-4509 | `_vesum_gate()` | Main gate; report is built at 4500-4502 from `unchecked_pairs[].surface` |
| 4512-4533 | `_normalize_for_vesum()` | Strips stress + `**`/`*`/`` ` ``/underline markdown |
| 4536-4568 | `_iter_vesum_lookup_surface_pairs()` | Pair-building: normalized path (4541-4545) + decorated path (4547-4567); test #2 passes with assert at line 49 → `_normalize_for_vesum("вмива́ю**ся**") == "вмиваюся"` works in isolation, so the bug is in how the gate routes the surface into `pairs` |
| 4685-4709 | `_strip_metalinguistic()` | Where `_PRONUNCIATION_CUE_PATTERN` is applied |
| `scripts/audit/config.py:56` | `VESUM_MIN_WORD_LENGTH = 3` | Filters short words on the normalized path (line 4544) |

## Hypotheses (to confirm or refute with `pytest -xvs`, not assume)

1. **Failure #1** (`'ся'` missing from lookup): the standalone `**ся**` token
   gets normalized to `"ся"` (length 2), then filtered by
   `VESUM_MIN_WORD_LENGTH=3` on the normalized path (line 4544). The DECORATED
   path has `_VESUM_SHORT_DECORATED_WORDS = {"ся","сь"}` allowlist (line 4554)
   but the normalized path doesn't honor it. Likely fix: extend the
   normalized-path filter to also allow `_VESUM_SHORT_DECORATED_WORDS`.

2. **Failure #2** (`['вмива́юся']` instead of `['вмива́ю**ся**']`): something
   in the chain is stripping `**` but preserving `́` stress in the
   surface that ends up in `pairs`. Possible: `_VESUM_DECORATED_WORD_RE`
   matching consumes the markdown when capturing groups (it shouldn't;
   `match.group(0)` returns the full match). More likely: there's a path
   that calls `_normalize_for_vesum` partially or the surface comes from
   `_iter_vesum_word_surfaces` operating on `_strip_metalinguistic(text)`
   which removed `**` but didn't strip stress. **Actually run the test
   with `-s` and add print statements at `unchecked_pairs` to trace
   what's in there.**

3. **Failure #3** (`вмиваєсся` reaches VESUM despite "sounds like" cue):
   `_PRONUNCIATION_CUE_PATTERN` at line 464-467 expects
   `cue + \s* + \*\*[^*]+\*\*`. The test text has
   `**вмиваєшся** sounds like **вмиваєсся**` — note the cue (`sounds like`)
   appears AFTER the first bold form. The regex should still match the
   second form starting from "sounds like", but the `\*\*` capture before
   the cue may interfere with the alternation. **Test the regex against
   the raw module_text in a Python REPL before assuming.**

These are HYPOTHESES, not the answer. **You diagnose before fixing.** The
brief gives you the surface area; the root cause might be different.

## #M-4 deterministic-evidence preamble

| Claim | Required evidence in PR body |
|---|---|
| "All 3 failing tests now pass" | `pytest tests/test_vesum_gate_distractor_and_phonetic.py::test_pronunciation_transcription_stripped_in_prose tests/test_vesum_verified_postfix.py::test_vesum_gate_normalizes_stress_and_markdown_before_lookup tests/test_vesum_verified_postfix.py::test_vesum_gate_missing_report_preserves_decorated_surface -v` raw final summary line |
| "Sibling tests still pass" | `pytest tests/test_vesum_gate_distractor_and_phonetic.py tests/test_vesum_verified_postfix.py -v` raw final summary (full both-files run) |
| "No wider regression" | `pytest tests/ -x -q` raw final summary (or note exclusions if any) |
| "Ruff clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py` raw output |
| "Commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view --json url -q '.url'` raw URL |

**No "I tested it" without quoted command + cwd + raw output.** A claim
without evidence is treated as fabrication per `docs/best-practices/deterministic-over-hallucination.md`.

## Numbered steps (MANDATORY)

### 1. Worktree (already created by dispatch wrapper)

The dispatch wrapper has already created your worktree at
`.worktrees/dispatch/codex/pr2019-vesum-gate-fixes-2026-05-16/` branched
from `origin/fix/m20-writer-gate-russianism-markers` (PR #2019's branch).
Your branch name is `codex/pr2019-vesum-gate-fixes-2026-05-16`.

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/pr2019-vesum-gate-fixes-2026-05-16
git log -1 --oneline   # verify you're starting from PR #2019's tip
git log --oneline origin/main..HEAD | head -5   # see #2019's commits relative to main
```

Your fix stacks on top of #2019's patches. When this fix-PR is merged
into PR #2019's branch, #2019 itself becomes mergeable into main.

### 2. Reproduce the failures locally first

```bash
.venv/bin/python -m pytest \
    tests/test_vesum_gate_distractor_and_phonetic.py::test_pronunciation_transcription_stripped_in_prose \
    tests/test_vesum_verified_postfix.py::test_vesum_gate_normalizes_stress_and_markdown_before_lookup \
    tests/test_vesum_verified_postfix.py::test_vesum_gate_missing_report_preserves_decorated_surface \
    -xvs
```

If any of them PASSES locally, you have a non-deterministic test or
a stale base. Stop and report.

### 3. Diagnose

For each failure, add print statements (or pytest `-s` + targeted
`assert False, repr(...)` traps) to capture the actual values flowing
through `_iter_vesum_lookup_surface_pairs` → `unchecked_pairs` →
`missing`. Quote a snippet of trace output in your final PR body.

### 4. Fix

Edit `scripts/build/linear_pipeline.py` (and `scripts/audit/config.py`
ONLY if a constant change is the right fix). Keep changes minimal —
the patches in PR #2019 are recent and we don't want to re-architect.

If the right fix would touch the writer prompt or
`scripts/audit/config.py:VESUM_MIN_WORD_LENGTH` itself, STOP and file
a comment on PR #2019 instead of mutating those globally. Those have
cross-project blast radius.

### 5. Re-run the 3 failing tests + their full files

```bash
.venv/bin/python -m pytest \
    tests/test_vesum_gate_distractor_and_phonetic.py \
    tests/test_vesum_verified_postfix.py \
    -v
```

Quote the final summary line.

### 6. Wider regression sweep

```bash
.venv/bin/python -m pytest tests/ -x -q --ignore=tests/test_pipeline_runtime.py
```

(Ignore `test_pipeline_runtime.py` if it's slow / requires services we
don't need; otherwise include it.)

Quote the final summary line. If anything went red that was previously
green, FIX before proceeding. The test mocks in #2019's siblings are
load-bearing for the orchestrator's morning review.

### 7. Lint

```bash
.venv/bin/ruff check scripts/build/linear_pipeline.py
.venv/bin/ruff format --check scripts/build/linear_pipeline.py
```

### 8. Commit

```bash
git add scripts/build/linear_pipeline.py
# only if you also touched config.py:
# git add scripts/audit/config.py
git commit -m "$(cat <<'EOF'
fix(vesum-gate): preserve decorated surface in report + allow ся on normalized path + tighten pronunciation cue

Three regressions surfaced by PR #2019's writer-prompt + gate patches:

1. Standalone **ся** (and **сь**) was filtered from the normalized
   lookup path by VESUM_MIN_WORD_LENGTH=3, even though the decorated
   path already allowlists them via _VESUM_SHORT_DECORATED_WORDS.
   Extend the allowlist to the normalized path.

2. The "missing" report stripped markdown from decorated surface forms
   while preserving stress, producing вмива́юся instead of вмива́ю**ся**.
   Fix: <one-line description of where the bug was>.

3. _PRONUNCIATION_CUE_PATTERN failed to strip the second bold form in
   "**X** sounds like **Y**" prose. Fix: <one-line description>.

All 3 failing tests in tests/test_vesum_gate_distractor_and_phonetic.py
and tests/test_vesum_verified_postfix.py now pass; no regressions in
the broader pytest suite.

Branched off PR #2019's tip (feat/m20-gate-and-writer-prompt) so this
fix stacks. Once merged into #2019, that PR becomes mergeable and
unblocks the m20 build queue.

Co-Authored-By: Codex (gpt-5.5)
EOF
)"
```

### 9. Push

```bash
git push -u origin codex/pr2019-vesum-gate-fixes-2026-05-16
```

### 10. Open PR — base is PR #2019's branch, NOT main

```bash
gh pr create \
    --base fix/m20-writer-gate-russianism-markers \
    --title "fix(vesum-gate): preserve decorated surface + allow ся on normalized path + tighten pronunciation cue" \
    --body "$(cat <<'EOF'
## Summary

Fixes the 3 vesum-gate test failures blocking PR #2019.

Branches off #2019's tip so the merge stacks. Once this lands, #2019 is
mergeable and the m20 build queue advances.

## Failures fixed

(One paragraph each summarizing root cause + fix.)

## Test plan

- [x] 3 originally-failing tests now pass (paste raw pytest summary)
- [x] Full both-files pytest green (paste raw summary)
- [x] Wider `pytest tests/` sweep clean (paste raw summary)
- [x] `ruff check scripts/build/linear_pipeline.py` clean (paste raw output)

## Verifiable evidence

(Codex must paste raw command + cwd + output for each claim above.)

🤖 Generated with [Codex](https://codex.openai.com)
EOF
)"
```

**No `--admin`, no auto-merge.** The orchestrator will review, then
merge into #2019's branch, then merge #2019 into main.

---

## Acceptance criteria

PR is ready for review when ALL satisfied with quoted evidence:

- [ ] All 3 originally-failing tests pass (raw `pytest -v` summary in PR body)
- [ ] Full file runs of both test files pass (raw summary)
- [ ] `pytest tests/ -x -q` shows no NEW failures (raw summary; document any pre-existing failures)
- [ ] `ruff check scripts/build/linear_pipeline.py` clean
- [ ] PR base is `feat/m20-gate-and-writer-prompt` (NOT main)
- [ ] PR body quotes the actual root cause for each of the 3 failures (not "the code was wrong")

If you find that fixing one test breaks another (e.g. stricter
pronunciation strip catches legitimate forms), tell the orchestrator
in the PR body — the test contract may need joint design review.

## Failure modes to avoid

- **Don't widen `_PRONUNCIATION_CUE_PATTERN` so it eats legitimate text.** The
  test `test_isolated_misspelling_still_caught` exists to guard against
  over-strip. Run it.
- **Don't lower `VESUM_MIN_WORD_LENGTH`.** That's a global threshold; the
  fix is per-path allowlist, not threshold mutation.
- **Don't merge into main directly.** PR base MUST be #2019's branch.
- **Don't edit the test files** unless you're fixing a typo in an
  expected value AND you can prove the new value is more correct than
  the old (rare; usually means the test was written wrong, not the
  code). Default: code adapts to the contract the test asserts.

---

## Orchestrator follow-up after PR opens

1. Read PR diff + verify quoted evidence (re-run a sample test).
2. If green: merge into PR #2019's branch with `--squash --delete-branch`.
3. PR #2019 should now show all blocking checks green; merge into main.
4. Then m20 unblocks — fire next phase (Codex dispatch for #2018 activity_schema gate).

---

*Brief format: MD per #M-2 (ai → ai). Authority: MEMORY DISPATCH-BRIEF
CHECKLIST + #M-4 deterministic-evidence preamble. Companion:
`docs/best-practices/deterministic-over-hallucination.md`.*
