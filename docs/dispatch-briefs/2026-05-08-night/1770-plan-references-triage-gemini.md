# Dispatch brief: #1770 plan-references triage — 32 plans citing missing textbooks

> **Issue:** #1770. Single triage report — paper work, no code.
> **Scope:** Read 32 plan files, the audit report, and `docs/dictionary-pipeline-status.md`. Produce per-plan A/B/C verdict.
> **Agent:** Gemini (curriculum/pedagogy domain knowledge)
> **Worktree:** mandatory.

## Worktree instructions (mandatory)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent gemini --mode danger --worktree --base origin/main \
    --task-id gemini-1770-plan-references \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1770-plan-references-triage-gemini.md
```

Lands in `.worktrees/dispatch/gemini/gemini-1770-plan-references`.

## Context

PR #1765 added a plan-review check that requires every `references:` entry in plan YAMLs to resolve against the textbook corpus in `data/sources.db`. After #1765 lands, plans citing un-ingested textbooks fail plan-review and block their modules from building.

The audit at `audit/plan-references-coverage-2026-05-07.md` lists **32 plans citing missing textbooks**. Most missing references concentrate on Grade 4 (`Заболотний`, `Кравцова`, `Варзацька`, `Пономарьова`, `Большакова`, `Вашуленко`) — these are likely real, accessible textbooks we should ingest, not fabrications.

## What to write

A single triage report at `audit/plan-references-triage-2026-05-08.md` with:

1. **Per-plan verdict** in a table. Three options:
   - **A — Ingest** the textbook into `data/sources.db` (use the dictionary-pipeline workflow). Best when the textbook is real, accessible, and pedagogically sound for the citation.
   - **B — Amend** the plan to cite an in-corpus textbook with equivalent pedagogical coverage. Best when an equivalent in-corpus textbook exists.
   - **C — Defer** the plan (mark blocked) until the textbook is ingested. Use when neither A nor B is feasible right now.

2. **Per-textbook recommendation** (consolidated):
   - List each unique missing textbook (~10-15 distinct ones, since same textbook is cited from multiple plans)
   - For each: provide ingestion priority (HIGH / MED / LOW) based on how many plans cite it × CEFR level × A1/A2/B1 priority per #1577
   - Note availability: do you know if it's accessible? Public PDF? Already in `docs/references/private/` or `data/textbooks/`? If unsure, mark "TBD — user to verify availability"

3. **Recommended action plan**:
   - Group A plans (ingest needed) by textbook → which textbooks should we ingest first to unblock the most plans
   - Group B plans (amendable) → suggest a specific replacement citation per plan with rationale
   - Group C plans (deferred) → list them for later

4. **Cross-reference with #1577 EPIC priority**:
   - Mark every A1, A2, B1 plan with `[A1-PRIORITY]`, `[A2-PRIORITY]`, `[B1-PRIORITY]` tags
   - These take precedence in the action plan

## Acceptance criteria

1. Report at `audit/plan-references-triage-2026-05-08.md`, ~200-400 lines markdown
2. All 32 plans triaged with explicit A/B/C verdict
3. Each verdict has a 1-2 sentence rationale citing the plan + textbook + alternatives considered
4. Per-textbook ingestion priority recommendations
5. Action plan section that names what would unblock the most A1/A2/B1 modules
6. Single PR landing the file

## Numbered execution steps

1. `git worktree add` — handled by delegate runner.
2. Read `audit/plan-references-coverage-2026-05-07.md` (full list of 32).
3. Read `docs/dictionary-pipeline-status.md` for ingestion process awareness.
4. Read `docs/references/private/` directory listing if accessible — see what textbooks we already have offline.
5. Read `data/textbooks/` listing — what's already loaded (gitignored, so just `ls -la data/textbooks/ | head -50` to see filenames).
6. For 5-10 representative plans, read the plan YAML to understand context (e.g. `curriculum/l2-uk-en/plans/a1/my-morning.yaml`).
7. Cross-reference the missing textbooks with the 81 in-corpus ones (you can list via `mcp__sources__collection_stats` or by querying the DB).
8. Triage all 32 plans and write the report.
9. Verify the file lints clean as markdown (basic check).
10. Commit: `docs(audit): #1770 plan-references triage (32 plans, A/B/C verdict per plan)`
11. `git push -u origin gemini-1770-plan-references`
12. `gh pr create` with title + body summary linking to the report.
13. **Do NOT auto-merge.** Report PR URL.

## Out of scope

- Don't actually ingest any textbook — that's a follow-up if user approves Option A for any plan.
- Don't modify any plan YAML — that's follow-up Option B work, separate PR.
- Don't write new plans.
- Don't cross-check `references:` formats — that's #1778's scope.

## Key constraint

This is a **triage report**, not an implementation. The output is a decision document for the user / next session to act on. Be specific about WHY each plan goes A/B/C — vague verdicts are useless.

If you find ambiguity (e.g. "is this textbook real?"), mark TBD and explain what evidence would resolve it. Do not silently guess.
