# Codex dispatch brief — VESUM gate scope tightening across 4 leak surfaces (#1962 gate 1)

> **Issue:** #1962 gate 1 — `vesum_verified` over-broad extraction pulls tokens from non-Ukrainian-assertion contexts
> **Mode:** danger
> **Worktree:** `.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13/`
> **Base:** `origin/main` (currently `53e61bc69c`)
> **Hard timeout:** 5400s
> **Silence timeout:** 1500s
> **Effort:** high

---

## ⚠️ CRITICAL — fresh-shell behavior

Each bash block runs in a FRESH SHELL. Prefix every command with `cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13 && ...` or absolute path. Inside the worktree, `.venv/` is gitignored — use main checkout's `.venv` via absolute path: `/Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/python`.

---

## Goal

Tighten `_vesum_gate` (and its helpers `_activity_vesum_text`, `_build_vesum_text`) to skip 4 distinct false-positive surfaces surfaced by m20 (`a1/my-morning`) build #3. The current gate already handles two cases (`_ERROR_CORRECTION_INTENTIONAL_FIELDS` and `{text, correct: false}` dict-shape wrong-options), but misses the bare-list options shape, the `explanation:` field for error-correction, and parenthetical meta-linguistic content in vocabulary `usage:`.

After this fix, the next m20 build should pass `vesum_verified` and advance to surface the remaining gates (citations_resolve, l2_exposure_floor, long_uk_ceiling — tracked in #1962 gates 2-4, NOT in scope for this PR).

---

## #M-4 preamble — verifiable claims this work will produce

| Claim | Deterministic tool | Output format |
|---|---|---|
| "Gate excludes bare-list options for fill-in" | `grep -n 'fill-in\|options' scripts/build/linear_pipeline.py` shows the new branch in `_activity_vesum_text` | quote grep output |
| "Gate excludes bare-list non-answer options for quiz" | same grep + new test | quote |
| "Gate excludes explanation field in error-correction" | `grep -n '_ERROR_CORRECTION_INTENTIONAL_FIELDS' scripts/build/linear_pipeline.py` shows `explanation` added | quote |
| "Gate strips parenthetical content from vocabulary `usage:`" | `grep -n 'usage\|paren' scripts/build/linear_pipeline.py` shows new strip | quote |
| "Real-world replay: m20 build #3's activities.yaml + vocabulary.yaml no longer yield the 11 missing forms" | new test loads/inlines those artifacts and asserts `_vesum_gate` returns `passed=True` (or at least drops Завтрак, користу, п'юся, стем, теся, юся, ються, ємося, єтеся, ється, єшся from missing) | quote test name + pass |
| "All `tests/build/test_linear_pipeline.py` tests pass" | `.venv/bin/pytest tests/build/test_linear_pipeline.py -v` | quote summary line |
| "Lint clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py` | quote final line |
| "PR opened" | `gh pr view <N> --json url` | quote URL |

Inline "I checked X" without quoted raw output = hallucination per #M-4. Quote.

---

## The 4 leak surfaces (read this carefully before coding)

### Leak 1: fill-in `options:` bare list

`activities.yaml` for `type: fill-in` activities has this shape:

```yaml
- id: act-2
  type: fill-in
  items:
  - sentence: Я вмива___ о сьомій.
    answer: юся
    options:                  # ← bare list of suffix fragments
    - юся                     # ← suffix fragment, NOT a VESUM lemma
    - єшся                    # ← suffix fragment
    - ється                   # ← suffix fragment
```

These options are morphological-suffix fragments designed for fill-in pedagogy. **None should be verified against VESUM.** The current `_activity_vesum_text` helper only handles the `{text, correct}` dict-shape wrong-option pattern — bare-list strings get walked as-is and verified.

**Fix:** When walking an activity with `type: fill-in`, skip the entire `options:` list value (don't descend into its strings). Treat the same way `error:`/`sentence:` are skipped for error-correction.

### Leak 2: quiz `options:` non-answer bare-list distractors

`type: quiz` activities have similar shape:

```yaml
- id: act-1
  type: quiz
  items:
  - question: Я ___ каву о восьмій.
    options:
    - п'юся     # ← fabricated WRONG form (no such word — synthesized distractor)
    - п'ю
    answer: п'ю
```

`п'юся` is intentionally fabricated to test learner overgeneralization. **Distractors that are non-answer should not be VESUM-verified.**

**Fix:** When walking an activity with `type: quiz` (or any type with a sibling `answer:` field on the item), only verify the `options:` entry that equals `answer:`. Skip the rest.

### Leak 3: error-correction `explanation:` field

`type: error-correction` activities:

```yaml
items:
- sentence: На сніданок я завжди їм завтрак.
  error: завтрак
  correction: сніданок
  explanation: «Завтрак» is a Russianism. Standard Ukrainian for the morning meal is сніданок.
```

`sentence:` and `error:` are already skipped. But `explanation:` ALWAYS references the wrong form (here capitalized `Завтрак` inside guillemets). Currently `explanation:` gets walked and verified.

**Fix:** Add `"explanation"` to `_ERROR_CORRECTION_INTENTIONAL_FIELDS`. (Or, more defensively, strip guillemet-quoted segments `«...»` from explanation text — but the field-level skip is simpler and the explanation always contextualizes the wrong form anyway.)

### Leak 4: vocabulary `usage:` parenthetical meta-linguistic content

`vocabulary.yaml`:

```yaml
- lemma: дивлюся
  pos: verb
  usage: Я дивлюся у дзеркало (стем + -л- у 1-й особі однини).
                              ↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑↑
                              meta-linguistic note, not the sentence
```

`стем` (English "stem") + linguistic abbreviations inside the parenthetical are not part of the sample sentence. The `usage:` field is currently passed through `_strip_metalinguistic` (which handles brackets `[...]` and inline code) but does NOT strip parenthetical `(...)` content.

**Fix:** In `_build_vesum_text`'s vocabulary section (around line 4524-4526), strip `(...)` parenthetical from `usage:` BEFORE appending to the parts list. Add a helper `_strip_usage_parentheticals(text: str) -> str` that removes `(...)` segments. Alternatively extend `_strip_metalinguistic` to optionally strip parentheticals when called from the vocabulary `usage:` path (controlled by a kwarg or a new function name like `_strip_metalinguistic_vocab_usage`).

Prefer the dedicated helper approach to keep `_strip_metalinguistic`'s contract unchanged for `module_text` (where prose parentheticals like `(вмиватися)` ARE meaningful Ukrainian).

---

## Suggested implementation order

1. **Leak 3 first (smallest)** — add `"explanation"` to `_ERROR_CORRECTION_INTENTIONAL_FIELDS` set (1-line edit at line 509-511).
2. **Leak 1** — in `_activity_vesum_text`, after the existing wrong-option logic, add a branch: if the activity's `type` is `fill-in` AND the current dict key is `options`, skip the value entirely.
3. **Leak 2** — similar branch for `quiz` (and probably `match-up`, `true-false` — any type with item-level `options` + `answer`). The right shape: when walking an item-level dict that has both `options` and `answer`, only walk the option(s) equal to `answer:`. This handles all `options + answer` quiz-like shapes uniformly.
4. **Leak 4** — add `_strip_usage_parentheticals` helper and call it in `_build_vesum_text` for the `usage:` field. Sequence: strip parenthetical first, THEN `_strip_metalinguistic`.

After each leak's fix, write a focused regression test in `tests/build/test_linear_pipeline.py`. Aim for 4 new tests (one per leak) plus a 5th integration test exercising the m20 build #3 artifacts.

---

## Tests

Write 5 tests adjacent to existing vesum-gate tests (search `def test_vesum`). Use realistic minimal fixtures derived from m20's artifacts:

**Test A — fill-in options skip:**

```python
def test_vesum_gate_skips_fillin_options_bare_list() -> None:
    """Regression for #1962 gate 1 leak 1. fill-in activities use bare-list
    options that are morphological suffix fragments (юся, єшся, ється).
    These are intentional pedagogical fragments — never valid VESUM lemmas."""
    activities = [{
        "id": "act-2",
        "type": "fill-in",
        "items": [{
            "sentence": "Я вмива___ о сьомій.",
            "answer": "юся",
            "options": ["юся", "єшся", "ється"],
        }],
    }]
    fake_verify = _build_fake_verify_words(known={"вмиватися": True})
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "юся" not in report["missing"]
    assert "єшся" not in report["missing"]
    assert "ється" not in report["missing"]
```

**Test B — quiz options non-answer skip:**

```python
def test_vesum_gate_skips_quiz_options_distractors() -> None:
    """Regression for #1962 gate 1 leak 2. quiz activities have bare-list
    options where non-`answer` strings are distractors — including
    fabricated wrong forms like п'юся that VESUM correctly rejects."""
    activities = [{
        "id": "act-1",
        "type": "quiz",
        "items": [{
            "question": "Я ___ каву.",
            "options": ["п'юся", "п'ю"],
            "answer": "п'ю",
        }],
    }]
    fake_verify = _build_fake_verify_words(known={"п'ю": True})
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "п'юся" not in report["missing"]
```

**Test C — error-correction explanation skip:**

```python
def test_vesum_gate_skips_error_correction_explanation() -> None:
    """Regression for #1962 gate 1 leak 3. error-correction explanations
    always reference the wrong form (often capitalized in guillemets)."""
    activities = [{
        "id": "act-8",
        "type": "error-correction",
        "items": [{
            "sentence": "На сніданок я завжди їм завтрак.",
            "error": "завтрак",
            "correction": "сніданок",
            "explanation": "«Завтрак» is a Russianism. Standard Ukrainian: сніданок.",
        }],
    }]
    fake_verify = _build_fake_verify_words(known={"сніданок": True})
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=activities,
        vocabulary=[],
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "Завтрак" not in report["missing"]
    assert "завтрак" not in report["missing"]
```

**Test D — vocabulary usage parenthetical strip:**

```python
def test_vesum_gate_strips_vocabulary_usage_parentheticals() -> None:
    """Regression for #1962 gate 1 leak 4. vocabulary usage often has
    parenthetical meta-linguistic notes containing English/linguistic terms
    (e.g. 'стем' = English 'stem')."""
    vocabulary = [{
        "lemma": "дивлюся",
        "pos": "verb",
        "usage": "Я дивлюся у дзеркало (стем + -л- у 1-й особі однини).",
    }]
    fake_verify = _build_fake_verify_words(known={"дивлюся": True, "дзеркало": True})
    report = linear_pipeline._vesum_gate(
        module_text="",
        activities=[],
        vocabulary=vocabulary,
        resources=[],
        verify_words_fn=fake_verify,
    )
    assert "стем" not in report["missing"]
```

**Test E — m20 build #3 integration replay:**

```python
def test_vesum_gate_passes_m20_build_3_artifacts() -> None:
    """Replay m20 (a1/my-morning) build #3 fixtures. Should no longer
    report Завтрак, користу, п'юся, стем, теся, юся, ються, ємося,
    єтеся, ється, єшся as missing. Skips if the build worktree is gone."""
    build_dir = (
        Path(__file__).resolve().parents[2]
        / ".worktrees/builds/a1-my-morning-20260513-164953"
        / "curriculum/l2-uk-en/a1/my-morning"
    )
    if not build_dir.exists():
        pytest.skip("m20 build #3 worktree not present")
    # ... load activities + vocabulary + resources + module.md from the worktree
    # ... call _vesum_gate with a fake verify_words that returns matches for
    #     real Ukrainian lemmas and empty for the previously-leaked fragments
    # ... assert the 11 fragments are no longer in report["missing"]
```

Provide a small helper `_build_fake_verify_words(known: dict[str, bool]) -> Callable` if one doesn't already exist — returns `[{"lemma": w}]` for known words, `[]` for unknown.

---

## Execution steps (numbered)

1. **Inspect current gate to confirm structure hasn't drifted:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13 && grep -nE '_ERROR_CORRECTION_INTENTIONAL_FIELDS|def _activity_vesum_text|def _build_vesum_text|_strip_metalinguistic' scripts/build/linear_pipeline.py | head -10
   ```
   Confirm line numbers approximate brief expectations.

2. **Implement leak 3 first** (1-line addition: `"explanation"` to `_ERROR_CORRECTION_INTENTIONAL_FIELDS`). Run test C.

3. **Implement leaks 1+2** (modify `_activity_vesum_text` to handle bare-list options uniformly: skip-all for fill-in, skip-non-answer for quiz/match-up/true-false). Run tests A+B.

4. **Implement leak 4** (add `_strip_usage_parentheticals` helper, call in `_build_vesum_text` vocabulary loop). Run test D.

5. **Add integration test E** for m20 build #3 replay.

6. **Run full linear_pipeline test suite:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/pytest tests/build/test_linear_pipeline.py -v 2>&1 | tail -30
   ```
   Quote summary line. Must show all new tests passing + existing tests still green. Per #M-7, pytest locally before push.

7. **Lint:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13 && /Users/krisztiankoos/projects/learn-ukrainian/.venv/bin/ruff check scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py 2>&1 | tail -5
   ```
   Quote final line.

8. **Commit:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13 && git add -A && git commit -m "$(cat <<'INNEREOF'
   fix(vesum_gate): scope extraction across 4 leak surfaces (#1962 gate 1)

   m20 (a1/my-morning) V7 build #3 halted at vesum_verified after ADR-008
   correction. 11 reported missing forms were ALL legitimate
   non-Ukrainian-assertion contexts the gate was over-extracting:

   1. fill-in bare-list options (юся, єшся, ється, теся, ємося, єтеся,
      ються) — morphological suffix fragments by design, never VESUM
      lemmas.
   2. quiz bare-list non-answer options (п'юся) — fabricated wrong-form
      distractors.
   3. error-correction explanation field (Завтрак, користу-) —
      explanations always contextualize the wrong form being criticized.
   4. vocabulary usage parenthetical (стем) — English meta-linguistic
      term inside Ukrainian sample sentence parenthetical.

   Fixes per surface:
   - Add `explanation` to _ERROR_CORRECTION_INTENTIONAL_FIELDS.
   - Extend _activity_vesum_text to skip bare-list options entirely for
     fill-in and to skip non-answer options for quiz/match-up/true-false.
   - Add _strip_usage_parentheticals helper called in _build_vesum_text
     vocabulary usage path.

   5 regression tests added covering each leak + an integration replay
   of m20 build #3's actual artifacts.

   Closes #1962 gate 1. Gates 2-4 (citations_resolve, l2_exposure_floor,
   long_uk_ceiling) remain — they interact and deserve joint design.

   X-Agent: codex/vesum-gate-scope-2026-05-13

   Co-Authored-By: Codex GPT-5.5 <noreply@openai.com>
   INNEREOF
   )"
   ```

9. **Push branch:**
   ```bash
   cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13 && git push -u origin codex/vesum-gate-scope-2026-05-13
   ```

10. **Open PR (NO auto-merge):**
    ```bash
    cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/vesum-gate-scope-2026-05-13 && gh pr create --title "fix(vesum_gate): scope extraction across 4 leak surfaces (#1962 gate 1)" --body "$(cat <<'INNEREOF'
    ## Summary

    - Adds \`explanation\` to \`_ERROR_CORRECTION_INTENTIONAL_FIELDS\` (leak 3).
    - Extends \`_activity_vesum_text\` to skip bare-list \`options:\` for \`type: fill-in\` and to skip non-\`answer\` entries in bare-list \`options:\` for \`type: quiz\` / \`match-up\` / \`true-false\` (leaks 1+2).
    - Adds \`_strip_usage_parentheticals\` helper called in \`_build_vesum_text\` vocabulary loop (leak 4).
    - 5 regression tests covering each leak surface + an integration replay of m20 build #3's actual artifacts.

    ## Why

    m20 V7 build #3 halted at \`vesum_verified\` after ADR-008 correction. All 11 reported missing forms were legitimate non-Ukrainian-assertion contexts (suffix fragments in fill-in options, distractor wrong-forms in quiz options, capitalized wrong-form references in error-correction explanations, English meta-linguistic terms in vocabulary usage parentheticals). The fix tightens gate scope without weakening the gate's real job (verifying actual Ukrainian-text assertions).

    ## Test plan

    - [x] \`pytest tests/build/test_linear_pipeline.py -v\` — all green including 5 new tests
    - [x] \`ruff check\` — clean
    - [ ] Follow-up: orchestrator re-runs m20 V7 build (#4) post-merge to confirm gate now passes

    Closes #1962 gate 1. Gates 2-4 deserve joint design — not in this PR's scope.

    🤖 Generated with [Codex CLI](https://github.com/openai/codex-cli)
    INNEREOF
    )"
    ```

11. **Do NOT merge.** Print PR URL via `gh pr view --json url`.

---

## Acceptance criteria

- [ ] Branch pushed; PR opened; URL printed.
- [ ] `pytest tests/build/test_linear_pipeline.py -v` shows 5 new tests passing + all existing tests green.
- [ ] `ruff check` clean.
- [ ] Commit body has `Closes #1962 gate 1` + X-Agent trailer.

## On halt

- The current `_activity_vesum_text` structure has refactored heavily → adapt the bare-list-options + answer-aware logic to the new shape, but keep the leak fixes' SEMANTICS intact.
- The m20 build worktree at `.worktrees/builds/a1-my-morning-20260513-164953/` is gone → make test E skip cleanly.
- Existing tests regress (especially `test_vesum_gate_skips_nested_error_subtree_in_error_correction` or `test_run_python_qg_passes_structural_fixture`) → quote the failures; you may have over-broadened the skip. Tighten and retry.
- Pre-existing failures (e.g. the #1958 stale-assertion tests `test_a1_20_plan_context_matches_phase_4_contract` + `test_no_writer_rewrite_in_correction`) → ignore. Quote them in your final report but don't try to fix them.

Do not deviate from the 4-leak, 5-test, 1-PR structure. Joint design on gates 2-4 is the orchestrator's next move; not in scope here.
