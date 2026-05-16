# Dispatch brief — #2018 activity_schema gate (m20 GREEN unblocker)

> **Owner:** Codex
> **Filed:** 2026-05-16
> **Scope:** Add a structural `_activity_schema_gate` in
> `scripts/build/linear_pipeline.py` that runs BEFORE `vesum_verified` and
> rejects activity items with non-canonical field names, with a
> writer-facing error message listing the offending field + the
> canonical alternative. This is the m20 GREEN unblocker per issue #2018.

---

## Why this matters

Per issue #2018: the V7 claude-tools writer keeps emitting non-canonical
inner field names for `error-correction` activity items
(`incorrect:` / `wrong:` / `mistake:` instead of canonical `error:`),
leaking the deliberate misspelling into `vesum_verified` as a false
positive. Three consecutive m20 builds (#6, #7, #8) failed on this
pattern despite progressively strengthened prompt rules including an
explicit 12-alias FORBIDDEN list.

The diagnosis (from #2018):

> Prompt iteration alone is the wrong layer. The writer keeps finding
> new aliases (build #6 used `incorrect:`, build #7 used `wrong:`,
> build #8 reverted to `incorrect:`).
>
> The strict YAML parser at `scripts/yaml_activities.py:_parse_error_correction`
> already requires `sentence:` and `error:` fields — but it only runs at
> MDX-render time, AFTER the python_qg gates fire, so the writer doesn't
> get a feedback signal to fix the field-name choice before the build halts.

The fix is structural: a deterministic gate that runs first and gives
the writer a clean, actionable error message in the correction round.

## Scope (concrete)

### Files to touch

- `scripts/build/linear_pipeline.py` — add `_activity_schema_gate()`
  and register it as the FIRST python_qg gate (before `vesum_verified`).
- Probably `scripts/yaml_activities.py` or wherever the
  `_ACTIVITY_AUTHORING_FIELDS` registry lives — extract a shared
  per-type whitelist if one exists; reuse don't duplicate.
- `tests/test_linear_pipeline.py` (or a new
  `tests/test_activity_schema_gate.py`) — add 4-6 unit tests covering
  pass/fail cases.

### What the gate does

1. Walk each activity item in the `activities` list (input shape: list of dicts).
2. For activities with a typed authoring schema (start with
   `error-correction` since that's the m20 blocker; extend to other
   types as the registry grows), validate every item's keys against
   the per-type whitelist.
3. If any item contains a forbidden alias OR is missing a required
   canonical field, return:
   ```python
   {
       "passed": False,
       "violations": [
           {
               "activity_id": "<activity id or index>",
               "item_index": <int>,
               "offending_field": "incorrect",
               "expected_field": "error",
               "message": "error-correction items must use 'error:' for the misspelled form, not 'incorrect:'"
           },
           ...
       ],
       "checked": <total items checked>,
   }
   ```
4. If all clean: `{"passed": True, "checked": <int>, "violations": []}`.

### Per-type whitelist (canonical fields for `error-correction`)

Authority: read `scripts/yaml_activities.py:_parse_error_correction` to
extract the existing required-fields contract. Don't invent. If the
parser requires `sentence` and `error`, that's the whitelist.

Forbidden aliases (from #2018, verbatim): `wrong`, `incorrect`,
`mistake`, `bad`, `original`, `wrong_form`, `incorrect_form`, `correct`,
`correctAnswer`, `right`, `fix`, `fixed`.

The gate's diagnostic should map each forbidden alias to its canonical
counterpart. Suggested mapping (verify against parser):
- `incorrect` / `wrong` / `mistake` / `bad` / `original` / `wrong_form` / `incorrect_form` → canonical `error`
- `correct` / `correctAnswer` / `right` / `fix` / `fixed` → canonical `correction` (or `answer`, whichever the parser accepts)

### Where in the gate sequence

Find the python_qg gate orchestrator in `linear_pipeline.py` (search
for `_vesum_gate(`, then walk up to find where it's called). Insert
`_activity_schema_gate` BEFORE `_vesum_gate` in the same orchestrator
function. If the activity_schema gate fails, halt python_qg early and
emit the violations as the writer-facing diagnostic — don't run the
later gates (no point checking VESUM if the items are structurally
wrong).

### Writer-facing diagnostic format

The gate's failure message goes back to the writer in the correction
round. It must be ACTIONABLE (writer can read it and immediately know
what to change). Example shape:

```
ACTIVITY_SCHEMA_GATE FAILED: 5 violations

  activity #3 'morning-routine-error-correction' (item 2):
    forbidden field 'incorrect' — use 'error:' for the misspelled form

  activity #3 'morning-routine-error-correction' (item 4):
    forbidden field 'incorrect' — use 'error:' for the misspelled form

  ... (3 more)

Canonical 'error-correction' item shape:
  - sentence: "Я <error> вранці."
    error: "вмиваюся"
    correction: "вмиваюся"  # or 'answer:' depending on parser
```

This goes into whatever telemetry / writer-loop feedback channel the
correction round uses — find it by tracing how `_vesum_gate`'s output
reaches the writer prompt.

## #M-4 deterministic-evidence preamble

| Claim | Required evidence in PR body |
|---|---|
| "Gate function exists and is invoked before vesum_verified" | grep showing the new function + grep showing it's in the gate sequence ahead of `_vesum_gate` |
| "Tests pass" | `pytest tests/test_activity_schema_gate.py -v` (or wherever you put them) raw final summary |
| "No regression" | `pytest tests/ -x -q` raw final summary |
| "Ruff clean" | `.venv/bin/ruff check scripts/build/linear_pipeline.py` raw output |
| "Replicates the m20 #8 failure shape" | A test asserting that an activity item with `incorrect:` field fails the gate with `offending_field=incorrect, expected_field=error` |
| "Commit landed" | `git log -1 --oneline` raw |
| "PR opened" | `gh pr view --json url -q '.url'` raw URL |

## Numbered steps (MANDATORY)

### 1. Worktree (already created by dispatch wrapper)

`.worktrees/dispatch/codex/2018-activity-schema-gate-2026-05-16/` from
`origin/main` at the post-#2019-merge tip. Branch:
`codex/2018-activity-schema-gate-2026-05-16`.

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian/.worktrees/dispatch/codex/2018-activity-schema-gate-2026-05-16
git log -1 --oneline   # verify you're on post-#2019 main
```

### 2. Read the issue + the existing parser contract

```bash
gh issue view 2018
grep -n "_parse_error_correction\|_ACTIVITY_AUTHORING_FIELDS" scripts/yaml_activities.py scripts/build/linear_pipeline.py | head -20
# Read the parser to extract the canonical field contract
```

### 3. Implement `_activity_schema_gate()` in `scripts/build/linear_pipeline.py`

- Place it near `_vesum_gate` (probably just above for code-locality).
- Reuse any existing per-type-field registry; don't duplicate.
- Output shape per the section above.

### 4. Wire it into the python_qg gate sequence

Find the orchestrator (search for `_vesum_gate(` calls — likely one
call site that runs the python_qg gate suite in order). Insert
`_activity_schema_gate(activities)` BEFORE it. On failure, return
early with the schema gate's violations as the failure reason.

### 5. Tests

Add `tests/test_activity_schema_gate.py` (new file) OR append to
`tests/test_linear_pipeline.py` if there's a clear pattern there. At
minimum:

1. `test_canonical_error_correction_passes` — items with `sentence` +
   `error` + `correction` pass.
2. `test_forbidden_alias_incorrect_fails` — items with `incorrect:`
   field fail with the right `offending_field` / `expected_field`.
3. `test_forbidden_alias_wrong_fails` — items with `wrong:` field fail.
4. `test_missing_required_error_field_fails` — items missing `error:`
   key fail with a "missing required" violation.
5. `test_multiple_violations_all_reported` — 3 items each with a
   different forbidden alias all surface in the violations list.
6. `test_non_error_correction_activities_pass_through` — items in
   activities of types that don't have a strict schema (e.g. dialogue,
   reading, vocab) are not affected by the gate.

If you decide a 7th test for the writer-facing diagnostic format is
warranted, add it.

### 6. Verify the m20 #8 failure shape replays

Reproduce the exact failing pattern from #2018 in a test:

```python
def test_replays_m20_build8_failure_shape():
    activities = [{
        "id": "morning-routine-error-correction",
        "type": "error-correction",
        "items": [
            {"incorrect": "Я прокидаєшся о сьомій."},
            {"incorrect": "Я дивюся в дзеркало."},
        ],
    }]
    result = _activity_schema_gate(activities)
    assert result["passed"] is False
    assert any(
        v["offending_field"] == "incorrect"
        and v["expected_field"] == "error"
        for v in result["violations"]
    )
```

This test is the empirical link between the issue and the fix.

### 7. Lint + full test sweep

```bash
.venv/bin/ruff check scripts/build/linear_pipeline.py tests/test_activity_schema_gate.py
.venv/bin/python -m pytest tests/ -x -q
```

Quote raw output. If anything went red that was previously green,
fix or stop and report.

### 8. Commit

```bash
git add scripts/build/linear_pipeline.py tests/
git commit -m "$(cat <<'EOF'
feat(qg): activity_schema gate runs first, rejects forbidden field aliases

Closes #2018 — the m20 GREEN unblocker.

Adds _activity_schema_gate() in linear_pipeline.py and wires it into
the python_qg gate sequence BEFORE _vesum_gate. The new gate validates
that every activity item's inner field names are in the per-type
canonical whitelist (e.g. error-correction items must use 'error:' and
'correction:', not 'incorrect:'/'wrong:'/'mistake:'/etc.).

When the writer emits a forbidden alias, the gate halts python_qg
early and returns a writer-facing diagnostic listing each offending
field with its canonical alternative — instead of letting VESUM
choke on the leaked misspelling and the writer guess what's wrong.

Why structural (not more prompt iteration): per #2018, the writer
prompt's 12-alias FORBIDDEN list still lost to training-induced
defaults across 3 consecutive m20 builds (build #6 incorrect:, #7
wrong:, #8 incorrect: again). Prompt was the wrong layer; the parser
contract at scripts/yaml_activities.py:_parse_error_correction was
already strict but only ran at MDX-render time, after python_qg.
The gate moves that contract earlier in the loop so the writer
gets a clean signal in the correction round.

6 unit tests + 1 m20-#8-replay regression test.

Co-Authored-By: Codex (gpt-5.5)
EOF
)"
```

### 9. Push + open PR (DO NOT auto-merge)

```bash
git push -u origin codex/2018-activity-schema-gate-2026-05-16
gh pr create --base main --title "feat(qg): activity_schema gate runs first, rejects forbidden field aliases (closes #2018)" --body "$(cat <<'EOF'
## Summary

Closes #2018 — the m20 GREEN unblocker.

Adds `_activity_schema_gate()` in `linear_pipeline.py` that runs BEFORE `_vesum_gate` and rejects activity items with non-canonical field names (e.g. `incorrect:` instead of `error:`).

## Why structural (not more prompt iteration)

Per #2018, the writer prompt's 12-alias FORBIDDEN list lost to training-induced defaults across 3 consecutive m20 builds (#6/#7/#8 cycled `incorrect:` → `wrong:` → `incorrect:`). The strict parser at `scripts/yaml_activities.py:_parse_error_correction` was already correct but only ran at MDX-render time, after python_qg gates fired.

This PR moves the parser contract earlier so the writer gets a clean, actionable diagnostic in the correction round.

## Test plan

- [x] 6+ unit tests (paste raw `pytest -v` summary)
- [x] m20 #8 failure-shape replay test (asserts `offending_field=incorrect, expected_field=error`)
- [x] Full pytest sweep clean (paste raw summary)
- [x] `ruff check` clean (paste raw output)

## Verifiable evidence

(Codex must paste raw command + cwd + output for each claim above.)

🤖 Generated with [Codex](https://codex.openai.com)
EOF
)"
```

## Acceptance criteria

- [ ] `_activity_schema_gate()` exists in `scripts/build/linear_pipeline.py`
- [ ] It is invoked BEFORE `_vesum_gate` in the python_qg sequence
- [ ] It rejects items with `incorrect:` field on `error-correction` activities
- [ ] It accepts items with canonical `error:` field
- [ ] All 6+ tests pass; m20-replay test specifically asserts the issue #2018 failure shape
- [ ] No regression in `pytest tests/ -x -q`
- [ ] PR body quotes raw evidence per #M-4

## Out of scope (file as follow-ups, do NOT include)

- Activity schemas for non-`error-correction` types (vocab, dialogue,
  multiple-choice, etc.) — extend incrementally as those types
  surface compliance issues. v1 is `error-correction` only.
- Writer prompt changes — the whole point is that prompt iteration
  doesn't fix this. Don't touch the prompt.
- MDX assembler changes — out of scope.
- A general "schema linter" CLI — overkill for v1.

## Failure modes to avoid

- **Don't silently widen the canonical whitelist.** If the parser
  accepts `error:`, that's the canonical. Don't add `incorrect:` to
  the whitelist as a "compatibility" alias — that defeats the entire fix.
- **Don't rewrite the writer prompt.** Out of scope per above.
- **Don't drop the gate's diagnostic precision.** The writer needs to
  see WHICH item, WHICH field, WHICH canonical alternative.
- **Don't add new MDX assembler code.** Out of scope.

---

*Brief format: MD per #M-2 (ai → ai). Authority: MEMORY DISPATCH-BRIEF
CHECKLIST + #M-4 deterministic-evidence preamble.*
