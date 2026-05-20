# Dispatch brief — backfill `references[].title` across all seminar plans

**Agent:** gemini
**Mode:** workspace-write (with `--worktree` enforced)
**Task ID:** `seminar-refs-title-backfill-20260521`

## Why now

Issue #2164. Plan validator at `scripts/build/linear_pipeline.py:768` rejects any plan where any ref dict lacks `title:`. Inventory across HIST + BIO + most LIT plans: **3,684 refs missing title across 1,124 plan files. Only 0 HIST plans, 1 BIO, 3 LIT pass `validate_plan` today.** This blocks ANY writer (gemini-tools, codex-tools, claude-tools, future agy) from running against ~95% of seminar plans. Fixing this is the prerequisite for the seminar-writer ADR to lock with an empirical baseline.

## Scope

In each seminar plan (`curriculum/l2-uk-en/plans/{hist,bio,istorio,lit,lit-essay,lit-hist-fic,lit-fantastika,lit-war,lit-humor,lit-youth,lit-doc,lit-drama,lit-crimea,oes,ruth,folk}/*.yaml`):

For every entry in the `references:` list that is a dict and lacks a non-empty `title:` field, derive a title from existing fields. Do NOT change refs that already have `title`. Do NOT touch other fields.

## Derivation rules (apply in this order — first match wins)

Inventory of shapes (descending frequency):

```
2363  keys=('author', 'note', 'type', 'work')           → title = work
 951  keys=('note', 'path', 'type')                      → title = derived from path
  84  keys=('name', 'notes', 'type', 'url')              → title = name
  70  keys=('name', 'note', 'type', 'url')               → title = name
  52  keys=('author', 'note', 'type', 'url', 'work')     → title = work
  39  keys=('note', 'type', 'work')                      → title = work
  36  keys=('note', 'type', 'url')                       → title = derived from url
  23  keys=('note', 'type', 'url', 'work')               → title = work
  11  keys=('note', 'path', 'type', 'work')              → title = work
  11  keys=('author', 'note', 'path', 'type', 'work')    → title = work
  11  keys=('name', 'note', 'type')                      → title = name
   8  keys=('note', 'source', 'type', 'url')             → title = derived from url
   7  keys=('note', 'source', 'type')                    → title = source
   3  keys=('name', 'type', 'url')                       → title = name
   3  keys=('author', 'note', 'type')                    → title = note (fallback)
   2  keys=('name', 'note', 'path', 'type')              → title = name
   2  keys=('author', 'notes', 'type', 'work')           → title = work
   2  keys=('note', 'source_url', 'type')                → title = derived from source_url
   1  + smaller shapes                                   → see fallback below
```

**Implementation order (first non-empty wins):**

1. If `ref.get("work")` is a non-empty string → `title = work`.
2. Else if `ref.get("name")` is non-empty → `title = name`.
3. Else if `ref.get("source")` is non-empty → `title = source`.
4. Else if `ref.get("path")` is non-empty → derive from path:
   - If path is a URL (starts with `http://` / `https://`) → use last URL path segment, replace `_` and `-` with space, Title Case Words. Strip a `.md` / `.html` / `.htm` suffix.
   - Else (filesystem-relative wiki path like `wiki/hist/figures/petro-sahaidachnyi.md`): take basename, drop `.md`, replace `-` with space, Title Case Words.
5. Else if `ref.get("url")` or `ref.get("source_url")` is non-empty → use the URL path segment (same transform as 4, on the last segment of the URL path).
6. Else (last resort) → use first 80 chars of `ref.get("note")` with trailing ellipsis if truncated.

For wiki refs with Ukrainian content in the `note:` field, prefer the path-derived title (rule 4) over the note (rule 6) — paths are stable, notes are descriptive.

## What NOT to touch

- CORE plans (a1, a2, b1, b2, c1, c2) — only the seminar levels listed above.
- Refs that already have non-empty `title:` (idempotent).
- Other plan fields (focus, phase, sequence, content_outline, etc.).
- Non-dict entries in references (skip with a warning).
- YAML formatting where possible — preserve key order; YAML safe-dump with `allow_unicode=True, sort_keys=False, default_flow_style=False, width=10**9` to keep lines unwrapped.

## Verifiable claims (per #M-4 — every claim in your PR body needs a tool call)

| Claim | Command |
|---|---|
| "Files modified count" | `git -C .worktrees/gemini/seminar-refs-title-backfill diff --name-only origin/main | wc -l` |
| "Refs backfilled count" | A small Python one-liner that compares before/after across all seminar plans, counting refs that gained a title |
| "All seminar plans now pass validate_plan" | `.venv/bin/python -c "from pathlib import Path; from scripts.build.linear_pipeline import plan_check; [plan_check(p) for p in Path('curriculum/l2-uk-en/plans').glob('**/*.yaml') if p.parent.name in {'hist','bio','istorio','lit','lit-essay','lit-hist-fic','lit-fantastika','lit-war','lit-humor','lit-youth','lit-doc','lit-drama','lit-crimea','oes','ruth','folk'}]; print('OK')"` |
| "ruff clean on new test file" | `.venv/bin/ruff check tests/curriculum/test_seminar_plan_refs_titles.py` |
| "pytest passes" | `.venv/bin/pytest tests/curriculum/test_seminar_plan_refs_titles.py -v` |

## Required test

`tests/curriculum/test_seminar_plan_refs_titles.py`:

1. `test_all_seminar_plans_pass_validate_plan` — iterates every plan in the seminar levels, calls `linear_pipeline.plan_check`, asserts no LinearPipelineError. This is the load-bearing regression test for #2164.
2. `test_backfilled_titles_match_derivation_rules` — for one representative plan from each major shape (work-based, name-based, wiki-path-based), check the title is what rule 1-5 would produce.

## Pre-submit checklist

1. `git worktree add .worktrees/gemini/seminar-refs-title-backfill -b fix/seminar-refs-title-backfill` (from main project dir). The branch-switch guard hook explicitly allows `git worktree add -b`.
2. `cd .worktrees/gemini/seminar-refs-title-backfill`
3. Write the backfill script at `scripts/curriculum/backfill_seminar_ref_titles.py` (or inline if simple enough — the script is just a tool, the DELIVERABLE is the YAML diff). Document the derivation rules in the script docstring.
4. Run the script. Verify with the validate_plan check above. Iterate until all seminar plans pass.
5. Write the test file at `tests/curriculum/test_seminar_plan_refs_titles.py`.
6. `.venv/bin/pytest tests/curriculum/test_seminar_plan_refs_titles.py -v` → green.
7. `.venv/bin/ruff check scripts/curriculum/backfill_seminar_ref_titles.py tests/curriculum/test_seminar_plan_refs_titles.py` → clean.
8. `.venv/bin/pytest tests/build/test_linear_pipeline.py -v` → still green (no regressions on plan validator tests).
9. `git add curriculum/l2-uk-en/plans/ scripts/curriculum/backfill_seminar_ref_titles.py tests/curriculum/test_seminar_plan_refs_titles.py` — targeted.
10. `git commit -m "fix(curriculum): backfill references[].title across all seminar plans (closes #2164)"`.
11. `git push -u origin fix/seminar-refs-title-backfill`.
12. `gh pr create --title "fix(curriculum): backfill references[].title across all seminar plans (closes #2164)" --body ...` — DO NOT auto-merge.

## Hard constraints

- DO NOT modify CORE plans (a1, a2, b1, b2, c1, c2).
- DO NOT modify any non-`references` field of any plan.
- DO NOT change file encoding, line endings, or comment placement.
- DO NOT delete the existing `.worktrees/builds/*` test data.
- The backfill script must be idempotent (running twice produces no diff).

## Sample data already verified

| Plan | Original ref | Expected title |
|---|---|---|
| `hist/afhanistan.yaml` | `{path: 'wiki/hist/soviet-ukraine/afghan-war.md', note: ..., type: wiki}` | `Afghan War` |
| `hist/afhanistan.yaml` | `{author: 'Serhii Plokhy', work: 'The Gates of Europe', ...}` | `The Gates of Europe` |
| `hist/andrusivske-peremyrya.yaml` | `{work: 'Літопис Самовидця', path: 'http://litopys.org.ua/...', ...}` | `Літопис Самовидця` |
| `lit-drama/lesia-ukrainka-dramatic-legacy.yaml` | `{name: 'Тексти та аналіз творів Лесі Українки', ...}` | `Тексти та аналіз творів Лесі Українки` |
| `bio/olena-pchilka.yaml` | `{url: 'https://uk.wikipedia.org/wiki/Олена_Пчілка', note: ...}` | `Олена Пчілка` (URL last segment, underscores→spaces) |

The first three are the dominant shapes (work / wiki-path / work-with-path) and together cover ~85% of refs.
