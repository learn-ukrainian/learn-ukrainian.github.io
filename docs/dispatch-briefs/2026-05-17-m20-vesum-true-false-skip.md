# Dispatch brief — VESUM gate: skip true-false statements when answer=false (#2104)

## Root cause (m20 build #19)

`_activity_vesum_text` at `scripts/build/linear_pipeline.py` walks activity fields and excludes intentional-wrong content. PR #2103 just added handling for:
- error-correction `error`/`errorWord`/`sentence` fields (existed before)
- quiz `correctAnswer` field (new in PR #2103)

But it does NOT handle **true-false** activities where the `statement` field contains intentionally-wrong content when `answer: false`. m20 build #19 evidence:

```yaml
- id: act-7
  type: true-false
  items:
  - statement: The verb «дивитися» has «я дивюся» in the 1st person singular.
    answer: false   # ← statement contains intentionally fabricated form
```

`vesum_verified.missing = ["дивюся"]` — leaked from the statement above.

## Fix

In `_activity_vesum_text`, add handling for `true-false` activity items:

- If item has `answer: false`, skip the item's `statement` field (intentionally wrong claim — may contain fabricated forms).
- If item has `answer: true`, scan the statement (valid claim — Ukrainian content).
- Items without an explicit `answer` should fail soft (treat as scan-the-statement OR skip — pick the conservative option that matches existing fill-in/quiz behavior — likely skip-the-statement since wrong content shouldn't pollute VESUM either way).

Implementation hint: follow the same pattern as `walk_answer_options` at the existing line ~5290. Add a `walk_truefalse_statement` helper that checks `answer` and decides whether to walk the statement string.

## Verification

```bash
# venv symlinked into worktree by delegate.py
.venv/bin/pytest tests/build/test_linear_pipeline.py -k vesum -v
git diff --stat main
.venv/bin/python -m pre_commit run --files scripts/build/linear_pipeline.py tests/build/test_linear_pipeline.py
```

## Regression test

Add to `tests/build/test_linear_pipeline.py`:

- true-false item with `answer: false` and statement containing fabricated form → form NOT in walker output.
- true-false item with `answer: true` and statement containing valid Ukrainian → valid words DO appear in walker output.

## Worktree + PR + commit

```bash
cd /Users/krisztiankoos/projects/learn-ukrainian
git fetch origin
git worktree add .worktrees/m20-vesum-truefalse -b fix/m20-vesum-skip-truefalse-false-statements origin/main
cd .worktrees/m20-vesum-truefalse
```

Standard commit + push + `gh pr create` flow, single file (+ test), conventional commit message referencing #2104.

NO auto-merge. Anti-fabrication: quote pytest raw output.

## Out of scope

- Do NOT touch error-correction or quiz logic (PR #2103 already handled those).
- Do NOT add wiki_manifest scope changes (separate concern).
- Do NOT change writer prompt.
