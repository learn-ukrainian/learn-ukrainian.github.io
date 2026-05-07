# Codex dispatch brief — #1765 plan-review-time corpus check

> **Worktree:** `.worktrees/dispatch/codex/1765-plan-review-corpus`
> **Branch:** `codex/1765-plan-review-corpus`
> **Base:** `main`
> **Mode:** danger
> **Effort:** medium
> **Hard timeout:** 5400s
> **Silence timeout:** 1800s

## Worktree setup

```bash
git worktree add -b codex/1765-plan-review-corpus .worktrees/dispatch/codex/1765-plan-review-corpus
cd .worktrees/dispatch/codex/1765-plan-review-corpus
```

## Goal

Closes #1765. PR #1757 (just merged at `28b7ceff8c`) made the textbook-grounding gate REJECT missing-corpus citations at module-build time. That's correct for the project promise, but creates a permablock if a plan happens to cite an out-of-corpus textbook. The right layer to catch this is **plan-review** — before the writer wastes compute generating a doomed module.

## Implementation

1. **Locate the plan validator.** Search for `plan_review.py`, `validate_plan`, or where plans are checked. Likely `scripts/plan_review.py` or similar (`grep -rn "validate_plan\|plan_review" scripts/`). If no validator exists, find the entry point where plans are loaded into the pipeline (`scripts/build/v7_build.py`?) and add the check there.

2. **Implement the check.** For each entry in `plan.references[]`:
   - Look up the textbook source in the corpus (likely `sources_db` SQLite — find the right query path; might already have a helper from #1757's gate work).
   - If absent, fail plan-validation with a clear error: `"Plan references unknown textbook: '{source_name}'. Known textbooks in corpus: {list-or-pointer-to-list}. To add this textbook, see docs/dictionary-pipeline-status.md."`

3. **Document it.** Create `docs/best-practices/plan-references.md` with:
   - The rule: "All cited textbooks MUST be present in `sources_db` at plan-review time."
   - Why: prevents shipping content with unverifiable citations (real textbook grounding promise).
   - How to handle a missing textbook: file an ingestion request via the documented pipeline.

4. **Tests:**
   - `test_plan_review_rejects_unknown_textbook`: feed a plan with one in-corpus + one out-of-corpus reference. Assert plan-review fails with the specific missing-source name.
   - `test_plan_review_passes_with_only_in_corpus_refs`: positive case.
   - `test_plan_review_handles_empty_references`: behavior unchanged if `references: []` (likely PASS for now — that's a separate concern tracked in PR #1757's gate).

5. **Audit existing plans.** Run the new check across all existing plans in `curriculum/l2-uk-en/plans/` and `curriculum/l2-uk-en/{level}/plans/`. Output a summary file `audit/plan-references-coverage-2026-05-07.md` listing which (if any) plans cite missing textbooks. **Don't auto-fix anything**; this is just a coverage report.

## Validation

```bash
.venv/bin/pytest tests/test_plan_review.py -v  # or the relevant test file
.venv/bin/ruff check $(git diff --name-only origin/main..HEAD --diff-filter=ACM | grep '\.py$')
```

## PR

Title: `feat(plan-review): reject plans citing textbooks not in sources_db (#1765)`

PR body must include:
- Why this layer is correct (cite #1757's BLOCK_PEDAGOGY synthesis on PR comment)
- Confirmation that the gate at module-build time still REJECTs as a safety net
- Audit report of existing plans (link to `audit/plan-references-coverage-2026-05-07.md`)
- `Closes #1765`

**NO auto-merge.** Orchestrator (Claude) reviews + merges.
