# Dispatch brief: D4 decision-lineage backlink scanner (#1785)

> **Issue:** #1785. Single PR closes the issue.
> **Scope:** ~150-200 LOC + tests + Monitor API endpoint. Single PR.
> **Agent:** Codex
> **Worktree:** mandatory.

## Worktree instructions (mandatory)

```bash
.venv/bin/python scripts/delegate.py dispatch \
    --agent codex --mode danger --worktree --base origin/main \
    --task-id codex-1785-d4-decision-lineage \
    --prompt-file docs/dispatch-briefs/2026-05-08-night/1785-d4-decision-lineage.md
```

## What to build

Standalone read-only tool that walks `docs/decisions/**/*.md` + scans `git log` to populate "Influenced" backlinks per decision. Multi-alias scan (filename, title, ADR-NNN shorthand, decision IDs, PR refs). Exposes via Monitor API + CLI. Paradigm-independent — useful even if the kubedojo Decision Graph view never lands.

## Full AC list

Copied from issue #1785 (these are the exact AC; do not silently relax):

1. Walk `docs/decisions/**/*.md` and emit one record per file
2. For each file, scan `git log --all -p` for commits that touched the file path OR mention any of these alias forms:
   - Filename slug (e.g. `2026-05-06-multi-ui-channel-participation`)
   - Title (from first `# heading` line)
   - `ADR-00N` shorthand
   - Decision IDs (whatever convention the file declares in frontmatter)
   - PR references that touch the file path
3. Output JSON: `{decision_id, file_path, aliases[], commits[], prs[], first_cited_at, last_cited_at}`
4. Expose via Monitor API endpoint `/api/decisions/lineage` (read-only)
5. CLI: `.venv/bin/python scripts/audit/decision_lineage.py [--decision-id X]`
6. Add a test fixture with 2 decision files + 3 fake commits referencing them in different alias forms; assert the scanner finds all 3
7. Update `docs/SCRIPTS.md` with the new script
8. Conform to `cli-help-standard.md` (description, epilog with examples, arg help, exit codes, related)

## Reference files

- `docs/decisions/INDEX.md` — existing decision index
- `scripts/audit/check_decisions.py` — existing decision-staleness checker (use the same module conventions)
- `docs/decisions/pending/README.md` — pending-decision protocol
- `scripts/api/state_router.py` (or similar) — find the right place to wire `/api/decisions/lineage`
- Monitor API conventions: read 1-2 existing endpoints to match style

## Numbered execution steps

1. `git worktree add` — handled by delegate runner.
2. Read `docs/decisions/INDEX.md` and 3-5 actual decision files to understand the corpus.
3. Read `scripts/audit/check_decisions.py` for module/argparse conventions.
4. Find the Monitor API router and look at 2 existing read-only endpoints for style.
5. Read `cli-help-standard.md`.
6. Implement scanner module with these phases:
   - Phase 1: walk files, parse frontmatter + first-heading
   - Phase 2: build alias lookup (filename, title, ADR-N shorthand, declared IDs)
   - Phase 3: `git log --all --name-only --grep=ADR-...` plus broader `git log --all -p -G '<alias>'` (be efficient — one git log call with multi-alias regex preferred over N separate calls)
   - Phase 4: aggregate into JSON shape
7. CLI wrapper at `scripts/audit/decision_lineage.py`.
8. Monitor API endpoint at `/api/decisions/lineage` (returns the same JSON; cache OK).
9. Tests with fixture repo (use `tmp_path` + `subprocess.run('git', 'init')` + 2 decision MDs + 3 fake commits).
10. Update `docs/SCRIPTS.md`.
11. `ruff check` clean.
12. `.venv/bin/pytest tests/audit/test_decision_lineage.py -x`.
13. **Validation pass**: run `scripts/audit/decision_lineage.py` on the live repo. Verify ADR-008 (the most-cited one) shows >5 commits, > 0 PR refs, and includes all alias forms it's been cited under.
14. Commit: `feat(audit): D4 decision-lineage backlink scanner with multi-alias support (#1785)`
15. `git push -u origin codex-1785-d4-decision-lineage`
16. `gh pr create` with title + body + AC checklist + validation-pass output snippet (e.g. "ADR-008 has 7 commits + 3 PR refs spanning 5 alias forms").
17. **Do NOT auto-merge.** Report PR URL.

## Out of scope

- No UI integration — that's a future kubedojo D3-style PR.
- No write access — read-only scanner only.
- Don't touch existing `check_decisions.py` (Boy Scout it only if you find something obviously broken in scope).

## Why this matters

D4 is the foundation for the future Decision Graph view (kubedojo's offered D3 PR). Even without UI, it gives us "who cited this decision" data for triage of stale ADRs and lets us close the loop on "did anyone actually build on this decision after we shipped it?"
